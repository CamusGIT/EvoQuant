#!/usr/bin/env python3
"""Autonomous data discovery for the Quant Research Experiment Executor.

Scans a code-repo root for data packages (directories containing a data-repo
``MANIFEST.json`` and/or ``README.md``), parses their layout, and emits a JSON
catalog of usable datasets. The Runtime does NOT hard-code any dataset path --
the agent inspects this catalog, picks a dataset, and passes its ``root`` to
the panel builder.

Note: the ``MANIFEST.json`` parsed here is the *data-repo* manifest (a file
list shipped with the data package), NOT an Artifact manifest -- the Executor
introduces no manifest for research artifacts.

Output (stdout JSON):
  {
    "code_repo": "<code-repo-dir>",
    "datasets": [
      {
        "name": "<dataset-folder-name>",        # the real folder name under code-repo
        "root": "<abs path to the dataset dir>",
        "manifest": { ... parsed MANIFEST.json ... },
        "readme_head": "<first lines of README.md>",
        "files": [ {"path": "...", "bytes": .., "num_rows": ..}, ... ],
        "artifacts_root": "<root>/artifacts"   # if present
      }, ...
    ]
  }

The dataset name is whatever the folder is actually called under the code-repo
(it is not fixed); the agent reads this catalog and passes the chosen
``root`` to ``build_panel.py --data-root``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _read_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _readme_head(path: Path, max_chars: int = 600) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except OSError:
        return ""


def _parse_manifest(manifest: dict) -> list[dict]:
    """Extract the file list from a data-repo MANIFEST.json (best-effort)."""
    files = manifest.get("files") if isinstance(manifest, dict) else None
    out: list[dict] = []
    if isinstance(files, list):
        for f in files:
            if not isinstance(f, dict):
                continue
            out.append(
                {
                    "path": str(f.get("path", "")),
                    "bytes": f.get("bytes"),
                    "num_rows": f.get("num_rows"),
                    "sha256": f.get("sha256"),
                }
            )
    return out


def discover(code_repo: Path) -> dict:
    code_repo = code_repo.resolve()
    datasets: list[dict] = []
    if not code_repo.exists():
        return {
            "code_repo": str(code_repo),
            "datasets": [],
            "error": "code-repo not found",
        }

    # a dataset = any directory containing MANIFEST.json or README.md
    for manifest_path in sorted(code_repo.rglob("MANIFEST.json")):
        ds_root = manifest_path.parent
        manifest = _read_json(manifest_path) or {}
        files = _parse_manifest(manifest)
        readme = ds_root / "README.md"
        artifacts_root = ds_root / "artifacts"
        datasets.append(
            {
                "name": ds_root.name,
                "root": str(ds_root),
                "manifest_path": str(manifest_path),
                "manifest": {
                    "name": manifest.get("name"),
                    "generated": manifest.get("generated"),
                }
                if manifest
                else None,
                "files": files,
                "readme_head": _readme_head(readme) if readme.exists() else "",
                "artifacts_root": str(artifacts_root)
                if artifacts_root.exists()
                else None,
            }
        )

    # also pick up dataset-like dirs that only have a README.md (no MANIFEST)
    seen_roots = {d["root"] for d in datasets}
    for readme_path in sorted(code_repo.rglob("README.md")):
        ds_root = readme_path.parent
        if str(ds_root) in seen_roots:
            continue
        # only treat as a dataset if it has parquet files underneath
        parquets = list(ds_root.rglob("*.parquet"))
        if not parquets:
            continue
        artifacts_root = ds_root / "artifacts"
        datasets.append(
            {
                "name": ds_root.name,
                "root": str(ds_root),
                "manifest_path": None,
                "manifest": None,
                "files": [{"path": str(p.relative_to(ds_root))} for p in parquets[:50]],
                "readme_head": _readme_head(readme),
                "artifacts_root": str(artifacts_root)
                if artifacts_root.exists()
                else None,
            }
        )

    return {"code_repo": str(code_repo), "datasets": datasets}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Discover usable datasets under a code-repo."
    )
    ap.add_argument(
        "--code-repo",
        type=Path,
        default=Path("code-repo"),
        help="code-repo dir to scan (relative to the EvoQuant workdir/cwd; default 'code-repo')",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write catalog JSON to file (default: stdout)",
    )
    args = ap.parse_args()

    catalog = discover(args.code_repo)
    text = json.dumps(catalog, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(
            f"wrote {args.out} ({len(catalog.get('datasets', []))} datasets)",
            file=sys.stderr,
        )
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
