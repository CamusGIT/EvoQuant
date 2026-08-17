#!/usr/bin/env python3
"""Generate structured literature report from local wiki data.

Replaces the network-based literature_report.py. All data comes from local
wiki JSONL files -- no API calls.

Intents
-------
survey        : Overview of all papers with key themes
quick_scan    : Brief one-line per paper
deep_dive     : Per-paper analysis with reading level and novelty classification
baseline_hunt : Focus on methodology detail and result quality

Usage
-----
python scripts/literature_report.py --paper-ids <sha1>,<sha2> --intent survey
python scripts/literature_report.py --paper-ids <sha1>,<sha2> --intent deep_dive --output report.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------

# Allow running as ``python scripts/literature_report.py`` from the repo root.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from utils import (  # noqa: E402
    add_workspace_args,
    load_all_wiki_records,
    load_wiki_record,
    resolve_workspace,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INTENTS = ("survey", "quick_scan", "deep_dive", "baseline_hunt")

# Fields that carry substantive content (used for richness / reading level).
_CONTENT_FIELDS = ("abstract", "tldr", "strategy", "method", "experiment", "result")

# ---------------------------------------------------------------------------
# Helper: compute derived metrics from wiki records
# ---------------------------------------------------------------------------


def _non_empty_fields(record: dict) -> list[str]:
    """Return content field names whose values are non-empty strings."""
    filled = []
    for field in _CONTENT_FIELDS:
        val = record.get(field, "")
        if isinstance(val, str) and val.strip():
            filled.append(field)
        elif isinstance(val, list) and val:
            filled.append(field)
    return filled


def reading_level(record: dict) -> str:
    """Classify reading level based on field richness.

    Uses the number of non-empty content fields as a proxy for how
    detailed / dense the paper record is.

    Returns one of: "skimmable", "moderate", "dense".
    """
    n = len(_non_empty_fields(record))
    if n <= 2:
        return "skimmable"
    if n <= 4:
        return "moderate"
    return "dense"


def _all_keywords(all_records: list[dict]) -> Counter:
    """Count keyword occurrences across all records."""
    counter: Counter = Counter()
    for rec in all_records:
        for kw in rec.get("keywords", []):
            counter[kw] += 1
    return counter


def keyword_overlap_count(record: dict, all_records: list[dict]) -> int:
    """How many *other* papers share at least one keyword with this one."""
    my_kws = set(record.get("keywords", []))
    if not my_kws:
        return 0
    my_id = record.get("paperId", "")
    count = 0
    for other in all_records:
        if other.get("paperId", "") == my_id:
            continue
        if my_kws & set(other.get("keywords", [])):
            count += 1
    return count


def novelty_classification(record: dict, kw_counter: Counter, total_papers: int) -> str:
    """Classify novelty based on keyword uniqueness.

    A keyword that appears in only one paper is "unique".  The fraction of
    unique keywords determines the novelty label.

    Returns one of: "incremental", "moderate", "high".
    """
    kws = record.get("keywords", [])
    if not kws:
        return "incremental"
    unique_count = sum(1 for kw in kws if kw_counter.get(kw, 0) <= 1)
    ratio = unique_count / len(kws)
    if ratio >= 0.5:
        return "high"
    if ratio >= 0.2:
        return "moderate"
    return "incremental"


def _similar_papers(
    record: dict, all_records: list[dict], max_suggestions: int = 3
) -> list[str]:
    """Suggest similar papers based on keyword overlap.

    Returns a list of short descriptions: "title (overlap=N)".
    """
    my_kws = set(record.get("keywords", []))
    if not my_kws:
        return []
    my_id = record.get("paperId", "")
    scored: list[tuple[int, str, int]] = []
    for other in all_records:
        oid = other.get("paperId", "")
        if oid == my_id:
            continue
        overlap = len(my_kws & set(other.get("keywords", [])))
        if overlap > 0:
            scored.append((overlap, other.get("title", oid[:12]), other.get("year", 0)))
    scored.sort(key=lambda t: (-t[0], t[2]))
    return [
        f"{title} (overlap={overlap})" for overlap, title, _ in scored[:max_suggestions]
    ]


def _xref_search(record: dict, all_records: list[dict]) -> list[str]:
    """Suggest cross-reference searches: source + shared keyword combos."""
    source = record.get("source", "")
    kws = record.get("keywords", [])
    suggestions: list[str] = []
    if source:
        suggestions.append(f'source:"{source}"')
    # Pick up to 3 of the rarest keywords for targeted cross-reference.
    kw_counter = _all_keywords(all_records)
    rarest = sorted(kws, key=lambda k: kw_counter.get(k, 0))[:3]
    for kw in rarest:
        suggestions.append(f'keyword:"{kw}"')
    return suggestions


# ---------------------------------------------------------------------------
# Report formatters
# ---------------------------------------------------------------------------


def _header(intent: str, paper_ids: list[str]) -> str:
    return f"# Literature Report ({intent})\n\nPapers: {len(paper_ids)}\n"


def _format_survey(records: list[dict], all_records: list[dict]) -> str:
    """Overview of all papers with key themes."""
    kw_counter = _all_keywords(all_records)

    lines: list[str] = []
    lines.append("## Papers\n")

    for rec in records:
        pid = rec.get("paperId", "?")[:12]
        title = rec.get("title", "Untitled")
        year = rec.get("year", "?")
        source = rec.get("source", "")
        kws = rec.get("keywords", [])
        overlap = keyword_overlap_count(rec, all_records)
        tldr = rec.get("tldr", "")
        tldr_text = f"\n> {tldr}" if tldr else ""

        lines.append(f"### {title}")
        lines.append(f"- ID: `{pid}...` | Year: {year} | Source: {source}")
        lines.append(f"- Keywords: {', '.join(kws) if kws else '(none)'}")
        lines.append(f"- Keyword overlap count: {overlap} other paper(s)")
        if tldr_text:
            lines.append(tldr_text)
        lines.append("")

    # Theme summary
    top_kw = kw_counter.most_common(10)
    if top_kw:
        lines.append("## Key Themes\n")
        for kw, cnt in top_kw:
            lines.append(f"- **{kw}** ({cnt} paper(s))")
        lines.append("")

    # Year distribution
    years = [r.get("year") for r in records if r.get("year")]
    if years:
        lines.append("## Year Distribution\n")
        year_counts = Counter(years)
        for yr in sorted(year_counts):
            lines.append(f"- {yr}: {year_counts[yr]} paper(s)")
        lines.append("")

    return "\n".join(lines)


def _format_quick_scan(records: list[dict]) -> str:
    """Brief one-line per paper."""
    lines: list[str] = []
    for rec in records:
        pid = rec.get("paperId", "?")[:12]
        title = rec.get("title", "Untitled")
        year = rec.get("year", "?")
        source = rec.get("source", "")
        tldr = rec.get("tldr", "")
        summary = tldr[:80] + "..." if len(tldr) > 80 else tldr
        lines.append(f"[{pid}] ({year}) {title} -- {source} | {summary}")
    return "\n".join(lines) + "\n" if lines else ""


def _format_deep_dive(records: list[dict], all_records: list[dict]) -> str:
    """Per-paper analysis with reading level and novelty classification."""
    kw_counter = _all_keywords(all_records)
    total = len(all_records)

    lines: list[str] = []

    for rec in records:
        pid = rec.get("paperId", "?")[:12]
        title = rec.get("title", "Untitled")
        year = rec.get("year", "?")
        source = rec.get("source", "")
        kws = rec.get("keywords", [])
        overlap = keyword_overlap_count(rec, all_records)
        rl = reading_level(rec)
        novelty = novelty_classification(rec, kw_counter, total)
        filled = _non_empty_fields(rec)
        similar = _similar_papers(rec, all_records)
        xrefs = _xref_search(rec, all_records)

        lines.append(f"## {title}")
        lines.append(f"- ID: `{pid}...`")
        lines.append(f"- Year: {year} | Source: {source}")
        lines.append(f"- Keywords: {', '.join(kws) if kws else '(none)'}")
        lines.append(f"- Keyword overlap count: {overlap} other paper(s)")
        lines.append(
            f"- Reading level: **{rl}** (field richness: {len(filled)}/{len(_CONTENT_FIELDS)})"
        )
        lines.append(f"- Novelty: **{novelty}**")

        # Unique vs shared keywords
        unique_kws = [kw for kw in kws if kw_counter.get(kw, 0) <= 1]
        shared_kws = [kw for kw in kws if kw_counter.get(kw, 0) > 1]
        if unique_kws:
            lines.append(f"- Unique keywords: {', '.join(unique_kws)}")
        if shared_kws:
            lines.append(f"- Shared keywords: {', '.join(shared_kws)}")

        lines.append("")
        lines.append("### Content Summary")

        for field in _CONTENT_FIELDS:
            val = rec.get(field, "")
            if isinstance(val, str) and val.strip():
                label = field.replace("_", " ").title()
                # Truncate very long fields for readability
                display = val if len(val) <= 500 else val[:497] + "..."
                lines.append(f"**{label}:** {display}")
                lines.append("")

        if similar:
            lines.append("### Similar Papers")
            for s in similar:
                lines.append(f"- {s}")
            lines.append("")

        if xrefs:
            lines.append("### Cross-reference Suggestions")
            for xr in xrefs:
                lines.append(f"- {xr}")
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def _format_baseline_hunt(records: list[dict], all_records: list[dict]) -> str:
    """Focus on methodology detail and result quality."""
    kw_counter = _all_keywords(all_records)

    lines: list[str] = []

    # Rank by method + result field richness (proxy for methodology detail).
    def _method_richness(rec: dict) -> int:
        score = 0
        for field in ("method", "experiment", "result"):
            val = rec.get(field, "")
            if isinstance(val, str) and val.strip():
                score += len(val) // 200  # rough length bonus
                score += 1  # field present
        return score

    ranked = sorted(records, key=_method_richness, reverse=True)

    for rec in ranked:
        pid = rec.get("paperId", "?")[:12]
        title = rec.get("title", "Untitled")
        year = rec.get("year", "?")
        source = rec.get("source", "")
        kws = rec.get("keywords", [])
        novelty = novelty_classification(rec, kw_counter, len(all_records))

        lines.append(f"## {title}")
        lines.append(f"- ID: `{pid}...` | Year: {year} | Source: {source}")
        lines.append(f"- Keywords: {', '.join(kws) if kws else '(none)'}")
        lines.append(f"- Novelty: **{novelty}**")
        lines.append("")

        # Methodology
        method = rec.get("method", "")
        if method:
            lines.append("### Methodology")
            lines.append(method if len(method) <= 800 else method[:797] + "...")
            lines.append("")

        # Experiment
        experiment = rec.get("experiment", "")
        if experiment:
            lines.append("### Experiment Setup")
            lines.append(
                experiment if len(experiment) <= 800 else experiment[:797] + "..."
            )
            lines.append("")

        # Results
        result = rec.get("result", "")
        if result:
            lines.append("### Results")
            lines.append(result if len(result) <= 800 else result[:797] + "...")
            lines.append("")

        # Strategy
        strategy = rec.get("strategy", "")
        if strategy:
            lines.append("### Strategy")
            lines.append(strategy if len(strategy) <= 600 else strategy[:597] + "...")
            lines.append("")

        # Baseline quality assessment
        has_method = bool(method and method.strip())
        has_experiment = bool(experiment and experiment.strip())
        has_result = bool(result and result.strip())
        quality_parts = []
        if has_method:
            quality_parts.append("methodology detail")
        if has_experiment:
            quality_parts.append("experimental setup")
        if has_result:
            quality_parts.append("result reporting")
        quality_label = " | ".join(quality_parts) if quality_parts else "minimal detail"
        lines.append(f"**Detail coverage:** {quality_label}")

        similar = _similar_papers(rec, all_records)
        if similar:
            lines.append("**Related baselines:**")
            for s in similar:
                lines.append(f"  - {s}")

        lines.append("")
        lines.append("---\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate structured literature report from local wiki data.",
    )
    parser.add_argument(
        "--paper-ids",
        required=True,
        help="Comma-separated paperIds (SHA-256 hex strings)",
    )
    parser.add_argument(
        "--intent",
        required=True,
        choices=_INTENTS,
        help="Report format intent",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: stdout)",
    )
    add_workspace_args(parser)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Resolve workspace
    workspace_dir = resolve_workspace(args)

    # Parse paper IDs
    paper_ids = [pid.strip() for pid in args.paper_ids.split(",") if pid.strip()]
    if not paper_ids:
        print("Error: no paper IDs provided.", file=sys.stderr)
        sys.exit(1)

    # Load requested records
    records: list[dict] = []
    missing: list[str] = []
    for pid in paper_ids:
        rec = load_wiki_record(pid, workspace_dir=workspace_dir)
        if rec is None:
            missing.append(pid)
        else:
            records.append(rec)

    if missing:
        print(
            f"Warning: {len(missing)} paper(s) not found: {', '.join(m[:12] + '...' for m in missing)}",
            file=sys.stderr,
        )

    if not records:
        print("Error: no valid paper records loaded.", file=sys.stderr)
        sys.exit(1)

    # Load all records for cross-paper metrics (keyword overlap, novelty, etc.)
    all_records = load_all_wiki_records(workspace_dir=workspace_dir)

    # Generate report
    intent = args.intent
    header = _header(intent, paper_ids)

    if intent == "survey":
        body = _format_survey(records, all_records)
    elif intent == "quick_scan":
        body = _format_quick_scan(records)
    elif intent == "deep_dive":
        body = _format_deep_dive(records, all_records)
    elif intent == "baseline_hunt":
        body = _format_baseline_hunt(records, all_records)
    else:
        # Should not reach here due to argparse choices.
        print(f"Error: unknown intent '{intent}'", file=sys.stderr)
        sys.exit(1)

    report = header + "\n" + body

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
