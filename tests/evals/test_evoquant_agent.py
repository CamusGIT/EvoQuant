"""DeepEval traced single-turn evals for the EvoQuant main agent.

Each golden is one bounded quant-research instruction run through the real
main agent (deepagents/LangGraph graph), traced end-to-end via DeepEval's
LangChain integration (``CallbackHandler`` in the invoke config — subagent
LLM/tool spans propagate automatically).

Run:
    EVOSCIENTIST_EVALS=1 uv run deepeval test run tests/evals/test_evoquant_agent.py \
        --identifier "iterating-on-<purpose>-round-N" --num-processes 3 --ignore-errors

The ``EVOSCIENTIST_EVALS`` guard keeps plain ``uv run pytest`` (the 109-file
unit suite) from collecting — and billing — these LLM-in-the-loop evals.
"""

import os
import shutil
import time
import uuid
from pathlib import Path

import httpx
import pytest

from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.integrations.langchain import CallbackHandler
from deepeval.tracing import observe

from tests.evals.metrics import build_trace_metrics

# Observability: print every outgoing zai request's body size. The 2026-08-21
# smoke died with a 4.5M-token request while the agent state only held
# ~170KB — the growth curve (which call, how fast) is the first diagnostic
# for transport/context failures. Harmless stdout-only.
_orig_httpx_send = httpx.AsyncClient.send
_orig_sync_send = httpx.Client.send
_ZAI_REQ_LOG = Path("/tmp/zai_req_smoke.log")


def _record(request) -> None:
    try:
        url = str(request.url)
        if "z.ai" not in url:
            return
        cl = request.headers.get("content-length", "?")
        body = request.content or b""
        # Fingerprints: message count + biggest single message in the
        # JSON payload (is the bloat from duplicated messages or one
        # giant message?).
        roles = body.count(b'"role"') if body else -1
        with open(_ZAI_REQ_LOG, "a") as fh:
            fh.write(
                f"{time.strftime('%H:%M:%S')} len={cl} "
                f"roles~{roles} body={len(body)}B\n"
            )
    except Exception:  # noqa: BLE001
        pass


async def _logging_send(self, request, **kwargs):
    _record(request)
    resp = await _orig_httpx_send(self, request, **kwargs)
    if resp.status_code == 400:
        with open("/tmp/zai_400_body.json", "wb") as fh:
            fh.write(request.content or b"<chunked/empty-body>")
        with open(_ZAI_REQ_LOG, "a") as fh:
            fh.write(
                f"{time.strftime('%H:%M:%S')} GOT-400 "
                f"body={len(request.content or b'')}B url={str(request.url)[:80]}\n"
            )
    return resp


def _logging_send_sync(self, request, *args, **kwargs):
    _record(request)
    resp = _orig_sync_send(self, request, *args, **kwargs)
    if resp.status_code == 400:
        with open("/tmp/zai_400_body.json", "wb") as fh:
            fh.write(request.content or b"<chunked/empty-body>")
    return resp


httpx.AsyncClient.send = _logging_send
httpx.Client.send = _logging_send_sync

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("EVOSCIENTIST_EVALS"),
        reason="LLM-in-the-loop eval; set EVOSCIENTIST_EVALS=1 (via deepeval test run)",
    ),
    pytest.mark.timeout(2400),  # 40 min per golden: glm-5.2 single calls run
    # 4-5 min (reasoning 40-100KB); a light task needs 7+ model calls
]

EVAL_DIR = Path(__file__).parent
FIXTURE_WS = EVAL_DIR / "fixtures" / "workspace"
DATASET_PATH = EVAL_DIR / ".dataset.json"

if not DATASET_PATH.exists():
    pytest.skip(
        "tests/evals/.dataset.json not generated yet; run deepeval generate first",
        allow_module_level=True,
    )
if not FIXTURE_WS.exists():
    pytest.skip(
        "tests/evals/fixtures/workspace snapshot missing; "
        "run tests/evals/fixtures/sync_from_source.sh first",
        allow_module_level=True,
    )

dataset = EvaluationDataset()
dataset.add_goldens_from_json_file(file_path=str(DATASET_PATH))

# Single-golden smoke/debug selector: `deepeval test run` has no -k passthrough,
# so EVOQUANT_SMOKE=<substring> filters goldens by input text instead.
_smoke_filter = os.environ.get("EVOQUANT_SMOKE", "")
if _smoke_filter:
    dataset.goldens = [
        g
        for g in dataset.goldens
        if _smoke_filter.lower() in (g.input or "").lower()
    ]


@pytest.fixture(scope="module")
def trace_metrics():
    """Lazily build the metric list — needs DEEPSEEK_API_KEY at run time."""
    return build_trace_metrics()


def _eval_config():
    """Effective app config with eval-forced flags.

    Both flags are required: ``auto_approve`` removes
    HumanInTheLoopMiddleware (EvoQuant/EvoQuant.py, ``if not cfg.auto_approve``)
    and ``auto_mode`` removes AskUserMiddleware (``... and not cfg.auto_mode``).
    Neither implies the other, and neither is env-mappable — cli_overrides is
    the forcing path (EvoQuant/config/settings.py::get_effective_config).
    """
    from EvoQuant.config import get_effective_config

    return get_effective_config(
        cli_overrides={
            # Fixed system-under-test: same model for all 5 iteration rounds,
            # otherwise scores are not comparable.
            "provider": "zai-code",
            "model": "glm-5.2",
            "auto_approve": True,
            "auto_mode": True,
            "enable_async_subagents": False,  # no langgraph dev in evals
            "recursion_limit": 2000,  # cost guard vs the default 1M
            "default_workdir": "",  # never hijack the workspace from user config
            # Same-model fallback entry: transient transport failures (zai
            # gateway dropping a mid-stream response -> RemoteProtocolError /
            # APIConnectionError, which the OpenAI SDK does NOT retry once a
            # stream has started) get one full-call retry on a fresh
            # connection. Without any chain entry ModelFallbackMiddleware is
            # a pass-through and the exception kills the whole run.
            "model_fallbacks": "glm-5.2:zai-code",
        }
    )


def _slim_trace_for_judge(thread_id: str, span_chars: int = 1000) -> None:
    """Cap every span's payload so the judge prompt stays in-window.

    deepeval's trace metrics serialize the WHOLE trace into the judge
    prompt — and each LLM span's input is the full message history of that
    call. A 7-call agent run produced an 11MB / 4.8M-token judge request
    (judge context: 1M), killing every smoke run at the scoring stage. Cap
    each span's payload instead; the tree structure, span names and the
    root trace's input/output (= actual_output the GEvals score) stay
    intact. Non-container leaves (langchain BaseMessage objects) are
    replaced with truncated string reprs — passing them through untouched
    was the 11MB leak. A budget loop re-walks at halved caps until the
    serialized nested dict fits 800KB (HTTP escaping inflates it ~2.5-3x
    more; deepseek's window is 1M tokens).
    """
    from deepeval.tracing import trace_manager

    def _slim(v, limit: int):
        if isinstance(v, str):
            if len(v) <= limit:
                return v
            return v[:limit] + f" ...[truncated, {len(v) - limit} chars omitted]"
        if isinstance(v, list):
            return [_slim(x, max(limit // 2, 200)) for x in v]
        if isinstance(v, dict):
            return {k: _slim(x, max(limit // 2, 200)) for k, x in v.items()}
        if v is None or isinstance(v, (bool, int, float)):
            return v
        # Arbitrary object — e.g. langchain BaseMessage. Its repr carries the
        # full payload (content + reasoning_content), and serialize_to_json
        # later model_dumps it whole, so passing it through untouched kept
        # judge prompts at 11MB. Replace with a truncated string repr.
        s = str(v)
        if len(s) <= limit:
            return v
        return s[:limit] + f" ...[truncated, {len(s) - limit} chars omitted]"

    def _walk(span, limit: int) -> None:
        # Every field that can carry unbounded payload AND has a loose
        # type on the API span. `tools_called` is strongly validated as
        # List[ToolCall] by _convert_span_to_api_span — replacing ToolCall
        # objects with strings crashes the conversion (pydantic
        # model_type error), and tool calls are small anyway. Leave it.
        for field in (
            "input",
            "output",
            "expected_output",
            "context",
            "retrieval_context",
            "error",
        ):
            v = getattr(span, field, None)
            if v is not None:
                setattr(span, field, _slim(v, limit))
        for child in getattr(span, "children", None) or []:
            _walk(child, limit)

    # The judge reads the trace off current_trace_context (same source as
    # assert_test), NOT necessarily off trace_manager.traces — grab both,
    # de-duplicated, and log the shape so a silent no-op can't hide.
    from deepeval.tracing.context import current_trace_context

    targets = []
    ctx_trace = current_trace_context.get()
    if ctx_trace is not None:
        targets.append(ctx_trace)
    for t in trace_manager.traces:
        if t is not ctx_trace:
            targets.append(t)

    # Serialized judge prompt inflates ~2.5-3x more over HTTP (JSON-in-JSON
    # escaping); deepseek's 1M-token window maps to roughly 800KB of
    # nested JSON. Round 0 saw 2.3MB nested -> 6.6MB request -> 400.
    _NESTED_BUDGET = 800_000

    def _nested_json_chars(trace) -> int:
        from deepeval.constants import PYTEST_TRACE_TEST_WRAPPER_SPAN_NAME
        from deepeval.utils import serialize_to_json

        root_for_dfs = trace.root_spans[0]
        if (
            getattr(root_for_dfs, "name", "") == PYTEST_TRACE_TEST_WRAPPER_SPAN_NAME
            and root_for_dfs.children
        ):
            root_for_dfs = root_for_dfs.children[0]
        return len(
            serialize_to_json(
                trace_manager.create_nested_spans_dict(root_for_dfs),
                indent=2,
            )
        )

    log_lines = [f"slim: ctx={type(ctx_trace).__name__ if ctx_trace else None}"]
    for trace in targets:
        n_roots = len(trace.root_spans or [])

        def _tree_size(spans) -> int:
            total = 0
            for s in spans or []:
                total += len(str(getattr(s, "input", "") or "")) + len(
                    str(getattr(s, "output", "") or "")
                )
                total += _tree_size(getattr(s, "children", None))
            return total

        before = _tree_size(trace.root_spans)
        limit = span_chars
        while True:
            for root in trace.root_spans:
                _walk(root, limit)
            try:
                nested_chars = _nested_json_chars(trace)
            except Exception as exc:  # noqa: BLE001
                nested_chars = -1
                log_lines.append(f"  nested measure err: {exc!r}")
                break
            if nested_chars <= _NESTED_BUDGET or limit < 150:
                break
            limit //= 2  # re-walk everything at a tighter cap (idempotent)
        after = _tree_size(trace.root_spans)
        log_lines.append(
            f"  trace={type(trace).__name__} roots={n_roots} "
            f"chars={before}->{after} nested_json={nested_chars} "
            f"final_limit={limit} "
            f"roots_types={[type(r).__name__ for r in trace.root_spans][:5]}"
        )
    with open("/tmp/zai_req_smoke.log", "a") as fh:
        fh.write("\n".join(log_lines) + "\n")


def _run_traced(golden_input: str, workspace: Path, run_async) -> str:
    """Build + invoke the real agent once, traced; returns the thread_id."""
    from EvoQuant.EvoQuant import create_cli_agent
    from EvoQuant.llm.models import get_chat_model
    from EvoQuant.paths import set_workspace_root

    thread_id = str(uuid.uuid4())

    cfg = _eval_config()
    chat_model = get_chat_model(model=cfg.model, provider=cfg.provider)

    # Order matters: memory-dir env override (per-test) -> workspace root ->
    # agent build. set_workspace_root re-reads EVOSCIENTIST_MEMORIES_DIR, and
    # create_cli_agent snapshots MEMORIES_DIR before its own
    # set_active_workspace call.
    os.environ["EVOSCIENTIST_MEMORIES_DIR"] = str(workspace / "memories")
    set_workspace_root(str(workspace))

    agent = create_cli_agent(
        workspace_dir=str(workspace),
        config=cfg,  # pure path: config + chat_model together -> no globals
        chat_model=chat_model,
    )

    @observe(name="evoquant-agent-run")
    async def _main() -> str:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": golden_input}]},
            config={
                "callbacks": [
                    CallbackHandler(
                        thread_id=thread_id, name="evoquant-main-agent"
                    )
                ],
                "configurable": {"thread_id": thread_id},
            },
        )
        # Fail fast on interrupt misconfiguration instead of scoring garbage.
        assert "__interrupt__" not in result, (
            f"graph hit an interrupt: {result.get('__interrupt__')}"
        )
        # The @observe return value becomes the trace's actual_output the
        # judge metrics score — hand them the final assistant text, not the
        # raw LangGraph state dict.
        messages = result.get("messages", []) if isinstance(result, dict) else []
        texts = [
            m.content
            for m in messages
            if getattr(m, "type", "") == "ai" and m.content
        ]
        return texts[-1] if texts else ""

    run_async(_main())
    return thread_id


@pytest.mark.parametrize("golden", dataset.goldens, ids=lambda g: (g.input or "")[:48])
def test_evoquant_single_turn(
    golden: Golden, tmp_path: Path, run_async, trace_metrics
):
    # Fixed corpus + a clean write area per run: copy the snapshot, never
    # mutate it (also keeps xdist workers independent).
    ws = tmp_path / "ws"
    shutil.copytree(FIXTURE_WS, ws)

    thread_id = _run_traced(golden.input, ws, run_async)

    # The pytest plugin keeps the @observe trace alive through the test
    # body; by now it is closed and its spans are assembled into
    # root_spans — trim BEFORE assert_test serializes it into the judge
    # prompts (otherwise 11MB / 4.8M-token judge requests).
    _slim_trace_for_judge(thread_id)

    assert_test(golden=golden, metrics=trace_metrics)
