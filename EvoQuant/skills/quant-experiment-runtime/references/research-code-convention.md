# Research Code Convention

What an LLM-generated Research Artifact must implement to be runnable by the
Executor. This is the convention that constrains generated code — not Python
types.

## 1. Expose one Entry Point

A Research Artifact is a runnable research product (single `.py`, or a
package). It exposes **one callable**:

```python
def run(context, config) -> results:
    ...
```

- Function name is not fixed (`run`/`experiment`/`evaluate`/`main`…). The
  Candidate's `compute_ref` names it.
- `context` = `RuntimeContext`; `config` = Candidate `params`.

## 2. Read data from `context.get_split`

```python
panel = context.get_split("train", lookback=window)   # lookback for rolling warmup
```

Use `lookback` when your factor needs history before the split start (any
rolling window). Without it, the first `window-1` days of the split have NaN.

## 3. Alignment is YOUR job (critical)

The Metric will NOT realign your output. You must produce a `pd.Series` whose
index is **exactly** the split panel's `MultiIndex(datetime, instrument)`:

```python
split_panel = context.get_split(split)        # un-lookbacked, exact split index
factor = factor.reindex(split_panel.index)    # align; rows outside split drop
factor.name = "factor"
```

> If you skip the `reindex`, the Metric's internal `reindex` silently produces
> NaN and you get IC≈0 / coverage≈0 without an error. This is the #1 demo bug.

For the default `ic_panel` metric, a plain `factor.reindex(split_panel.index)` is
sufficient (shown above). No external factor-research package is required.

## 4. Return the `results` default contract

```python
results = {split: aligned_factor_series for split in ("train", "val")}
return results
```

`dict[split, pd.Series]` of **already-aligned** exposure. The default `ic_panel`
Metric consumes this. (For portfolio weights or a batch distribution, return a
compatible structure and register a matching Metric — see `metrics-extension.md`.)

## 5. Write byproducts to `context.artifacts`

```python
factor.to_frame("factor").to_parquet(context.artifacts / f"factor_{split}.parquet")
```

Anything you write here (factor values, curves, plots, logs, intermediate CSV)
is listed in `ExperimentResult.artifacts` and read directly by Reflection — no
Workflow file management needed.

## 6. Self-contained — no external factor-research package needed

A pure-python factor (no DSL) is fully supported and is the recommended default.
The Executor's panel and metrics are implemented inside this skill
(`scripts/_panel.py`, `scripts/_metrics.py`); your research code only needs
`pandas`/`numpy` plus whatever it computes itself.

- Default label column: `label_1d_close_to_close` (also available:
  `label_1d_open_to_open`, `label_10d_close_to_close`, `label_20d_close_to_close`).
- Available panel columns: `open/high/low/close`, `adj_*`, `volume/amount`,
  `vwap/adj_vwap`, `ret`, `turnover_rate*`, `pe*/pb/ps*`, `float_cap/tot_cap`, etc.
- Read whichever columns your factor needs from `context.get_split(split)`.

## Per object-type guidance

- **Alpha Factor Research** (demo main line): return `dict[split, pd.Series]`
  of aligned exposure; use `ic_panel`. See `assets/research-artifact-example/`.
- **Alpha Generation Methodology**: a *batch* of Candidates, each with its own
  Artifact; the pipeline calls `run_batch`. Each Artifact returns the same
  default contract; you evaluate the distribution of `ic`/`icir` across the batch.
- **Portfolio Strategy Research** (scaffolded, not demoed): return portfolio
  weights per split; register a portfolio Metric (future). The Executor does
  not branch on object type — the difference is entirely in your Artifact + Metric.

## Minimal complete example (copy-paste template)

See `assets/research-artifact-example/factor.py` — a 20-day reversal factor that
implements all six points above. Imitate its shape; replace the factor logic.