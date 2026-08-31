#!/usr/bin/env python3
"""Shared utilities for local-paper-navigator scripts.

Zero network. All operations are local file I/O over the repo corpus
(<repo>/corpus: cards/, markdown/, manifest.jsonl; override with
EVOSCIENTIST_CORPUS_DIR or --corpus-dir).

The corpus location is derived from this file's own path, so no
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
# Corpus configuration
# ---------------------------------------------------------------------------

_CORPUS_ENV = "EVOSCIENTIST_CORPUS_DIR"


def _default_corpus_dir() -> Path:
    """env override > <repo>/corpus derived from this file's location.

    scripts/ -> local-paper-navigator/ -> skills/ -> package/ -> repo root.
    Kept local (no package import): these scripts run on ad-hoc sys.paths.
    """
    explicit = os.environ.get(_CORPUS_ENV)
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[4] / "corpus"


def get_corpus_dir() -> Path:
    """Resolve the corpus root; warns (never crashes) when missing."""
    d = _default_corpus_dir()
    if not d.is_dir():
        print(
            f"Warning: corpus dir not found: {d} (set {_CORPUS_ENV} to override)",
            file=sys.stderr,
        )
    return d


def get_workspace_dir() -> Path:
    """DEPRECATED alias of get_corpus_dir — kept for old imports."""
    print(
        "Warning: get_workspace_dir is deprecated; use get_corpus_dir.",
        file=sys.stderr,
    )
    return get_corpus_dir()


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def load_manifest(corpus_dir: Path | None = None) -> list[dict]:
    """Read manifest.jsonl from the corpus. Returns list of dicts."""
    wd = corpus_dir or get_corpus_dir()
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
# Card JSONL helpers (cards/ in the corpus; wiki/ in legacy workspaces)
# ---------------------------------------------------------------------------


def _cards_dir(base: Path) -> Path:
    """cards/ when present (corpus layout), else wiki/ (legacy layout)."""
    cards = base / "cards"
    return cards if cards.is_dir() else base / "wiki"


def load_all_wiki_records(corpus_dir: Path | None = None) -> list[dict]:
    """Load all card records (cards/*.jsonl, first line each)."""
    wd = corpus_dir or get_corpus_dir()
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


def load_wiki_record(paper_id: str, corpus_dir: Path | None = None) -> dict | None:
    """Load a single card record by paperId."""
    wd = corpus_dir or get_corpus_dir()
    path = _cards_dir(wd) / f"{paper_id}.jsonl"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.loads(f.readline().strip())
    except (json.JSONDecodeError, OSError):
        return None


def find_markdown_path(paper_id: str, corpus_dir: Path | None = None) -> Path | None:
    """Resolve markdown/{paperId}.md path."""
    wd = corpus_dir or get_corpus_dir()
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
    """Add --corpus-dir (plus the deprecated --workspace-dir) argument."""
    parser.add_argument(
        "--corpus-dir",
        default=None,
        help="Corpus root containing cards/, markdown/, manifest.jsonl "
        f"(default: ${_CORPUS_ENV} or <repo>/corpus)",
    )
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="(deprecated legacy wiki/ layout; prefer --corpus-dir)",
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
    """Resolve the corpus dir from args (--corpus-dir wins) or default."""
    if hasattr(args, "corpus_dir") and args.corpus_dir:
        return Path(args.corpus_dir).resolve()
    if hasattr(args, "workspace_dir") and args.workspace_dir:
        print(
            "Warning: --workspace-dir is the deprecated legacy layout; "
            "prefer --corpus-dir.",
            file=sys.stderr,
        )
        return Path(args.workspace_dir).resolve()
    return get_corpus_dir()


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
