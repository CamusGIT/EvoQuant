"""Incremental corpus refresh: rebuild the derived artifacts after ingestion.

Thin CLI over :mod:`EvoQuant.corpus.migrate`'s pure functions — called by
the quant-paper-extractor skill after each new card lands:

    python -m EvoQuant.corpus.refresh [paperId ...]

``context_brief.md`` and ``index.jsonl`` are cheap full recomputes over
cards/ (milliseconds at current scale); the optional paperId arguments are
accepted for call-site ergonomics and logged, but the recompute is always
total so the derived files can never drift from cards/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .migrate import refresh_derived
from .paths import resolve_corpus_dir


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    corpus_dir = resolve_corpus_dir()
    if corpus_dir is None:
        print("No corpus directory found; set EVOSCIENTIST_CORPUS_DIR.", file=sys.stderr)
        return 2
    refresh_derived(Path(corpus_dir))
    note = f" (noted: {', '.join(argv)})" if argv else ""
    print(f"refreshed context_brief.md + index.jsonl in {corpus_dir}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
