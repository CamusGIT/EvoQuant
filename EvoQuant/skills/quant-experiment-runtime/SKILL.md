---
name: quant-experiment-runtime
description: "Quant research experiment executor: discover an offline source database under the workdir's code-repo, build a panel, run a Research Artifact's entry point to compute research-object values, and evaluate IC/ICIR/RANKIC/coverage metrics. Runtime = Experiment Executor; it runs a Research Artifact via a Python-native Entry Point and is agnostic to research-object type and expression form. Self-contained: panel building and IC metrics are implemented inside this skill. The dataset is identified at runtime by discover_data.py (never hard-coded). Use when: a research proposal is ready and you need to actually run the proposed factor/method on real data and get quantitative metrics. Do NOT use for: designing which experiments to run (use experiment-pipeline / paper-planning), debugging a single failed experiment (use experiment-craft), or searching papers (use local-paper-navigator)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: quant-research-team
  version: '1.0.0'
  tags: [core, experimentation, quant, runtime, executor, data, metrics]
---

# Quant Research Experiment Runtime

An **Experiment Executor** for quant auto-research: take a Research Artifact
(LLM-generated, exposing a callable entry point), run it against a real
offline source database to compute research-object values, and evaluate
quantitative metrics. It does **not** design experiments (that is
`experiment-pipeline`) — it executes one.

## Mental model: Runtime = Experiment Executor

```
Workflow (experiment-pipeline)   ── owns when/whether to run
        │
        ▼
Experiment Runtime               ── owns how to run one experiment
        │
        ▼
Research Artifact                ── a runnable research product (py file / package / future workspace|docker|notebook)
        │
        ▼
Entry Point                      ── Python-native callable, e.g. "path/to/code.py::run" or "pkg.mod:run"
        │
        ▼
Results                          ── Runtime does NOT interpret; Metric does
        │
        ▼
Metric (registry, extensible)    ── evaluates; does NOT realign
        │
        ▼
ExperimentResult (+ artifacts/) ── Reflection / downstream Workflow depend only on this
```

The Runtime only knows "I run a Research Artifact via its Entry Point." It is
agnostic to: research-object type (factor / generation method / portfolio),
expression form (DSL / python / generator), and the internal structure of
`results`. Those belong to the Research Artifact / Workflow / Metric.

This skill is **self-contained**: panel building (`scripts/_panel.py`) and IC
metrics (`scripts/_metrics.py`) are implemented inside the skill and need only
`pandas` / `pyarrow` / `numpy`. There is no dependency on any external
factor-research project.

## When to use

- You need to actually run the proposed object on real data.
- Experiment needs concrete IC-style metrics.
- You need to evaluate a batch of candidates.

## When NOT to use

- Designing which experiments to run / stage budgets → `experiment-pipeline`.
- Debugging a single failed experiment → `experiment-craft`.
- Searching/reading papers → `local-paper-navigator`.

## The convention that constrains LLM-generated code

LLM-generated research code is constrained by **this convention**, not by
Python types:

> A **Research Artifact** exposes one **Entry Point** — a callable with
> signature `entry(context, config) -> results`. The function name is not
> fixed (`run`/`experiment`/`evaluate`/`main` all fine); `compute_ref` names it.
> `results` default contract for the IC metric is `dict[split, pd.Series]`
> where each Series is factor exposure **already aligned** to that split's
> panel index — **alignment is the research code's job**, the Metric only
> evaluates.

See `references/research-code-convention.md` for the full contract and
`assets/research-artifact-example/` for a runnable copy-pasteable example.

## Database identification contract

The dataset is **not hard-coded**. The agent identifies it at runtime:

1. Run `discover_data.py --code-repo code-repo` → a JSON catalog of every
   data package under the code-repo (each entry has `name`, `root`,
   `artifacts_root`, file list, coverage).
2. Inspect the catalog, pick a dataset, and pass its `root` to
   `build_panel.py --data-root <root>`.
3. `--data-root` / `--panel` are **required**, with no default — the dataset name
   must come from the discover step, never hard-coded in a Candidate or script.

Paths follow the convention: **script paths** use the `/skills/` virtual mount
(`/skills/<skill>/scripts/...`, resolved by the EvoQuant sandbox to the
installed skill directory — same convention used by `paper-graph`); **data/output paths** point into the EvoQuant **workdir**
and may be given relative to the workdir (with the workdir as cwd) or as
absolute paths. In docs, a leading `/` denotes the workdir root (e.g.
`/code-repo/`, `/experiments/`); in shell commands these are plain relative
paths (`code-repo`, `experiments/...`).

## How to run (minimal demo)

Run with the EvoQuant **workdir as cwd** (the code-repo lives at `code-repo`
under it). Script paths use the `/skills/` virtual mount, matching the convention (`python /skills/<skill>/scripts/<x>.py`); data/output
paths are relative to the workdir (cwd). Experiment outputs go under the
current cycle's project directory `experiments/<project>/` (see
`experiment-pipeline`'s "Project directory" convention — one per research cycle).

```bash
# 1. discover usable datasets under the code-repo (autonomous, no hard-coded names)
python /skills/quant-experiment-runtime/scripts/discover_data.py --code-repo code-repo --out catalog.json

# 2. from catalog.json pick datasets[i].root, then build the panel offline
python /skills/quant-experiment-runtime/scripts/build_panel.py \
  --data-root <selected-dataset-root> \
  --out experiments/<project>/panel_1d.parquet

# 3. run an experiment (single or batch Candidate JSON -> ExperimentResult JSON)
python /skills/quant-experiment-runtime/scripts/run_experiment.py \
  --panel experiments/<project>/panel_1d.parquet \
  --candidate /skills/quant-experiment-runtime/assets/candidate-template.json \
  --label-col label_1d_close_to_close --splits train val \
  --artifacts-dir experiments/<project>/artifacts --out experiments/<project>/result.json
```

`<selected-dataset-root>` is whatever `discover_data.py` reported for the chosen
dataset (e.g. `code-repo/<dataset-folder>`); it is never typed by hand from
memory.

A Candidate JSON points its `compute_ref` at the Research Artifact's entry
point (see `assets/candidate-template.json`). The example artifact at
`assets/research-artifact-example/factor.py` computes a 20-day reversal factor
and is the reference LLMs should imitate.

## What the Executor owns (vs Workflow / Research Artifact)

| Layer | Owns |
|-------|------|
| **Workflow (`experiment-pipeline`)** | when/whether to run; stage budgets; reflection → evo-memory |
| **Executor (this skill)** | data discovery/load, train/val/test split, calling the Entry Point, Metric evaluation, artifacts dir, ExperimentResult |
| **Research Artifact (LLM-generated)** | the object's logic, expression form, alignment, byproducts |
| **Metric** | how to evaluate results (only evaluate; never realign) |

## Demo scope

- **Demo-verified**: Alpha Factor Research (single + batch). Optional: Alpha
  Generation Methodology (`run_batch`).
- **Scaffolded, not demoed**: Portfolio Strategy Research. No portfolio Metric
  is registered yet — only `ic_panel`. SKILL.md does NOT claim all three types
  are demoable. Adding a portfolio Metric later requires no Runtime change
  (register it; see `references/metrics-extension.md`).

## Train / val / test

Split is **ratio-based, not hard-coded years** (data coverage changes over
time). Defaults: train 56% / val 22% / test 22% of coverage; `test` is opt-in.
The agent may override dates/ratios/label_col via `--split-config`. See
`references/split-policy.md`.

## Extensibility

- New **Metric**: `metrics_registry.register(name, fn)` — see
  `references/metrics-extension.md`.
- New **Research Artifact form** (package/workspace/docker): the Entry Point
  abstraction already accommodates this; only `load_entry_point` may need a new
  loader. Candidate/ExperimentResult/Entry-Point signature do not change.
- New **research-object type**: a new Research Artifact + (if needed) a new
  Metric. No Runtime branching.

## Reference Navigation

| Topic | File |
|-------|------|
| Entry Point / RuntimeContext / Candidate / ExperimentResult contract | [references/runtime-interface.md](references/runtime-interface.md) |
| What research code must implement + alignment duty + examples | [references/research-code-convention.md](references/research-code-convention.md) |
| Train/val/test rules, fixed vs overridable, 4-stage alignment | [references/split-policy.md](references/split-policy.md) |
| Registering new metrics / experiment types | [references/metrics-extension.md](references/metrics-extension.md) |
| Runnable factor Research Artifact example | [assets/research-artifact-example/factor.py](assets/research-artifact-example/factor.py) |
| Candidate input template | [assets/candidate-template.json](assets/candidate-template.json) |
| ExperimentResult schema | [assets/experiment-result-schema.json](assets/experiment-result-schema.json) |
| Example split config | [assets/split-config.example.json](assets/split-config.example.json) |

## Skill Integration

| Stage | Action |
|-------|--------|
| From `experiment-pipeline` Stage 1/3 | build panel → run Candidate → get IC metrics → record in stage log |
| From `experiment-pipeline` (batch) | `run_batch` a generation round, evaluate distribution |
| To `evo-memory` / reflection | hand off `ExperimentResult` + `artifacts/` |
| See | [experiment-pipeline/references/quant-experiment-integration.md](../experiment-pipeline/references/quant-experiment-integration.md) for calling-time contract |