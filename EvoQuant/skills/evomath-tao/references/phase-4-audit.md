# Phase 4 — Audit Protocol Detail

Phase 4 is the only phase authorized to award PROVED. It is also the most vulnerable to LLM self-bias, so its protocol is intentionally stricter than generic "review your work" patterns.

The audit uses **three structural safeguards** matching math-olympiad's pure-reasoning approach. PROVED requires all three to pass plus the named-pattern screen and counterexample-first rule.

## Three Structural Safeguards

### Safeguard 1 — Verifier Context Isolation

Each Phase 4 reviewer sees **only the cleaned proof**, not:
- Phase 2 reasoning traces
- Phase 3 deliberation
- Phase 4 earlier reviewers' verdicts
- The original brainstorming or method-selection rationale

Why: thinking traces bias verifiers toward agreement. A reviewer who sees "the agent considered three approaches and settled on induction because…" is psychologically primed to confirm induction. A reviewer who sees only the induction proof is psychologically free to attack it.

**Implementation rule (math-olympiad VERBATIM "strip thinking" step)**: before submitting the proof to a reviewer, **strip all thinking blocks, false starts, exploratory prose, and method-selection commentary**. This is a separate, named pre-verification step — not a soft suggestion. Pass to the verifier only:

- The theorem statement (verbatim from Intake Card)
- The cleaned proof text (with every step justified)
- The cited claims (with their statements, but not their proofs unless requested)
- An explicit instruction: "Attack this proof. Look for the hole. Do not assume good faith."

**Forbidden in the verifier's view**:
- Solver's internal reasoning ("I considered three approaches…")
- Phase 2 candidate scores or revisions
- Earlier reviewers' verdicts (Safeguard 2 isolation)
- Encouragement / praise language

The strip-thinking step is what makes Safeguard 2's asymmetric vote meaningful. Without isolation, reviewers anchor to the proof's confidence; with isolation, each reviewer is independently adversarial.

### Safeguard 2 — Asymmetric Voting

Phase 4 launches **multiple independent reviewers** on the same cleaned proof. The decision rule is asymmetric:

| Outcome | Threshold |
|---|---|
| **CONFIRM** (verdict = PASS or WARN, allowing PROVED) | ≥ 4 reviewers HOLDS and 0 HOLE FOUND |
| **REFUTE** (verdict = FAIL, must repair or escalate) | ≥ 2 reviewers HOLE FOUND |
| **INCONCLUSIVE / REPAIR NEEDED** (repair, re-run, or Phase 5) | Anything else |

The asymmetry exists because finding a flaw is asymmetric evidence: one careful reviewer finding a real FATAL is more reliable than five superficial reviewers passing the proof. **Two HOLE FOUND verdicts stop the audit immediately, regardless of how many HOLDS were collected.** A single HOLE FOUND does not by itself refute the proof, but it blocks PROVED until repaired or shown to be a reviewer error by a fresh isolated review.

### Safeguard 3 — Pigeonhole Exit

Reviewers are launched serially or in parallel. Once the asymmetric threshold is reached, **stop launching more reviewers**.

| State after k reviewers | Action |
|---|---|
| 4 HOLDS, 0 HOLE | Exit confirmed |
| 3 HOLDS, 1 HOLE | Continue (could still go either way; need 4 HOLDS or 2 HOLE) |
| 2 HOLDS, 2 HOLE | Exit refuted |
| 1 HOLDS, 2 HOLE | Exit refuted |
| 0 HOLDS, 2 HOLE | Exit refuted |
| 4 HOLDS, 1 HOLE | Repair or Phase 5; PROVED forbidden |
| 5 HOLDS, 1 HOLE | Repair or Phase 5; PROVED forbidden |

Empirically, pigeonhole exit saves ~30% of verifier cost on clear-cut cases (both clearly correct and clearly broken).

## Anti-Pattern: Resist Case-Split Reflex (math-olympiad "Unified Argument" principle)

When a Phase 4 audit triggers a return to Phase 3 because **one specific case** of a proof's case split fails, the temptation is to attack that case in isolation and patch the proof. Resist this.

The math-olympiad principle: **when one case in a split resists, step back and look for an intermediate object whose properties eliminate the case split entirely**.

**Why**: a hard case often signals the case split was wrong, not that the case is genuinely harder. The intermediate object exists because the original problem has a unifying structure the case split hid.

**Implementation in EvoMath**:

| Trigger | Action |
|---|---|
| Phase 4 found CRITICAL only in one case of a multi-case proof | Phase 3 must explicitly try: "is there an object X whose existence makes this case split unnecessary?" before re-attempting case-specific repair |
| 2 consecutive failed repairs of the same case | Mandate the Unified Argument search; forbid further case-specific patching |
| The case-by-case proof has > 4 cases | Pre-emptive Unified Argument search before Phase 3 even starts (high prior of structural issue) |

**Example**: instead of splitting "n even" and "n odd" and finding the odd case hard, look for a parity-independent invariant. If you find one, the case split was a sign your viewpoint was wrong; the unified proof is cleaner *and* more likely correct.

## Reviewer Protocol

### Launch Protocol

Preferred: launch four independent reviewer contexts or subagents. Each receives only the reviewer prompt below and the cleaned proof bundle.

If independent reviewer contexts are unavailable:
- Run a single local 20-class audit and mark `reviewer-independence: unavailable`.
- Do not award PROVED. The strongest allowed status is CONJECTURED, unless a verified counterexample gives REFUTED or Phase 5 gives HANDED_OFF.

If independent contexts are available but must be launched serially, they are acceptable if each reviewer receives no earlier reviewer verdicts and no upstream reasoning traces.

### Reviewer Prompt Template

```text
You are an isolated proof auditor for EvoMath Phase 4.

Input:
1. The theorem statement from Phase 0.
2. The cleaned proof text only.
3. Cited claim statements and their granted-status values.
4. The cases-tried list so far, but not previous reviewer verdicts.

Task:
1. Check named patterns P4, P5, P6, P18, P40.
2. Check the generic 20 issue classes.
3. Try at least one new counterexample or boundary/degenerate case.
4. Check restatement drift.
5. Return exactly:

reviewer-id: R<n>
verdict: HOLDS | HOLE FOUND | UNCLEAR
new-cases-tried:
  - <case and result>
issues:
  - severity: FATAL | CRITICAL | MAJOR | MINOR
    issue-class: <taxonomy id>
    location: <step/line>
    description: <one sentence>
    repair-suggestion: <one sentence>
notes: <one short paragraph>
```

Each reviewer follows this protocol per launch:

1. **First-pass named-pattern screen** (cheap, fast). Check the proof against P4 / P5 / P6 / P18 / P40 from `grading-taxonomy.md`. Any named-pattern hit at FATAL / CRITICAL severity is an immediate HOLE FOUND.
2. **Generic 20-class sweep**. Audit against the full taxonomy. Any FATAL or CRITICAL is HOLE FOUND.
3. **Counterexample attempt** (mandatory per reviewer). Each reviewer tries at least one new counterexample case the previous reviewers did not try (smallest non-trivial, boundary, degenerate, adversarial scaling).
4. **Restatement drift check**. If the proof contains multiple statements of the theorem, check consistency.
5. **Verdict**: HOLDS / HOLE FOUND / UNCLEAR.

Reviewers MAY share their attempted counterexamples through a shared cases-tried list (so reviewer 3 doesn't repeat reviewer 1's case), but reviewers do NOT share their final verdicts until all are complete.

## Persistent Reviewer Across Iterations

Phase 4 sometimes sends the proof back to Phase 3 for repair, then re-audits the repaired proof. In this case:

- The first audit (iteration 1) uses **fresh reviewers** with full context isolation (Safeguard 1 applies in full).
- The re-audit (iteration 2+) uses the **same reviewer identities** as iteration 1 — they see the before/after diff and can specifically check whether their original concerns were addressed.

Why the difference: in iteration 1, isolation protects against bias. In iteration 2+, the bias risk is reversed — fresh reviewers might re-discover flaws that were already raised and fixed, wasting cycles. Persistent reviewers ensure focused incremental review.

**Implementation rule**: when iteration 2+ starts, the reviewer prompt should include:
- Their iteration-1 HOLE FOUND comments (if any)
- The Phase 3 repair notes (what was changed and why)
- The before/after diff of the proof

But still **NOT** the Phase 2/3 reasoning traces of the *original* attempts. Persistent identity does not mean unblinding to the full upstream history.

## Edge Cases

| Edge case | Handling |
|---|---|
| Reviewer crashes mid-audit | Restart with a fresh reviewer; do not count the partial result |
| Reviewer says UNCLEAR | Treat as 0 HOLDS and 0 HOLE FOUND; continue launching reviewers |
| All 4 reviewers say UNCLEAR | Run single-pass detailed audit with full 20-class sweep; do not award PROVED on UNCLEAR consensus |
| Reviewer flags a MAJOR issue (not FATAL/CRITICAL) | HOLDS with notes; collect MAJOR in the audit summary but does not block PROVED |
| Reviewer flags MINOR only | HOLDS; collect for the final audit report |
| Proof relies on a subclaim the reviewer cannot verify | Reviewer must check whether the subclaim is in positive memory at PROVED status. If yes, accept. If no, HOLE FOUND. |

## Counterexample Cases-Tried Pool

Across all reviewers in a single audit, the pool of counterexample cases tried should expand monotonically. Each reviewer is required to add at least one new case. The final audit report lists the full pool.

Example progression for an inequality on positive integers:
- Reviewer 1: n = 1, n = 2
- Reviewer 2: n = 100, boundary n = 0 (out of domain, vacuously skipped)
- Reviewer 3: n = 1000, adversarial large coefficient
- Reviewer 4: degenerate edge case (all-equal inputs)

By the end, 7+ distinct counterexample cases have been tried. If none refute, the proof has been stress-tested.

## PROVED Award Conditions (recap)

PROVED requires ALL of:
1. ≥ 4 HOLDS (asymmetric voting threshold)
2. 0 HOLE FOUND
3. 0 named-pattern FATAL/CRITICAL hits
4. 0 generic taxonomy FATAL/CRITICAL hits
5. At least 4 distinct counterexample cases tried, none refute
6. Restatement drift check performed (no drift, or drift is MAJOR-or-lower)
7. The PROVED Self-Check Checklist in `output-formats.md` is fully ticked

If any one fails, the verdict is FAIL or WARN, not PASS. WARN allows PROVED only when issues are MAJOR-or-lower; FAIL forbids PROVED entirely.

These seven conditions match math-olympiad's pure-reasoning audit. No external proof assistant is required for PROVED — the audit's strength comes from adversarial isolation, asymmetric voting, and exhaustive counterexample probing.

## Why Phase 4 Looks Like This

The protocol's strictness reflects EvoMath's central commitment: **LLM self-evaluation cannot be trusted to award PROVED**. The asymmetric vote, the context isolation, the named-pattern screen, the counterexample cases pool — each is a counter to a specific bias mode:

| Bias mode | Counter |
|---|---|
| Confirmation bias from reading own reasoning | Verifier context isolation |
| Social proof from seeing other verifiers' opinions | Isolation extended to other reviewers' verdicts |
| Fluency reward (clean-looking proofs feel right) | P40 named pattern + 20-class taxonomy |
| Single-reviewer error | Asymmetric voting with multiple independent reviewers |
| Oversearching for confirmation | Pigeonhole exit on clear refutation signals |
| Drift across iterations | Persistent reviewer identity in iteration 2+ |
| Ritualized self-audit (model walks the workflow and ticks every box without genuine scrutiny) | Mandatory adversarial-attack reviewer prompt + counterexample-first rule + named-pattern screen |

A proof that survives Phase 4 has been pressure-tested. A proof that fails has been honestly rejected.
