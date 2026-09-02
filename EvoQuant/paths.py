"""Path resolution utilities for EvoQuant runtime directories."""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _expand(path: str) -> Path:
    return Path(path).expanduser()


def _env_path(key: str) -> Path | None:
    value = os.getenv(key)
    if not value:
        return None
    return _expand(value)


# Workspace root: current working directory by default (user's project dir)
WORKSPACE_ROOT = _env_path("EVOSCIENTIST_WORKSPACE_DIR") or Path.cwd()

RUNS_DIR = _env_path("EVOSCIENTIST_RUNS_DIR") or (WORKSPACE_ROOT / "runs")
USER_SKILLS_DIR = _env_path("EVOSCIENTIST_SKILLS_DIR") or (WORKSPACE_ROOT / "skills")
MEDIA_DIR = _env_path("EVOSCIENTIST_MEDIA_DIR") or (WORKSPACE_ROOT / "media")


def _global_data_dir() -> Path:
    """Global application data directory (~/.evoquant/ by default).

    This is the base for sessions.db, skills/, memories/, history — things
    that are NOT configuration but application state. Config files (config.yaml,
    mcp.yaml) continue to live in XDG_CONFIG_HOME.
    """
    return Path.home() / ".evoquant"


# Global data dir: ~/.evoquant/ by default, overridable via env var.
DATA_DIR: Path = _env_path("EVOSCIENTIST_DATA_DIR") or _global_data_dir()


def _global_skills_dir() -> Path:
    return DATA_DIR / "skills"


def _global_memories_dir() -> Path:
    return DATA_DIR / "memories"


# Global skills: shared across all workspaces (~/.evoquant/skills/)
GLOBAL_SKILLS_DIR: Path = _global_skills_dir()

# Global memories: shared across all workspaces (~/.evoquant/memories/)
GLOBAL_MEMORIES_DIR: Path = _global_memories_dir()

# Memories dir: global by default, overridable via env var.
# Supports both new (EVOSCIENTIST_MEMORIES_DIR) and old (EVOSCIENTIST_MEMORY_DIR) env vars.
MEMORIES_DIR: Path = (
    _env_path("EVOSCIENTIST_MEMORIES_DIR")
    or _env_path("EVOSCIENTIST_MEMORY_DIR")
    or GLOBAL_MEMORIES_DIR
)
MEMORY_DIR = MEMORIES_DIR  # backward compat alias

# Papers dir: repo-level read-only papers library (see papers/paths.py for the
# layout and precedence). None when no papers library exists — callers must treat
# that as "feature absent", never mount empty routes.
from .papers.paths import resolve_papers_dir  # noqa: E402  (needs constants above)

PAPERS_DIR: Path | None = resolve_papers_dir()


# DEPRECATED(0.1.0): remove this migration helper and its call site below.
def migrate_legacy_sessions_db() -> None:
    """One-time migration: copy sessions.db (and its WAL/SHM siblings) from
    ~/.config/evoquant/ to ~/.evoquant/.

    Scope is intentionally narrow — only the SQLite trio, because users can't
    easily move those by hand. User-facing files (skills/, memories/, history)
    are migrated via an agent prompt documented in the release notes.

    Idempotent via ``.migrated`` marker file. The marker is not written when
    a copy fails, so transient I/O errors don't permanently block retry.
    """
    marker = DATA_DIR / ".migrated"
    if marker.exists():
        return

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.debug("Could not create %s; skipping legacy migration.", DATA_DIR)
        return

    # Resolve legacy source via XDG_CONFIG_HOME (matches config.settings.get_config_dir).
    # Inlined here to avoid importing config.settings at paths load time.
    xdg = os.environ.get("XDG_CONFIG_HOME")
    legacy = (
        (Path(xdg) / "evoquant")
        if xdg
        else (Path.home() / ".config" / "evoquant")
    )
    if not legacy.exists():
        marker.touch()
        return

    migrated: list[str] = []
    failed: list[str] = []
    for name in ("sessions.db", "sessions.db-wal", "sessions.db-shm"):
        src = legacy / name
        dst = DATA_DIR / name
        if not src.exists():
            continue
        if dst.exists():
            continue  # already migrated
        try:
            shutil.copy2(src, dst)
            migrated.append(name)
        except OSError as e:
            logger.warning("Failed to migrate %s: %s", src, e)
            failed.append(name)

    if migrated:
        logger.info(
            "Migrated legacy session DB from %s to %s: %s. "
            "Legacy files are kept as backup; this auto-migration will be "
            "removed in EvoQuant 0.1.0.",
            legacy,
            DATA_DIR,
            ", ".join(migrated),
        )

    # Only write the marker when there were no failures — preserves retry
    # on transient I/O errors.
    if not failed:
        marker.touch()


# DEPRECATED(0.1.0): remove this call together with migrate_legacy_sessions_db().
try:
    migrate_legacy_sessions_db()
except Exception:
    # Never block startup on migration failures
    logger.exception("Legacy session DB migration failed; continuing without it.")


def set_workspace_root(path: str | Path) -> None:
    """Update workspace root and re-derive dependent directories.

    Directories with an explicit environment-variable override keep their
    env-var value; all others are re-derived from the new root.
    Also resets ``_active_workspace`` to the new root as a safe default.

    Note: MEMORIES_DIR is global (not workspace-scoped) but env var overrides
    are re-evaluated here to support late-set environment variables.
    """
    global \
        WORKSPACE_ROOT, \
        RUNS_DIR, \
        MEMORIES_DIR, \
        MEMORY_DIR, \
        USER_SKILLS_DIR, \
        MEDIA_DIR, \
        PAPERS_DIR, \
        _active_workspace
    WORKSPACE_ROOT = Path(path).resolve()
    _active_workspace = WORKSPACE_ROOT
    RUNS_DIR = _env_path("EVOSCIENTIST_RUNS_DIR") or (WORKSPACE_ROOT / "runs")
    MEMORIES_DIR = (
        _env_path("EVOSCIENTIST_MEMORIES_DIR")
        or _env_path("EVOSCIENTIST_MEMORY_DIR")
        or GLOBAL_MEMORIES_DIR
    )
    MEMORY_DIR = MEMORIES_DIR
    USER_SKILLS_DIR = _env_path("EVOSCIENTIST_SKILLS_DIR") or (
        WORKSPACE_ROOT / "skills"
    )
    MEDIA_DIR = _env_path("EVOSCIENTIST_MEDIA_DIR") or (WORKSPACE_ROOT / "media")
    # The papers library is repo-level (not workspace-scoped) but the env var is
    # re-evaluated here to support late-set environments, matching MEMORIES_DIR.
    PAPERS_DIR = resolve_papers_dir()


def ensure_dirs() -> None:
    """Create runtime subdirectories if they do not exist.

    Creates DATA_DIR (and MEMORIES_DIR as its subdir). Skills directories
    are created on demand by ``install_skill()`` when the user first
    installs a skill.

    Does NOT create the workspace root itself — it should already exist
    (either the user's cwd or a directory they specified).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)


def default_workspace_dir() -> Path:
    """Default workspace for non-CLI usage."""
    return WORKSPACE_ROOT


def new_run_dir(session_id: str | None = None) -> Path:
    """Create a new run directory name under RUNS_DIR (path only)."""
    if session_id is None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return RUNS_DIR / session_id


# Active workspace (may differ from WORKSPACE_ROOT in per-session modes)
_active_workspace: Path = WORKSPACE_ROOT


def set_active_workspace(path: str | Path) -> None:
    """Update the active workspace root (called on agent creation)."""
    global _active_workspace
    _active_workspace = Path(path).resolve()


def resolve_virtual_path(virtual_path: str) -> Path:
    """Resolve a virtual workspace path (e.g. /image.png) to a real filesystem path."""
    vpath = virtual_path if virtual_path.startswith("/") else "/" + virtual_path
    return (_active_workspace / vpath.lstrip("/")).resolve()
