"""Onboarding hints: tell a first-time user how to feed the library.

Pure functions — the CLI prints whatever they return, nothing else. The
hints are stateless: derived entirely from what is (or is not) on disk,
so a hint disappears the moment the condition that raised it clears. No
"shown once" flag file: a healthy library prints nothing at all.
"""

from __future__ import annotations

import json
from pathlib import Path


def onboarding_hint(papers_dir: Path | str | None) -> str | None:
    """One actionable line for a new user; ``None`` when all is well.

    Branches:
    1. No papers directory at all → point at ``papers/raw/`` and the
       「入库」 trigger phrase.
    2. ``raw/`` holds PDFs the manifest does not mark ``extraction_done``
       → count them and point at the same trigger.
    3. Everything ingested → ``None`` (zero output, no noise for
       returning users).
    """
    if papers_dir is None or not Path(papers_dir).is_dir():
        return (
            "语料库未初始化：把研报 PDF 放入仓库根的 papers/raw/ "
            "（先 mkdir -p papers/raw），然后对 agent 说「入库」。"
        )
    root = Path(papers_dir)
    raw_dir = root / "raw"
    raw_pdfs = sorted(raw_dir.glob("*.pdf")) if raw_dir.is_dir() else []
    ingested = _ingested_ids(root)
    pending = [p for p in raw_pdfs if p.stem not in ingested]
    if pending:
        return (
            f"检测到 {len(pending)} 份未入库 PDF（papers/raw/）。"
            "对 agent 说「入库」即可构建语料库；"
            "入库后 paper 工具自新会话起可用。"
        )
    return None


def _ingested_ids(root: Path) -> set[str]:
    """paperIds the manifest marks fully extracted (card written)."""
    manifest = root / "manifest.jsonl"
    if not manifest.is_file():
        return set()
    done: set[str] = set()
    with manifest.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("status") == "extraction_done":
                done.add(entry.get("paperId", ""))
    return done
