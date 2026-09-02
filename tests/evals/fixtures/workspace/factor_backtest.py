"""Minimal single-factor backtest: monthly IC / ICIR of one simulated factor.

Self-contained on purpose — no data files: the factor panel and forward
returns are drawn from a seeded RNG (factor + noise for returns), so results
depend only on ``--seed`` and "run it and see" always works.

Current behavior: one seed per run, metrics appended to
``artifacts/metrics.json``.
"""

import argparse
import json
from pathlib import Path

import numpy as np

OUT_PATH = Path("artifacts/metrics.json")


def load_factor_panel(seed: int, n_dates: int = 24, n_tickers: int = 50):
    """Simulate a monthly factor panel and next-month returns.

    Returns (dates, tickers, factor, forward_return) where factor and
    forward_return are (n_dates, n_tickers) arrays; returns embed the factor
    with noise so a nonzero IC is guaranteed.
    """
    rng = np.random.default_rng(seed)
    factor = rng.standard_normal((n_dates, n_tickers))
    noise = rng.standard_normal((n_dates, n_tickers))
    forward_return = 0.2 * factor + noise
    dates = [f"2024-{m:02d}-28" for m in range(1, n_dates + 1)]
    tickers = [f"S{i:03d}" for i in range(n_tickers)]
    return dates, tickers, factor, forward_return


def compute_ic_series(factor: np.ndarray, forward_return: np.ndarray):
    """Cross-sectional Spearman IC per date (rank correlation factor vs return)."""
    from scipy.stats import spearmanr

    return [
        float(spearmanr(factor[t], forward_return[t]).statistic)
        for t in range(factor.shape[0])
    ]


def run_backtest(seed: int) -> dict:
    dates, tickers, factor, forward_return = load_factor_panel(seed)
    ic_series = compute_ic_series(factor, forward_return)
    ic_arr = np.asarray(ic_series)
    return {
        "seed": seed,
        "n_dates": len(dates),
        "n_tickers": len(tickers),
        "ic_mean": float(ic_arr.mean()),
        "ic_std": float(ic_arr.std()),
        "icir": float(ic_arr.mean() / ic_arr.std()) if ic_arr.std() > 0 else 0.0,
        "run_config": {"model": "simulated-panel", "seed": seed},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()

    metrics = run_backtest(args.seed)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"seed={args.seed} ic_mean={metrics['ic_mean']:.4f} "
          f"icir={metrics['icir']:.4f} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
