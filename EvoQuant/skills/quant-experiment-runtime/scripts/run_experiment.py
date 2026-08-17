#!/usr/bin/env python3
"""CLI for the Quant Research Experiment Executor.

Runs one or many Candidates against a panel and emits unified ExperimentResult
JSON. Candidate JSON format::

    { "id": "...", "compute_ref": "path/to/code.py::run", "params": {...}, "metadata": {...} }

Single candidate file may be either a Candidate object or a list of Candidates
(batch). ``--panel`` is a panel parquet built by build_panel.py (or any panel
with a MultiIndex(datetime, instrument) and a label column).

Example:
  python scripts/run_experiment.py --panel panel_1d.parquet \
      --candidate assets/candidate-template.json --splits train val
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _panel
import experiment_runtime as er


def _build_split_config(args) -> er.SplitConfig:
    if args.split_config:
        cfg = json.loads(Path(args.split_config).read_text(encoding="utf-8"))
        dates = cfg.get("dates")
        ratios = cfg.get("ratios")
        include_test = cfg.get("include_test", args.splits and "test" in args.splits)
        return er.SplitConfig(
            dates={k: tuple(v) for k, v in dates.items()} if dates else {},
            ratios=ratios or None,
            include_test=bool(include_test),
        )
    return er.SplitConfig(include_test=bool(args.splits and "test" in args.splits))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run quant experiments against a panel.")
    ap.add_argument("--panel", type=Path, required=True, help="panel parquet path")
    ap.add_argument(
        "--candidate", type=Path, required=True, help="Candidate JSON (object or list)"
    )
    ap.add_argument(
        "--label-col",
        type=str,
        default="label_1d_close_to_close",
        help="label column in panel",
    )
    ap.add_argument(
        "--splits", nargs="+", default=["train", "val"], help="splits to evaluate"
    )
    ap.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("./experiments/<project>/artifacts"),
        help="artifacts output root (per-cycle project dir under experiments/; e.g. experiments/01_20260729_slug/artifacts)",
    )
    ap.add_argument(
        "--split-config",
        type=Path,
        default=None,
        help="optional split config JSON (dates/ratios/include_test)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write results JSON to file (default: stdout)",
    )
    args = ap.parse_args()

    panel = _panel.load_panel(args.panel)
    if args.label_col not in panel.columns:
        avail = [c for c in panel.columns if str(c).startswith("label")]
        print(
            f"ERROR: label_col {args.label_col!r} not in panel. Available labels: {avail}",
            file=sys.stderr,
        )
        return 2

    cand_raw = json.loads(args.candidate.read_text(encoding="utf-8"))
    if isinstance(cand_raw, dict):
        cand_raw = [cand_raw]
    candidates = [er.Candidate.from_dict(c) for c in cand_raw]

    runtime = er.ExperimentRuntime(
        panel=panel,
        split_config=_build_split_config(args),
        label_col=args.label_col,
        metrics_registry=er.MetricsRegistry(),
        artifacts_dir=args.artifacts_dir,
    )
    results = runtime.run_batch(candidates, splits=tuple(args.splits))

    out = [r.to_dict() for r in results]
    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 1 if any(r.status != "ok" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
