#!/usr/bin/env bash
# Sync the fixed eval-workspace snapshot from the real research workspace.
#
# Whole-directory copies only — pairing is guaranteed by manifest.jsonl
# (each line maps paperId <-> sourcePdf <-> markdownPath <-> wikiPath), so
# there is no manual file picking and no way to mismatch pairs. Other test
# artifacts in the source workspace (artifacts/, experiments/, code-repo/,
# .bg_processes/, drafts, ...) are deliberately NOT copied.
#
# Usage:
#   bash tests/evals/fixtures/sync_from_source.sh
# Override the source with EVOSCIENTIST_EVAL_WS_SOURCE if it moves.
set -euo pipefail

SRC="${EVOSCIENTIST_EVAL_WS_SOURCE:-/Users/caishijie/LLM/Agent/EvoScientist/workspace}"
DEST="$(cd "$(dirname "$0")" && pwd)/workspace"

if [ ! -f "$SRC/manifest.jsonl" ]; then
    echo "ERROR: $SRC/manifest.jsonl not found (bad source workspace?)" >&2
    exit 1
fi

mkdir -p "$DEST"
for item in rawpaper wiki markdown; do
    rm -rf "$DEST/$item"
    cp -R "$SRC/$item" "$DEST/$item"
done
cp "$SRC/manifest.jsonl" "$DEST/manifest.jsonl"

# Integrity check: every manifest entry's three files must exist in the copy.
python3 - "$DEST/manifest.jsonl" <<'PY'
import json
import pathlib
import sys

manifest = pathlib.Path(sys.argv[1])
root = manifest.parent
rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
missing = []
for row in rows:
    for key in ("sourcePdf", "markdownPath", "wikiPath"):
        if not (root / row[key]).exists():
            missing.append(f"{row['paperId'][:12]}: {key} -> {row[key]}")
if missing:
    print("SNAPSHOT INCOMPLETE:")
    print("\n".join(missing))
    sys.exit(1)
print(f"snapshot OK: {len(rows)} papers, all source/markdown/wiki files present")
PY
