"""Metrics for the EvoQuant traced single-turn eval suite.

Judge: DeepSeek ``deepseek-v4-flash``. DeepEval 4.x does NOT parse
provider-prefixed model strings (e.g. ``"deepseek/deepseek-chat"`` would be
sent to the OpenAI API), so pass ``DeepSeekModel`` instances instead.

Metrics are built lazily via :func:`build_trace_metrics` — DeepSeekModel
requires ``DEEPSEEK_API_KEY`` at construction time, and constructing at import
time would crash plain ``pytest`` collection in key-less environments.
"""

from deepeval.metrics import GEval, StepEfficiencyMetric, TaskCompletionMetric
from deepeval.models import DeepSeekModel
from deepeval.test_case import SingleTurnParams

# Trajectory pair (trace-scoped, library default thresholds):
# - TaskCompletionMetric: did the agent accomplish the task inferred from the
#   ordered trace.
# - StepEfficiencyMetric: were the steps/tool calls efficient, without
#   unnecessary actions.
# Two custom GEvals capture EvoQuant-specific success the generic pair misses:
# research rigor and deliverable quality. evaluation_params stick to
# input/actual_output — referenceless, safe with generated goldens.
_RIGOR_CRITERIA = (
    "Evaluate whether the output demonstrates rigorous quantitative-research "
    "practice: claims about factors, signals, data or metrics (IC/ICIR/RANKIC, "
    "coverage, returns, correlations) are supported by the work actually "
    "performed or by retrieved paper evidence; methodology, assumptions and "
    "limitations are stated; numbers are not fabricated or asserted without a "
    "computation or source; the agent is honest when the local papers library lacks "
    "the needed evidence instead of inventing papers or results."
)

_DELIVERABLE_CRITERIA = (
    "Evaluate whether the output is a usable research deliverable for a quant "
    "researcher: it addresses the requested bounded task directly and ends "
    "with a concrete result (answer, artifact path, metric table, or explicit "
    "next-step decision) rather than an open-ended plan or a restatement of "
    "the question; the structure is clear enough to act on without re-running "
    "the agent."
)


def build_trace_metrics():
    """Build the trace-level metric list (requires ``DEEPSEEK_API_KEY``)."""
    judge = DeepSeekModel(model="deepseek-v4-flash")
    return [
        TaskCompletionMetric(model=judge),
        StepEfficiencyMetric(model=judge),
        GEval(
            name="Quant Research Rigor",
            criteria=_RIGOR_CRITERIA,
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
            ],
            model=judge,
        ),
        GEval(
            name="Actionable Research Deliverable",
            criteria=_DELIVERABLE_CRITERIA,
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
            ],
            model=judge,
        ),
    ]
