# From-Scratch Reproduction Protocol

Activated when no usable source code exists for a baseline (determined by the
Stage 1 Source Code Audit). In this mode there is no repo to "get running" —
the agent must **turn the paper into executable code, run it on the available
data, and obtain result metrics**, exactly as Adapt mode's "get the code
running in your environment" goal, but starting from the paper text instead of
a repository.

The protocol is a closed loop: **understand → plan modules → generate code →
run → measure → compare → fix**. Every milestone ends with code that has
actually executed and produced a number, not just a specification.

## What "done" means for From-Scratch

A baseline is reproduced when **all** hold:
- The code runs end-to-end on the **chosen** dataset (the one scoped from what
  is actually available — see Step 1) without errors.
- It produces the evaluation metric defined in the proposal (e.g. IC/ICIR).
- The result is consistent with the paper's claim **at the level the data
  allows**. The local dataset usually differs from the paper's (different
  universe, date window, vendor), so an exact-2%-match is often impossible and
  is NOT the gate. Instead:
  - If the paper reports a number AND the local scope overlaps the paper's
    scope, compare on the overlap and pass when the result is within a
    **tolerance you pre-state and justify** from the documented dataset
    differences (e.g. different universe breadth, shorter window). Record the
    tolerance and why.
  - If the local data cannot be matched to the paper's (different universe /
    no reported number), the gate is **a sane, non-degenerate signal in the
    paper's stated direction**: coverage > 0, IC finite, sign and rough
    magnitude consistent with the claim, stable across the eval window.
- The run is logged in the stage trajectory with config + metric + the
  dataset-difference notes + artifacts.

If after the budget the result cannot be brought to the above, do NOT silently
move on — classify the gap (implementation bug vs. missing paper detail vs.
dataset mismatch vs. paper claim not holding on this data) and either iterate
or hand off to `evo-memory` IVE per the Stage 1 rules.

## Step 0: Source Code Audit (already done in Stage 1)

This protocol assumes Stage 1's audit already classified the baseline as
From-Scratch and wrote `/experiments/<project>/stage1_baseline/source-code-audit.md`
(using `assets/source-code-audit-template.md`). The audit's `find_code.py` /
`code_repo_search.py` results carry over — do not re-run them. If a usable
repo appears during the work, **switch to Adapt mode** instead of continuing
from scratch.

## Step 1: Extract a runnable specification from the paper

Read the anchor paper at L1 via `local-paper-navigator`'s
`fetch_paper.py --paper-id <ID> --reading-level L1 --full-stdout` and write
`/experiments/<project>/stage1_baseline/implementation-spec.md`
(`assets/implementation-spec-template.md`).

The specification must be **implementation-oriented, not summary-oriented**:
extract what a programmer needs to type. The template is research-object
agnostic — first identify the object type from the proposal (Alpha Factor
Research / Alpha Generation Methodology / Portfolio Strategy Research), then
fill the common sections plus the typed section for that object:

- **Common — inputs / outputs / evaluation**: which panel columns the method
  reads; the chosen universe + date window (scoped to the paper's tested range
  intersected with what `discover_data.py` shows is available and the budget —
  not the dataset's maximum range); the output shape (per-instrument exposure
  Series? a batch of candidates? daily portfolio weights?); the label column,
  the metric and its exact definition, and the paper's reported value.
- **Common — data pipeline**: the exact preprocessing order with parameters;
  an explicit no-look-ahead confirmation (every computation at date `t` uses
  only data up to `t`; rolling windows shifted correctly; the label column is
  never an input). Note point-in-time concerns.
- **Typed section** (one of):
  - **Factor**: every factor equation converted to the exact pandas/numpy op;
    window lengths (time-series rolling vs cross-sectional); neutralization /
    standardization / outlier parameters.
  - **Generation methodology**: the generator's inputs and config; the
    generation loop that produces candidate factors; the batch-evaluation plan
    (distribution of IC/ICIR across candidates).
  - **Portfolio**: signal aggregation; the portfolio construction rule /
    optimizer + constraints (turnover, exposure, costs); the portfolio-level
    metrics.

For every equation, prefer writing the concrete operation
(`close.groupby('instrument').rolling(20).std()`) over restating the math —
this is the bridge from paper to code and the most common failure point.

Mark anything the paper omits but implementation requires as `[IMPLICIT]` and
assign a resolution level:

| Level | Meaning | Action |
|-------|---------|--------|
| L1 | Infer from the paper's other sections | re-read the paper |
| L2 | Defined in the method's original publication | find via `local-paper-navigator` |
| L3 | Domain engineering practice | search community guides |
| L4 | Only verifiable empirically | design a tiny validation run |

Do not start coding until the spec has a concrete answer (or an explicit
`[IMPLICIT]` plan) for: inputs, output shape, preprocessing order, and every
hyperparameter. These four gaps block everything downstream.

## Step 2: Map the paper to code modules

Before writing code, decide the module structure so each module can be built
and verified **independently**. For each module record: a name, its
responsibility, its inputs → outputs, and a **verification signal** — a
concrete, runnable check that confirms the module works on its own (borrowed
from the phase-decomposition discipline: name / goal / verification signal).
Write the map into `implementation-spec.md`'s Module map table.

The decomposition depends on the research-object type. Start from the matching
template below, then trim to 3–5 modules. Resist designing the "full system"
first — from-scratch baselines fail by over-building before anything runs.

### Alpha Factor Research

| Module | Responsibility | Inputs → Outputs | Verification signal |
|--------|----------------|------------------|---------------------|
| Data | load panel, ensure required columns, apply universe/window | panel → panel subset | row/stock counts match the paper's universe within reason; required columns present |
| Factor | compute the core exposure | panel → exposure Series | coverage > 0.5; **single-instrument single-day hand calculation matches** the code's value |
| Cross-sectional processing | winsorize / neutralize / standardize | exposure Series → processed Series | no runaway outliers; correlation with the neutralizer drops after neutralizing |
| Evaluation | compute the metric on a split | Series + panel → metric dict | on a synthetic factor with known IC, the metric recovers it; finite + correct sign |

### Alpha Generation Methodology

| Module | Responsibility | Inputs → Outputs | Verification signal |
|--------|----------------|------------------|---------------------|
| Data | load panel | panel → panel | as above |
| Generator | produce candidate factors from seeds/config | panel + config → list of candidate Series | produces the expected number of candidates; each is finite on >50% of rows |
| Candidate evaluation | evaluate the candidate batch | candidates + panel → per-candidate metrics | the metric distribution is finite; a known-good seed candidate scores as expected |
| (Selection) | filter / rank candidates by metric | metrics → shortlist | shortlist length and ordering are stable |

### Portfolio Strategy Research

| Module | Responsibility | Inputs → Outputs | Verification signal |
|--------|----------------|------------------|---------------------|
| Data | load panel | panel → panel | as above |
| Signal aggregation | combine factor(s) into an alpha score | factor Series → score Series | score is finite; cross-sectional rank distribution is sane |
| Portfolio construction | turn score into weights under constraints | score → daily weights | weights sum to the target exposure; turnover within cap; no weight on untradable names |
| Evaluation | compute portfolio metrics | weights + panel → metric dict | on a known signal, long-short return has the expected sign; turnover / Sharpe finite |

### Module decomposition rules (all types)

- One responsibility per module; no module reads another's internals, only its
  declared output.
- Every module has a verification signal you can run **without** the rest of the
  system. If a module can't be verified in isolation, split it.
- Order modules by dependency (Data first, Evaluation last). Each becomes one
  milestone in Step 3.

## Step 3: Generate and run, milestone by milestone

Execute milestones in dependency order. **Each milestone must produce running
code and a verification number in the same attempt**, following the Stage loop
(generate → execute → record → diagnose → revise):

1. **Generate** the module's code, structured as a Research Artifact that
   exposes an Entry Point `entry(context, config) -> results` (see
   `quant-experiment-runtime/references/research-code-convention.md`).
   Reuse the bundled example artifact's shape; replace the logic.
2. **Refine the code** if it is non-trivial (multiple files, tricky logic): you
   may delegate the plan → code → evaluate → refine loop to
   `experiment-iterative-coder` (lint/test/self-evaluation cycles). It raises
   code quality; it does **not** read the paper or decide the module structure
   — that stays in this protocol's spec. Keep the Entry Point contract intact
   when you hand code off.
3. **Execute** it. To run the artifact and get a metric, use
   `quant-experiment-runtime`:
   - Discover the dataset: `discover_data.py --code-repo code-repo --out catalog.json`
   - Build the panel once: `build_panel.py --data-root <root> --out experiments/<project>/panel_1d.parquet`
   - Run the candidate: `run_experiment.py --panel experiments/<project>/panel_1d.parquet --candidate <candidate.json> --splits train val --out experiments/<project>/<milestone>_result.json`
4. **Record** the metric and the exact config in the stage trajectory log.
5. **Diagnose** against the milestone's verification signal (the Module map in
   the spec). On failure, load `experiment-craft` for the 5-step diagnostic —
   it does not consume budget.
6. **Revise** and re-run, or advance to the next milestone.

### Milestone verification

Each milestone's gate is the **verification signal** defined for its module in
the Step 2 Module map. Every signal must actually run and produce a concrete
result (a count, a coverage fraction, a recovered IC, a hand-checked value) —
not just "it ran without error".

**Do not skip milestones.** An unverified module compounds debugging cost in
every later module. If a milestone cannot pass its verification signal within
~3 attempts, stop and re-read the paper section it implements — the spec is
usually wrong, not the code.

## Step 4: Close the loop — reproduce the reported number

Once all milestones pass their verification signals, run the **full** baseline
(all modules chained) and compare to the paper. Because the local dataset is
usually **not** the paper's dataset, the goal is a *faithful reconstruction on
the scoped data*, not an exact match:

1. **Align the methodology, not the dataset.** Match what the paper *does* —
   label column, factor/window semantics, preprocessing order and parameters,
   evaluation metric definition. Do **not** assume you can match the paper's
   universe or date window; use the scope chosen in Step 1 (the paper's tested
   range ∩ what `discover_data.py` shows is available ∩ budget).
2. **Document the dataset differences** explicitly: local universe vs. paper's,
   local window vs. paper's, vendor/source differences, any columns the paper
   used that are unavailable. This determines how close a match is achievable.
3. **Set a comparison basis and tolerance up front**, justified by those
   differences:
   - If the scopes overlap, compare on the overlap and state the tolerance
     (e.g. "IC sign matches and magnitude within 0.02, expected given a
     narrower universe").
   - If they cannot overlap, the bar is directional consistency (sign + rough
     magnitude + stability), and you say so.
4. **Compute the primary metric and judge against that basis.**
   - Met → reproduction succeeded; record the verified baseline code + config +
     result + dataset-difference notes in
     `/experiments/<project>/stage1_baseline/`.
   - Not met → diagnose. Distinguish "implementation/paper-detail gap" (fixable)
     from "expected dataset delta already exceeded" (may be acceptable if
     documented) from "claim doesn't hold on this data" (IVE candidate). The
     usual fixable culprits, in order:
     1. a preprocessing step in the wrong order or with wrong parameters
     2. an `[IMPLICIT]` hyperparameter guessed wrong
     3. a label-column mismatch (e.g. open-to-open vs close-to-close)
     4. an IC-caliber mismatch (Pearson vs Spearman, cross-sectional vs
        time-series)
     Fix one suspect per attempt and re-run. Load `experiment-craft` if
     repeated attempts fail to converge.

## Step 5: Resolve knowledge gaps ([IMPLICIT] markers)

For each `[IMPLICIT]` marker still open after Step 4:
- **L1/L2**: re-read the paper / the method's original publication via
  `local-paper-navigator`.
- **L3**: search community implementations and engineering guides.
- **L4**: design the smallest validation run that confirms the choice (e.g.
  one hyperparameter value on a short date window).

Record resolutions in `/experiments/<project>/stage1_baseline/knowledge-gap-resolution.md`.
Each resolution should change the code and be re-run, not just be written down.

## Step 6: Budget adjustment

From-Scratch costs more than Adapt (see `references/attempt-budget-guide.md`):
- Stage 1 budget: ≤20 → ≤30–40.
- Total pipeline cap: 62 → 82–92.
- Estimated LOC: paper's claimed LOC × 5–10 (papers report core deltas only).
- Estimated time: paper's claimed time × 2–3.

If the milestone map suggests the baseline exceeds the adjusted budget, surface
this to `evo-memory` via IVE *before* burning the budget — a baseline that
cannot be reproduced in budget is a feasibility failure, not a coding failure.

## Common From-Scratch pitfalls

General:

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Spec is a summary, not a build plan | Can't start coding | Re-extract with concrete numpy/pandas ops, output shapes, preprocessing order |
| Building the whole system before anything runs | One bug breaks everything; no signal | Milestone-by-milestone; each module must pass its verification signal first |
| No verification signal, just "it ran" | Silent NaN / degenerate signal | Every module needs a runnable numeric check (coverage, recovered IC, hand-checked value) |
| `[IMPLICIT]` hyperparameter guessed | Metric reasonable but wrong magnitude | L4 validation: sweep that one parameter on a short window |

Quant-specific (check these whenever the metric is off with no obvious bug):

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Look-ahead bias | IC unrealistically high / too stable | Confirm rolling windows shift correctly; the label column is never an input; fundamentals are point-in-time |
| Wrong price adjustment | Level shifts corrupt the factor | Use adjusted prices (`adj_close`) for returns/rolling stats; raw price only where the paper explicitly uses it |
| Cross-sectional vs time-series confusion | IC sign or magnitude wrong | Confirm the operation's groupby: rolling windows group by instrument, cross-sectional ops group by datetime |
| IC caliber mismatch | Metric near paper's but not equal | Match Pearson vs Spearman, and cross-sectional (per-day) vs time-series (per-instrument) IC definition |
| Wrong label column | Sign or magnitude systematically off | Confirm open-to-open vs close-to-close and the holding period against the paper |
| Universe / window differs from paper | Metric reasonable, won't reproduce | Re-scope to the paper's tested universe × date range (within budget), not the dataset's max range |
| Portfolio turnover/cost ignored (Portfolio type) | Returns look too good | Apply the paper's transaction-cost model and turnover constraint in portfolio construction |

## Hand-off

On success: verified baseline code (as a Research Artifact), config, and the
reproduced metric land in `/experiments/<project>/stage1_baseline/`, ready for Stage 2
tuning. The same `quant-experiment-runtime` execution path is reused in
Stages 2–4 — only the Candidate (the artifact / params) changes.