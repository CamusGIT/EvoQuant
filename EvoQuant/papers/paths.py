"""Papers path resolution — where the papers library lives.

Kept dependency-free (stdlib only) on purpose: the top-level ``paths``
module imports this at load time, so any heavyweight import here would
slow every CLI startup.
"""

from __future__ import annotations

import os
from pathlib import Path

# papers/ lives at EvoQuant/EvoQuant/papers/ → repo root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_papers_dir(explicit: str | Path | None = None) -> Path | None:
    """Locate the library directory; ``None`` means "no library" (graceful no-op).

    Precedence: explicit argument > ``EVOSCIENTIST_PAPERS_DIR`` env var
    (legacy alias: ``EVOSCIENTIST_CORPUS_DIR``) >
    ``<repo>/papers``. The first candidate that actually exists wins; a
    missing path is skipped, and if none exists we return ``None`` so callers
    can skip mounting the ``/papers/`` route and the paper tools entirely
    instead of erroring at startup.
    """
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_val = os.getenv("EVOSCIENTIST_PAPERS_DIR") or os.getenv(
        # Legacy alias kept so existing shell exports keep working.
        "EVOSCIENTIST_CORPUS_DIR"
    )
    if env_val:
        candidates.append(Path(env_val).expanduser())
    candidates.append(_REPO_ROOT / "papers")

    for cand in candidates:
        if cand.is_dir():
            return cand.resolve()
    return None


def papers_are_available(papers_dir: str | Path | None) -> bool:
    """True only when the dir actually holds papers content.

    A bare ``papers/`` directory (e.g. freshly cloned, data not synced) does
    not count: we require ``cards/`` or ``index.jsonl`` — the two artifacts
    every migrate/extract run produces.
    """
    if not papers_dir:
        return False
    root = Path(papers_dir)
    if not root.is_dir():
        return False
    return (root / "cards").is_dir() or (root / "index.jsonl").is_file()
