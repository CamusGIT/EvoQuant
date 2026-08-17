# Confidence Rules

The 5-state status system, the `is_sound` gate condition, hard prohibitions, and status promotion rules.

## The 5-State System

EvoMath awards exactly one of these five labels to every final result. They are mutually exclusive.

### PROVED
**Awarded by**: Phase 4 only (Safeguards 1–3; matching math-olympiad's pure-reasoning audit).
**Conditions** (ALL must hold):
- A complete human-readable proof text exists.
- Every non-trivial step has explicit justification (cited theorem, claim, or computation).
- No language like "obviously", "clearly", "显然", "易见", or unjustified "WLOG" remains.
- Phase 4 audit reports 0 FATAL and 0 CRITICAL issues.
- Phase 4 records 4 HOLDS and 0 HOLE FOUND (asymmetric voting).
- At least 4 distinct Phase-4 counterexample cases were tried and none refute.

**Meaning**: agent-audited human-readable proof. This is the strongest label EvoMath awards.

### REFUTED
**Awarded by**: Any phase.
**Conditions** (any one suffices):
- A counterexample term verified by exact arithmetic
- A contradiction proof reaching a known-false statement (e.g., 0 = 1, derived from the original statement)

**Hard rules**:
- Floating-point or approximate-arithmetic counterexamples do **not** refute. Re-verify exactly first.

### VERIFIED_NUMERICALLY
**Awarded by**: Any phase.
**Conditions**:
- Finite-N exhaustive or random-sampled cases passed.
- The label `N` and the test domain are explicitly recorded in the output.

**Meaning**: empirical evidence within a bounded domain. **Numerical evidence is NOT a proof step** — this label exists to record empirical support honestly without inflating to PROVED.

### CONJECTURED
**Awarded by**: Phase 1 or Phase 2.
**Conditions**:
- Data or partial reasoning supports the statement, but no Phase-4-audited proof exists.
- Or, an `is_sound` candidate from Phase 2 that has not yet passed Phase 4.

### HANDED_OFF
**Awarded by**: Phase 5.
**Conditions**:
- Phase 5 termination triggered (see SKILL.md termination rules)
- A complete Handoff Report has been issued (see `handoff-template.md`)

## Hard Prohibitions

1. ❌ Self-evaluation cannot upgrade a label. CONJECTURED → PROVED requires Phase 4 audit; the same model "agreeing with itself" is not evidence.
2. ❌ LLM grader score is a ranking signal only. Even `score = 7` candidates remain CONJECTURED until Phase 4 awards PROVED.
3. ❌ Best-effort drafts that did not pass Phase 4 must not be labeled PROVED.
4. ❌ Approximate-arithmetic counterexamples are not REFUTED until exact-verified.
5. ❌ Numerical verification on `n ≤ N` does not extrapolate beyond `N`. Always state the domain.
6. ❌ A status label assigned in Phase 1 or Phase 2 is provisional; downstream phases may downgrade but not upgrade without Phase 4.

## is_sound (Gate Condition, NOT a Status)

```
is_sound(candidate) :=
    candidate.score >= 5
    AND candidate.fatal_flaws is empty
    AND every gap in candidate.gaps is local AND fixable
```

Definitions:
- **local gap**: affects only the current subgoal, not upstream or downstream.
- **fixable**: can be addressed by adding a justification step, not by changing the proof strategy.

A candidate that `is_sound`:
- Proceeds to assembly (Phase 3 if multi-step) and Phase 4 audit
- Is **not** PROVED yet — only Phase 4 awards PROVED
- May receive CONJECTURED in any interim user-facing output

## Confidence vs Memory-Layer Semantics

The 5-state system applies to claims, not memory layers. L1 claim entries carry a `granted-status` field using the 5-state vocabulary. L2 strategy entries and L3 pattern entries do NOT carry confidence labels — they have their own semantics:

| Entry type | Confidence semantics | Promotion |
|---|---|---|
| L1 claim | 5-state label (`is_sound-only` / CONJECTURED / VERIFIED_NUMERICALLY / PROVED / REFUTED / HANDED_OFF) | Via Phase 4 audit |
| L2 strategy | `status: provisional | confident | confident-negative` + `success-rate: 0.0–1.0` | Via Phase 6 ESE after repeated successes |
| L3 pattern | No status field; presence in the library is the confidence signal | Via Phase 6 IVE after cross-type evidence |

A confident L2 strategy is NOT the same as a PROVED L1 claim. A strategy says "this technique works repeatedly for this problem-type"; a PROVED claim says "this specific claim is correct". Do not conflate them.

A new L3 pattern (e.g., P41) is not "proved" in the claim sense — it is a named observation about failure / success modes. Patterns are about *meta-knowledge*, not about specific mathematical truths.

## Output Modes vs Confidence Labels

These are orthogonal. Confidence labels describe trustworthiness; output modes describe the form of the final artifact. The user's `goal` (from Phase 0) determines the output mode; Phase 4 / Phase 5 determine the confidence label.

| Output mode | Typical confidence labels | Notes |
|---|---|---|
| Proof | PROVED, sometimes CONJECTURED for subclaims | Markdown proof by default; optional LaTeX source with provenance annotations |
| Refutation | REFUTED | Counterexample + verification log |
| Audit Report | mix (per audited step) | Each step independently labeled |
| Handoff Report | HANDED_OFF | Wall report; subclaims may be partially PROVED |
| Exploratory Report | Mostly CONJECTURED and VERIFIED_NUMERICALLY, with inline uncertainty markers | Legitimate research output. Does NOT require any PROVED claims. Failed explorations are first-class content. |

Exploratory Report is an output mode for `theory-building` and `literature-synthesis` goals. It is NOT a confidence label; do not include it in the 5-state system.

## Status Promotion Rules (summary)

| From | To | Allowed? | Required action |
|---|---|---|---|
| CONJECTURED | PROVED | ✅ | Phase 4 audit with 4 HOLDS, 0 HOLE FOUND, 0 FATAL/CRITICAL, and at least 4 distinct counterexample cases tried |
| CONJECTURED | REFUTED | ✅ | Verified counterexample (exact arithmetic) |
| CONJECTURED | VERIFIED_NUMERICALLY | ✅ | Run finite-N test, record N and domain |
| PROVED → CONJECTURED | downgrade allowed | ✅ | If a downstream check finds an issue |
| Any | PROVED | ❌ via self-eval only | Phase 4 audit required |
