#!/usr/bin/env python3
"""Local title lookup in wiki JSONL. Replaces network-based match_paper_by_title.py.

Searches all wiki/*.jsonl records for a matching title using case-insensitive
substring match. Optionally falls back to token-overlap scoring when no exact
match is found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running without installing as a package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    add_output_args,
    add_workspace_args,
    emit_results,
    load_all_wiki_records,
    match_score,
    resolve_workspace,
    tokenize,
)

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_paper_card(paper: dict) -> str:
    """Format a paper record as a Paper Card."""
    title = paper.get("title", "Unknown")
    source = paper.get("source", "")
    year = paper.get("year", "?")
    paper_id = paper.get("paperId", "?")
    tldr = paper.get("tldr", "")
    return (
        f"\U0001f4c4 **{title}**\n"
        f"Source: {source} | Year: {year} | ID: {paper_id}\n"
        f"TLDR: {tldr}"
    )


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def exact_substring_match(records: list[dict], query: str) -> list[dict]:
    """Case-insensitive substring match on the title field."""
    q_lower = query.lower()
    return [r for r in records if q_lower in r.get("title", "").lower()]


def fallback_token_match(records: list[dict], query: str) -> list[dict]:
    """Score records by token overlap with the query and return sorted results."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scored = []
    for r in records:
        title = r.get("title", "")
        score = match_score(title, query_tokens)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [r for _, r in scored]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search wiki JSONL records by paper title (local, no network).",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Title query string (case-insensitive substring match).",
    )
    parser.add_argument(
        "--fallback-search",
        action="store_true",
        help="Use token-overlap scoring when exact substring match finds nothing.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results to return (default: 5).",
    )
    add_workspace_args(parser)
    add_output_args(parser)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    workspace_dir = resolve_workspace(args)
    records = load_all_wiki_records(workspace_dir)

    if not records:
        print("No wiki records found.", file=sys.stderr)
        emit_results([], args, format_fn=format_paper_card)
        return

    # Primary: case-insensitive substring match
    results = exact_substring_match(records, args.title)

    # Fallback: token-overlap scoring
    if not results and args.fallback_search:
        results = fallback_token_match(records, args.title)
        if results:
            print(
                f"No substring match for '{args.title}'; "
                f"showing {len(results)} result(s) by token overlap.",
                file=sys.stderr,
            )

    if not results:
        print(f"No matches found for '{args.title}'.", file=sys.stderr)

    results = results[: args.limit]
    emit_results(results, args, format_fn=format_paper_card)


if __name__ == "__main__":
    main()
