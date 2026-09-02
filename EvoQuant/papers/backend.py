"""PapersBackend: a read-only, filtered view over the papers library.

Mounted at the ``/papers/`` virtual route. The library holds three layers
with different access policies:

    /papers/cards/**        readable    — paper cards, the default layer
    /papers/context_brief.md, index.jsonl, manifest.jsonl
                            readable    — overview + derived indexes
    /papers/markdown/**     blocked     — full texts caused context blowups;
                                          reach them per-section via
                                          ``paper_section`` instead
    /papers/raw/**          blocked     — original PDFs (also up to 4.4MB of
                                          base64); the card carries the
                                          distilled content

Every block is a *guiding* error: it names the tool call that works instead,
so a blocked read reads as a redirect, not a failure.

Two invariants keep the CompositeBackend merge safe (composite.py merges
global grep/glob across routes and any route error would poison the whole
result):

1. Global-scope grep/glob NEVER returns an error — failures degrade to
   empty/partial matches.
2. Global-scope grep/glob only searches the readable layer (cards + root
   files), so full-text lines never leak into workspace-wide searches.
"""

from __future__ import annotations

import fnmatch
import posixpath
from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import (
    EditResult,
    FileDownloadResponse,
    FileUploadResponse,
    GlobResult,
    GrepResult,
    ReadResult,
    WriteResult,
)

_MARKDOWN_BLOCKED = (
    "Full-text reads under /papers/markdown are blocked by design — whole "
    "papers previously blew up the context window. Use "
    "paper_section(paper_id, heading) to read one section, or "
    "paper_read(paper_id) for the structured card (sections outline included)."
)
_RAW_BLOCKED = (
    "PDFs under /papers/raw are blocked by design (multi-MB base64). Use "
    "paper_read(paper_id) — the card already carries the distilled content, "
    "and paper_section(paper_id, heading) reaches any section verbatim."
)
_WRITE_BLOCKED = (
    "The papers library is read-only (it is shared reference data, not "
    "workspace state). Write experiments to the workspace instead."
)
_GLOBAL_GREP_BLOCKED_HINT = (
    " (Global paper search covers cards and index files only; to search "
    "full texts use paper_search.)"
)

# Root files agents may read directly (everything else at the root is either
# derived or internal).
_ROOT_FILES = ("context_brief.md", "index.jsonl", "manifest.jsonl")


def _normalize(virtual_path: str) -> str:
    """Canonical virtual path inside the route: absolute, ``..`` collapsed.

    Normalization happens BEFORE policy checks so ``/cards/../markdown/x``,
    ``/markdown//x`` and friends cannot smuggle a blocked path through.
    """
    return posixpath.normpath("/" + virtual_path.strip().lstrip("/"))


def _in_layer(path: str, layer: str) -> bool:
    """True when the normalized path is the layer dir or inside it."""
    return path == f"/{layer}" or path.startswith(f"/{layer}/")


class PapersBackend(FilesystemBackend):
    """Read-only filtered view over ``papers_dir`` for the /papers/ route."""

    def __init__(self, papers_dir: str | Path):
        super().__init__(root_dir=str(papers_dir), virtual_mode=True)

    # ------------------------------------------------------------------
    # Reads: cards + root files pass through; markdown/raw redirect.
    # ------------------------------------------------------------------
    def read(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> ReadResult:
        normalized = _normalize(file_path)
        if _in_layer(normalized, "markdown"):
            return ReadResult(error=_MARKDOWN_BLOCKED)
        if _in_layer(normalized, "raw"):
            return ReadResult(error=_RAW_BLOCKED)
        return super().read(file_path, offset, limit)

    # ------------------------------------------------------------------
    # Grep. Two scopes with different rules:
    #   * Explicit path: normal behavior; markdown/raw get a guiding error
    #     (only this one grep call is affected — safe under CompositeBackend).
    #   * Global scope (path None/"/"): NEVER error — the composite merge
    #     would poison every other route's matches with ours. Also restrict
    #     the search to the readable layer so full-text lines stay out of
    #     workspace-wide searches.
    # ------------------------------------------------------------------
    def grep(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> GrepResult:
        if path is None or path == "/":
            return self._grep_readable_layer(pattern, glob)

        normalized = _normalize(path)
        if _in_layer(normalized, "markdown") or _in_layer(normalized, "raw"):
            blocked = _MARKDOWN_BLOCKED if _in_layer(normalized, "markdown") else _RAW_BLOCKED
            return GrepResult(error=blocked + _GLOBAL_GREP_BLOCKED_HINT, matches=[])
        return super().grep(pattern, path, glob)

    def _grep_readable_layer(self, pattern: str, glob: str | None) -> GrepResult:
        """Search cards/ + root files; degrade to partial/empty on errors.

        ``cards/`` goes through the parent (directory scopes behave the same
        under ripgrep and the Python fallback). Root files are searched by
        hand instead: the parent's Python fallback walks the whole tree for
        single-file scopes (upstream bug), which is exactly the full-text
        leak this backend exists to prevent.
        """
        matches: list[dict] = []
        try:
            result = super().grep(pattern, "cards", glob)
            if not result.error:
                matches.extend(result.matches or [])
        except Exception:  # noqa: BLE001 — global scope must never raise
            pass

        for name in _ROOT_FILES:
            file_path = self.cwd / name
            if not file_path.is_file():
                continue
            if glob and not fnmatch.fnmatch(name, glob):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if pattern in line:
                    matches.append({"path": f"/{name}", "line": line_no, "text": line})
        return GrepResult(matches=matches)

    # ------------------------------------------------------------------
    # Glob. CompositeBackend ignores route errors for glob, but leaking
    # markdown/raw *filenames* invites agents to try reading them — so the
    # global scope filters results down to the readable layer anyway.
    # ------------------------------------------------------------------
    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        if path is None or path == "/":
            try:
                result = super().glob(pattern, "/")
            except Exception as exc:  # noqa: BLE001 — never error globally
                return GlobResult(matches=[])
            if result.error:
                return GlobResult(matches=[])
            readable = [
                fi
                for fi in (result.matches or [])
                if not (
                    _in_layer(_normalize(fi.get("path", "")), "markdown")
                    or _in_layer(_normalize(fi.get("path", "")), "raw")
                )
            ]
            return GlobResult(matches=readable)

        normalized = _normalize(path)
        if _in_layer(normalized, "markdown") or _in_layer(normalized, "raw"):
            blocked = _MARKDOWN_BLOCKED if _in_layer(normalized, "markdown") else _RAW_BLOCKED
            return GlobResult(error=blocked)
        return super().glob(pattern, path)

    # ------------------------------------------------------------------
    # Mutations: all blocked, including download (the base64 side-channel
    # that previously shipped 4.4MB PDFs into the context).
    # ------------------------------------------------------------------
    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error=_WRITE_BLOCKED)

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error=_WRITE_BLOCKED)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return [
            FileUploadResponse(path=file_path, error=_WRITE_BLOCKED)
            for file_path, _ in files
        ]

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        return [
            FileDownloadResponse(path=p, content=None, error=_RAW_BLOCKED)
            for p in paths
        ]
