#!/usr/bin/env python3
"""Search code-repo/ for local code implementation metadata.

Each subdirectory under code-repo/ should contain a meta.json with:
  method_name, anchor_paper_id, anchor_paper_title, description,
  framework, language, key_files, interfaces, results, last_updated
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from utils import get_corpus_dir, match_score, tokenize


def search_code_repo(
    query: str | None = None,
    paper_id: str | None = None,
    workspace_dir: Path | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search local code-repo metadata by keyword or paper ID."""
    wd = workspace_dir or get_corpus_dir()
    code_repo_dir = wd / "code-repo"
    if not code_repo_dir.is_dir():
        print(
            f"Warning: code-repo directory not found: {code_repo_dir}", file=sys.stderr
        )
        return []

    results: list[tuple[dict, int]] = []
    query_tokens = tokenize(query or "") if query else set()

    for meta_file in sorted(code_repo_dir.glob("*/meta.json")):
        try:
            with open(meta_file, encoding="utf-8") as f:
                meta = json.loads(f.read())
        except (json.JSONDecodeError, OSError):
            continue

        # Match by paper_id (prefix match on first 12 chars)
        if paper_id:
            stored_id = meta.get("anchor_paper_id", "")
            if stored_id.startswith(paper_id[:12]):
                results.append((meta, 999))  # exact match = highest score
                continue

        # Match by keyword (token overlap on method_name + title + description)
        if query:
            method = meta.get("method_name", "")
            title = meta.get("anchor_paper_title", "")
            desc = meta.get("description", "")
            score = (
                match_score(method, query_tokens) * 2
                + match_score(title, query_tokens) * 2
                + match_score(desc, query_tokens)
            )
            if score > 0:
                results.append((meta, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Format output
    output = []
    for meta, score in results[:limit]:
        output.append(
            {
                "method_name": meta.get("method_name", ""),
                "anchor_paper_id": meta.get("anchor_paper_id", ""),
                "anchor_paper_title": meta.get("anchor_paper_title", ""),
                "description": meta.get("description", "")[:200],
                "framework": meta.get("framework", ""),
                "language": meta.get("language", ""),
                "key_files": meta.get("key_files", []),
                "interfaces": meta.get("interfaces", []),
                "results": meta.get("results", ""),
                "local_path": str(meta_file.parent),
                "match_score": score,
            }
        )

    return output


def format_entry(e: dict, idx: int) -> str:
    name = e.get("method_name", "Unknown")
    title = e.get("anchor_paper_title", "")
    framework = e.get("framework", e.get("language", ""))
    desc = e.get("description", "")[:120]
    path = e.get("local_path", "")
    score = e.get("match_score", 0)

    framework_str = f" | {framework}" if framework else ""
    return (
        f"{idx}. **{name}**{framework_str} (score: {score})\n"
        f"   Anchor: {title}\n"
        f"   {desc}\n"
        f"   Path: `{path}`\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Search local code-repo for implementation metadata"
    )
    parser.add_argument(
        "--query", "-q", help="Keyword search (method name, title, description)"
    )
    parser.add_argument("--paper-id", "-p", help="Paper ID (SHA-256 prefix)")
    parser.add_argument(
        "--limit", "-l", type=int, default=5, help="Max results (default 5)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="Corpus root (default: <repo>/corpus; EVOSCIENTIST_CORPUS_DIR overrides)",
    )
    args = parser.parse_args()

    if not args.query and not args.paper_id:
        print("Error: --query or --paper-id required", file=sys.stderr)
        sys.exit(1)

    workspace_dir = Path(args.workspace_dir).resolve() if args.workspace_dir else None

    results = search_code_repo(args.query, args.paper_id, workspace_dir, args.limit)

    if not results:
        print("No local code implementations found", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print("# Local Code Implementations\n")
    print(f"Found **{len(results)}** entries\n")
    for i, r in enumerate(results, 1):
        print(format_entry(r, i))


if __name__ == "__main__":
    main()
