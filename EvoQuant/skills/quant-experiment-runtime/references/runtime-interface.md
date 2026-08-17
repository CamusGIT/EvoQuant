# Runtime Interface Contract

The Executor is thin and convention-driven. This file is the authoritative
contract for what a Research Artifact must provide and what the Executor hands
back. It deliberately avoids DSL / object-type / manifest concepts.

## Candidate (input — description only, not routing)

```json
{
  "id": "rev20_v3",
  "compute_ref": "experiments/<project>/factor_rev20.py::run",
  "params": { "window": 20, "src_col": "ret" },
  "metadata": { "object_type": "factor", "source": "llm", "anchor_paper_id": "..." }
}
```

| Field | Meaning |
|-------|---------|
| `id` | unique candidate id (artifacts dir is namespaced by it) |
| `compute_ref` | **Python-native Entry Point** to the research artifact: `"path/to/file.py::func"` or `"pkg.mod:func"`. The Executor loads the callable named here. The artifact may be a single file or a package; the Executor does not assume either. |
| `params` | hyperparameters passed to the entry point as `config` |
| `metadata` | arbitrary Workflow-level info. `object_type` lives HERE (not as a Runtime field) — it is Workflow's concern. |

`compute_ref` is a Python-native callable reference. There is **no
manifest.json**. Two forms:

- `"path/to/file.py::run"` — file + function (default name `experiment` if omitted)
- `"pkg.module:run"` — importable module + function

## Entry Point (the callable the Artifact exposes)

```python
def run(context, config) -> results:   # name is whatever compute_ref points to
    ...
```

- `context`: `RuntimeContext` (below).
- `config`: the Candidate's `params` dict.
- `results`: returned to the Executor, passed UNCHANGED to the Metric. The
  Executor does NOT inspect it.

### `results` default contract (for the `ic_panel` Metric)

```python
results: dict[split_name, pd.Series]
```

Each `Series` is factor exposure **already aligned** to that split panel's
`MultiIndex(datetime, instrument)`. **Alignment is the research code's job** —
the Metric only evaluates; if the index is misaligned it silently produces NaN.
See `research-code-convention.md` for the alignment snippet.

For non-factor objects (portfolio weights, a generation batch's distribution),
the research code returns a compatible structure and a matching Metric is
registered; the Runtime enforces no single shape.

## RuntimeContext (Executor → research code; forward-extensible)

| Member | Type / returns | Purpose |
|--------|----------------|---------|
| `context.get_split(split, *, lookback=0)` | `pd.DataFrame` | rows of the panel for `split` (closed date interval). `lookback` extends the slice backwards by that many trading days for rolling-window warmup; the *un-lookbacked* index is what you should align to. |
| `context.label_col` | `str` | the label column to evaluate against (e.g. `label_1d_close_to_close`) |
| `context.config` | `dict` | splits/label/coverage meta |
| `context.artifacts` | `Path` (created) | write byproducts here (Reflection reads) |
| `context.workspace` | `Path` | workspace root |
| `context.meta` | `dict` | coverage dates, universe, funda flag, etc. |

Future members (logger, cache, …) may be added without changing the call
signature.

## Metric (only evaluates; never realigns)

```python
Metric = Callable[[results, split_panel: pd.DataFrame, label_col: str], dict[str, Any]]
```

A Metric consumes the research code's `results` + the split panel + label_col
and returns a flat metrics dict. It must NOT realign/transform data into an
evaluation target. Default registered: `ic_panel` (IC/ICIR/RANKIC/coverage/
decile/mls), selected via `candidate.params["metric"]` (default `"ic_panel"`).
See `metrics-extension.md`.

## ExperimentResult (output — unified, JSON-serialisable)

```json
{
  "candidate_id": "rev20_v3",
  "status": "ok",
  "per_split": {
    "train": { "date_range": ["2023-01-03","2023-04-13"], "metrics": {...}, "timing": {} },
    "val":   { "date_range": ["2023-04-14","2023-05-23"], "metrics": {...}, "timing": {} }
  },
  "metrics": { "ic": -0.091, "icir": -0.67, "rank_ic": -0.16, "coverage": 0.24, ... },
  "error": null,
  "runtime_meta": { "metric": "ic_panel", "splits": ["train","val"], "label_col": "...", "object_type": "factor" },
  "artifacts": ["rev20_v3/factor_train.parquet", "rev20_v3/factor_val.parquet"]
}
```

- `metrics` = the **val** split's flat metrics (headline).
- `artifacts` = files written under the per-candidate artifacts dir.
- `status` = `"ok"` or `"error"` (an error in one candidate does not crash a batch).
- Reflection / downstream Workflow depend ONLY on `ExperimentResult` + `artifacts/`.