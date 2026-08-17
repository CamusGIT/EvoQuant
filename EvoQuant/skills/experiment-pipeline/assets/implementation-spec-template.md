# Implementation Specification: [Method Name]

> Fill this when entering From-Scratch mode (no usable baseline source code).
> Read the anchor paper at L1 via `local-paper-navigator`'s
> `fetch_paper.py --paper-id <ID> --reading-level L1 --full-stdout` and extract
> what a programmer needs to type — not a paper summary.
>
> This template is **research-object agnostic**. Fill the common sections, then
> use the section matching the proposal's research-object type (Factor /
> Generation Method / Portfolio). Mark anything the paper omits but code needs
> as `[IMPLICIT]` with a resolution level (L1 re-read paper / L2 original
> publication / L3 community practice / L4 empirical validation).

## Research object type

[Alpha Factor Research | Alpha Generation Methodology | Portfolio Strategy Research]
— determines which typed section below applies.

## Common: inputs, outputs, evaluation

- **Inputs**: which panel columns / data the method reads (e.g. `close`,
  `amount`, `turnover_rate`), and the universe + date window chosen from the
  available data (scoped to the paper's tested range × budget, not max range).
- **Output shape**: what the method produces per row/day
  (e.g. a per-instrument factor exposure `pd.Series` indexed by
  `(datetime, instrument)`; a set of candidate factors; daily portfolio weights).
  This is what the evaluation Metric consumes.
- **Evaluation**: the label column used (e.g. `label_1d_close_to_close`), the
  metric(s) and their exact definition (IC: Pearson vs Spearman; cross-sectional
  vs time-series; portfolio: turnover / Sharpe / drawdown), and the reported
  value to reproduce.

## Common: data pipeline

- **Preprocessing order**: the exact sequence with parameters
  (e.g. drop untradable/ST → winsorize at 1%/99% → industry-neutralize →
  standardize). Order bugs are the most common from-scratch failure; list it
  step by step.
- **Alignment / no look-ahead**: confirm every computation at date `t` uses only
  data up to `t` (shift rolling windows correctly; never use the label column as
  an input). Note any point-in-time concerns (e.g. fundamental PIT).

## Typed section — fill the one matching the research object

### If Alpha Factor Research (factor / signal)

- **Factor definition**: every equation defining the factor, each converted to
  the exact pandas/numpy operation (e.g. `std_20 = close.rolling(20).std()`;
  cross-sectional rank: `groupby('datetime').rank()`).
- **Lookback / windows**: every window length and whether it is time-series
  (per-instrument rolling) or cross-sectional (per-day).
- **Cross-sectional processing**: neutralization targets (industry / market-cap /
  Barra), standardization, outlier handling — with parameters.

### If Alpha Generation Methodology (a method that produces / mines / evolves factors)

- **Generator inputs**: what seeds the generation (random expressions? a trained
  model? a search policy?) and its configuration.
- **Generation process**: the loop that produces candidate factors
  (e.g. `for round in range(N): candidates = generator.propose(...)`), including
  any selection / filtering of candidates.
- **Output**: a batch of candidate factors (each an exposure Series); how the
  batch is evaluated (distribution of IC/ICIR across candidates, not a single
  number).

### If Portfolio Strategy Research (signal → weights → portfolio)

- **Signal aggregation**: how one or more factor signals are combined into an
  alpha score (equal weight? inverse volatility? learned weights?).
- **Portfolio construction**: the optimizer or rule turning the score into
  weights (e.g. top-decile long-short, mean-variance, risk parity), with
  constraints (turnover cap, gross/net exposure, transaction-cost model).
- **Output**: daily portfolio weights; the portfolio-level metrics used
  (return, Sharpe, max drawdown, turnover, hit rate).

## [IMPLICIT] markers summary

| # | Detail (what the paper omits but code needs) | Inference basis | Resolution level |
|---|-----------------------------------------------|-----------------|------------------|
| 1 | [e.g. exact neutralization target] | [how you infer it] | L1/L2/L3/L4 |
| 2 | ... | ... | ... |

## Module map (filled in From-Scratch Step 2)

| Module | Responsibility | Inputs → Outputs | Verification signal |
|--------|----------------|------------------|---------------------|
| [name] | [what it does] | [in] → [out] | [how to confirm it works in isolation] |