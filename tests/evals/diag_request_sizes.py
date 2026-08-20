"""Print the content-length of EVERY request sent to zai during an agent run.

The smoke run died with a 4.5M-token request while the SizeProbe callback
(= langchain's view of outgoing messages) only ever saw ~170KB. Something
below the langchain layer — or in a call path without our callbacks —
inflates the actual HTTP body. This patches httpx.AsyncClient.send to log
every zai request's body size, revealing the growth curve (linear vs
exponential) and any hidden aux/background call loops.

Run: uv run python tests/evals/diag_request_sizes.py
"""

import asyncio
import os
import shutil
import time
import uuid
from pathlib import Path

for _line in Path(".env").read_text().splitlines():
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _, _v = _line.partition("=")
        os.environ.setdefault(_k.strip(), _v.strip())

import httpx  # noqa: E402

_orig_send = httpx.AsyncClient.send


async def _logging_send(self, request, **kwargs):
    try:
        url = str(request.url)
        if "z.ai" in url or "zai" in url:
            cl = request.headers.get("content-length", "?")
            print(
                f"[{time.strftime('%H:%M:%S')}] ZAI-REQ {request.method} "
                f"{url[:60]} content-length={cl} "
                f"({int(cl) // 1000 if cl != '?' else '?'}KB)",
                flush=True,
            )
    except Exception:  # noqa: BLE001
        pass
    return await _orig_send(self, request, **kwargs)


httpx.AsyncClient.send = _logging_send

WS = "/tmp/evoquant-diag/ws3"
os.environ["EVOSCIENTIST_MEMORIES_DIR"] = WS + "/memories"
if os.path.exists(WS):
    shutil.rmtree(WS)
shutil.copytree("tests/evals/fixtures/workspace", WS)

from EvoQuant.EvoQuant import create_cli_agent  # noqa: E402
from EvoQuant.config import get_effective_config  # noqa: E402
from EvoQuant.llm.models import get_chat_model  # noqa: E402
from EvoQuant.paths import set_workspace_root  # noqa: E402

GOLDEN_INPUT = (
    "Design a new turnover-based alpha factor for CSI 500 constituents. "
    "Deliver a self-contained factor design document covering: the "
    "economic hypothesis, a precise construction formula, data "
    "requirements, a validation plan (rank IC / ICIR by month, decile "
    "long-short backtest, turnover-cost sensitivity), and known failure "
    "modes. This task does not require the local corpus — reason from "
    "first principles and standard A-share market microstructure. Write "
    "the document as a markdown file in the workspace and summarize it "
    "in your reply."
)


async def main() -> None:
    # DIFFERENTIAL EXPERIMENT: inject the exact same deepeval CallbackHandler
    # the eval harness uses. If the 4.5M-token bloat reproduces here (bare
    # asyncio, no pytest/deepeval plugin env), the handler interaction is the
    # culprit; if not, it's something about the deepeval test-run process.
    from deepeval.integrations.langchain import CallbackHandler

    cfg = get_effective_config(
        cli_overrides={
            "provider": "zai-code",
            "model": "glm-5.2",
            "auto_approve": True,
            "auto_mode": True,
            "enable_async_subagents": False,
            "recursion_limit": 60,  # enough calls to expose the growth curve
            "default_workdir": "",
            "model_fallbacks": "glm-5.2:zai-code",
        }
    )
    model = get_chat_model(model=cfg.model, provider=cfg.provider)
    set_workspace_root(WS)
    agent = create_cli_agent(workspace_dir=WS, config=cfg, chat_model=model)
    t0 = time.time()
    thread_id = str(uuid.uuid4())
    try:
        await agent.ainvoke(
            {"messages": [{"role": "user", "content": GOLDEN_INPUT}]},
            config={
                "callbacks": [
                    CallbackHandler(thread_id=thread_id, name="evoquant-main-agent")
                ],
                "configurable": {"thread_id": thread_id},
            },
        )
        print(f"\n完成 {time.time() - t0:.0f}s")
    except Exception as exc:  # noqa: BLE001
        print(
            f"\n失败 {time.time() - t0:.0f}s: {type(exc).__name__}: "
            f"{str(exc)[:300]}",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
