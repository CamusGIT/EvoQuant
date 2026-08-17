"""Offline panel builder (self-contained).

This module only needs ``numpy`` / ``pandas`` / ``pyarrow``. It reads a local
daily-hq parquet cache **offline** (no network / no token) and builds a daily
panel with a ``MultiIndex(datetime, instrument)`` plus derived columns
(adjusted prices, vwap, ret, and close-to-close / open-to-open label columns).

Layout of a data package (what ``discover_data.py`` finds)::

    <data-root>/artifacts/
      market/daily_hq.parquet          # required: (datetime, instrument) wide table
      fundamental/quarterly.parquet    # optional (not enriched in v1)
      industry/sw_l1_membership.parquet# optional (not enriched in v1)

v1 builds a price-volume panel (no fundamental/industry enrichment) — sufficient
for IC-style factor evaluation. Enrichment can be added later without changing
the Runtime contract.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Tushare daily_basic native fields kept as-is in the hq cache.
DAILY_BASIC_COLUMNS = [
    "turnover_rate",
    "turnover_rate_f",
    "volume_ratio",
    "pe",
    "pe_ttm",
    "pb",
    "ps",
    "ps_ttm",
    "dv_ratio",
    "dv_ttm",
    "total_share",
    "float_share",
    "free_share",
]

# Final panel column order (labels included).
OUTPUT_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "adj_open",
    "adj_high",
    "adj_low",
    "adj_close",
    "adjfactor",
    "volume",
    "amount",
    "float_cap",
    "tot_cap",
    *DAILY_BASIC_COLUMNS,
    "is_trade",
    "not_st",
    "ret",
    "vwap",
    "adj_vwap",
    "label_1d_close_to_close",
    "label_1d_open_to_open",
    "label_10d_close_to_close",
    "label_20d_close_to_close",
]

# label_{N}d_close_to_close: T+1 close -> T+(N+1) close
CLOSE_TO_CLOSE_LABEL_HOLD_DAYS = (1, 10, 20)

DEFAULT_LABEL_COL = "label_1d_close_to_close"


def close_to_close_label_name(hold_days: int) -> str:
    return f"label_{hold_days}d_close_to_close"


_DERIVED_COLUMNS = (
    "ret",
    "label_1d_open_to_open",
    *(close_to_close_label_name(n) for n in CLOSE_TO_CLOSE_LABEL_HOLD_DAYS),
)


def _coerce_datetime_index(panel: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(panel.index, pd.MultiIndex):
        return panel
    if panel.index.names[0] != "datetime":
        return panel
    dt = panel.index.get_level_values("datetime")
    if not pd.api.types.is_datetime64_any_dtype(dt):
        dt = pd.to_datetime(dt)
        inst = panel.index.get_level_values("instrument")
        panel = panel.copy()
        panel.index = pd.MultiIndex.from_arrays(
            [dt, inst], names=["datetime", "instrument"]
        )
    return panel.sort_index()


def slice_panel(
    panel: pd.DataFrame, *, start: str | None = None, end: str | None = None
) -> pd.DataFrame:
    """Closed-interval [start, end] slice on the datetime level."""
    if start is None and end is None:
        return panel
    dt = panel.index.get_level_values("datetime")
    mask = pd.Series(True, index=panel.index)
    if start is not None:
        mask &= dt >= pd.Timestamp(start)
    if end is not None:
        mask &= dt <= pd.Timestamp(end)
    return panel.loc[mask]


def filter_universe(df: pd.DataFrame, *, universe_mask: bool = True) -> pd.DataFrame:
    """Keep tradable, non-ST rows. Uses is_trade + (is_st==0 or not_st==1)."""
    if not universe_mask:
        return df
    if "is_st" in df.columns:
        st_ok = df["is_st"] == 0
    elif "not_st" in df.columns:
        st_ok = df["not_st"] == 1
    else:
        st_ok = pd.Series(True, index=df.index)
    trade_ok = (
        df["is_trade"] == 1
        if "is_trade" in df.columns
        else pd.Series(True, index=df.index)
    )
    return df[trade_ok & st_ok]


def _calc_label_1d_open_to_open(adj_open: pd.Series) -> pd.Series:
    open_t1 = adj_open.shift(-1)
    open_t2 = adj_open.shift(-2)
    denom = open_t1.replace(0, np.nan)
    return (open_t2 - open_t1) / denom


def _calc_label_nd_close_to_close(adj_close: pd.Series, hold_days: int) -> pd.Series:
    entry = adj_close.shift(-1)
    exit_ = adj_close.shift(-(hold_days + 1))
    denom = entry.replace(0, np.nan)
    return (exit_ - entry) / denom


def _derive_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Derive adj_* and vwap from the raw hq wide table (no ret/label)."""
    df = df.copy()
    if (
        df.index.names
        and "code" in df.index.names
        and "instrument" not in df.index.names
    ):
        df = df.rename_axis(index={"code": "instrument"})

    for col in ("open", "high", "low", "close"):
        df[f"adj_{col}"] = df[col] * df["adjfactor"]

    vol = df["volume"].replace(0, np.nan)
    df["vwap"] = df["amount"] / vol
    df["adj_vwap"] = df["vwap"] * df["adjfactor"]
    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute ret and label columns on the full time series (per instrument)."""
    df = df.copy()
    df["ret"] = df.groupby(level="instrument", sort=False)["adj_close"].pct_change(
        fill_method=None
    )
    g_close = df.groupby(level="instrument", sort=False)["adj_close"]
    for hold_days in CLOSE_TO_CLOSE_LABEL_HOLD_DAYS:
        col = close_to_close_label_name(hold_days)
        df[col] = g_close.transform(
            lambda s, d=hold_days: _calc_label_nd_close_to_close(s, d)
        )
    df["label_1d_open_to_open"] = df.groupby(level="instrument", sort=False)[
        "adj_open"
    ].transform(_calc_label_1d_open_to_open)
    return df


def _finalize_panel(df: pd.DataFrame, *, dtype: str = "float32") -> pd.DataFrame:
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    panel = df[OUTPUT_COLUMNS].copy()
    numeric_cols = [c for c in OUTPUT_COLUMNS if c not in ("is_trade", "not_st")]
    for col in numeric_cols:
        panel[col] = panel[col].astype(dtype)
    panel = panel.sort_index()
    panel = _coerce_datetime_index(panel)
    assert panel.index.names == ["datetime", "instrument"]
    assert not panel.index.duplicated().any()
    return panel


def _slice_hq_by_date(
    hq: pd.DataFrame, *, start: str | None, end: str | None
) -> pd.DataFrame:
    if start is None and end is None:
        return hq
    dt = pd.to_datetime(hq.index.get_level_values(0))
    mask = pd.Series(True, index=hq.index)
    if start is not None:
        mask &= dt >= pd.Timestamp(start)
    if end is not None:
        mask &= dt <= pd.Timestamp(end)
    return hq.loc[mask]


def build_panel_from_hq(
    hq: pd.DataFrame,
    *,
    start: str | None = None,
    end: str | None = None,
    universe_mask: bool = True,
    dtype: str = "float32",
) -> pd.DataFrame:
    """Build a panel from the (datetime, instrument) hq wide table."""
    df = _slice_hq_by_date(hq, start=start, end=end)
    if universe_mask:
        df = filter_universe(df)
    if df.empty:
        return df
    df = _derive_base_columns(df)
    df = _add_derived_columns(df)
    return _finalize_panel(df, dtype=dtype)


def load_market_hq(path: Path | str) -> pd.DataFrame:
    """Load the hq parquet cache; return empty DataFrame if missing."""
    p = Path(path)
    if not p.is_file():
        return pd.DataFrame()
    hq = pd.read_parquet(p)
    if "instrument" not in hq.index.names and "code" in hq.index.names:
        hq = hq.rename_axis(index={"code": "instrument"})
    dt = hq.index.get_level_values("datetime")
    if not pd.api.types.is_datetime64_any_dtype(dt):
        inst = hq.index.get_level_values("instrument")
        hq.index = pd.MultiIndex.from_arrays(
            [pd.to_datetime(dt), inst], names=["datetime", "instrument"]
        )
    return hq.sort_index()


def build_panel(
    *,
    start: str | None = None,
    end: str | None = None,
    out_path: Path | str | None = None,
    market_path: Path | str,
    universe_mask: bool = True,
    dtype: str = "float32",
    verbose: bool = True,
) -> pd.DataFrame:
    """Offline panel build from a local hq cache -> optional parquet write.

    Note: ``market_path`` is REQUIRED (no hard-coded default) — pass the path
    discovered by ``discover_data.py``.
    """
    hq = load_market_hq(market_path)
    if hq.empty:
        raise FileNotFoundError(f"hq 缓存不存在或为空: {market_path}")
    if verbose:
        print(f"build_panel(offline): hq={hq.shape} from {market_path}")
    panel = build_panel_from_hq(
        hq, start=start, end=end, universe_mask=universe_mask, dtype=dtype
    )
    if out_path is not None:
        save_panel(panel, out_path)
        if verbose:
            n_inst = panel.index.get_level_values("instrument").nunique()
            print(f"已保存: {out_path} shape={panel.shape} 股票数={n_inst}")
    return panel


def load_panel(path: Path | str) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"panel 不存在: {p}")
    panel = pd.read_parquet(p)
    if "instrument" not in panel.index.names and "code" in panel.index.names:
        panel = panel.rename_axis(index={"code": "instrument"})
    return _coerce_datetime_index(panel)


def save_panel(panel: pd.DataFrame, path: Path | str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out)
    return out
