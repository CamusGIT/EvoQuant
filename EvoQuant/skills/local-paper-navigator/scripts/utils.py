#!/usr/bin/env python3
"""Shared utilities for local-paper-navigator scripts.

Zero network. All operations are local file I/O over the repo papers
directory (<repo>/papers: cards/, markdown/, manifest.jsonl; override with
EVOSCIENTIST_PAPERS_DIR or --papers-dir).

The papers location is derived from this file's own path, so no
environment-variable fiddling is needed — and none is honored beyond the
single documented override. When pointed at a legacy workspace (wiki/
layout), loaders fall back to wiki/ so old call sites keep working.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Papers configuration
# ---------------------------------------------------------------------------

_PAPERS_ENV = "EVOSCIENTIST_PAPERS_DIR"
# Legacy alias kept so existing shell exports keep working.
_CORPUS_ENV_LEGACY = "EVOSCIENTIST_CORPUS_DIR"


def _default_papers_dir() -> Path:
    """env override > <repo>/papers derived from this file's location.

    scripts/ -> local-paper-navigator/ -> skills/ -> package/ -> repo root.
    Kept local (no package import): these scripts run on ad-hoc sys.paths.
    """
    explicit = os.environ.get(_PAPERS_ENV) or os.environ.get(_CORPUS_ENV_LEGACY)
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[4] / "papers"


def get_papers_dir() -> Path:
    """Resolve the papers root; warns (never crashes) when missing."""
    d = _default_papers_dir()
    if not d.is_dir():
        print(
            f"Warning: papers dir not found: {d} (set {_PAPERS_ENV} to override)",
            file=sys.stderr,
        )
    return d


def get_workspace_dir() -> Path:
    """DEPRECATED alias of get_papers_dir — kept for old imports."""
    print(
        "Warning: get_workspace_dir is deprecated; use get_papers_dir.",
        file=sys.stderr,
    )
    return get_papers_dir()


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def load_manifest(papers_dir: Path | None = None) -> list[dict]:
    """Read manifest.jsonl from the papers directory. Returns list of dicts."""
    wd = papers_dir or get_papers_dir()
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
# Card JSONL helpers (cards/ in the papers directory; wiki/ in legacy workspaces)
# ---------------------------------------------------------------------------


def _cards_dir(base: Path) -> Path:
    """cards/ when present (papers layout), else wiki/ (legacy layout)."""
    cards = base / "cards"
    return cards if cards.is_dir() else base / "wiki"


def load_all_wiki_records(papers_dir: Path | None = None) -> list[dict]:
    """Load all card records (cards/*.jsonl, first line each)."""
    wd = papers_dir or get_papers_dir()
    cards_dir = _cards_dir(wd)
    if not cards_dir.is_dir():
        return []
    records = []
    for f in sorted(cards_dir.glob("*.jsonl")):
        try:
            with open(f, encoding="utf-8") as fh:
                line = fh.readline().strip()
                if line:
                    records.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            continue
    return records


def load_wiki_record(paper_id: str, papers_dir: Path | None = None) -> dict | None:
    """Load a single card record by paperId."""
    wd = papers_dir or get_papers_dir()
    path = _cards_dir(wd) / f"{paper_id}.jsonl"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.loads(f.readline().strip())
    except (json.JSONDecodeError, OSError):
        return None


def find_markdown_path(paper_id: str, papers_dir: Path | None = None) -> Path | None:
    """Resolve markdown/{paperId}.md path."""
    wd = papers_dir or get_papers_dir()
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
    """Add --papers-dir (plus the deprecated --workspace-dir) argument."""
    parser.add_argument(
        "--papers-dir",
        default=None,
        help="Papers root containing cards/, markdown/, manifest.jsonl "
        f"(default: ${_PAPERS_ENV} or <repo>/papers)",
    )
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="(deprecated legacy wiki/ layout; prefer --papers-dir)",
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
    """Resolve the papers dir from args (--papers-dir wins) or default."""
    if hasattr(args, "papers_dir") and args.papers_dir:
        return Path(args.papers_dir).resolve()
    if hasattr(args, "workspace_dir") and args.workspace_dir:
        print(
            "Warning: --workspace-dir is the deprecated legacy layout; "
            "prefer --papers-dir.",
            file=sys.stderr,
        )
        return Path(args.workspace_dir).resolve()
    return get_papers_dir()


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
