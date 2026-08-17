# Metrics & Experiment-Type Extension

Metrics are the one extension point the Runtime keeps. The Runtime never
interprets `results` — a Metric does. Adding a metric or a new experiment type
requires **no Runtime or Workflow change**.

## Metric contract

```python
Metric = Callable[[results, Any, split_panel: pd.DataFrame, label_col: str], dict[str, Any]]
```

A Metric receives:
- `results` — whatever the Research Artifact returned (default contract:
  `dict[split, pd.Series]` of aligned exposure),
- `split_panel` — the panel rows for the split being evaluated,
- `label_col` — the label column,
- (keyword) `split` — the split name, available if the Metric needs to index
  a dict-shaped `results`.

It returns a **flat** metrics dict. It must NOT realign or transform the data
into an evaluation target — alignment is the research code's job. Keep Metrics
light; if a "metric" starts doing data wrangling, that wrangling belongs in the
Research Artifact.

## Registering a new metric

In code that constructs the `ExperimentRuntime`:

```python
from experiment_runtime import MetricsRegistry

reg = MetricsRegistry()
reg.register("my_metric", my_metric_fn)
runtime = ExperimentRuntime(..., metrics_registry=reg, ...)
```

Select it per-Candidate via `candidate.params["metric"] = "my_metric"`.

```python
def my_metric_fn(results, split_panel, label_col, *, split=None):
    series = results[split] if isinstance(results, dict) else results
    # ... evaluate, return flat dict
    return {"my_score": ...}
```

## Default registered metric

`ic_panel` — IC / ICIR / RANKIC / coverage / decile_mean_label / mls_fmb,
implemented in the skill's own `scripts/_metrics.py` (self-contained,
`numpy`/`pandas` only).

## Adding a new research-object type / experiment type

The Runtime does not branch on object type. To support, say, Portfolio
Strategy evaluation:

1. The Research Artifact returns portfolio weights (a compatible `results`
   shape), aligned appropriately.
2. Register a portfolio Metric (e.g. `portfolio_returns`) that consumes those
   weights.
3. Select it via `candidate.params["metric"]`.

No Runtime change. No Workflow change. The three task types (factor /
generation / portfolio) share one Executor; the difference is only Artifact +
Metric, chosen per Candidate.

## Future: backtest

A backtest is a future Metric (portfolio-return / turnover / Sharpe / drawdown)
over a portfolio-shaped `results`. It is not in the first demo (no portfolio
Metric registered), but the extension seam is already in place.