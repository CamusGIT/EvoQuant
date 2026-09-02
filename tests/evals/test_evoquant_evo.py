"""DeepEval traced single-turn evals for the evo10 suite (quant-adapted).

Adapted from the EvoScientist eval set (``evo(1).jsonl``): 10 goldens across
all 8 categories, content rewritten for the quant domain, schema frozen —
every source key survives and EVOSCI-G087 keeps its missing ``expected_tools``.

Two schema generations intentionally coexist (not unified, per project
decision): the generated golden 12 (``test_evoquant_agent.py``) and this
hand-adapted set. Differences from the golden suite's runner:

- per-golden metric list from ``additional_metadata.primary_metrics``
  (:func:`build_evo_metrics`) instead of one fixed module-level list
- ``expected_tool_sequence`` is richer than the top-level ``expected_tools``
  (carries ``task:<subagent>`` and ordering), so it is pushed onto the
  current trace for the ordering-aware ToolCorrectnessMetric; the golden's
  own ``expected_tools`` remains the fallback through deepeval's trace
  fallback chain
- ``EVOQUANT_SMOKE`` also matches metadata ids (EVOSCI-G###) — the evo10
  inputs are short and share vocabulary, ids are the stable selector

Run (single process — REQUIRED: under xdist the per-worker test-run writers
race and clobber each other, and one worker crash loses its whole batch;
Round 1's 3-process run persisted only 1/10 cases):
    EVOSCIENTIST_EVALS=1 uv run deepeval test run tests/evals/test_evoquant_evo.py \
        --identifier "evo10-quant-baseline-1" --num-processes 1 --ignore-errors

The ``EVOSCIENTIST_EVALS`` guard keeps plain ``uv run pytest`` from
collecting — and billing — these LLM-in-the-loop evals.
"""

import os
import shutil
from pathlib import Path

import pytest

from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import ToolCall
from deepeval.tracing import update_current_trace

from tests.evals.harness import (
    FIXTURE_WS,
    _run_traced,
    _slim_trace_for_judge,
)
from tests.evals.metrics import build_evo_metrics

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("EVOSCIENTIST_EVALS"),
        reason="LLM-in-the-loop eval; set EVOSCIENTIST_EVALS=1 (via deepeval test run)",
    ),
    pytest.mark.timeout(2400),  # same ceiling as the golden suite per golden
]

EVAL_DIR = Path(__file__).parent
DATASET_PATH = EVAL_DIR / ".evo10_dataset.json"

if not DATASET_PATH.exists():
    pytest.skip(
        "tests/evals/.evo10_dataset.json missing (hand-adapted evo10 set)",
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


def _golden_id(golden: Golden) -> str:
    md = golden.additional_metadata or {}
    return str(md.get("id", "")) or (golden.input or "")[:48]


# Single-golden smoke/debug selector: matches input text OR metadata id,
# e.g. EVOQUANT_SMOKE=EVOSCI-G087 (ids are the stable selector for this set).
_smoke_filter = os.environ.get("EVOQUANT_SMOKE", "")
if _smoke_filter:
    _needle = _smoke_filter.lower()
    dataset.goldens = [
        g
        for g in dataset.goldens
        if _needle in (g.input or "").lower() or _needle in _golden_id(g).lower()
    ]
    if not dataset.goldens:
        raise RuntimeError(
            f"EVOQUANT_SMOKE={_smoke_filter!r} matched no evo10 goldens; "
            "check the filter instead of silently running zero tests"
        )


def _seq_to_tool_calls(seq: list[str]) -> list[ToolCall]:
    """`task:planner-agent` -> ToolCall(task, {subagent_type: planner-agent}).

    Input parameters are carried for traceability; ToolCorrectnessMetric
    compares tool names only (input-parameter comparison stays off — the
    key-union overlap dilutes real calls to ~0.5).
    """
    calls = []
    for token in seq:
        name, _, sub = token.partition(":")
        params = {"subagent_type": sub} if sub and name == "task" else None
        calls.append(ToolCall(name=name, input_parameters=params))
    return calls


@pytest.mark.parametrize("golden", dataset.goldens, ids=_golden_id)
def test_evo10_single_turn(golden: Golden, tmp_path: Path, run_async):
    # Same environment as the golden suite: fixed papers + a clean write area
    # per run, copied (never mutated) — cross-suite comparability.
    ws = tmp_path / "ws"
    shutil.copytree(FIXTURE_WS, ws)

    thread_id = _run_traced(golden.input, ws, run_async)

    # Trim BEFORE assert_test serializes the trace into judge prompts
    # (otherwise multi-MB judge requests; see harness docstring).
    _slim_trace_for_judge(thread_id)

    md = golden.additional_metadata or {}
    seq = md.get("expected_tool_sequence") or []
    if seq:
        # Ordering-aware expectation straight onto the live trace; without
        # this the fallback chain would see only the single-element top-level
        # expected_tools and lose both order and subagent routing.
        update_current_trace(expected_tools=_seq_to_tool_calls(seq))
    # else: golden.expected_tools (or its absence, EVOSCI-G087) flows through
    # deepeval's own trace fallback chain untouched.

    assert_test(
        golden=golden,
        metrics=build_evo_metrics(md.get("primary_metrics", [])),
    )
