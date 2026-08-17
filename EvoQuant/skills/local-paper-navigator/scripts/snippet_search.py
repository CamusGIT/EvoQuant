#!/usr/bin/env python3
"""Two-tier snippet search across wiki JSONL fields and markdown full-text.

Tier 1 (wiki): Search strategy, method, experiment, result fields in wiki/*.jsonl
Tier 2 (markdown fallback): Only invoked when Tier 1 yields zero matches;
         searches markdown/*.md files using re.finditer with context windows.

Usage:
    python scripts/snippet_search.py --query "夏普比率" --context-chars 500
    python scripts/snippet_search.py --query "annualized return" --paper-ids "sha1,sha2"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import shared utilities (same directory)
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    add_output_args,
    add_workspace_args,
    emit_results,
    load_all_wiki_records,
    resolve_workspace,
    tokenize,
)

# Wiki fields searched in Tier 1
WIKI_SEARCH_FIELDS = ("strategy", "method", "experiment", "result")


# ---------------------------------------------------------------------------
# Tier 1: wiki JSONL field search
# ---------------------------------------------------------------------------


def search_wiki_fields(
    records: list[dict],
    query_tokens: set[str],
    paper_ids: set[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search wiki JSONL records for query token matches in key fields.

    Returns a list of result dicts with keys:
        paperId, title, snippet, source, field, score
    """
    results: list[dict] = []

    for rec in records:
        pid = rec.get("paperId", "")
        if paper_ids and pid not in paper_ids:
            continue

        title = rec.get("title", "")

        for field in WIKI_SEARCH_FIELDS:
            value = rec.get(field, "")
            if not value or not isinstance(value, str):
                continue

            score = len(query_tokens & tokenize(value))
            if score == 0:
                continue

            results.append(
                {
                    "paperId": pid,
                    "title": title,
                    "snippet": value,
                    "source": "wiki",
                    "field": field,
                    "score": score,
                }
            )

    # Sort by score descending, then by paperId for stable ordering
    results.sort(key=lambda r: (-r["score"], r["paperId"]))
    return results[:limit]


# ---------------------------------------------------------------------------
# Tier 2: markdown full-text search
# ---------------------------------------------------------------------------


def search_markdown_files(
    workspace_dir: Path,
    query: str,
    paper_ids: set[str] | None = None,
    limit: int = 50,
    context_chars: int = 500,
) -> list[dict]:
    """Search markdown/*.md files for query string, extracting context windows.

    Uses re.finditer to locate all occurrences of the query (case-insensitive)
    and extracts a context window of `context_chars` characters around each match.
    """
    results: list[dict] = []
    md_dir = workspace_dir / "markdown"
    if not md_dir.is_dir():
        return results

    # Build pattern from raw query (escape regex special chars, allow flexible whitespace)
    # Join query tokens with \s+ to match across whitespace variations
    query_parts = query.strip().split()
    if not query_parts:
        return results
    pattern = r"\s+".join(re.escape(p) for p in query_parts)
    regex = re.compile(pattern, re.IGNORECASE)

    seen_snippets: set[str] = set()  # deduplicate identical snippets

    # Determine which paper IDs to scan
    if paper_ids:
        md_files = []
        for pid in paper_ids:
            p = md_dir / f"{pid}.md"
            if p.exists():
                md_files.append((pid, p))
    else:
        md_files = [(f.stem, f) for f in sorted(md_dir.glob("*.md"))]

    for pid, md_path in md_files:
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue

        # Derive title from first heading or filename
        title = pid
        first_heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if first_heading:
            title = first_heading.group(1).strip()

        for m in regex.finditer(text):
            start = max(0, m.start() - context_chars // 2)
            end = min(len(text), m.end() + context_chars // 2)
            snippet = text[start:end].strip()

            # Deduplicate by snippet content
            dedup_key = (pid, snippet)
            if dedup_key in seen_snippets:
                continue
            seen_snippets.add(dedup_key)

            # Score: number of query tokens found in the snippet
            snippet_tokens = tokenize(snippet)
            query_tokens = tokenize(query)
            score = len(query_tokens & snippet_tokens)

            if score == 0:
                continue

            # Add ellipsis markers if snippet was trimmed
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            results.append(
                {
                    "paperId": pid,
                    "title": title,
                    "snippet": snippet,
                    "source": "markdown",
                    "field": "fulltext",
                    "score": score,
                }
            )

    results.sort(key=lambda r: (-r["score"], r["paperId"]))
    return results[:limit]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Two-tier snippet search: wiki fields first, markdown fallback."
    )
    parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="Search query (tokens are matched independently in wiki fields; "
        "full-text pattern in markdown).",
    )
    parser.add_argument(
        "--paper-ids",
        default=None,
        help="Comma-separated list of paper IDs to restrict search scope",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results (default: 50)",
    )
    parser.add_argument(
        "--context-chars",
        type=int,
        default=500,
        help="Context window size in characters for markdown matches (default: 500)",
    )
    add_workspace_args(parser)
    add_output_args(parser)
    return parser


def format_result(r: dict) -> str:
    """Format a single search result for text output."""
    pid = r.get("paperId", "?")[:12]
    title = r.get("title", "Unknown")[:60]
    source = r.get("source", "?")
    field = r.get("field", "?")
    score = r.get("score", 0)
    snippet = r.get("snippet", "")
    return f"[{source}/{field}] score={score}  {pid}...  {title}\n  {snippet}"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    workspace_dir = resolve_workspace(args)

    # Parse optional paper-id filter
    paper_ids: set[str] | None = None
    if args.paper_ids:
        paper_ids = {pid.strip() for pid in args.paper_ids.split(",") if pid.strip()}

    query_tokens = tokenize(args.query)

    # ------------------------------------------------------------------
    # Tier 1: wiki JSONL field search
    # ------------------------------------------------------------------
    wiki_records = load_all_wiki_records(workspace_dir)
    results = search_wiki_fields(
        wiki_records,
        query_tokens,
        paper_ids=paper_ids,
        limit=args.limit,
    )

    # ------------------------------------------------------------------
    # Tier 2: markdown fallback (only if Tier 1 returned nothing)
    # ------------------------------------------------------------------
    if not results:
        results = search_markdown_files(
            workspace_dir,
            args.query,
            paper_ids=paper_ids,
            limit=args.limit,
            context_chars=args.context_chars,
        )

    # ------------------------------------------------------------------
    # Emit output
    # ------------------------------------------------------------------
    emit_results(
        results,
        args,
        format_fn=format_result,
    )


if __name__ == "__main__":
    main()
