"""Incremental papers refresh: rebuild the derived artifacts after ingestion.

Thin CLI over :mod:`EvoQuant.papers.migrate`'s pure functions — called by
the quant-paper-extractor skill after each new card lands:

    python -m EvoQuant.papers.refresh [paperId ...]

``context_brief.md`` and ``index.jsonl`` are cheap full recomputes over
cards/ (milliseconds at current scale); the optional paperId arguments are
accepted for call-site ergonomics and logged, but the recompute is always
total so the derived files can never drift from cards/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .migrate import refresh_derived
from .paths import resolve_papers_dir


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    papers_dir = resolve_papers_dir()
    if papers_dir is None:
        print("No papers directory found; set EVOSCIENTIST_PAPERS_DIR.", file=sys.stderr)
        return 2
    refresh_derived(Path(papers_dir))
    note = f" (noted: {', '.join(argv)})" if argv else ""
    print(f"refreshed context_brief.md + index.jsonl in {papers_dir}{note}")
    print(
        "note: paper tools mount at agent startup — "
        "start a new session to use them"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
