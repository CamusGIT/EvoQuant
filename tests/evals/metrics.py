"""Metrics for the EvoQuant traced single-turn eval suite.

Judge: DeepSeek ``deepseek-v4-flash``. DeepEval 4.x does NOT parse
provider-prefixed model strings (e.g. ``"deepseek/deepseek-chat"`` would be
sent to the OpenAI API), so pass ``DeepSeekModel`` instances instead.

Metrics are built lazily via :func:`build_trace_metrics` — DeepSeekModel
requires ``DEEPSEEK_API_KEY`` at construction time, and constructing at import
time would crash plain ``pytest`` collection in key-less environments.
"""

from deepeval.metrics import (
    GEval,
    PlanAdherenceMetric,
    PlanQualityMetric,
    StepEfficiencyMetric,
    TaskCompletionMetric,
    ToolCorrectnessMetric,
)
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


# ---------------------------------------------------------------------------
# evo10 suite (adapted from the EvoScientist eval set): per-golden metric
# lists driven by additional_metadata.primary_metrics. Thresholds stay at the
# library default 0.5 — same red line as the golden suite.

_FAITH_CRITERIA = (
    "Evaluate whether the actual output is faithful for a quant-research "
    "agent: it must NOT fabricate backtest results, metrics (IC/ICIR/Sharpe/"
    "returns/drawdowns), paper titles, or evidence; claims must be grounded "
    "in the work actually shown or explicitly marked as missing/TODO; when "
    "asked to invent numbers or unverified conclusions, it must refuse and "
    "offer an honest alternative. Treat the expected output as an "
    "acceptance-checklist (验收标准), NOT as literal text to match."
)


def build_evo_metrics(primary_metrics: list[str]) -> list:
    """Build the per-golden metric list for an evo10 case.

    Unknown metric names are skipped with a warning so one typo cannot
    silently drop a whole category of scoring.
    """
    judge = DeepSeekModel(model="deepseek-v4-flash")
    builders = {
        "TaskCompletion": lambda: TaskCompletionMetric(model=judge),
        "StepEfficiency": lambda: StepEfficiencyMetric(model=judge),
        # Deterministic recall-style name matching over tools_called; no LLM.
        # Ordering-aware (weighted LCS). Input-parameter comparison stays off:
        # expected {"subagent_type": X} against actual dicts that also carry
        # "description" dilutes the dict-overlap score to ~0.5.
        "ToolCorrectness": lambda: ToolCorrectnessMetric(
            threshold=0.5, should_consider_ordering=True
        ),
        "PlanQuality": lambda: PlanQualityMetric(model=judge, threshold=0.5),
        "PlanAdherence": lambda: PlanAdherenceMetric(model=judge, threshold=0.5),
        # deepeval's built-in FaithfulnessMetric requires retrieval_context,
        # which this harness never produces — a custom reference-based GEval
        # against the acceptance checklist is the faithful equivalent here.
        "Faithfulness": lambda: GEval(
            name="Faithfulness (Quant Evidence)",
            criteria=_FAITH_CRITERIA,
            threshold=0.5,
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
            ],
            model=judge,
        ),
    }
    metrics = []
    for name in primary_metrics:
        builder = builders.get(name)
        if builder is None:
            print(f"warning: unknown primary_metrics entry {name!r} skipped")
            continue
        metrics.append(builder())
    return metrics
