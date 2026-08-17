#!/usr/bin/env python3
"""Fetch a paper's wiki record and/or markdown content by paperId.

Zero network. All operations are local file I/O over workspace directories.

Reading levels:
  L2 (default) -- Output the COMPLETE wiki JSONL record including strategy,
                   method, experiment, result fields.  This is the default for
                   most papers where you need structured knowledge.
  L1            -- Output the FULL markdown file content.  Use for papers you
                   will directly build upon, where you need the raw detail.
"""

from __future__ import annotations

import argparse
import sys

# ---------------------------------------------------------------------------
# Import from utils
# ---------------------------------------------------------------------------
from utils import (
    add_workspace_args,
    find_markdown_path,
    load_wiki_record,
    normalize_paper_id,
    resolve_workspace,
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

WIKI_DETAIL_FIELDS = (
    "strategy",
    "method",
    "experiment",
    "result",
)

WIKI_META_FIELDS = (
    "title",
    "year",
    "source",
    "keywords",
    "tldr",
    "abstract",
)


def _format_paper_card(record: dict) -> str:
    """Build a short Paper Card header from the wiki record."""
    pid = record.get("paperId", "?")
    title = record.get("title", "Unknown")
    year = record.get("year", "?")
    source = record.get("source", "")
    return f"=== Paper Card ===\n  ID:     {pid}\n  Title:  {title}\n  Year:   {year}\n  Source: {source}"


def _format_wiki_fields(record: dict) -> str:
    """Format all wiki fields (meta + detail) for L2 reading."""
    lines: list[str] = []

    # Meta fields
    for field in WIKI_META_FIELDS:
        value = record.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"\n{field.capitalize()}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"\n{field.capitalize()}:\n{value}")

    # Detail fields (strategy, method, experiment, result)
    for field in WIKI_DETAIL_FIELDS:
        value = record.get(field)
        if value is None:
            continue
        lines.append(f"\n{field.capitalize()}:\n{value}")

    return "\n".join(lines)


def _format_metadata_only(record: dict) -> str:
    """Format only the wiki JSONL fields (no markdown)."""
    lines: list[str] = [_format_paper_card(record)]

    # All fields from the record, pretty-printed
    for key, value in record.items():
        if key == "paperId":
            continue  # already shown in card
        if isinstance(value, list):
            lines.append(f"  {key}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def _format_l2(record: dict) -> str:
    """L2 reading: Paper Card header + all wiki fields."""
    parts = [_format_paper_card(record), _format_wiki_fields(record)]
    return "\n".join(parts)


def _format_l1(record: dict, md_content: str) -> str:
    """L1 reading: Paper Card header + full markdown content."""
    header = _format_paper_card(record)
    return f"{header}\n\n---\n\n{md_content}"


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending [truncated] if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[truncated]"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a paper's wiki record and/or markdown content by paperId.",
    )
    parser.add_argument(
        "--paper-id",
        required=True,
        help="SHA-256 paperId of the paper to fetch",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only output wiki JSONL fields (no markdown)",
    )
    parser.add_argument(
        "--full-stdout",
        action="store_true",
        help="Output entire content without truncation",
    )
    parser.add_argument(
        "--max-output",
        type=int,
        default=2000,
        help="Truncate output to N chars in non-full mode (default: 2000)",
    )
    parser.add_argument(
        "--reading-level",
        choices=["L1", "L2"],
        default="L2",
        help="Reading level: L2=complete wiki record (default), L1=full markdown content",
    )
    add_workspace_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolve workspace
    workspace_dir = resolve_workspace(args)

    # Normalize paper ID
    paper_id = normalize_paper_id(args.paper_id)
    if len(paper_id) != 64 or not all(c in "0123456789abcdef" for c in paper_id):
        print(f"Error: invalid paperId: {args.paper_id}", file=sys.stderr)
        print("  Expected a 64-character lowercase hex SHA-256 hash.", file=sys.stderr)
        return 1

    # Load wiki record
    record = load_wiki_record(paper_id, workspace_dir)
    if record is None:
        print(f"Error: no wiki record found for paperId: {paper_id}", file=sys.stderr)
        return 1

    # --metadata-only mode
    if args.metadata_only:
        output = _format_metadata_only(record)
        if not args.full_stdout:
            output = _truncate(output, args.max_output)
        print(output)
        return 0

    # Reading-level logic
    if args.reading_level == "L2":
        # L2: complete wiki JSONL record
        output = _format_l2(record)
    else:
        # L1: full markdown content
        md_path = find_markdown_path(paper_id, workspace_dir)
        if md_path is None:
            print(
                f"Error: no markdown file found for paperId: {paper_id}",
                file=sys.stderr,
            )
            return 1
        try:
            md_content = md_path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error reading markdown file: {e}", file=sys.stderr)
            return 1
        output = _format_l1(record, md_content)

    # Truncation
    if not args.full_stdout:
        output = _truncate(output, args.max_output)

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
