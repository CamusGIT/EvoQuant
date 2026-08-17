#!/usr/bin/env python3
"""Shared utilities for local-paper-navigator scripts.

Zero network. All operations are local file I/O over workspace directories.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Workspace configuration
# ---------------------------------------------------------------------------

WORKSPACE_DIR = Path(os.environ.get("PAPER_NAV_WORKSPACE_DIR", "."))


def get_workspace_dir() -> Path:
    """Resolve workspace directory from env or default."""
    d = Path(os.environ.get("PAPER_NAV_WORKSPACE_DIR", ".")).resolve()
    if not d.is_dir():
        print(f"Warning: workspace dir not found: {d}", file=sys.stderr)
    return d


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def load_manifest(workspace_dir: Path | None = None) -> list[dict]:
    """Read manifest.jsonl from workspace. Returns list of dicts."""
    wd = workspace_dir or get_workspace_dir()
    manifest_path = wd / "manifest.jsonl"
    if not manifest_path.exists():
        return []
    entries = []
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


# ---------------------------------------------------------------------------
# Wiki JSONL helpers
# ---------------------------------------------------------------------------


def load_all_wiki_records(workspace_dir: Path | None = None) -> list[dict]:
    """Load all wiki/*.jsonl records. Returns list of dicts."""
    wd = workspace_dir or get_workspace_dir()
    wiki_dir = wd / "wiki"
    if not wiki_dir.is_dir():
        return []
    records = []
    for f in sorted(wiki_dir.glob("*.jsonl")):
        try:
            with open(f, encoding="utf-8") as fh:
                line = fh.readline().strip()
                if line:
                    records.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            continue
    return records


def load_wiki_record(paper_id: str, workspace_dir: Path | None = None) -> dict | None:
    """Load a single wiki JSONL record by paperId."""
    wd = workspace_dir or get_workspace_dir()
    path = wd / "wiki" / f"{paper_id}.jsonl"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.loads(f.readline().strip())
    except (json.JSONDecodeError, OSError):
        return None


def find_markdown_path(paper_id: str, workspace_dir: Path | None = None) -> Path | None:
    """Resolve markdown/{paperId}.md path."""
    wd = workspace_dir or get_workspace_dir()
    path = wd / "markdown" / f"{paper_id}.md"
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# JSONL I/O
# ---------------------------------------------------------------------------


def write_jsonl(path: str | Path, records: list[dict], append: bool = False) -> None:
    """Write records to a JSONL file."""
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        f.writelines(json.dumps(rec, ensure_ascii=False) + "\n" for rec in records)


def read_jsonl(path: str | Path) -> list[dict]:
    """Read all records from a JSONL file."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def dedup_papers(papers: list[dict], key: str = "paperId") -> list[dict]:
    """Deduplicate papers by key field, keeping the first occurrence."""
    seen = set()
    result = []
    for p in papers:
        pid = p.get(key, "")
        if pid and pid not in seen:
            seen.add(pid)
            result.append(p)
    return result


# ---------------------------------------------------------------------------
# Token matching
# ---------------------------------------------------------------------------


def tokenize(text: str) -> set[str]:
    """Simple whitespace + punctuation tokenization, lowercased."""
    import re

    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return {t for t in tokens if len(t) > 1}


def match_score(text: str, query_tokens: set[str]) -> int:
    """Return overlap count of query tokens with text."""
    text_tokens = tokenize(text)
    return len(query_tokens & text_tokens)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def add_workspace_args(parser: argparse.ArgumentParser) -> None:
    """Add --workspace-dir argument."""
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="Workspace directory containing wiki/, markdown/, manifest.jsonl (default: $PAPER_NAV_WORKSPACE_DIR or .)",
    )


def add_output_args(parser: argparse.ArgumentParser) -> None:
    """Add --output, --append, --json arguments."""
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file instead of overwriting",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON lines")


def resolve_workspace(args) -> Path:
    """Resolve workspace dir from args or env."""
    if hasattr(args, "workspace_dir") and args.workspace_dir:
        return Path(args.workspace_dir).resolve()
    return get_workspace_dir()


def emit_results(
    results: list[dict],
    args,
    json_mode: bool = False,
    format_fn=None,
) -> None:
    """Output results to stdout and/or file.

    Args:
        results: List of paper record dicts
        args: Parsed argparse namespace (needs --output, --append, --json)
        json_mode: Whether to default to JSON output
        format_fn: Optional function(paper_dict) -> str for formatted output
    """
    use_json = getattr(args, "json", False) or json_mode

    if use_json:
        lines = [json.dumps(r, ensure_ascii=False) for r in results]
        output = "\n".join(lines) + ("\n" if lines else "")
    elif format_fn:
        output = "\n".join(format_fn(r) for r in results) + "\n"
    else:
        # Default: simple tabular format
        output = ""
        for r in results:
            pid = r.get("paperId", "?")[:12]
            title = r.get("title", "Unknown")[:60]
            year = r.get("year", "?")
            source = r.get("source", "")
            output += f"{pid}...  {year}  {source:20s}  {title}\n"

    if output.strip():
        print(output, end="")

    out_path = getattr(args, "output", None)
    if out_path:
        append = getattr(args, "append", False)
        mode = "a" if append else "w"
        with open(out_path, mode, encoding="utf-8") as f:
            f.write(output)


# ---------------------------------------------------------------------------
# Paper ID normalization
# ---------------------------------------------------------------------------


def normalize_paper_id(raw_id: str) -> str:
    """Normalize a paper ID to the SHA-256 hex format used in wiki/markdown.

    If already a 64-char hex string, return as-is.
    Otherwise, try to find a matching paperId in the wiki index.
    """
    raw_id = raw_id.strip()
    if len(raw_id) == 64 and all(c in "0123456789abcdef" for c in raw_id):
        return raw_id
    # Not a valid SHA-256 — caller should use match_by_title instead
    return raw_id
