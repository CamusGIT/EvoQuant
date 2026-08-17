# Memory Architecture (Three Layers)

## Table of Contents

- [Memory Architecture (Three Layers)](#memory-architecture-three-layers) — overview of L1/L2/L3 layers
- [Runtime Persistence Contract](#runtime-persistence-contract) — how memory survives across problems
- [L1 — Working Memory (ProofArtifact)](#l1--working-memory-proofartifact) — per-problem positive + negative memory
  - [Why Per-Problem, Not Global](#why-per-problem-not-global)
  - [ProofArtifact Schema](#proofartifact-schema)
  - [Sort Order, When to Read/Update, Self-Promotion, Status Tracking, Refutation/Demotion, Decay, Truncation](#sort-order-positive-memory)
  - [Example: Memory Through a Multi-Phase Solve](#example-memory-through-a-multi-phase-solve)
- [L2 — Strategy Memory](#l2--strategy-memory) — per-problem-type reusable strategies
- [L3 — Pattern Library](#l3--pattern-library) — global named failure/success patterns (P4/P5/P6/P18/P40/…)
- [Phase 6 — Reflection Protocols](#phase-6--reflection-protocols)
  - [ESE — Empirical Strategy Extraction (success path)](#ese--empirical-strategy-extraction-success-path)
  - [IVE — Implementation vs Fundamental Failure Classification](#ive--implementation-vs-fundamental-failure-classification)
- [Inter-Layer Flow Diagram](#inter-layer-flow-diagram)

**When to read which section**:
- Default workflow: read overview + Runtime Persistence Contract only.
- Editing memory behavior in code: read L1 schema + Sort Order + Self-Promotion.
- Adding a new strategy or pattern: read L2/L3 sections + Phase 6 protocols.
- Debugging a failed reflection step: read Phase 6 ESE/IVE protocols + Flow Diagram.

---

EvoMath's memory is the substrate for **self-evolution**. It is organized as three layers with distinct scopes and update behaviors:

| Layer | Name | Scope | Contents |
|---|---|---|---|
| **L1** | Working Memory (ProofArtifact) | Per-problem | Positive claims + negative attempts + candidate counterexamples |
| **L2** | Strategy Memory | Per-problem-type | Reusable strategies (e.g., "modular + Vieta jumping for Diophantine") |
| **L3** | Pattern Library | Global | Named failure/success patterns (P4, P5, P6, P18, P40, ...) |

The layered design implements seven self-evolution principles: dual-track storage (positive + negative), failure typing (implementation vs fundamental), success distillation (claim → strategy → pattern), critique-driven loop, usage-frequency curation, honest demotion, and scoped reuse.

Phase 6 (Reflection) is the engine that moves knowledge between layers — extracting strategies from L1 successes (ESE) and patterns from L2 cross-type failures (IVE).

## Runtime Persistence Contract

Memory is useful only if the runtime can actually carry it forward.

- L1 Working Memory is always in-session and per-problem. It lives in the phase ledger and resets at the start of each new problem.
- L2 Strategy Memory and L3 Pattern Library are current-session state by default.
- If the runtime can read/write files, use `.evomath/session-memory.json` at the workspace root as the storage file for L2/L3.
- At the start of a new problem, read `.evomath/session-memory.json` if it exists. If it does not exist, start with the seeded L3 patterns from `grading-taxonomy.md` and empty L2.
- At Phase 6, write updates to `.evomath/session-memory.json` only when file writing is available. If not, output `proposed-memory-updates` and set `memory-persisted: false`.
- Do not claim that future problems will use a strategy or pattern unless it was either saved to `.evomath/session-memory.json` or is still present in the active session context.

---

# L1 — Working Memory (ProofArtifact)

A structured per-problem record of proven subclaims (**positive memory**) and failed attempts (**negative memory**). It is the cross-phase substrate that lets the pipeline avoid repeating itself: once a fact is proven or refuted within a problem, downstream phases must consult the memory before launching new work.

## Why Per-Problem, Not Global

Research-level mathematical claims are deeply problem-specific. The claim "in this Diophantine problem, the LHS is divisible by 7 mod p" almost never transfers to another problem. A global memory would:
- Inject irrelevant claims into prompts, diluting attention
- Produce false confidence when an old claim's hypotheses don't match the new problem
- Tie the skill to a stateful storage layer it cannot rely on existing

Per-problem memory:
- Resets on every new problem (no carry-over)
- Stays small (only relevant facts)
- Mirrors how a human mathematician works: "I proved this earlier in the same proof, so I can use it now"

This design choice is based on the practical behavior of olympiad-level proof
workflows: problem-specific facts transfer poorly, while compact local memory
keeps later proof attempts focused.

## ProofArtifact Schema

```yaml
positive-memory:
  - id: <subclaim id, e.g., g3 or c1>
    statement: <the proven claim, normalized>
    proof-summary: <one-paragraph compressed proof>
    granted-status: PROVED | VERIFIED_NUMERICALLY | CONJECTURED | is_sound-only
    confidence: 0.0–1.0     # from grading score / 7, or post-audit score
    usage-count: <int>      # how many later phases cited this claim
    source-phase: 2 | 3 | 4
    proven-by: <method name, e.g., "induction-on-n">

negative-memory:
  - id: <attempt id>
    target: <what was being attempted, e.g., "g3 via probabilistic method">
    failure-mode: <one-line reason, e.g., "expected value calculation depended on independence that was not given">
    failed-at: <step number or sub-step>
    severity: dead-end | local-only | recoverable-with-modification
    relates-to: <subclaim id whose proof was being attempted>

candidate-counterexamples:
  - id: <case id>
    case: <the candidate counterexample term, e.g., "n = 41, x = 1/3">
    verification-status: not-verified | exact-verified | exact-refuted
    relates-to: <subclaim id whose claim it would refute>
```

## Sort Order (Positive Memory)

When injecting positive memory into a downstream prompt, sort by:
1. `usage-count` (descending) — facts cited more often are more central to the proof structure
2. `confidence` (descending) — higher-confidence facts first
3. `id` (ascending, stable) — for deterministic ordering

This concentrates attention on the claims most likely to be cited again. A claim proven once but never reused is a candidate for truncation if memory grows.

## When to Update Memory

| Phase | What enters positive memory | What enters negative memory |
|---|---|---|
| Phase 1 | Patterns confirmed by exact arithmetic on the test domain (status: VERIFIED_NUMERICALLY) | Patterns ruled out by exact arithmetic (entered as candidate-counterexamples) |
| Phase 2 | Candidates that pass `is_sound` AND whose parent moves forward (status: is_sound-only until Phase 4) | Methods with FATAL flaws + their failure mode (severity = dead-end) |
| Phase 3 | Subclaims marked PROVABLE and proven via Phase 2 recursion | Subclaims marked NOT_JUSTIFIED that cannot be weakened (severity = dead-end); refuted decomposition shapes (severity = local-only) |
| Phase 4 | Audited subclaims promoted to PROVED (status updated in-place; usage-count preserved) | Issues found that downgrade earlier subclaims — see Demotion section |
| Phase 5 | (no new positive entries) | The wall record (the failure that triggered handoff, severity = dead-end) |

## When to Read Memory

| Phase | Read positive memory | Read negative memory |
|---|---|---|
| Phase 0 | No (Phase 0 must not solve) | No |
| Phase 1 | Yes — to avoid recomputing already-confirmed patterns | Yes — known counterexamples |
| Phase 2 | Yes — proven subclaims can be cited; pick top-k by sort order | Yes — avoid methods already failed for this goal |
| Phase 3 | Yes — proven children can be assumed when proving parents | Yes — refuted decompositions warn against re-trying same shape |
| Phase 4 | Yes — verify that every cited claim in the proof is actually in positive memory at PROVED or higher status | Yes — ensure no negative entry contradicts a proof step |
| Phase 5 | Yes — list proven subclaims in handoff report (Section 4: Partial Progress) | Yes — list failed methods in handoff report (Section 2: Methods Attempted) |

## Self-Promotion Prohibition

A candidate enters **positive memory** only when:
1. Its `is_sound` was established by an AdvGrader (in Phase 2), AND
2. Its parent goal advanced to Phase 4 or beyond (i.e., the subclaim was actually used downstream).

A candidate must NOT enter positive memory just because:
- It had a high score (e.g., 7) but was not yet integrated into the upstream proof chain
- The model "felt good about it"
- A single grader call returned `is_sound`

This mirrors the self-eval prohibition in `confidence-rules.md`: a high score is a ranking signal, not a certificate. Memory must be earned by actual use, not by hopeful self-assessment.

## Status Tracking Within Memory

Positive-memory entries carry a `granted-status` that is updated in-place as the claim's standing changes:

| Granted-status | Meaning | Promotion path |
|---|---|---|
| `is_sound-only` | Candidate passed Phase 2 grading; parent has not yet completed Phase 4 | → CONJECTURED if parent reaches Phase 4 without auditing this subclaim; → PROVED if Phase 4 audits it cleanly |
| `CONJECTURED` | Used in proof chain but not independently audited | → PROVED if a later phase audits the claim directly |
| `VERIFIED_NUMERICALLY` | Confirmed on a finite domain (entered via Phase 1) | Cannot promote to PROVED without an actual proof; remains numerical evidence only |
| `PROVED` | Phase 4 audit confirmed | Stable; only demotion path is contradiction by another Phase 4 finding |

A claim's `granted-status` is part of the memory state and must travel with it into downstream prompts.

## Refutation and Demotion

If a positive-memory entry is later contradicted (e.g., Phase 4 audit finds the claim was overclaimed, or a Phase 4 counterexample violates it):

1. **Remove** the entry from positive memory.
2. **Migrate** to negative memory with `failure-mode = "previously claimed proven, refuted by Phase 4 issue: <issue>"` and `severity = dead-end`.
3. **Transitive re-audit**: any subclaim in positive memory whose proof depended on the demoted claim must be re-audited. Downgrade transitively if the dependency is essential. If the dependent proof has alternative justification, keep it but record the dependency change.

Demotion is part of honesty: a memory that never demotes is a memory that lies under pressure. The pipeline must be willing to give back PROVED labels when evidence requires.

## Negative Memory Decay

Negative memory entries with `severity = local-only` may be re-evaluated if the surrounding subclaim changes. A method that "failed for goal g3" may work for goal g4 because the goals' hypotheses differ. Tag negative entries with `relates-to: <goal-id>` so re-evaluation is scoped, not global.

Entries with `severity = dead-end` do not decay. If a method has a fundamental obstruction (e.g., produces a contradiction with the problem's hypotheses), it should not be retried within this problem.

## Truncation (Soft Rule)

If positive memory grows large enough to risk bloating downstream prompts:
- Keep all entries with `usage-count ≥ 1`
- Drop the lowest-confidence entries with `usage-count = 0` first
- Always retain entries with `granted-status = PROVED`
- Always retain entries that are referenced as dependencies in the dependency DAG

Specific size thresholds are a runtime decision, not a methodology rule. The principle is: prefer a smaller, hotter memory over a complete, cold one. A bloated memory degrades downstream attention and is worse than a curated one.

## Integration with State Compression

ProofArtifact is the **organized, persistent layer** of the State Compression rule:
- State Compression (in SKILL.md) says: "pass structured conclusions, drop raw traces"
- ProofArtifact says: "here is exactly what 'structured conclusions' means, sorted by usefulness, and here are the failures alongside them"

When a phase exits, its outputs (per `output-schema.md`) are the **raw compressed summaries** for that phase. ProofArtifact is the **cumulative memory** built up across all phases of the same problem so far. Both must respect the rule: no raw traces enter the next phase's prompt.

## Integration with the 6 Status System

Memory entries' `granted-status` field uses the same vocabulary as `confidence-rules.md`'s 5-state system, with one addition: `is_sound-only` for working-state candidates that have not yet been audited.

The promotion rules from `confidence-rules.md` apply equally to memory entries:
- Self-eval cannot upgrade `is_sound-only` to `PROVED`. Phase 4 audit is required.
- A `score=7` candidate enters memory as `is_sound-only`, not as `PROVED`.
- Memory `granted-status` uses the 5-state vocabulary (`is_sound-only` / `CONJECTURED` / `VERIFIED_NUMERICALLY` / `PROVED` / `REFUTED`).

## Example: Memory Through a Multi-Phase Solve

For a problem decomposed into subclaims g1 → g2 → g3:

1. **Phase 2 attacks g1**:
   - Method "induction" succeeds, candidate scores 6, `is_sound = true`
   - g1 enters positive memory: `granted-status: is_sound-only, source-phase: 2, usage-count: 0`

2. **Phase 2 attacks g2**:
   - Reads positive memory, sees g1 available
   - Method "use g1 + extremal" succeeds, candidate scores 5, `is_sound = true`
   - g2 enters positive memory; g1's `usage-count` increments to 1
   - Method "direct construction" fails with FATAL → enters negative memory

3. **Phase 2 attacks g3**:
   - Reads positive memory: g1 (usage 1, conf 0.86), g2 (usage 0, conf 0.71)
   - Reads negative memory: "direct construction failed for g2"
   - Method "use g1 + g2" succeeds, candidate scores 7, `is_sound = true`
   - g3 enters positive memory; g1 and g2 both have `usage-count: 1` and `usage-count: 1`

4. **Phase 4 audits the assembled proof (g1 → g2 → g3 → main)**:
   - g1: PASS → status promoted to PROVED
   - g2: WARN (one MAJOR issue, fixable) → status promoted to PROVED with note
   - g3: PASS → status promoted to PROVED
   - Main theorem: PASS → final status PROVED

5. **Counterfactual**: if Phase 4 finds g2 overclaimed:
   - g2 demoted from positive memory to negative (severity: dead-end)
   - g3 transitively re-audited; if g3's proof essentially uses g2, g3 also demoted
   - Main theorem either re-audited under weakened g2 or escalated to Phase 5

## Rationale Notes (L1)

This design follows the ProofArtifact pattern used by EvoMath. Practical
findings:
- Per-problem scoping outperforms global memory for olympiad-level problems
- Negative memory is roughly as important as positive memory for reducing wasted attempts
- Sort by (usage_count, confidence) concentrates relevance better than by recency or score alone
- Truncation matters; bloated memory degrades downstream attention quality

---

# L2 — Strategy Memory

Strategy Memory holds **reusable, problem-type-level techniques** distilled from successful L1 claims. Unlike L1 claims (specific facts about specific problems), strategies are general approaches that have been observed to work on a class of problems.

## When to Add a Strategy

A strategy enters L2 only via **Phase 6 ESE** (Empirical Strategy Extraction). After Phase 4 awards PROVED:
1. Identify the winning technique(s) at the problem-type level (not the specific claim).
2. Check if a matching strategy already exists in L2 for this problem-type.
3. If matching strategy exists: increment `usage-count`, recompute `success-rate`.
4. If not: add new entry with `status: provisional`.

A `provisional` strategy promotes to `confident` after observed working on **multiple distinct problems of the same problem-type** (recommended threshold: 3 successful uses with success-rate ≥ 0.6).

## Strategy Memory Schema

```yaml
strategies:
  - id: s-NT-001
    problem-type: number-theory
    technique-summary: "For symmetric Diophantine equations, try Vieta jumping after small-prime mod analysis"
    success-rate: 0.0–1.0      # successful uses / total attempts
    usage-count: <int>          # total times applied
    success-count: <int>        # times it led to PROVED
    failure-count: <int>        # times it led to HANDED_OFF or REFUTED-of-method
    status: provisional | confident | confident-negative
    source-problems: [<problem-id-1>, <problem-id-2>, ...]
    created-at: <session marker>
    last-updated-at: <session marker>
```

## When to Read Strategy Memory

| Phase | Read L2? | Use |
|---|---|---|
| Phase 2 | YES | Before selecting top-5 from angle library, prioritize `confident` strategies whose `problem-type` matches the current problem |
| Phase 3 | YES | When decomposing, check whether known strategies suggest a natural decomposition |
| Phase 6 ESE | YES | Comparing new winning technique against existing entries |

## Negative Strategy Entries

If Phase 6 IVE classifies a failure as **fundamental** (technique categorically does not apply), log it as an L2 entry with:
- `status: provisional` (always; fundamental claims need multi-problem evidence to harden)
- `success-rate: 0`
- `failure-count: 1+`

A negative strategy with multiple `failure-count` and `success-count = 0` becomes a recommendation: "do not try X for problem-type Y". After 3 consistent fundamental failures of the same technique on the same problem-type, promote to `confident-negative` status.

## L2 Demotion

Strategy entries can be demoted:
- If a `confident` strategy fails on a problem-type where it previously succeeded, downgrade to `provisional` and record the counterexample problem.
- A `confident-negative` entry can be revoked if a counterexample emerges (the technique DID work somewhere unexpected).

L2 entries persist across problems only within the same session unless `.evomath/session-memory.json` was successfully written. Their authority depends on continued observation.

---

# L3 — Pattern Library

Pattern Library holds **named failure/success patterns** observed across **multiple problem types**. These are the highest-abstraction layer — they describe structural failure modes that transcend any specific problem type.

The library starts seeded with five empirical patterns (see `references/grading-taxonomy.md`):
- **P4**: Open Problem Reduction
- **P5**: Hypothesis Re-Verification Bypass
- **P6**: Divergent Series Regularization
- **P18**: Tautology Disguised
- **P40**: Overly Clean One-Liner

## When to Add a New Pattern

A new pattern enters L3 only via **Phase 6 IVE** when cross-type evidence accrues:
1. After IVE classifies a failure as **fundamental** in L1, check whether a similar fundamental signature already exists in L2 or L3.
2. If the same fundamental signature is observed in **2+ problem-types**, propose a new Pattern entry.
3. Assign the next P-number (P41, P42, ...).
4. Patterns are conservative additions — premature naming is worse than missing one. Require explicit cross-type evidence.

## Pattern Library Schema

```yaml
patterns:
  - id: P41
    name: <short descriptive label, e.g., "Probabilistic Method Without Independence">
    diagnostic: <one-line trigger description; how to detect this pattern>
    severity-guidance: <e.g., "CRITICAL when used in main theorem proof; MAJOR in claim">
    generic-classes-mapped-to: [<one or more of the 20 issue classes>]
    observed-in-types: [<list of problem-types where this has been seen>]
    discovery-trail:
      - problem-id: <id>
        problem-type: <type>
        failure-summary: <one line>
    created-at: <session marker>
```

## When to Read Pattern Library

| Phase | Read L3? | Use |
|---|---|---|
| Phase 4 audit | YES | First-pass named-pattern screen (see `phase-4-audit.md`): scan against all known P-numbered patterns before doing generic 20-class sweep |
| Phase 6 IVE | YES | Compare new fundamental failures against existing patterns to update or propose new ones |

## L3 Decay

Pattern entries are nearly permanent. They can be:
- **Refined**: diagnostic wording updated based on new observations
- **Cross-linked**: when patterns co-occur, note the relationship
- **Deprecated**: only if explicit evidence shows the pattern was a false generalization (rare; requires meta-review)

Patterns are NOT removed simply because they haven't been seen recently. They represent crystallized failure modes.

---

# Phase 6 — Reflection Protocols

Phase 6 runs **unconditionally** after Phase 4 (success) or Phase 5 (handoff). It does NOT modify the user-facing artifact; it only updates L2 and L3 memory when runtime storage or active session state exists. If no storage exists, it records proposed updates only. This separation is intentional: the artifact is decided before any self-evolution writes, so Phase 6 cannot be used to retroactively justify a PROVED claim.

## ESE — Empirical Strategy Extraction (success path)

Triggered when Phase 4 awards PROVED or REFUTED.

**Steps**:
1. **Identify winning technique**: from L1, find the candidate(s) with highest confidence that led to PROVED. Extract their `proven-by` field.
2. **Abstract to problem-type level**: rephrase the technique from "induction with this specific recurrence" to "induction on monotone parameter" — a level abstract enough to be reusable, specific enough to be discriminating.
3. **Check L2 for match**: search existing strategies in this problem-type. Match by technique-summary semantics, not exact string.
4. **Update or insert**:
   - Match found: increment `usage-count` and `success-count`; recompute `success-rate`; if previously `provisional`, check whether the new evidence promotes to `confident`.
   - No match: insert new strategy with `status: provisional` and `success-count: 1`.
5. **Conservative threshold for promotion**: `confident` requires `success-count ≥ 3` on the same problem-type with `success-rate ≥ 0.6`.

## IVE — Implementation vs Fundamental Failure Classification

Triggered whenever any `fatal_flaws` were recorded in any phase (regardless of final outcome).

**Steps**:
1. **Iterate over each fatal_flaw entry** in L1 negative memory.
2. **Classify failure type** (see `grading-taxonomy.md` for full criteria):
   - **implementation**: arithmetic error, wrong citation, missed case, off-by-one, naming collision — *fixable by retrying carefully*
   - **fundamental**: technique categorically does not apply (e.g., density argument for finite set; probabilistic method without independence; modular argument where modulus is wrong dimension) — *no retry will help*
3. **Update L1 negative memory**: set `severity: dead-end` for fundamental; `severity: recoverable-with-modification` for implementation.
4. **Promote fundamental failures to L2**: add as a negative strategy entry (`success-rate: 0`, `failure-count: 1`) for the problem-type. Multiple cross-problem occurrences harden it.
5. **Cross-type pattern detection**: if the same fundamental failure signature is observed in 2+ problem-types (combining L2 negative strategies across types), propose a new L3 Pattern entry.

## When Each Sub-Protocol Runs

| Trigger | Sub-protocols |
|---|---|
| Phase 4 → PROVED, no failures recorded | ESE only |
| Phase 4 → PROVED, failures recorded in Phase 2/3 | Both ESE and IVE |
| Phase 4 → REFUTED | ESE (the refutation method is a winning technique) |
| Phase 5 → HANDED_OFF, with failures | IVE only |
| Phase 5 → HANDED_OFF, no failures (rare) | Neither |

## Phase 6 Output (Reflection Log)

Phase 6 does NOT alter the user-facing output. It produces a separate reflection log:

```yaml
phase-6-reflection:
  memory-persisted: true | false
  storage-location: <".evomath/session-memory.json" or null>
  ese:
    performed: true | false
    strategy-updates:
      - strategy-id: <id>
        action: created | promoted | usage-incremented | demoted
        rationale: <one line>
  ive:
    performed: true | false
    failures-classified:
      - failure-id: <id from L1 negative memory>
        classification: implementation | fundamental
        rationale: <one line>
    new-pattern-proposed:
      - pattern-id: P<n>
        signature: <one line>
        cross-type-evidence: [<problem-types>]
  memory-state-after-phase-6:
    l2-strategies-count: <int>
    l3-patterns-count: <int>
```

This log is internal but auditable. It is the agent's record of what it learned from this problem. If `memory-persisted: false`, treat entries as proposals, not durable memory.

## Rationale: Why a Dedicated Phase 6

Without an explicit reflection step, self-evolution does not happen:
- Without **ESE**, every problem starts from the angle library; cumulative experience is wasted.
- Without **IVE**, failures look identical and repeated attempts happen.
- Without **cross-type Pattern detection**, structural failure modes never crystallize into nameable warnings.

Phase 6 is intentionally **separate** from Phase 4 / Phase 5 so the user-facing artifact is **decided before** any self-evolution writes occur. The agent cannot use Phase 6 to retroactively justify a PROVED claim; the artifact is locked first.

## Inter-Layer Flow Diagram

```
                    ┌─────────────────┐
                    │   L1: Working   │
   user problem →   │   Memory        │  ← Phases 1–5 read/write
                    │   (per-problem) │
                    └────────┬────────┘
                             │
                             │ Phase 6 (Reflection)
                             ▼
              ┌──────────────────────────────┐
              │  ESE → success → L2 strategy  │
              │  IVE → failure → L2 negative  │
              │       → if cross-type        │
              │          → L3 pattern         │
              └──────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   L2: Strategy  │  ← Phase 2 reads (top-k)
                    │   Memory        │  ← Phase 6 writes
                    │   (per-type)    │
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   L3: Pattern   │  ← Phase 4 reads (audit screen)
                    │   Library       │  ← Phase 6 writes
                    │   (global)      │
                    └─────────────────┘
```

Each layer feeds higher abstraction to the next. L1 is throwaway after the problem; L2 retains type-level knowledge; L3 retains universal failure modes. Together they implement self-evolution at three timescales: within a problem, across problems of the same type, and across problem types.
