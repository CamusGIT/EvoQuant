#!/usr/bin/env python3
"""Seed-based similarity search. Replaces recommend.py.

For each positive seed paper, extract tokens from title + keywords + tldr +
abstract. Merge positive tokens (union), subtract negative tokens. Score all
other wiki records by Jaccard-like overlap: |intersection| / |union|.

CLI examples:
    python scripts/similar_papers.py --positive <sha1>,<sha2> --limit 15
    python scripts/similar_papers.py --positive <sha1> --negative <sha3>
"""

from __future__ import annotations

import argparse
import sys

from utils import (
    add_output_args,
    add_workspace_args,
    emit_results,
    load_all_wiki_records,
    load_wiki_record,
    resolve_workspace,
    tokenize,
)

# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------


def extract_paper_tokens(record: dict) -> set[str]:
    """Extract tokens from a paper record's title, keywords, tldr, and abstract."""
    parts: list[str] = []

    title = record.get("title", "")
    if title:
        parts.append(title)

    keywords = record.get("keywords")
    if keywords:
        if isinstance(keywords, list):
            parts.extend(str(k) for k in keywords)
        else:
            parts.append(str(keywords))

    tldr = record.get("tldr", "")
    if tldr:
        parts.append(tldr)

    abstract = record.get("abstract", "")
    if abstract:
        parts.append(abstract)

    combined = " ".join(parts)
    return tokenize(combined)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def jaccard_score(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    """Compute Jaccard-like overlap: |intersection| / |union|.

    Returns 0.0 when both sets are empty.
    """
    if not query_tokens and not candidate_tokens:
        return 0.0
    union = query_tokens | candidate_tokens
    if not union:
        return 0.0
    intersection = query_tokens & candidate_tokens
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed-based similarity search over wiki records.",
    )
    parser.add_argument(
        "--positive",
        required=True,
        help="Comma-separated paperIds to use as positive seeds",
    )
    parser.add_argument(
        "--negative",
        default="",
        help="Comma-separated paperIds to use as negative seeds",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum number of results (default: 15)",
    )
    add_workspace_args(parser)
    add_output_args(parser)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    workspace_dir = resolve_workspace(args)

    # Parse seed IDs
    positive_ids = [pid.strip() for pid in args.positive.split(",") if pid.strip()]
    negative_ids = [pid.strip() for pid in args.negative.split(",") if pid.strip()]

    if not positive_ids:
        print("Error: at least one positive seed paperId is required.", file=sys.stderr)
        sys.exit(1)

    # Build positive token set (union across all positive seeds)
    positive_tokens: set[str] = set()
    for pid in positive_ids:
        record = load_wiki_record(pid, workspace_dir)
        if record is None:
            print(f"Warning: positive seed not found: {pid}", file=sys.stderr)
            continue
        positive_tokens |= extract_paper_tokens(record)

    if not positive_tokens:
        print("Error: no tokens extracted from positive seeds.", file=sys.stderr)
        sys.exit(1)

    # Build negative token set (union across all negative seeds)
    negative_tokens: set[str] = set()
    for pid in negative_ids:
        record = load_wiki_record(pid, workspace_dir)
        if record is None:
            print(f"Warning: negative seed not found: {pid}", file=sys.stderr)
            continue
        negative_tokens |= extract_paper_tokens(record)

    # Subtract negative tokens from positive
    query_tokens = positive_tokens - negative_tokens

    if not query_tokens:
        print(
            "Error: after subtracting negative tokens, no tokens remain.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load all records and score candidates (excluding seed papers themselves)
    seed_ids = set(positive_ids) | set(negative_ids)
    all_records = load_all_wiki_records(workspace_dir)

    candidates = []
    for rec in all_records:
        pid = rec.get("paperId", "")
        if pid in seed_ids:
            continue
        candidate_tokens = extract_paper_tokens(rec)
        score = jaccard_score(query_tokens, candidate_tokens)
        if score > 0.0:
            rec_scored = dict(rec)
            rec_scored["similarity"] = round(score, 6)
            candidates.append(rec_scored)

    # Sort by similarity descending, then by title for stable ordering
    candidates.sort(key=lambda r: (-r["similarity"], r.get("title", "")))

    # Apply limit
    results = candidates[: args.limit]

    if not results:
        print("No similar papers found.", file=sys.stderr)
        sys.exit(0)

    # Use a format function that includes similarity score
    def format_result(r: dict) -> str:
        pid = r.get("paperId", "?")[:12]
        title = r.get("title", "Unknown")[:50]
        year = r.get("year", "?")
        sim = r.get("similarity", 0.0)
        return f"{pid}...  {year}  sim={sim:.4f}  {title}"

    emit_results(results, args, format_fn=format_result)


if __name__ == "__main__":
    main()
