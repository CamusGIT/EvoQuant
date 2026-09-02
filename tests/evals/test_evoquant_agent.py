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
from pathlib import Path

import pytest

from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden

from tests.evals.harness import (
    FIXTURE_WS,
    _run_traced,
    _slim_trace_for_judge,
)
from tests.evals.metrics import build_trace_metrics

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("EVOSCIENTIST_EVALS"),
        reason="LLM-in-the-loop eval; set EVOSCIENTIST_EVALS=1 (via deepeval test run)",
    ),
    pytest.mark.timeout(2400),  # 40 min per golden: glm-5.2 single calls run
    # 4-5 min (reasoning 40-100KB); a light task needs 7+ model calls
]

EVAL_DIR = Path(__file__).parent
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


@pytest.mark.parametrize("golden", dataset.goldens, ids=lambda g: (g.input or "")[:48])
def test_evoquant_single_turn(
    golden: Golden, tmp_path: Path, run_async, trace_metrics
):
    # Fixed papers + a clean write area per run: copy the snapshot, never
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
