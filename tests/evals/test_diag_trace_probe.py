"""Zero-LLM probe for the deepeval trace lifecycle under ``deepeval test run``.

The eval harness must shrink the judge prompt (TaskCompletion/StepEfficiency
serialize ``test_case._trace_dict`` into the prompt; a real 7-call agent run
produced an 11MB dict). Three slim attempts no-opped because the trace was
read off the wrong object. This probe answers, WITHOUT any model call:

1. What does ``current_trace_context.get()`` hold in the test body (the
   pytest plugin's eval scope), and does its ``root_spans`` tree already
   contain our ``@observe`` span mid-flight?
2. Does truncating ``span.input``/``span.output`` in the test body stick
   through ``assert_test`` → ``create_nested_spans_dict``? (TraceSizeMetric
   reports the serialized ``_trace_dict`` size the judge would receive.)
3. What does ``trace_manager.traces`` hold at that moment (explains the
   earlier no-ops)?

Run:
    EVOSCIENTIST_EVALS=1 uv run deepeval test run tests/evals/test_diag_trace_probe.py
"""

import json
import os

import pytest

from deepeval import assert_test
from deepeval.dataset import Golden
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from deepeval.tracing import observe, trace_manager, update_current_span
from deepeval.tracing.context import current_trace_context

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("EVOSCIENTIST_EVALS"),
        reason="probe; run via deepeval test run with EVOSCIENTIST_EVALS=1",
    ),
    pytest.mark.timeout(120),
]

BIG_IN = "A" * 100_000  # simulate a fat span input (message history)
BIG_OUT = "B" * 100_000


def _object_input():
    """Simulate the REAL agent-span input shape: a dict of langchain
    BaseMessage objects (pydantic models). The first slim pass-through'd
    these untouched (not str/list/dict), keeping judge prompts at 11MB —
    this case reproduces that regression chain-wide.
    """
    from langchain_core.messages import AIMessage, HumanMessage

    return {
        "messages": [
            HumanMessage(content="H" * 60_000),
            AIMessage(
                content="A" * 60_000,
                additional_kwargs={"reasoning_content": "R" * 60_000},
            ),
        ]
    }


class TraceSizeMetric(BaseMetric):
    """requires_trace metric that never calls a model.

    Reports the serialized ``_trace_dict`` size the trace-level judge
    metrics would embed in their prompt — the exact quantity the slim
    must shrink.
    """

    def __init__(self):
        self.threshold = 0.0
        self.requires_trace = True
        self.async_mode = False
        self.score = None
        self.success = None
        self.reason = ""
        self.trace_dict_chars = -1

    def measure(self, test_case: LLMTestCase, _show_indicator=True, _in_component=False):
        td = getattr(test_case, "_trace_dict", None)
        self.trace_dict_chars = len(json.dumps(td)) if isinstance(td, dict) else -1
        self.score = 1.0
        self.success = self.score >= self.threshold
        self.reason = f"_trace_dict json chars = {self.trace_dict_chars}"
        return self.score

    @property
    def __name__(self):
        return "Trace Size Probe"


def _tree_dump(spans, depth=0):
    lines = []
    for s in spans or []:
        i = len(str(getattr(s, "input", "") or ""))
        o = len(str(getattr(s, "output", "") or ""))
        lines.append(
            f"{'  ' * depth}- {type(s).__name__}:{getattr(s, 'name', '?')} "
            f"in={i} out={o} children={len(getattr(s, 'children', None) or [])}"
        )
        lines += _tree_dump(getattr(s, "children", None) or [], depth + 1)
    return lines


def test_probe_trace_lifecycle():
    log = []

    @observe(name="evoquant-agent-run")
    def fake_agent():
        update_current_span(input=_object_input(), output=BIG_OUT)
        return "final answer"

    fake_agent()

    ctx = current_trace_context.get()
    log.append(f"ctx type: {type(ctx).__name__ if ctx else None}")
    if ctx is not None:
        log.append(f"root_spans ({len(ctx.root_spans or [])}):")
        log += _tree_dump(ctx.root_spans)
    tm = list(trace_manager.traces)
    log.append(f"trace_manager.traces: {len(tm)}")
    for t in tm:
        log.append(f"  tm trace root_spans ({len(t.root_spans or [])}):")
        log += _tree_dump(t.root_spans)

    # Truncate in-place, mirroring the harness slim — INCLUDING the object
    # branch (str() any non-container leaf over the limit) that fixes the
    # langchain-BaseMessage pass-through.
    def _slim(v, limit=2000):
        if isinstance(v, str):
            return v[:limit] if len(v) > limit else v
        if isinstance(v, list):
            return [_slim(x, max(limit // 2, 200)) for x in v]
        if isinstance(v, dict):
            return {k: _slim(x, max(limit // 2, 200)) for k, x in v.items()}
        if v is None or isinstance(v, (bool, int, float)):
            return v
        s = str(v)
        return s[:limit] if len(s) > limit else v

    def _walk(span):
        if getattr(span, "input", None) is not None:
            span.input = _slim(span.input)
        if getattr(span, "output", None) is not None:
            span.output = _slim(span.output)
        for c in getattr(span, "children", None) or []:
            _walk(c)

    if ctx is not None:
        for r in ctx.root_spans or []:
            _walk(r)
    log.append("--- after slim (ctx tree) ---")
    if ctx is not None:
        log += _tree_dump(ctx.root_spans)

    print("\n".join(log))
    with open("/tmp/trace_probe.log", "w") as fh:  # pytest eats stdout
        fh.write("\n".join(log))

    # If the truncation sticks, the dict the judge receives is a few KB
    # instead of >=200KB (two 100KB fields on the promoted root).
    metric = TraceSizeMetric()
    assert_test(golden=Golden(input="probe task"), metrics=[metric])
    with open("/tmp/trace_probe.log", "a") as fh:
        fh.write(f"\nPROBE RESULT: _trace_dict chars = {metric.trace_dict_chars}\n")
