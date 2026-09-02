"""One-shot migration: workspace legacy layout → repo root layout.

Moves (hard-links when possible, never deletes until asked):

    workspace/rawpaper/{中文名}.pdf   →  root/raw/{paperId}.pdf
    workspace/markdown/{paperId}.md   →  root/markdown/{paperId}.md
    workspace/wiki/{paperId}.jsonl    →  root/cards/{paperId}.jsonl
    workspace/manifest.jsonl          →  root/manifest.jsonl (+ papersPath)

then derives ``context_brief.md`` and ``index.jsonl``. With ``prune=True``
the legacy trio is moved into ``workspace/_papers_migrated_backup_<date>/``
(moved, not deleted).

The paperId rename is the point: PDFs stop being addressed by Chinese
filenames agents had to guess, and every layer (pdf/markdown/card) shares
one join key.

Run: ``python -m EvoQuant.papers.migrate --workspace-dir ... [--dry-run]``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from .paths import papers_are_available
from .tools import _load_cards

_LEGACY_DIRS = ("rawpaper", "markdown", "wiki")
_LEGACY_MANIFEST = "manifest.jsonl"


def _file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _load_manifest(workspace_dir: Path) -> list[dict]:
    manifest_path = workspace_dir / _LEGACY_MANIFEST
    if not manifest_path.is_file():
        return []
    entries = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # skip corrupt lines rather than abort the migration
    return entries


def build_context_brief(papers_dir: Path) -> str:
    """Rules-only brief (no LLM): one entry per paper, year-desc, kw cloud."""
    cards = _load_cards(papers_dir)
    cards = sorted(cards, key=lambda c: str(c.get("year", "")), reverse=True)
    lines = [f"# Papers brief — {len(cards)} papers"]
    for card in cards[:20]:
        tldr = str(card.get("tldr", "")).replace("\n", " ")
        lines.append(
            f"\n## {card.get('title', '(untitled)')} "
            f"({card.get('year', '?')}, {card.get('source', '?')})\n"
            f"- id: {str(card.get('paperId', ''))[:12]} — {tldr}"
        )
    if len(cards) > 20:
        lines.append(f"\n(+{len(cards) - 20} more — paper_search discovers them)")
    kw_counts: dict[str, int] = {}
    for card in cards:
        for kw in card.get("keywords") or []:
            kw_counts[str(kw)] = kw_counts.get(str(kw), 0) + 1
    cloud = sorted(kw_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:30]
    if cloud:
        lines.append("\n## Keywords\n" + ", ".join(kw for kw, _ in cloud))
    return "\n".join(lines) + "\n"


def _markdown_title_cn(papers_dir: Path, paper_id: str) -> str:
    """Original Chinese title: first ``# `` line of the markdown, minus .pdf."""
    md = papers_dir / "markdown" / f"{paper_id}.md"
    if not md.is_file():
        return ""
    try:
        for line in md.read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
            line = line.strip()
            if line.startswith("# ") and not line.startswith("# Total"):
                title = line[2:].strip()
                if title.endswith(".pdf"):
                    title = title[: -len(".pdf")]
                return title
    except OSError:
        pass
    return ""


def build_index(papers_dir: Path) -> str:
    """Derived index.jsonl content: one compact record per card.

    ``titleCn`` (the markdown's original heading) is extracted here once
    so runtime search needs no extra IO — it is what lets Chinese queries
    find cards whose summaries are English.
    """
    records = []
    for card in _load_cards(papers_dir):
        paper_id = str(card.get("paperId", ""))
        records.append(
            json.dumps(
                {
                    "paperId": paper_id,
                    "title": card.get("title", ""),
                    "titleCn": _markdown_title_cn(papers_dir, paper_id),
                    "year": card.get("year"),
                    "source": card.get("source", ""),
                    "keywords": card.get("keywords") or [],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(records) + ("\n" if records else "")


def refresh_derived(papers_dir: Path) -> None:
    """(Re)write context_brief.md and index.jsonl from cards/."""
    (papers_dir / "context_brief.md").write_text(
        build_context_brief(papers_dir), encoding="utf-8"
    )
    (papers_dir / "index.jsonl").write_text(
        build_index(papers_dir), encoding="utf-8"
    )


def _transfer(src: Path, dst: Path, *, link: bool, dry_run: bool, log: list[str]) -> bool:
    """Copy/link src→dst; True when done or already identical (idempotent)."""
    if not src.exists():
        log.append(f"MISS  {src.name}: source missing, skipped")
        return False
    if dst.exists():
        if _file_sha256(src) == _file_sha256(dst):
            log.append(f"KEEP  {dst.name}: identical, skipped")
            return True
        log.append(f"DIFF  {dst.name}: hashes differ, destination overwritten")
    if dry_run:
        log.append(f"PLAN  {src} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    if link:
        try:
            if dst.exists():
                dst.unlink()
            dst.hardlink_to(src)
            log.append(f"LINK  {dst}")
            return True
        except OSError:
            pass  # cross-device etc. — fall through to copy
    shutil.copy2(src, dst)
    log.append(f"COPY  {src} -> {dst}")
    return True


def migrate(
    workspace_dir: str | Path,
    papers_dir: str | Path,
    *,
    link: bool = True,
    prune: bool = True,
    dry_run: bool = False,
) -> list[str]:
    """Migrate the legacy workspace trio into the root; returns the log."""
    workspace = Path(workspace_dir)
    root = Path(papers_dir)
    manifest = _load_manifest(workspace)
    done = [m for m in manifest if m.get("status") == "extraction_done"]
    log = [f"manifest: {len(done)}/{len(manifest)} entries extraction_done"]

    if not dry_run:
        for sub in ("raw", "markdown", "cards"):
            (root / sub).mkdir(parents=True, exist_ok=True)

    new_manifest_lines = []
    for entry in done:
        paper_id = str(entry.get("paperId", ""))
        if not paper_id:
            continue
        src_pdf = workspace / str(entry.get("sourcePdf", ""))
        _transfer(src_pdf, root / "raw" / f"{paper_id}.pdf", link=link, dry_run=dry_run, log=log)
        md_rel = str(entry.get("markdownPath", "")).removeprefix("markdown/")
        _transfer(
            workspace / "markdown" / md_rel,
            root / "markdown" / f"{paper_id}.md",
            link=link, dry_run=dry_run, log=log,
        )
        wiki_rel = str(entry.get("wikiPath", "")).removeprefix("wiki/")
        _transfer(
            workspace / "wiki" / wiki_rel,
            root / "cards" / f"{paper_id}.jsonl",
            link=link, dry_run=dry_run, log=log,
        )
        record = dict(entry)
        record["papersPath"] = {
            "raw": f"raw/{paper_id}.pdf",
            "markdown": f"markdown/{paper_id}.md",
            "card": f"cards/{paper_id}.jsonl",
        }
        new_manifest_lines.append(json.dumps(record, ensure_ascii=False))

    if not dry_run and new_manifest_lines:
        (root / "manifest.jsonl").write_text(
            "\n".join(new_manifest_lines) + "\n", encoding="utf-8"
        )
    if not dry_run and papers_are_available(root):
        refresh_derived(root)
        log.append("WROTE context_brief.md + index.jsonl")

    if prune:
        legacy = [d for d in _LEGACY_DIRS if (workspace / d).is_dir()]
        if (workspace / _LEGACY_MANIFEST).is_file():
            legacy.append(_LEGACY_MANIFEST)
        if not legacy:
            log.append("PRUNE nothing to move (already migrated?)")
        elif dry_run:
            log.append(f"PRUNE PLAN move {legacy} -> workspace/_papers_migrated_backup_<date>/")
        else:
            backup = workspace / f"_papers_migrated_backup_{date.today():%Y%m%d}"
            backup.mkdir(parents=True, exist_ok=True)
            for item in legacy:
                shutil.move(str(workspace / item), str(backup / item))
            log.append(f"PRUNE moved {legacy} -> {backup.name}/")
    return log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-dir", required=True, help="legacy workspace root")
    parser.add_argument(
        "--papers-dir",
        default=None,
        help="root root (default: resolve_papers_dir(), i.e. <repo>/root)",
    )
    parser.add_argument("--no-link", action="store_true", help="copy instead of hard-link")
    parser.add_argument("--no-prune", action="store_true", help="keep legacy files in place")
    parser.add_argument("--dry-run", action="store_true", help="plan only, write nothing")
    args = parser.parse_args(argv)

    papers_dir = Path(args.papers_dir) if args.papers_dir else resolve_papers_dir_or_fail()
    log = migrate(
        args.workspace_dir,
        papers_dir,
        link=not args.no_link,
        prune=not args.no_prune,
        dry_run=args.dry_run,
    )
    print("\n".join(log))
    return 0


def resolve_papers_dir_or_fail() -> Path:
    from .paths import resolve_papers_dir

    resolved = resolve_papers_dir()
    if resolved is None:
        print("No root directory found; pass --papers-dir.", file=sys.stderr)
        raise SystemExit(2)
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
