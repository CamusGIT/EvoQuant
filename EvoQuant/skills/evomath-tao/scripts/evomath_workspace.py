#!/usr/bin/env python3
"""Create, validate, and check lightweight EvoMath Markdown workspaces.

Subcommands:
    init                  Create the 5 Markdown workspace files in a directory.
    check                 Verify final.md contains a valid `final-status:` line.
    validate-phase N      Verify the .md output for step N (1..5) is structurally complete.
    validate-proved       When final-status=PROVED, verify the 10-item Self-Check Checklist.

This script enforces the deterministic parts of the EvoMath workflow. Use it
together with a TodoWrite list (one TODO per step) so that:
  - The agent writes the .md content.
  - The agent marks each TODO `in_progress` before working.
  - The agent runs `validate-phase N` before marking the TODO `completed`.
  - If validate-phase exits non-zero, the TODO is NOT completed; the .md is revised.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

STATUS_VALUES = {
    "PROVED",
    "REFUTED",
    "VERIFIED_NUMERICALLY",
    "CONJECTURED",
    "HANDED_OFF",
}

VERDICT_VALUES = {"sound", "repair", "fail"}
AUDIT_VERDICTS = {"PASS", "WARN", "FAIL"}
SHIELDING_PHRASES = ["obviously", "clearly", "显然", "易见"]


TEMPLATES = {
    "plan.md": """# Plan

## Problem Type

## Goal

## Strategy

## Subgoals

- [ ] g1:

## Notes
""",
    "proof-artifact.md": """# Proof Artifact

## Positive Lemmas

| ID | Statement | Proof Summary | Used By |
|---|---|---|---|

## Negative Attempts

| Subgoal | Attempt | Reason To Avoid |
|---|---|---|
""",
    "candidates.md": """# Candidates

| Subgoal | Candidate | Idea | Verdict | Issue Or Reason |
|---|---|---|---|---|
""",
    "audit.md": """# Audit

## Clean Proof Checked

## Findings

| Severity | Location | Issue |
|---|---|---|

## Verdict
""",
    "final.md": """final-status: HANDED_OFF

## Result

## Proof / Report

## Audit

- audits-run:
- critical-issues:
- remaining-gaps:

## Proof Artifact

- positive lemmas:
- negative attempts:

## Reflection

- memory-persisted:
- storage-location:
- proposed-memory-updates:
""",
}


# ─── init / check ───────────────────────────────────────────────────


def init_workspace(target: Path, force: bool) -> int:
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in TEMPLATES.items():
        path = target / name
        if path.exists() and not force:
            continue
        path.write_text(content, encoding="utf-8")
        written.append(path)
    for path in written:
        print(path)
    return 0


def extract_status(text: str) -> str | None:
    match = re.search(r"(?im)^\s*final-status\s*:\s*([A-Z_]+)\s*$", text)
    if not match:
        return None
    value = match.group(1)
    return value if value in STATUS_VALUES else None


def check_final(path: Path) -> int:
    if not path.exists():
        print(f"{path}: missing")
        return 1
    text = path.read_text(encoding="utf-8")
    status = extract_status(text)
    if status is None:
        print(f"{path}: missing or invalid final-status")
        return 1
    print(f"{path}: final-status={status}")
    return 0


# ─── Markdown helpers ───────────────────────────────────────────────


def _extract_section(text: str, heading: str) -> str:
    """Return the text between '## heading' and the next '## ' (or EOF).

    Matches the heading exactly (case-sensitive). The returned string excludes
    the heading line itself.
    """
    lines = text.split("\n")
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$")
    capture = False
    out: list[str] = []
    for line in lines:
        if pattern.match(line):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def _section_has_content(text: str, heading: str) -> bool:
    section = _extract_section(text, heading)
    meaningful = [
        line.strip()
        for line in section.split("\n")
        if line.strip() and not line.strip().startswith("<!--")
    ]
    return bool(meaningful)


def _table_data_rows(text: str) -> list[list[str]]:
    """Parse Markdown table rows, skipping header and separator lines.

    A row is recognised by starting with '|'. The separator line (containing
    only dashes and pipes) is skipped. Header is the first non-separator row
    and is also skipped.
    """
    rows = [line for line in text.split("\n") if line.strip().startswith("|")]
    data: list[list[str]] = []
    seen_header = False
    for row in rows:
        if re.match(r"^\s*\|\s*[-: ]+\s*(\|\s*[-: ]+\s*)+\|\s*$", row):
            continue
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        data.append(cells)
    return data


# ─── Per-step validators ────────────────────────────────────────────


def validate_step_1(workspace: Path) -> tuple[int, list[str]]:
    """Step 1 — Plan Briefly. Checks plan.md."""
    plan_path = workspace / "plan.md"
    if not plan_path.exists():
        return 1, [f"{plan_path}: missing"]
    text = plan_path.read_text(encoding="utf-8")
    failures: list[str] = []
    for section in ("Problem Type", "Goal", "Strategy"):
        if not _section_has_content(text, section):
            failures.append(f"plan.md: section '{section}' is empty")
    subgoals_text = _extract_section(text, "Subgoals")
    filled = [
        line
        for line in subgoals_text.split("\n")
        if re.match(r"^\s*-\s*\[[ x]\]\s*g\d+:\s*\S", line)
    ]
    if not filled:
        failures.append(
            "plan.md: no filled subgoal in 'Subgoals' (template line not enough)"
        )
    return (1 if failures else 0), failures


def validate_step_2(workspace: Path) -> tuple[int, list[str]]:
    """Step 2 — Try Candidates. Checks candidates.md."""
    candidates_path = workspace / "candidates.md"
    if not candidates_path.exists():
        return 1, [f"{candidates_path}: missing"]
    text = candidates_path.read_text(encoding="utf-8")
    failures: list[str] = []
    data_rows = _table_data_rows(text)
    if not data_rows:
        failures.append("candidates.md: no candidate data rows")
    else:
        valid_rows = 0
        for row in data_rows:
            # Expected columns: Subgoal | Candidate | Idea | Verdict | Issue Or Reason
            if len(row) < 4:
                continue
            idea = row[2].strip()
            verdict = row[3].strip().lower()
            if not idea:
                continue
            if verdict not in VERDICT_VALUES:
                failures.append(
                    f"candidates.md: row '{row[1] or '?'}' has invalid Verdict '{row[3]}' "
                    f"(must be one of {sorted(VERDICT_VALUES)})"
                )
                continue
            valid_rows += 1
        if valid_rows == 0:
            failures.append(
                "candidates.md: no valid candidate rows (need Idea + Verdict filled)"
            )
    return (1 if failures else 0), failures


def validate_step_3(workspace: Path) -> tuple[int, list[str]]:
    """Step 3 — Assemble. Checks final.md 'Proof / Report' section."""
    final_path = workspace / "final.md"
    if not final_path.exists():
        return 1, [f"{final_path}: missing"]
    text = final_path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not _section_has_content(text, "Proof / Report"):
        failures.append("final.md: 'Proof / Report' section is empty")
    proof_text = _extract_section(text, "Proof / Report")
    for phrase in SHIELDING_PHRASES:
        if re.search(re.escape(phrase), proof_text, re.IGNORECASE):
            failures.append(
                f"final.md: proof contains shielding phrase '{phrase}'; every non-trivial step must be justified"
            )
    return (1 if failures else 0), failures


def validate_step_4(workspace: Path) -> tuple[int, list[str]]:
    """Step 4 — Audit. Checks audit.md."""
    audit_path = workspace / "audit.md"
    if not audit_path.exists():
        return 1, [f"{audit_path}: missing"]
    text = audit_path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not _section_has_content(text, "Clean Proof Checked"):
        failures.append("audit.md: 'Clean Proof Checked' section is empty")
    if not _section_has_content(text, "Verdict"):
        failures.append("audit.md: 'Verdict' section is empty")
    else:
        verdict_text = _extract_section(text, "Verdict").upper()
        if not any(v in verdict_text for v in AUDIT_VERDICTS):
            failures.append(
                f"audit.md: 'Verdict' must contain one of {sorted(AUDIT_VERDICTS)}"
            )
    return (1 if failures else 0), failures


def validate_step_5(workspace: Path) -> tuple[int, list[str]]:
    """Step 5 — Reflect. Checks final.md 'Reflection' section.

    Requires each tracked key (memory-persisted, storage-location,
    proposed-memory-updates) to have a non-empty value, not just the bare key.
    """
    final_path = workspace / "final.md"
    if not final_path.exists():
        return 1, [f"{final_path}: missing"]
    text = final_path.read_text(encoding="utf-8")
    failures: list[str] = []
    reflection_text = _extract_section(text, "Reflection")
    if not reflection_text:
        return 1, ["final.md: 'Reflection' section is empty"]
    for key in ("memory-persisted", "storage-location", "proposed-memory-updates"):
        match = re.search(rf"(?im)^\s*-?\s*{re.escape(key)}\s*:(.*)$", reflection_text)
        if not match:
            failures.append(f"final.md: Reflection missing '{key}:' line")
        elif not match.group(1).strip():
            failures.append(f"final.md: Reflection key '{key}:' has empty value")
    return (1 if failures else 0), failures


def validate_proved_checklist(workspace: Path) -> tuple[int, list[str]]:
    """When final-status: PROVED, check the 10-item PROVED Self-Check Checklist.

    The checklist must appear in final.md under a heading containing
    'PROVED Self-Check' (case-insensitive). Each item must be a ticked
    Markdown checkbox '- [x]'.
    """
    final_path = workspace / "final.md"
    if not final_path.exists():
        return 1, [f"{final_path}: missing"]
    text = final_path.read_text(encoding="utf-8")
    status = extract_status(text)
    if status != "PROVED":
        return 0, [f"final-status is {status}; PROVED checklist not required"]
    heading_match = re.search(r"(?im)^##\s+(.*proved\s+self-check.*)$", text)
    if not heading_match:
        return 1, [
            "final.md: final-status=PROVED but no 'PROVED Self-Check Checklist' section found"
        ]
    heading = heading_match.group(1).strip()
    checklist_text = _extract_section(text, heading)
    ticked_items = re.findall(r"^\s*-\s*\[x\]", checklist_text, re.MULTILINE)
    unticked_items = re.findall(r"^\s*-\s*\[\s*\]", checklist_text, re.MULTILINE)
    failures: list[str] = []
    if len(ticked_items) < 10:
        failures.append(
            f"final.md: PROVED checklist has {len(ticked_items)} ticked items (need at least 10)"
        )
    if unticked_items:
        failures.append(
            f"final.md: PROVED checklist has {len(unticked_items)} unticked items; "
            "all must be ticked or final-status must be downgraded"
        )
    return (1 if failures else 0), failures


STEP_VALIDATORS = {
    1: validate_step_1,
    2: validate_step_2,
    3: validate_step_3,
    4: validate_step_4,
    5: validate_step_5,
}


def validate_phase(workspace: Path, step: int, strict: bool) -> int:
    if step not in STEP_VALIDATORS:
        print(f"Unknown step: {step}. Must be 1-5.")
        return 2
    if strict:
        for prior in range(1, step):
            rc, fails = STEP_VALIDATORS[prior](workspace)
            if rc != 0:
                print(
                    f"Step {prior}: FAIL (required before Step {step} in strict mode)"
                )
                for f in fails:
                    print(f"  - {f}")
                return rc
            print(f"Step {prior}: PASS")
    rc, failures = STEP_VALIDATORS[step](workspace)
    if rc == 0:
        print(f"Step {step}: PASS")
    else:
        print(f"Step {step}: FAIL")
        for f in failures:
            print(f"  - {f}")
    return rc


def validate_proved_cmd(workspace: Path) -> int:
    rc, msgs = validate_proved_checklist(workspace)
    label = "PROVED checklist"
    if rc == 0:
        for m in msgs:
            print(m)
        print(f"{label}: PASS")
    else:
        print(f"{label}: FAIL")
        for m in msgs:
            print(f"  - {m}")
    return rc


# ─── CLI ────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create Markdown workspace files.")
    init_parser.add_argument("--dir", default=".evomath/current", type=Path)
    init_parser.add_argument("--force", action="store_true")

    check_parser = subparsers.add_parser(
        "check", help="Check final.md final-status line."
    )
    check_parser.add_argument("--file", default=".evomath/current/final.md", type=Path)

    vp_parser = subparsers.add_parser(
        "validate-phase",
        help="Validate the .md file(s) for a specific workflow step (1..5).",
    )
    vp_parser.add_argument("step", type=int, choices=[1, 2, 3, 4, 5])
    vp_parser.add_argument("--dir", default=".evomath/current", type=Path)
    vp_parser.add_argument(
        "--strict",
        action="store_true",
        help="Also validate all prior steps before this one.",
    )

    vproved_parser = subparsers.add_parser(
        "validate-proved",
        help="If final-status=PROVED, verify the 10-item Self-Check Checklist.",
    )
    vproved_parser.add_argument("--dir", default=".evomath/current", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        return init_workspace(args.dir, args.force)
    if args.command == "check":
        return check_final(args.file)
    if args.command == "validate-phase":
        return validate_phase(args.dir, args.step, args.strict)
    if args.command == "validate-proved":
        return validate_proved_cmd(args.dir)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
