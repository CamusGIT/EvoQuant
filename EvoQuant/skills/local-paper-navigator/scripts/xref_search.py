#!/usr/bin/env python3
"""Cross-reference search by keyword overlap.

Replaces citation_traverse.py (forward/backward/co-citation) with
keyword-overlap–based discovery across wiki JSONL records.

Direction modes:
  related          — all fields (title + keywords + tldr + abstract +
                     strategy + method + experiment + result)
                     replaces "co-citation"
  shared-keywords  — title + keywords only
                     replaces "forward citations"
  shared-method    — method + strategy only
                     replaces "backward references"

Weighting: title/keywords tokens count 2x; body tokens count 1x.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Local imports from utils
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
# Field sets per direction
# ---------------------------------------------------------------------------

# Fields that receive 2x weighting (title-like)
_TITLE_FIELDS = ("title", "keywords")

# Body fields used in 'related' mode
_BODY_FIELDS = ("tldr", "abstract", "strategy", "method", "experiment", "result")

# Direction -> (title-tier fields, body-tier fields)
DIRECTION_FIELDS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "related": (_TITLE_FIELDS, _BODY_FIELDS),
    "shared-keywords": (_TITLE_FIELDS, ()),
    "shared-method": ((), ("method", "strategy")),
}

# ---------------------------------------------------------------------------
# Token extraction helpers
# ---------------------------------------------------------------------------


def _field_text(record: dict, field: str) -> str:
    """Extract text from a wiki record field, handling lists and strings."""
    val = record.get(field)
    if val is None:
        return ""
    if isinstance(val, list):
        return " ".join(str(v) for v in val)
    return str(val)


def _extract_weighted_tokens(
    record: dict,
    title_fields: tuple[str, ...],
    body_fields: tuple[str, ...],
) -> dict[str, int]:
    """Return a token -> weight mapping for a record.

    Tokens from title_fields get weight 2; tokens from body_fields get
    weight 1.  If a token appears in both tiers it retains the higher
    weight (2).
    """
    token_weights: dict[str, int] = {}
    for field in title_fields:
        for tok in tokenize(_field_text(record, field)):
            token_weights[tok] = 2
    for field in body_fields:
        for tok in tokenize(_field_text(record, field)):
            # Only downgrade if not already present at weight 2
            if tok not in token_weights:
                token_weights[tok] = 1
    return token_weights


# ---------------------------------------------------------------------------
# Overlap scoring
# ---------------------------------------------------------------------------


def _overlap_score(
    seed_tokens: dict[str, int],
    candidate_tokens: dict[str, int],
) -> int:
    """Compute weighted overlap score between two token-weight maps."""
    score = 0
    for tok, seed_w in seed_tokens.items():
        cand_w = candidate_tokens.get(tok)
        if cand_w is not None:
            # The overlap contribution is the product of weights,
            # capped by the minimum weight so duplicate tokens don't
            # explode the score.  In practice: min(seed_w, cand_w)
            # gives a clean 1 or 2 per shared token.
            score += min(seed_w, cand_w)
    return score


def _raw_overlap_count(
    seed_tokens: dict[str, int],
    candidate_tokens: dict[str, int],
) -> int:
    """Return the count of distinct shared tokens (ignoring weights)."""
    return len(set(seed_tokens) & set(candidate_tokens))


# ---------------------------------------------------------------------------
# Main search
# ---------------------------------------------------------------------------


def xref_search(
    seed_id: str,
    direction: str = "related",
    limit: int = 15,
    min_overlap: int = 2,
    year_min: int | None = None,
    year_max: int | None = None,
    workspace_dir: Path | None = None,
) -> list[dict]:
    """Search wiki records for keyword overlap with a seed paper.

    Returns a list of dicts sorted by descending overlap score, each
    augmented with 'overlapScore' and 'overlapCount' keys.
    """
    seed = load_wiki_record(seed_id, workspace_dir=workspace_dir)
    if seed is None:
        print(f"Error: seed paper not found: {seed_id}", file=sys.stderr)
        return []

    title_fields, body_fields = DIRECTION_FIELDS[direction]
    seed_tokens = _extract_weighted_tokens(seed, title_fields, body_fields)

    if not seed_tokens:
        print(
            f"Warning: seed paper has no extractable tokens for direction '{direction}'",
            file=sys.stderr,
        )
        return []

    all_records = load_all_wiki_records(workspace_dir=workspace_dir)
    results: list[dict] = []

    for rec in all_records:
        # Skip the seed itself
        if rec.get("paperId") == seed_id:
            continue

        # Year filtering
        rec_year = rec.get("year")
        if rec_year is not None:
            if year_min is not None and rec_year < year_min:
                continue
            if year_max is not None and rec_year > year_max:
                continue

        cand_tokens = _extract_weighted_tokens(rec, title_fields, body_fields)
        overlap_count = _raw_overlap_count(seed_tokens, cand_tokens)

        if overlap_count < min_overlap:
            continue

        score = _overlap_score(seed_tokens, cand_tokens)

        # Shallow-copy the record and attach scoring metadata
        entry = dict(rec)
        entry["overlapScore"] = score
        entry["overlapCount"] = overlap_count
        results.append(entry)

    # Sort by overlapScore descending, then overlapCount as tiebreaker
    results.sort(key=lambda r: (r["overlapScore"], r["overlapCount"]), reverse=True)

    return results[:limit]


# ---------------------------------------------------------------------------
# CLI formatting helper
# ---------------------------------------------------------------------------


def _format_result(r: dict) -> str:
    pid = r.get("paperId", "?")[:12]
    title = r.get("title", "Unknown")[:60]
    year = r.get("year", "?")
    score = r.get("overlapScore", 0)
    count = r.get("overlapCount", 0)
    return f"{pid}...  {year}  score={score:<4d} overlap={count:<3d}  {title}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-reference search by keyword overlap across wiki records",
    )
    parser.add_argument(
        "--paper-id",
        required=True,
        help="SHA-256 paperId of the seed paper",
    )
    parser.add_argument(
        "--direction",
        choices=list(DIRECTION_FIELDS.keys()),
        default="related",
        help="Direction mode: related (all fields), shared-keywords (title+keywords), "
        "shared-method (method+strategy) [default: related]",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum number of results [default: 15]",
    )
    parser.add_argument(
        "--min-overlap",
        type=int,
        default=2,
        help="Minimum number of shared tokens [default: 2]",
    )
    parser.add_argument(
        "--year-min",
        type=int,
        default=None,
        help="Only include papers from this year onward",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=None,
        help="Only include papers up to and including this year",
    )
    add_workspace_args(parser)
    add_output_args(parser)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    workspace_dir = resolve_workspace(args)

    results = xref_search(
        seed_id=args.paper_id,
        direction=args.direction,
        limit=args.limit,
        min_overlap=args.min_overlap,
        year_min=args.year_min,
        year_max=args.year_max,
        workspace_dir=workspace_dir,
    )

    emit_results(results, args, format_fn=_format_result)


if __name__ == "__main__":
    main()
