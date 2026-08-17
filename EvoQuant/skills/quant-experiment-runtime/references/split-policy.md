# Train / Val / Test Split Policy

The split is **ratio-based over the dataset's coverage**, never hard-coded
years — the source database's coverage changes over time (2026-06 today,
later 2028/2032), so fixed dates would silently break.

## Fixed (not overridable by the agent)

- **Split semantics**: closed date intervals `[start, end]` over the panel's
  `datetime` index; chronological ordering train → val → test.
- **No look-ahead**: train must not see val/test information; val must not see
  test. The Executor derives dates from coverage so segments are contiguous.
- **Test is terminal**: `test` is used only for final confirmation and MUST NOT
  be used to re-optimize the factor/method (prevents overfitting / look-ahead).
- **Three-way meaning**: train = build/tune the object; val = compare/select;
  test = final reported numbers.

## Overridable by the agent (via `--split-config` JSON)

| Override | Key | Default |
|----------|-----|---------|
| Explicit per-split dates | `dates: {"train":["YYYY-MM-DD","YYYY-MM-DD"], ...}` | derived from ratios |
| Split ratios | `ratios: {"train":0.56,"val":0.22,"test":0.22}` | 0.56/0.22/0.22 |
| Enable test | `include_test: true` (or pass `--splits ... test`) | off (train+val only) |
| Label column | `--label-col` | `label_1d_close_to_close` |
| Fundamental columns | (panel build flag, not split) | off by default |

## Default derivation (no config given)

Given coverage `[start, end]`, the Executor computes total days and allocates
by ratio. The last split absorbs rounding so the window is contiguous.

## Alignment with EvoQuant's 4-stage pipeline

| Pipeline stage | Split used |
|----------------|------------|
| Stage 1 — initial implementation (reproduce baseline) | train |
| Stage 2 — hyperparameter tuning | train (stability across 3 runs) |
| Stage 3 — proposed method | train + val (compare vs tuned baseline) |
| Stage 4 — ablation / final | test (terminal confirmation) |

The agent may shift this mapping (e.g. skip test in early cycles); the Executor
only enforces the fixed semantics above.

## Example split config (reference, NOT a Runtime default)

See `assets/split-config.example.json` for an explicit-dates example anchored to
the current data coverage. It is a *reference*; the Runtime's actual default is
ratio-derived from whatever dataset the agent selects.

## Rolling-window warmup

`context.get_split(split, lookback=N)` extends the slice backwards by N trading
days so rolling factors are defined on the split's first day. The *exposed*
factor rows are still only the split's (you reindex to the un-lookbacked panel).
This is a RuntimeContext feature, not a split-policy change.