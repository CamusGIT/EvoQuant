"""Static validation for tests/evals/.evo10_dataset.json (no LLM calls).

The evo10 set is adapted from the EvoScientist eval set (evo(1).jsonl):
content rewritten for the quant domain, schema frozen — every top-level key
and additional_metadata sub-key of the source must survive, `expected_tools`
stays absent exactly where the source lacks it (EVOSCI-G087). This script
checks schema shape, subagent/tool-name whitelists against the real EvoQuant
runtime, metric-name support, leftover EvoScientist-only vocabulary, and
category coverage.

Run:  uv run python tests/evals/validate_evo10.py
"""

import json
import pathlib
import sys

DATASET = pathlib.Path(__file__).parent / ".evo10_dataset.json"

FULL_TOP_KEYS = {
    "input",
    "expected_output",
    "context",
    "additional_metadata",
    "comments",
    "expected_tools",
}
METADATA_KEYS = {
    "id",
    "category",
    "difficulty",
    "eval_level",
    "expected_subagents",
    "expected_tool_sequence",
    "forbidden_tools",
    "primary_metrics",
    "acceptance_criteria",
    "risk_tags",
    "language",
    "source_basis",
}
SUBAGENTS = {
    "general-purpose",
    "planner-agent",
    "code-agent",
    "data-analysis-agent",
    "debug-agent",
    "research-agent",
    "writing-agent",
    "scheduler",
}
TOOLS = {
    "task",
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
    "think_tool",
    "skill_manager",
    "tavily_search",
    "paper_search",
    "paper_read",
    "paper_section",
    "schedule_task",
    "run_in_background",
}
SUPPORTED_METRICS = {
    "TaskCompletion",
    "StepEfficiency",
    "ToolCorrectness",
    "PlanQuality",
    "PlanAdherence",
    "Faithfulness",
}
# EvoScientist-only vocabulary that must not survive the rewrite. Scanned in
# user-facing content fields only — `source_basis`/`comments` intentionally
# name the upstream set for traceability.
FORBIDDEN_VOCAB = [
    "ask_user",
    "code_interpreter",
    "start_async_task",
    "Lite 模式",
    "More Effort",
    "EvoScientist 的",
    "EvoScientist 在",
    "EvoScientist 科研流程",
    "EvoScientist 规划",
]
CATEGORIES_8 = {
    "code_implementation",
    "data_analysis",
    "safety_grounding",
    "planning",
    "research",
    "orchestration",
    "debugging",
    "scientific_writing",
}


def _check_tool_token(tok: str) -> str | None:
    name, sep, sub = tok.partition(":")
    if name not in TOOLS:
        return f"tool {tok!r}: unknown tool name {name!r}"
    if sep and name == "task" and sub not in SUBAGENTS:
        return f"tool {tok!r}: unknown subagent {sub!r}"
    if sep and name != "task":
        return f"tool {tok!r}: ':' suffix only valid on task"
    return None


def main() -> int:
    rows = json.loads(DATASET.read_text())
    errors: list[str] = []
    ids, categories = set(), set()

    if len(rows) != 10:
        errors.append(f"expected 10 rows, got {len(rows)}")

    for i, row in enumerate(rows):
        rid = row.get("additional_metadata", {}).get("id", f"row#{i}")
        keys = set(row)
        if keys not in (FULL_TOP_KEYS, FULL_TOP_KEYS - {"expected_tools"}):
            errors.append(f"{rid}: top-level keys {sorted(keys)} not the frozen set")
        md = row.get("additional_metadata", {})
        if set(md) != METADATA_KEYS:
            missing = METADATA_KEYS - set(md)
            extra = set(md) - METADATA_KEYS
            errors.append(
                f"{rid}: metadata keys mismatch (missing={missing}, extra={extra})"
            )
        if rid in ids:
            errors.append(f"{rid}: duplicate id")
        ids.add(rid)
        categories.add(md.get("category", ""))

        for sub in md.get("expected_subagents", []):
            if sub not in SUBAGENTS:
                errors.append(f"{rid}: expected_subagents unknown {sub!r}")
        for field in ("expected_tool_sequence", "forbidden_tools"):
            for tok in md.get(field, []):
                if err := _check_tool_token(tok):
                    errors.append(f"{rid}: {field}: {err}")
        for m in md.get("primary_metrics", []):
            if m not in SUPPORTED_METRICS:
                errors.append(f"{rid}: primary_metrics unsupported {m!r}")
        if "ToolCorrectness" in md.get("primary_metrics", []) and not (
            row.get("expected_tools") or md.get("expected_tool_sequence")
        ):
            errors.append(f"{rid}: ToolCorrectness without expected tools")
        if not md.get("expected_output") and "expected_output" not in row:
            pass  # expected_output is top-level; guard below covers it
        if not row.get("expected_output", "").startswith("验收标准："):
            errors.append(f"{rid}: expected_output not in 验收标准 form")

        for field in ("input", "expected_output", "context", "comments"):
            text = row.get(field)
            text = " ".join(text) if isinstance(text, list) else str(text or "")
            for vocab in FORBIDDEN_VOCAB:
                if vocab in text:
                    errors.append(f"{rid}: {field} contains leftover {vocab!r}")
        for crit in md.get("acceptance_criteria", []):
            for vocab in FORBIDDEN_VOCAB:
                if vocab in crit:
                    errors.append(f"{rid}: acceptance_criteria contains {vocab!r}")

    missing_cat = CATEGORIES_8 - categories
    if missing_cat:
        errors.append(f"category coverage incomplete: {sorted(missing_cat)}")

    if errors:
        print(f"INVALID ({len(errors)} errors):")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK: 10 rows, ids={sorted(ids)}, categories={sorted(categories)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
