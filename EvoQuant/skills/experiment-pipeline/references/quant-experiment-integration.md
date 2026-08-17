# quant-experiment-runtime Integration (for experiment-pipeline)

`experiment-pipeline` remains the **orchestrator**: it owns when/whether to run
experiments, the 4-stage structure, attempt budgets, and the reflection →
evo-memory handoff. `quant-experiment-runtime` is the **executor** it calls to
actually run one experiment on real data and get quantitative metrics.

This document only describes the calling contract — the pipeline's 4-stage
body is unchanged.

## When the pipeline calls the runtime

| Pipeline stage | Runtime use | Splits |
|----------------|-------------|--------|
| Stage 1 — initial implementation | reproduce the anchor/baseline factor on the database → IC metrics to verify the data+eval pipeline works | train |
| Stage 2 — hyperparameter tuning | re-run the baseline with varied `params`; check stability | train (3 runs) |
| Stage 3 — proposed method | run the new Research Artifact → compare IC/ICIR vs the tuned baseline | train + val |
| Stage 4 — ablation / final | run variants → terminal confirmation | test (opt-in) |

For **Alpha Generation Methodology**, the pipeline calls `run_batch` over a
generation round and evaluates the distribution of `ic`/`icir` across candidates.

## Calling contract

1. The pipeline (or the engineer agent) generates a **Research Artifact**
   exposing an Entry Point `entry(context, config) -> results`, following
   `quant-experiment-runtime/references/research-code-convention.md` and
   imitating `assets/research-artifact-example/`.
2. Build the panel once per dataset (offline):
   `build_panel.py --data-root <discovered dataset> --out panel.parquet`
3. Run a Candidate:
   `run_experiment.py --panel panel.parquet --candidate <Candidate JSON> --splits ... --out result.json`
4. Read `ExperimentResult` (JSON) + `artifacts/` into the stage log and the
   code-trajectory log. Hand off to `evo-memory` (ESE on success / IVE on
   failure) as usual.

## What stays out of the pipeline

The pipeline does NOT: read the database, compute factor values, or compute
metrics. All of that is the runtime's job. The pipeline only decides when to
call it and what to do with the `ExperimentResult`.

## Agent autonomy

Calling the runtime is the agent's decision, not a hard-coded pipeline step.
Not every task type or cycle needs it (e.g. pure methodology/abstraction work
may skip it). The pipeline references this runtime; it does not force it.