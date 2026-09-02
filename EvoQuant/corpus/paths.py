"""Corpus path resolution — where the paper corpus lives.

Kept dependency-free (stdlib only) on purpose: the top-level ``paths``
module imports this at load time, so any heavyweight import here would
slow every CLI startup.
"""

from __future__ import annotations

import os
from pathlib import Path

# corpus/ lives at EvoQuant/EvoQuant/corpus/ → repo root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_corpus_dir(explicit: str | Path | None = None) -> Path | None:
    """Locate the corpus directory; ``None`` means "no corpus" (graceful no-op).

    Precedence: explicit argument > ``EVOSCIENTIST_CORPUS_DIR`` env var >
    ``<repo>/papers``. The first candidate that actually exists wins; a
    missing path is skipped, and if none exists we return ``None`` so callers
    can skip mounting the ``/papers/`` route and the paper tools entirely
    instead of erroring at startup.
    """
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_val = os.getenv("EVOSCIENTIST_CORPUS_DIR")
    if env_val:
        candidates.append(Path(env_val).expanduser())
    candidates.append(_REPO_ROOT / "papers")

    for cand in candidates:
        if cand.is_dir():
            return cand.resolve()
    return None


def corpus_is_available(corpus_dir: str | Path | None) -> bool:
    """True only when the dir actually holds corpus content.

    A bare ``papers/`` directory (e.g. freshly cloned, data not synced) does
    not count: we require ``cards/`` or ``index.jsonl`` — the two artifacts
    every migrate/extract run produces.
    """
    if not corpus_dir:
        return False
    root = Path(corpus_dir)
    if not root.is_dir():
        return False
    return (root / "cards").is_dir() or (root / "index.jsonl").is_file()
