#!/usr/bin/env python3
"""Local keyword search over wiki JSONL records.

Replaces the network-based scholar_search.py. Searches all wiki/*.jsonl files
in the workspace directory, computing weighted token-overlap scores against
query terms and returning ranked results.

Scoring weights:
    title    : 2x
    keywords : 2x  (joined list)
    tldr     : 1x
    abstract : 1x
    source   : 1x

Usage:
    python scripts/local_search.py --query "factor momentum" --limit 15
    python scripts/local_search.py --query "volatility" --year-min 2024 --sort-by year
    python scripts/local_search.py --query "risk premium" --workspace-dir /path/to/workspace --json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add scripts directory to path so utils is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    add_output_args,
    add_workspace_args,
    dedup_papers,
    emit_results,
    load_all_wiki_records,
    match_score,
    resolve_workspace,
    tokenize,
)

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

# Field name -> weight for relevance scoring
FIELD_WEIGHTS: dict[str, int] = {
    "title": 2,
    "keywords": 2,
    "tldr": 1,
    "abstract": 1,
    "source": 1,
}


def compute_score(record: dict, query_tokens: set[str]) -> float:
    """Compute weighted token-overlap score for a record against query tokens.

    For each field in FIELD_WEIGHTS, compute match_score (token overlap count)
    and multiply by the field weight. Returns the weighted sum.
    """
    total = 0.0
    for field, weight in FIELD_WEIGHTS.items():
        value = record.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        elif not isinstance(value, str):
            value = str(value) if value else ""
        if value:
            total += match_score(value, query_tokens) * weight
    return total


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search(
    query: str,
    workspace_dir: Path,
    year_min: int | None = None,
    year_max: int | None = None,
    sort_by: str = "relevance",
    limit: int = 15,
) -> list[dict]:
    """Search wiki records by keyword overlap.

    Args:
        query: Search query string.
        workspace_dir: Path to workspace containing wiki/*.jsonl.
        year_min: Optional minimum year filter (inclusive).
        year_max: Optional maximum year filter (inclusive).
        sort_by: "relevance" (score DESC, year DESC) or "year" (year DESC).
        limit: Maximum number of results to return.

    Returns:
        List of record dicts with an added "_score" field.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        print("Warning: query produced no searchable tokens.", file=sys.stderr)
        return []

    records = load_all_wiki_records(workspace_dir)
    if not records:
        print("No wiki records found in workspace.", file=sys.stderr)
        return []

    # Score and filter
    scored: list[dict] = []
    for rec in records:
        score = compute_score(rec, query_tokens)
        if score <= 0:
            continue

        # Year filtering
        year = rec.get("year")
        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None
        if year_min is not None and (year is None or year < year_min):
            continue
        if year_max is not None and (year is None or year > year_max):
            continue

        rec["_score"] = score
        scored.append(rec)

    # Deduplicate before sorting
    scored = dedup_papers(scored)

    # Sort
    if sort_by == "year":
        scored.sort(
            key=lambda r: (r.get("year") or 0, r.get("_score", 0)), reverse=True
        )
    else:
        scored.sort(
            key=lambda r: (r.get("_score", 0), r.get("year") or 0), reverse=True
        )

    return scored[:limit]


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_result(record: dict) -> str:
    """Format a single search result for tabular display."""
    pid = record.get("paperId", "?")[:12]
    year = record.get("year", "?")
    source = record.get("source", "")[:20]
    title = record.get("title", "Unknown")[:60]
    score = record.get("_score", 0)
    return f"{pid}...  {year}  {source:20s}  {score:5.0f}  {title}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Local keyword search over wiki JSONL records.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --query "factor momentum" --limit 15
  %(prog)s --query "volatility" --year-min 2024 --sort-by year
  %(prog)s --query "risk premium" --workspace-dir /path/to/workspace --json
""",
    )
    parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="Search query string (tokenized for keyword overlap matching)",
    )
    parser.add_argument(
        "--year-min",
        type=int,
        default=None,
        help="Minimum publication year (inclusive)",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=None,
        help="Maximum publication year (inclusive)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=15,
        help="Maximum number of results (default: 15)",
    )
    parser.add_argument(
        "--sort-by",
        choices=["relevance", "year"],
        default="relevance",
        help="Sort order: relevance (score DESC, year DESC) or year (year DESC) (default: relevance)",
    )
    add_workspace_args(parser)
    add_output_args(parser)
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for local_search.py."""
    parser = build_parser()
    args = parser.parse_args(argv)

    workspace_dir = resolve_workspace(args)

    if not workspace_dir.is_dir():
        parser.error(f"Workspace directory does not exist: {workspace_dir}")

    results = search(
        query=args.query,
        workspace_dir=workspace_dir,
        year_min=args.year_min,
        year_max=args.year_max,
        sort_by=args.sort_by,
        limit=args.limit,
    )

    if not results:
        print("No results found.", file=sys.stderr)
        return

    emit_results(
        results,
        args,
        format_fn=format_result,
    )


if __name__ == "__main__":
    main()
