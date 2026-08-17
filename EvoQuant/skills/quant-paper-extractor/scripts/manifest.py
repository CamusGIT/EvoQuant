#!/usr/bin/env python3
"""Manifest utilities for quant-paper-extractor.

Tracks processing state for each PDF: conversion status, extraction status,
file paths, and error messages. Manifest is a JSONL file with one entry per
paper, keyed by paperId (SHA-256 of the PDF binary content).

Usage (imported by pdf_to_markdown.py and extract.py):
    from manifest import compute_paper_id, read_manifest, append_entry, ...
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paper ID
# ---------------------------------------------------------------------------


def compute_paper_id(pdf_path: str) -> str:
    """Compute SHA-256 hash of a PDF file's binary content.

    Returns the hex digest (64 lowercase chars). Used as paperId and as
    the filename stem for both markdown and JSONL outputs.
    """
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------


def read_manifest(manifest_path: str) -> list[dict]:
    """Read all entries from a manifest JSONL file.

    Returns an empty list if the file does not exist.
    """
    if not os.path.exists(manifest_path):
        return []
    entries: list[dict] = []
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def append_entry(manifest_path: str, entry: dict) -> None:
    """Append a single entry to the manifest JSONL file.

    Creates the file if it does not exist.
    """
    os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _rewrite_manifest(manifest_path: str, entries: list[dict]) -> None:
    """Rewrite the entire manifest file (used by update_status)."""
    tmp = manifest_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)
    os.replace(tmp, manifest_path)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def find_by_paper_id(manifest_path: str, paper_id: str) -> dict | None:
    """Find the first entry matching the given paperId. Returns None if not found."""
    for entry in read_manifest(manifest_path):
        if entry.get("paperId") == paper_id:
            return entry
    return None


def find_by_status(manifest_path: str, status: str) -> list[dict]:
    """Return all entries with the given status."""
    return [e for e in read_manifest(manifest_path) if e.get("status") == status]


def is_processed(manifest_path: str, paper_id: str) -> bool:
    """Check if a paper has already been fully processed (markdown + extraction done).

    Returns True if the entry exists and status is one of the terminal states.
    """
    entry = find_by_paper_id(manifest_path, paper_id)
    if entry is None:
        return False
    return entry.get("status") in (
        "markdown_done",
        "markdown_short",
        "extraction_done",
        "extraction_incomplete",
    )


def is_extracted(manifest_path: str, paper_id: str) -> bool:
    """Check if a paper has already been extracted (JSONL exists)."""
    entry = find_by_paper_id(manifest_path, paper_id)
    if entry is None:
        return False
    return entry.get("status") == "extraction_done"


# ---------------------------------------------------------------------------
# Update helpers
# ---------------------------------------------------------------------------


def update_status(
    manifest_path: str,
    paper_id: str,
    new_status: str,
    error_message: str | None = None,
) -> None:
    """Update the status of an existing entry. Rewrites the full manifest file."""
    entries = read_manifest(manifest_path)
    found = False
    for entry in entries:
        if entry.get("paperId") == paper_id:
            entry["status"] = new_status
            entry["timestamp"] = datetime.now(UTC).isoformat()
            if error_message is not None:
                entry["errorMessage"] = error_message
            found = True
            break
    if not found:
        print(f"Warning: paperId {paper_id} not found in manifest", file=sys.stderr)
    _rewrite_manifest(manifest_path, entries)


def make_entry(
    paper_id: str,
    source_pdf: str,
    markdown_path: str = "",
    wiki_path: str = "",
    status: str = "pending",
    error_message: str | None = None,
) -> dict:
    """Create a new manifest entry dict."""
    return {
        "paperId": paper_id,
        "sourcePdf": source_pdf,
        "markdownPath": markdown_path,
        "wikiPath": wiki_path,
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        "errorMessage": error_message,
        "retryCount": 0,
    }


# ---------------------------------------------------------------------------
# Rebuild from filesystem
# ---------------------------------------------------------------------------


def rebuild_from_filesystem(
    rawpaper_dir: str,
    markdown_dir: str,
    wiki_dir: str,
    manifest_path: str,
) -> int:
    """Rebuild the manifest by scanning the actual directories.

    Determines status by checking which files exist. Returns the number of
    entries written.
    """
    entries: list[dict] = []

    # Index existing markdown files by paperId
    md_files: dict[str, str] = {}
    if os.path.isdir(markdown_dir):
        for f in Path(markdown_dir).glob("*.md"):
            md_files[f.stem] = str(f)

    # Index existing wiki files by paperId
    wiki_files: dict[str, str] = {}
    if os.path.isdir(wiki_dir):
        for f in Path(wiki_dir).glob("*.jsonl"):
            wiki_files[f.stem] = str(f)

    # Scan rawpaper for all PDFs
    if not os.path.isdir(rawpaper_dir):
        print(f"Error: rawpaper directory not found: {rawpaper_dir}", file=sys.stderr)
        return 0

    for pdf_file in sorted(Path(rawpaper_dir).glob("*.pdf")):
        paper_id = compute_paper_id(str(pdf_file))
        md_path = md_files.get(paper_id, "")
        wiki_path = wiki_files.get(paper_id, "")

        if wiki_path:
            status = "extraction_done"
        elif md_path:
            # Check if markdown is suspiciously short
            md_size = os.path.getsize(md_path) if os.path.exists(md_path) else 0
            status = "markdown_short" if md_size < 500 else "markdown_done"
        else:
            status = "pending"

        entries.append(
            make_entry(
                paper_id=paper_id,
                source_pdf=str(pdf_file),
                markdown_path=md_path,
                wiki_path=wiki_path,
                status=status,
            )
        )

    _rewrite_manifest(manifest_path, entries)
    print(f"Rebuilt manifest with {len(entries)} entries", file=sys.stderr)
    return len(entries)


# ---------------------------------------------------------------------------
# CLI (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manifest utilities")
    sub = parser.add_subparsers(dest="command")

    # rebuild
    rb = sub.add_parser("rebuild", help="Rebuild manifest from filesystem")
    rb.add_argument("--rawpaper-dir", required=True)
    rb.add_argument("--markdown-dir", required=True)
    rb.add_argument("--wiki-dir", required=True)
    rb.add_argument("--manifest-path", required=True)

    # list
    ls = sub.add_parser("list", help="List manifest entries")
    ls.add_argument("--manifest-path", required=True)
    ls.add_argument("--status", default=None, help="Filter by status")

    # check
    ck = sub.add_parser("check", help="Check if a paper is processed")
    ck.add_argument("--manifest-path", required=True)
    ck.add_argument("--paper-id", required=True)

    args = parser.parse_args()

    if args.command == "rebuild":
        rebuild_from_filesystem(
            args.rawpaper_dir,
            args.markdown_dir,
            args.wiki_dir,
            args.manifest_path,
        )
    elif args.command == "list":
        entries = read_manifest(args.manifest_path)
        if args.status:
            entries = [e for e in entries if e.get("status") == args.status]
        for e in entries:
            print(
                f"{e['paperId'][:12]}...  {e['status']:25s}  {e.get('sourcePdf', '')}"
            )
        print(f"Total: {len(entries)}")
    elif args.command == "check":
        if is_extracted(args.manifest_path, args.paper_id):
            print("extracted")
            sys.exit(0)
        elif is_processed(args.manifest_path, args.paper_id):
            print("converted")
            sys.exit(0)
        else:
            print("not_found")
            sys.exit(1)
    else:
        parser.print_help()
