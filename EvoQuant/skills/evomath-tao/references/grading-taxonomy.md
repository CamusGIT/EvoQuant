# Grading Taxonomy — 20 Issue Classes

Used in Phase 2 (per-candidate grading) and Phase 4 (final audit).

## The 4 Groups × 5 Classes

### Group A: Logic & Proof Structure

1. **Unjustified assertion** — "clearly", "obviously", "显然", "易见" without backing reasoning.
2. **Unproven sub-claim** — intermediate step asserted but never derived (no proof, no citation).
3. **Quantifier confusion** — ∀ / ∃ swap, scope ambiguity, missing universe of discourse.
4. **Case incompleteness** — disjunction not exhaustive (e.g., "n is even or odd" without ruling out negative n if n ∈ ℤ).
5. **Circular reasoning** — the conclusion (or a chain ending at it) is used to prove itself.

### Group B: Analysis & Measure Theory

6. **Illegal limit / integral interchange** — swap of lim, ∫, Σ, ∂ without DCT / MCT / Fubini citation and verification.
7. **Non-uniform convergence misuse** — pointwise convergence treated as uniform; affects continuity, integration of limit, etc.
8. **Missing dominating function** — DCT applied without |f_n| ≤ g, ∫g < ∞.
9. **Boundary / endpoint mishandling** — open vs closed interval mismatch; behavior at infinity not addressed.
10. **Differentiation under integral sign without conditions** — Leibniz rule needs hypotheses (continuity, dominated derivative).

### Group C: Model & Parameter Tracking

11. **Hidden assumption** — used a property never stated (continuity, finiteness, smoothness, connectedness, …).
12. **Insufficient assumption** — premise too weak to support conclusion as stated.
13. **Dimension / normalization mismatch** — units, dimensions, or scaling inconsistent across the proof.
14. **Constant tracking failure** — uniformity of constants (e.g., big-O) not preserved across nested limits.
15. **Variable shadowing / re-binding** — same symbol used for different objects in different parts of the proof.

### Group D: Scope & Claims

16. **Overclaim** — conclusion stronger than what was actually proved.
17. **Reference mismatch** — cited theorem's hypotheses don't match the use case.
18. **Tautological reasoning** — restating the definition is presented as a proof.
19. **Specialization to open problem** — "proof" reduces to a famous unsolved case (Riemann, P=NP, …); a gap has been hidden.
20. **Non-constructive existence used as construction** — existence claim treated as if it produced an algorithm or explicit witness.

## Two-Axis Severity

| Status \ Scope | Global (main theorem) | Local (side result, claim) |
|---|---|---|
| **Invalid** (logically wrong) | **FATAL** | **CRITICAL** |
| **Unjustified** (cannot be defended as written) | **CRITICAL** | **MAJOR** |
| **Overstated / Understated** (correct but misframed) | **MAJOR** | **MINOR** |
| **Unclear** (ambiguous wording, may be fine) | **MINOR** | **MINOR** |

## Severity → Phase 4 Verdict

- Any **FATAL** present → verdict = **FAIL** → return to Phase 3 to fix the responsible subclaim, or to Phase 2 if the entire approach is broken
- Any **CRITICAL** present (with no FATAL) → verdict = **FAIL** → return to Phase 3 to repair, or escalate to Phase 5 if irreparable
- Only **MAJOR** present → verdict = **WARN** → proof may be marked PROVED, but issues are listed in the audit report and surfaced to the user
- Only **MINOR** present → verdict = **PASS** → PROVED label may be awarded
- No issues → **PASS**

## Counterexample-First Rule

Before assigning any score in Phase 2 or before declaring PROVED in Phase 4, attempt to construct a counterexample to the candidate / proof for at least one of:

- Smallest non-trivial case (n = 1, 2, 3, …)
- Boundary case (boundary of variable domain, ε → 0, n → ∞)
- Degenerate configuration (collinear points, zero matrix, empty set, …)
- Adversarial parameter scaling (very large constants, near-singular matrices, distributions with heavy tails)

If a counterexample is found and survives exact-arithmetic verification → status = **REFUTED**, halt the candidate / proof immediately.

If no counterexample is found → proceed with grading or PROVED award.

## fatal_flaws and gaps Output Structure

```yaml
fatal_flaws:
  - issue-class: <one of the 20 classes>
    named-pattern: <P-number if matched, else null>
    failure-type: implementation | fundamental | unclassified   # set by IVE in Phase 6
    severity: FATAL | CRITICAL | MAJOR | MINOR
    location: <step number, line reference, or subclaim id>
    description: <one sentence>
gaps:
  - location: <step or line reference>
    missing: <what is missing — e.g., "justification that f is differentiable">
    local: <true/false — does fixing this affect upstream/downstream steps?>
    fixable: <true/false — addressable without changing strategy?>
```

The `failure-type` field is initially `unclassified` when the flaw is first recorded in Phase 2 or Phase 4. **Phase 6 IVE** classifies it as `implementation` or `fundamental` (see below). The classification determines whether the flaw becomes a dead-end in L1 negative memory and whether it is promoted to L2 / L3.

## IVE — Implementation vs Fundamental Failure Classification

Phase 6 classifies each recorded `fatal_flaw` into one of two types. The classification is binary and consequential — get it right.

### implementation Failure

A failure whose root cause is a *correctable execution error*, not a categorical mismatch between technique and problem.

Examples:
- **Arithmetic error**: "5! = 120, but I wrote 5! = 100 in the proof"
- **Wrong citation**: "I cited Theorem 3.2 from [Smith 2020], but the actual theorem there is about something else"
- **Missed case**: "I split into n even and n odd, but forgot n = 0"
- **Off-by-one indexing**: "I wrote S_n = sum to n-1 instead of sum to n"
- **Naming collision**: "I used x for two different variables in the same scope"
- **Computation timeout**: "the enumeration didn't finish in the alotted time"

Action:
- Set `failure-type: implementation`
- Set L1 negative-memory `severity: recoverable-with-modification`
- Do NOT promote to L2 (the technique itself is fine; the application was sloppy)
- Allow retry of the same technique with the correction

### fundamental Failure

A failure whose root cause is a *categorical mismatch* between the technique and the problem class. No correction will fix it; trying again will fail again.

Examples:
- **Density argument applied to a finite set**: "I argued by positive density, but the set has size at most 7"
- **Probabilistic method without independence**: "I computed E[X·Y] = E[X]·E[Y], but X and Y are dependent"
- **Modular argument with wrong modulus**: "I tried mod p, but p doesn't divide the relevant quantity for any choice"
- **Compactness in non-compact space**: "I extracted a convergent subsequence, but the space is not sequentially compact"
- **Reduction to open problem**: "the step reduces to a special case of the Riemann hypothesis"
- **Inductive step requires constructing X**: "induction step needs an object that itself requires proving the conjecture"

Action:
- Set `failure-type: fundamental`
- Set L1 negative-memory `severity: dead-end`
- **Promote to L2 Strategy Memory** as a negative entry (`success-rate: 0`, `failure-count: +1`) for this problem-type
- If the same fundamental signature is now observed in 2+ problem-types (combined across L2), propose a new L3 Pattern entry
- Forbid retry of the same technique on this problem

### unclassified

If IVE cannot confidently classify, leave as `unclassified`. The flaw stays in L1 negative memory at its original severity and is not promoted to L2. Unclassified flaws should be rare — if many appear, IVE is being too cautious.

## IVE Heuristics

When classifying:
- Ask: **"if I retry with the same technique, can the failure go away?"**
  - Yes → implementation
  - No → fundamental
- Ask: **"does the failure stem from the technique's hypotheses being violated, or from a slip in applying it?"**
  - Hypothesis violation → fundamental
  - Slip → implementation
- Ask: **"would a careful human, given enough time, fix this with the same technique?"**
  - Yes → implementation
  - No → fundamental
- When in doubt, prefer `implementation` (allowing retry); `fundamental` is a stronger claim that locks out future attempts.

## IVE Edge Cases

| Situation | Classification |
|---|---|
| Proof has both an arithmetic slip AND a fundamental gap | Two separate `fatal_flaw` entries: one `implementation`, one `fundamental` |
| Failure mode is genuinely novel (not in any existing pattern) | `fundamental` if a careful retry won't help; flag for human review during Phase 6 if cross-type signature unclear |
| Reviewer disagrees with Phase 6 IVE classification | Allow downgrade from `fundamental` to `implementation` only if explicit counterexample is shown (a successful retry of the same technique elsewhere) |

## Score → Action Mapping

| Score | Tier | Action |
|---|---|---|
| 0–1 | Fundamentally Flawed | Discard candidate, force regenerate from a different angle |
| 2–3 | Significant Issues | Force revision (max 2 rounds) with critique fed back |
| 4 | Plausible but Incomplete | Targeted gap-filling allowed |
| 5–6 | Sound / Good | Accept as `is_sound` (if fatal_flaws empty); proceed to Phase 4 |
| 7 | Excellent | Accept; Phase 4 audit still required before PROVED label |

`is_sound` requires: score ≥ 5 AND fatal_flaws empty AND every gap is local AND fixable.

## Phase 4 Restatement Drift Check

If the proof or its surrounding text contains multiple statements of the theorem (abstract, introduction, main statement, summary, table caption), check for:
- **Conditional loss** — hypothesis dropped in a restatement
- **Scope change** — universal/existential quantifier altered
- **Quantifier loss** — "for all" → "there exists" or vice versa
- **Constant divergence** — different constants given in different restatements

Drift findings:
- A drift of conditional-loss or scope-change at the abstract or main statement → **CRITICAL** (statement-level mismatch is a Group D #16 overclaim).
- A drift in summary or caption only → **MAJOR**.

## Common Fatal Patterns (cheat sheet)

| Pattern | Issue Class | Typical severity |
|---|---|---|
| "Clearly, f is continuous" without proof | #1 | CRITICAL+ |
| Swapping lim and ∫ without justification | #6 | CRITICAL |
| "WLOG assume X" where X strengthens hypothesis | #11 | CRITICAL |
| Using "for some n" then later "for all n" without re-deriving | #3 | FATAL |
| "By the same argument…" applied to a non-symmetric case | #4 | CRITICAL |
| Citing Theorem X but X requires hypothesis user's setup violates | #17 | CRITICAL |
| Reduces to "if Riemann hypothesis is true" without saying so | #19 | FATAL (hidden gap) |
| "There exists f" then writing code as if f were given | #20 | CRITICAL |

## Named Failure Patterns (Olympiad-Style)

These are concrete, named failure patterns observed in competition-level proofs. Each maps to one or more generic 20-class entries above, but carries its own diagnostic name for easy reference. Use these as **first-pass screens** during Phase 4 audit — they catch the most common olympiad-proof failures faster than the generic taxonomy.

### P4 — Open Problem Reduction
- **Generic class**: Group D #19
- **Diagnostic**: the proof, when traced through, reduces to a famous unsolved problem (Riemann hypothesis, Goldbach, ABC, P=NP, twin primes) without acknowledgement.
- **How to detect**: ask "what would I need to assume to make this step work?" If the answer is an open conjecture, P4 fires.
- **Severity**: FATAL (the gap is hidden, often dressed up in derived language)

### P5 — Hypothesis Re-Verification Bypass
- **Generic class**: Group C #11 + Group D #17
- **Diagnostic**: a cited theorem's hypotheses are not re-verified for the current problem's setup. Common with classical theorems whose conditions are "obvious" but not explicit.
- **How to detect**: every citation in the proof must have an explicit checklist of "the theorem requires A, B, C; A holds because…, B holds because…".
- **Severity**: CRITICAL (often invisible to the proof author)

### P6 — Divergent Series Regularization
- **Generic class**: Group B #6
- **Diagnostic**: manipulates an infinite series or product whose convergence was not verified. Includes telescoping that doesn't telescope finitely, rearrangement of conditionally convergent series, formal manipulation of generating functions outside their domain of convergence.
- **How to detect**: every Σ, Π, lim must have an explicit convergence justification.
- **Severity**: CRITICAL

### P18 — Tautology Disguised
- **Generic class**: Group D #18
- **Diagnostic**: a restatement of a definition is presented as a proof step. Common with "by definition, X is Y, therefore Y holds".
- **How to detect**: ask "does this step add new information?" If not, P18 fires.
- **Severity**: CRITICAL (proof becomes vacuous)

### P40 — Overly Clean One-Liner
- **Generic class**: Group A #2 + Group D #18
- **Diagnostic**: a single line dismisses a non-trivial sub-claim ("by AM-GM, X = Y", "by symmetry, WLOG", "by induction, true for all n"). The line *looks* like a citation, but the substance is hidden.
- **How to detect**: ask the line to expand into 3-5 sub-steps. If it cannot, P40 fires.
- **Severity**: at minimum require expansion; if expansion reveals gaps, escalate to FATAL/CRITICAL
- **Why named**: math-olympiad work has found this pattern especially common in LLM-generated proofs — fluency rewards compression, but the compression often hides errors.

### P41 — 2×2 Case Test (general-lemma stress)
- **Generic class**: Group A #2 + Group D #18 (P40 sibling, but for "for all" claims)
- **Diagnostic**: a claim "for all matrices / sets / configurations X, P(X) holds" with a short one-shot proof. P40 catches the proof; P41 catches the claim itself.
- **How to detect**: take the smallest non-trivial instance — for matrices, 2×2; for sets, 2-element; for n in ℕ, n=1 and n=2. Walk the alleged proof through these cases by hand. If the proof's reasoning doesn't track the small case faithfully (steps that vanish, hypotheses that don't apply), P41 fires.
- **Severity**: matches P40 — at minimum require explicit small-case verification; if the small case refutes the claim, escalate to **FATAL** (counterexample found).
- **Why it complements P40**: P40 attacks the proof's compression. P41 attacks the claim's generality. A proof can pass P40 (looks rigorous) yet fail P41 (the general claim breaks at n=2). math-olympiad's "extract general lemmas from short proofs" principle is operationalized as P41.

## How to Use Named Patterns

1. **First pass (in Phase 4 audit)**: scan for P4 / P5 / P6 / P18 / P40 / P41 explicitly before doing the generic 20-class sweep. These are cheap to check and frequently positive.
2. **Each named-pattern hit triggers an audit alert** with the same severity as the underlying 20-class entry.
3. **Treat as a recall mnemonic, not as a replacement for the 20 classes**. Named patterns are common; the 20 classes are comprehensive.
4. **Extending the list**: when a new failure mode is observed repeatedly across audits, give it a P-number and add it here. The list is intended to grow with empirical experience.
