"""Cross-sectional factor evaluation metrics (self-contained).

This module only needs ``numpy`` / ``pandas``. The Runtime's default
``ic_panel`` Metric delegates here.

Coverage: cross-sectional IC / ICIR / RANKIC, coverage, lag-1 cross-sectional
autocorrelation, decile-mean-label, and MLS-FMB (non-parametric monotonicity +
long/short with Newey-West t-stats). All operate on a panel with a
``MultiIndex(datetime, instrument)`` and a label column.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_LABEL_COL = "label_1d_open_to_open"
"""Default label column the IC metric evaluates against when none is given."""


def coverage(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=np.float32)
    if len(arr) == 0:
        return 0.0
    return float(np.isfinite(arr).mean())


def pearson_ic(factor: np.ndarray, label: np.ndarray, *, min_pairs: int = 30) -> float:
    x = np.asarray(factor, dtype=np.float64)
    y = np.asarray(label, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < min_pairs:
        return float("nan")
    xs = x[mask]
    ys = y[mask]
    xs = xs - xs.mean()
    ys = ys - ys.mean()
    denom = float(np.sqrt((xs * xs).sum() * (ys * ys).sum()))
    if denom <= 0.0:
        return float("nan")
    return float((xs * ys).sum() / denom)


def spearman_ic(factor: np.ndarray, label: np.ndarray, *, min_pairs: int = 10) -> float:
    x = np.asarray(factor, dtype=np.float64)
    y = np.asarray(label, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < min_pairs:
        return float("nan")
    xr = pd.Series(x[mask]).rank(method="average").to_numpy(dtype=np.float64)
    yr = pd.Series(y[mask]).rank(method="average").to_numpy(dtype=np.float64)
    return pearson_ic(xr, yr, min_pairs=min_pairs)


def cross_sectional_ic(
    factor: pd.Series,
    label: pd.Series,
    *,
    time_level: str = "datetime",
    min_pairs: int = 10,
) -> pd.Series:
    if not isinstance(factor.index, pd.MultiIndex):
        raise ValueError(
            "cross_sectional_ic 需要 MultiIndex 面板 (datetime, instrument)"
        )
    if time_level not in factor.index.names:
        raise ValueError(f"索引缺少 level={time_level!r}")
    rows: list[float] = []
    idx: list[object] = []
    for ts, f_sub in factor.groupby(level=time_level, sort=False):
        y_sub = label.xs(ts, level=time_level)
        ic = pearson_ic(
            f_sub.to_numpy(dtype=np.float64, copy=False),
            y_sub.to_numpy(dtype=np.float64, copy=False),
            min_pairs=min_pairs,
        )
        rows.append(ic)
        idx.append(ts)
    return pd.Series(rows, index=pd.Index(idx, name=time_level), dtype=float)


def cross_sectional_rank_ic(
    factor: pd.Series,
    label: pd.Series,
    *,
    time_level: str = "datetime",
    min_pairs: int = 10,
) -> pd.Series:
    if not isinstance(factor.index, pd.MultiIndex):
        raise ValueError(
            "cross_sectional_rank_ic 需要 MultiIndex 面板 (datetime, instrument)"
        )
    if time_level not in factor.index.names:
        raise ValueError(f"索引缺少 level={time_level!r}")
    rows: list[float] = []
    idx: list[object] = []
    for ts, f_sub in factor.groupby(level=time_level, sort=False):
        y_sub = label.xs(ts, level=time_level)
        ic = spearman_ic(
            f_sub.to_numpy(dtype=np.float64, copy=False),
            y_sub.to_numpy(dtype=np.float64, copy=False),
            min_pairs=min_pairs,
        )
        rows.append(ic)
        idx.append(ts)
    return pd.Series(rows, index=pd.Index(idx, name=time_level), dtype=float)


def cross_sectional_lag1_pearson_autocorr_series(
    factor: pd.Series,
    *,
    time_level: str = "datetime",
    instrument_level: str = "instrument",
    min_pairs: int = 30,
) -> pd.Series:
    if not isinstance(factor.index, pd.MultiIndex):
        raise ValueError(
            "cross_sectional_lag1_pearson_autocorr_series 需要 MultiIndex 面板"
        )
    if (
        time_level not in factor.index.names
        or instrument_level not in factor.index.names
    ):
        raise ValueError(f"索引缺少 level={time_level!r} 或 {instrument_level!r}")
    lag1 = factor.groupby(level=instrument_level, sort=False).shift(1)
    rows: list[float] = []
    idx: list[object] = []
    for ts, cur in factor.groupby(level=time_level, sort=False):
        prev = lag1.xs(ts, level=time_level)
        corr = pearson_ic(
            cur.to_numpy(dtype=np.float64, copy=False),
            prev.to_numpy(dtype=np.float64, copy=False),
            min_pairs=min_pairs,
        )
        rows.append(corr)
        idx.append(ts)
    return pd.Series(rows, index=pd.Index(idx, name=time_level), dtype=float)


def cross_sectional_lag1_pearson_autocorr(
    factor: pd.Series, *, min_pairs: int = 30
) -> float:
    daily = cross_sectional_lag1_pearson_autocorr_series(factor, min_pairs=min_pairs)
    finite = daily[np.isfinite(daily.to_numpy(dtype=float, copy=False))]
    return float(finite.mean()) if len(finite) else float("nan")


def cs_ic_summary(
    daily_ic: pd.Series,
    daily_rank_ic: pd.Series | None = None,
) -> dict[str, float | int]:
    ic_vals = daily_ic[np.isfinite(daily_ic.to_numpy(dtype=float, copy=False))]
    n_days = len(ic_vals)
    if n_days == 0:
        return {
            "ic": float("nan"),
            "icir": float("nan"),
            "rank_ic": float("nan"),
            "n_days": 0,
        }
    ic_mean = float(ic_vals.mean())
    ic_std = float(ic_vals.std(ddof=1)) if n_days > 1 else float("nan")
    icir = (
        ic_mean / ic_std
        if ic_std and np.isfinite(ic_std) and ic_std > 0
        else float("nan")
    )
    rank_ic_mean = float("nan")
    if daily_rank_ic is not None:
        rv = daily_rank_ic[np.isfinite(daily_rank_ic.to_numpy(dtype=float, copy=False))]
        rank_ic_mean = float(rv.mean()) if len(rv) else float("nan")
    return {"ic": ic_mean, "icir": icir, "rank_ic": rank_ic_mean, "n_days": n_days}


def _round_label_mean(value: float) -> float:
    return float(round(value, 6))


def label_quantile_buckets(
    factor: np.ndarray,
    label: np.ndarray,
    *,
    n_quantiles: int = 10,
) -> list[dict[str, Any]]:
    if n_quantiles < 2:
        return []
    xf = np.asarray(factor, dtype=float)
    yl = np.asarray(label, dtype=float)
    m = np.isfinite(xf) & np.isfinite(yl)
    xf, yl = xf[m], yl[m]
    if xf.size < n_quantiles:
        return []
    fac_s = pd.Series(xf)
    try:
        qbins = pd.qcut(fac_s, n_quantiles, duplicates="drop")
    except ValueError:
        qbins = pd.qcut(fac_s.rank(method="first"), n_quantiles, duplicates="drop")
    n_q = int(qbins.cat.categories.size)
    codes = qbins.cat.codes.to_numpy()
    out: list[dict[str, Any]] = []
    for i in range(n_q):
        mask = codes == i
        cnt = int(mask.sum())
        if cnt == 0:
            mean_v = None
        else:
            mv = float(np.mean(yl[mask]))
            mean_v = _round_label_mean(mv) if np.isfinite(mv) else None
        cat = qbins.cat.categories[i]
        out.append(
            {"quantile": i + 1, "n": cnt, "mean_label": mean_v, "factor_bin": str(cat)}
        )
    return out


def decile_mean_label(
    factor: np.ndarray, label: np.ndarray, *, n_deciles: int = 10
) -> list[dict[str, Any]]:
    buckets = label_quantile_buckets(factor, label, n_quantiles=n_deciles)
    return [{"decile": b["quantile"], "mean_label": b["mean_label"]} for b in buckets]


def _cross_section_decile_mean_labels(
    factor: np.ndarray,
    label: np.ndarray,
    *,
    n_deciles: int = 10,
    min_stocks: int = 30,
) -> list[float] | None:
    xf = np.asarray(factor, dtype=float)
    yl = np.asarray(label, dtype=float)
    mask = np.isfinite(xf) & np.isfinite(yl)
    xf, yl = xf[mask], yl[mask]
    if xf.size < min_stocks or xf.size < n_deciles:
        return None
    fac_s = pd.Series(xf)
    try:
        qbins = pd.qcut(fac_s, n_deciles, duplicates="drop")
    except ValueError:
        qbins = pd.qcut(fac_s.rank(method="first"), n_deciles, duplicates="drop")
    n_q = int(qbins.cat.categories.size)
    if n_q < 2:
        return None
    codes = qbins.cat.codes.to_numpy()
    means: list[float] = []
    for i in range(n_q):
        bucket = codes == i
        if not bucket.any():
            means.append(float("nan"))
        else:
            means.append(float(np.mean(yl[bucket])))
    return means


def _iter_daily_decile_mean_labels(
    factor: pd.Series,
    label: pd.Series,
    *,
    time_level: str = "datetime",
    n_deciles: int = 10,
    min_stocks: int = 30,
):
    if not isinstance(factor.index, pd.MultiIndex):
        raise ValueError(
            "_iter_daily_decile_mean_labels 需要 MultiIndex 面板 (datetime, instrument)"
        )
    if time_level not in factor.index.names:
        raise ValueError(f"索引缺少 level={time_level!r}")
    for ts, f_sub in factor.groupby(level=time_level, sort=False):
        y_sub = label.xs(ts, level=time_level)
        means = _cross_section_decile_mean_labels(
            f_sub.to_numpy(dtype=np.float64, copy=False),
            y_sub.to_numpy(dtype=np.float64, copy=False),
            n_deciles=n_deciles,
            min_stocks=min_stocks,
        )
        if means is not None:
            yield ts, means


def daily_decile_monotonicity_series(
    factor: pd.Series,
    label: pd.Series,
    *,
    time_level: str = "datetime",
    n_deciles: int = 10,
    min_stocks: int = 30,
    min_deciles_for_rho: int = 3,
) -> pd.Series:
    rows: list[float] = []
    idx: list[object] = []
    ranks_template = np.arange(1, n_deciles + 1, dtype=np.float64)
    for ts, means in _iter_daily_decile_mean_labels(
        factor, label, time_level=time_level, n_deciles=n_deciles, min_stocks=min_stocks
    ):
        means_arr = np.asarray(means, dtype=np.float64)
        valid = np.isfinite(means_arr)
        n_valid = int(valid.sum())
        if n_valid < min_deciles_for_rho:
            rho = float("nan")
        else:
            ranks = ranks_template[: len(means_arr)][valid]
            rho = spearman_ic(ranks, means_arr[valid], min_pairs=min_deciles_for_rho)
        rows.append(rho)
        idx.append(ts)
    return pd.Series(rows, index=pd.Index(idx, name=time_level), dtype=float)


def daily_long_short_series(
    factor: pd.Series,
    label: pd.Series,
    *,
    time_level: str = "datetime",
    n_deciles: int = 10,
    min_stocks: int = 30,
) -> pd.Series:
    rows: list[float] = []
    idx: list[object] = []
    for ts, means in _iter_daily_decile_mean_labels(
        factor, label, time_level=time_level, n_deciles=n_deciles, min_stocks=min_stocks
    ):
        top = means[-1]
        bottom = means[0]
        if np.isfinite(top) and np.isfinite(bottom):
            rows.append(float(top - bottom))
        else:
            rows.append(float("nan"))
        idx.append(ts)
    return pd.Series(rows, index=pd.Index(idx, name=time_level), dtype=float)


def newey_west_mean_tstat(
    series: pd.Series | np.ndarray, *, lags: int | None = None
) -> dict[str, float | int]:
    if isinstance(series, pd.Series):
        x = series.to_numpy(dtype=np.float64, copy=False)
    else:
        x = np.asarray(series, dtype=np.float64)
    x = x[np.isfinite(x)]
    t_n = len(x)
    nan_out: dict[str, float | int] = {
        "mean": float("nan"),
        "se_nw": float("nan"),
        "t_nw": float("nan"),
        "n": t_n,
        "lags": 0,
    }
    if t_n < 2:
        return nan_out
    if lags is None:
        lags = max(1, int(4.0 * (t_n / 100.0) ** (2.0 / 9.0)))
    lags = min(int(lags), t_n - 1)
    x_mean = float(x.mean())
    u = x - x_mean
    gamma0 = float(np.dot(u, u) / t_n)
    nw_var_mean = gamma0
    for k in range(1, lags + 1):
        w = 1.0 - k / (lags + 1.0)
        gamma_k = float(np.dot(u[k:], u[:-k]) / t_n)
        nw_var_mean += 2.0 * w * gamma_k
    nw_var_mean /= t_n
    if nw_var_mean <= 0.0 or not np.isfinite(nw_var_mean):
        se_nw = float("nan")
        t_nw = float("nan")
    else:
        se_nw = float(math.sqrt(nw_var_mean))
        t_nw = float(x_mean / se_nw)
    return {"mean": x_mean, "se_nw": se_nw, "t_nw": t_nw, "n": t_n, "lags": lags}


def _resolve_mls_params(
    factor: pd.Series,
    *,
    n_deciles: int,
    min_stocks: int,
    instrument_level: str = "instrument",
) -> tuple[int, int]:
    n_inst = int(factor.index.get_level_values(instrument_level).nunique())
    eff_deciles = min(int(n_deciles), n_inst)
    eff_min = min(int(min_stocks), n_inst)
    if eff_min < eff_deciles:
        eff_min = eff_deciles
    return eff_deciles, eff_min


def mls_fmb_summary(
    factor: pd.Series,
    label: pd.Series,
    *,
    n_deciles: int = 10,
    min_stocks: int = 30,
    annualization_factor: float = 252.0,
    nw_lags: int | None = None,
) -> dict[str, Any]:
    eff_deciles, eff_min_stocks = _resolve_mls_params(
        factor, n_deciles=n_deciles, min_stocks=min_stocks
    )
    rho_series = daily_decile_monotonicity_series(
        factor, label, n_deciles=eff_deciles, min_stocks=eff_min_stocks
    )
    ls_series = daily_long_short_series(
        factor, label, n_deciles=eff_deciles, min_stocks=eff_min_stocks
    )
    rho_nw = newey_west_mean_tstat(rho_series, lags=nw_lags)
    ls_nw = newey_west_mean_tstat(ls_series, lags=nw_lags)
    rho_vals = rho_series[np.isfinite(rho_series.to_numpy(dtype=float, copy=False))]
    ls_vals = ls_series[np.isfinite(ls_series.to_numpy(dtype=float, copy=False))]
    mean_rho = float(rho_vals.mean()) if len(rho_vals) else float("nan")
    mean_ls = float(ls_vals.mean()) if len(ls_vals) else float("nan")
    if len(ls_vals) > 1:
        ls_std = float(ls_vals.std(ddof=1))
    elif len(ls_vals) == 1:
        ls_std = float("nan")
    else:
        ls_std = float("nan")
    ir_ls = (
        mean_ls / ls_std
        if ls_std and np.isfinite(ls_std) and ls_std > 0
        else float("nan")
    )
    ir_ls_annual = (
        float(ir_ls * math.sqrt(annualization_factor))
        if np.isfinite(ir_ls)
        else float("nan")
    )
    mls = (
        float(mean_rho * ir_ls_annual)
        if np.isfinite(mean_rho) and np.isfinite(ir_ls_annual)
        else float("nan")
    )
    return {
        "mean_rho": mean_rho,
        "mean_ls": mean_ls,
        "ir_ls": ir_ls,
        "ir_ls_annual": ir_ls_annual,
        "mls": mls,
        "nw_t_rho": rho_nw["t_nw"],
        "nw_t_ls": ls_nw["t_nw"],
        "nw_se_rho": rho_nw["se_nw"],
        "nw_se_ls": ls_nw["se_nw"],
        "n_days_rho": int(rho_nw["n"]),
        "n_days_ls": int(ls_nw["n"]),
        "nw_lags": int(rho_nw["lags"]),
        "n_deciles": int(eff_deciles),
        "n_deciles_requested": int(n_deciles),
        "min_stocks": int(eff_min_stocks),
        "min_stocks_requested": int(min_stocks),
        "annualization_factor": float(annualization_factor),
        "note": "MLS+FMB 非参数版：ρ_t=逐日十分组 Spearman 单调性，LS_t=Q10-Q1 多空；IR_LS 为日频 LS 均值/标准差，ir_ls_annual=IR_LS×√252；MLS=mean(ρ)×ir_ls_annual。",
    }


def evaluate_cs_on_panel(
    values: np.ndarray,
    panel: pd.DataFrame,
    *,
    label_col: str = DEFAULT_LABEL_COL,
    min_pairs: int = 5,
) -> dict[str, Any]:
    panel = panel.sort_index()
    if label_col not in panel.columns:
        raise KeyError(f"panel 缺少标签列: {label_col}")
    if len(values) != len(panel):
        raise ValueError(f"values 长度 {len(values)} != panel 行数 {len(panel)}")
    factor_series = pd.Series(values, index=panel.index, dtype=np.float32)
    label_series = panel[label_col]
    daily_ic = cross_sectional_ic(factor_series, label_series, min_pairs=min_pairs)
    daily_rank_ic = cross_sectional_rank_ic(
        factor_series, label_series, min_pairs=min_pairs
    )
    cs = cs_ic_summary(daily_ic, daily_rank_ic)
    cs_autocorr_min_pairs = min(
        30,
        max(int(panel.index.get_level_values("instrument").nunique()) - 1, min_pairs),
    )
    mls_min_stocks = min(30, max(min_pairs * 6, 10))
    fac = factor_series.to_numpy(dtype=float, copy=False)
    lab = label_series.to_numpy(dtype=float, copy=False)
    return {
        "coverage": coverage(values),
        "ic": cs["ic"],
        "icir": cs["icir"],
        "rank_ic": cs["rank_ic"],
        "n_days": cs["n_days"],
        "cs_pearson_autocorr": cross_sectional_lag1_pearson_autocorr(
            factor_series, min_pairs=cs_autocorr_min_pairs
        ),
        "decile_mean_label": decile_mean_label(fac, lab, n_deciles=10),
        "mls_fmb": mls_fmb_summary(
            factor_series, label_series, min_stocks=mls_min_stocks
        ),
        "label_col": label_col,
    }


def evaluate_on_panel(
    values: np.ndarray,
    panel: pd.DataFrame,
    *,
    label_col: str = DEFAULT_LABEL_COL,
    min_ic_pairs: int = 5,
) -> dict[str, Any]:
    """coverage + cross-sectional IC / ICIR / RANKIC on a panel."""
    return evaluate_cs_on_panel(
        values, panel, label_col=label_col, min_pairs=min_ic_pairs
    )
