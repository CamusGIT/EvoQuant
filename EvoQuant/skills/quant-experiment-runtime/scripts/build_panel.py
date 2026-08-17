#!/usr/bin/env python3
"""Offline panel builder for the Quant Research Experiment Executor.

Builds a daily panel from a discovered data package's local parquet cache --
**offline, no network / no token**. The data package layout (from
``discover_data.py``) is::

    <data-root>/artifacts/
      market/daily_hq.parquet
      fundamental/quarterly.parquet
      industry/sw_l1_membership.parquet
      index/<code>_members.parquet

v1 builds a price-volume panel (no fundamental/industry enrichment) —
sufficient for IC-style factor evaluation.

Example:
  # <selected-dataset-root> comes from discover_data.py output, never typed by hand
  python EvoQuant/skills/quant-experiment-runtime/scripts/build_panel.py \
    --data-root code-repo/<dataset-folder> \
    --out experiments/<project>/panel_1d.parquet --start 2019-01-01 --end 2026-06-30
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _panel


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Offline panel builder from a data package."
    )
    ap.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="data package root (containing artifacts/); from discover_data.py",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("panel_1d.parquet"),
        help="output panel parquet path",
    )
    ap.add_argument("--start", type=str, default=None, help="coverage start YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="coverage end YYYY-MM-DD")
    ap.add_argument(
        "--no-universe-mask", action="store_true", help="do not filter tradable/non-ST"
    )
    args = ap.parse_args()

    data_root: Path = args.data_root.resolve()
    if not data_root.exists():
        print(f"ERROR: data-root not found: {data_root}", file=sys.stderr)
        return 2
    market_path = data_root / "artifacts" / "market" / "daily_hq.parquet"
    if not market_path.exists():
        print(f"ERROR: market cache not found: {market_path}", file=sys.stderr)
        return 2

    print(f"[build_panel] data_root={data_root} -> {args.out}", file=sys.stderr)
    panel = _panel.build_panel(
        start=args.start,
        end=args.end,
        out_path=args.out,
        market_path=market_path,
        universe_mask=not args.no_universe_mask,
    )
    print(
        f"[build_panel] panel shape={panel.shape} cols={list(panel.columns)[:6]}...",
        file=sys.stderr,
    )

    loaded = _panel.load_panel(args.out)
    print(f"[verify] reloaded shape={loaded.shape}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
