# Phase 5 — Handoff Report Template

When the agent cannot proceed within EvoMath's termination rules, output this structured wall report instead of a fabricated proof.

## When to Issue a Handoff Report

Triggered by any of:

- **From Phase 2**: max score < 3 AND Phase 3 found no testable subclaims
- **From Phase 2**: 5 distinct techniques tried, no `is_sound` candidate, and decomposition cannot produce a testable next step
- **From Phase 3**: any subclaim is NOT_JUSTIFIED and cannot be weakened; OR recursion depth > 2; OR 2 decomposition attempts produce circular dependency
- **From Phase 4**: a FATAL or CRITICAL issue is found that cannot be repaired by returning to Phase 3 within reasonable bounds
- **From any phase**: phase budget exhausted, same-route stall rule triggered twice, or a required phase artifact cannot be produced
- **From runtime**: tool/model limit reached after partial progress; report the last reliable phase output instead of returning no status
- **From any phase**: a built-in fallback exhausted itself (one-shot degradation rule)

## Deep Mode (mandatory prerequisite to Handoff)

Before issuing a Handoff Report, the agent MUST run **Deep Mode**: one last focused attempt on the precise failure location, with the following constraints.

### Target

The specific subclaim or step that triggered the termination condition. Do **not** re-attack the whole problem or restart broad exploration.

### Allowed Tactics (the Deep Mode toolbox)

This list is exhaustive. Anything not on it is forbidden during Deep Mode.

| Tactic | When to use | Example |
|---|---|---|
| **Modular arithmetic** | Number-theory gaps; parity / residue arguments | "compute the claim mod 7 to find a contradiction" |
| **Bounded enumeration** (`n ≤ 10`) | Existence / forall claims over integers | "verify the conjecture for n = 1..10 exhaustively, find a small counterexample or pattern" |
| **Symbolic verification** | Algebra / calculus gaps; identity claims | "sympy `simplify`, `expand`, `solve` on the disputed identity" |
| **Boundary / degenerate case enumeration** | Continuity / topology / geometry gaps | "test n=0, n=∞, x at the domain boundary, collinear / coincident configurations" |
| **2×2 case test** (math-olympiad named pattern P41) | Suspected overly-clean one-liner; general-lemma claims | "if claim says ∀ matrices A, prove or disprove for 2×2 matrices first" |
| **Re-reading the proof under different angle** | Hidden assumption gaps | "treat the proof line-by-line as if reviewing a stranger's work" |

### Prohibitions

- ❌ No web access
- ❌ No literature lookup  
- ❌ No fresh problem reinterpretation (Phase 0 has already locked the interpretation)
- ❌ No new broad strategy search (that is Phase 2's job)
- ❌ No fabrication-friendly tools (avoid LLMs querying other LLMs)

### Duration

One focused pass, **at most 2 tool calls** on the precise gap. Deep Mode is depth, not breadth.

### Deep Mode Outcomes

| Outcome | Next step |
|---|---|
| Deep Mode succeeds (gap closed) | Return to Phase 4. The audit re-runs on the repaired proof. |
| Deep Mode finds a counterexample | Status: REFUTED. Skip Handoff. |
| Deep Mode produces partial progress (e.g., weakened claim provable) | Issue Handoff with weakened version as an offer. |
| Deep Mode finds nothing | Proceed to full Handoff Report. Record Deep Mode attempt in the report. |

Deep Mode is the rescue for "almost there" cases. It is intentionally narrow: it must not restart broad exploration, repeat a failed route, or delay the Handoff Report indefinitely.

## Required Sections

````markdown
# EvoMath Handoff Report

## 1. Failure Location

- **Subclaim ID** (if from decomposition): <e.g., g3>
- **Statement**: <precise claim that could not be proved or refuted>
- **Failure mode**: NOT_JUSTIFIED | RECURSION_DEPTH_EXCEEDED | CIRCULAR_DEPENDENCY | NO_PROGRESS_OVER_2_ROUNDS | SINGLE_METHOD_STALL | PHASE_BUDGET_EXHAUSTED | REQUIRED_ARTIFACT_MISSING | UNRESOLVABLE_AMBIGUITY | FATAL_IRREPARABLE | TOOL_OR_MODEL_LIMIT | FALLBACK_EXHAUSTED

## 2. Methods Attempted

| Method | Outcome | Reason for failure |
|---|---|---|
| <e.g., Extremal principle> | failed | <e.g., boundary condition n=0 cannot be satisfied> |
| <e.g., Induction on n> | failed | <e.g., induction step requires constructing X; no construction found> |
| <e.g., Contradiction> | failed | <e.g., assumed counterexample turns out to be allowed by hypotheses> |
| <e.g., Probabilistic method> | failed | <e.g., expected value calculation depends on unproven independence> |

## 2b. Deep Mode Outcome

- **Target**: <the subclaim or step Deep Mode attacked>
- **Methods within Deep Mode**: <e.g., "exhaustive enumeration for n ∈ [1, 10]", "symbolic verification via sympy">
- **Result**: succeeded | refuted | partial-progress | failed
- **Notes**: <what was learned or eliminated>

## 3. Empirical Observations (from Phase 1)

- **Test domain**: <e.g., n ∈ [1, 200], integers>
- **Patterns observed**: <e.g., the inequality holds with equality at n = 7, slack elsewhere>
- **Counterexample status**: not-found | candidate-found-but-not-verified | verified
- **Notable anomalies**: <e.g., n = 21 behaves differently from n ≤ 20>

## 4. Partial Progress

- **Proved subclaims**:
  - g1: <statement> — proved by <method>
  - g2: <statement> — proved by <method>
- **Refuted subclaims**:
  - <list — these may simplify the problem>
- **Subclaim proven only under stronger hypothesis H'**:
  - <if so, state H' precisely; this is a candidate weakening>

## 5. Question to the User

Use one of the following structures (do not fabricate; use only the one that fits the situation):

**A. Conceptual gap**
> "We cannot bridge from <subclaim A> to <subclaim B> using standard methods <list>. We suspect a new conceptual ingredient is needed.
> 
> What is your intuition — should we (a) introduce a new invariant? (b) change the topology / structure? (c) accept the weakened conclusion under H'?"

**B. Suspected falsity**
> "The data suggests the statement is true for n ≤ N but breaks at n = N+1 in <specific way>. We could not verify this case under exact arithmetic because <reason>.
> 
> Is this a candidate counterexample worth investigating, or do you want a corrected statement?"

**C. Unverified candidate counterexample**
> "We found a candidate counterexample at <case>, but cannot verify it under exact arithmetic because <reason>.
> 
> Can you confirm or refute this case manually, or provide computational tools to verify?"

**D. Statement ambiguity**
> "Two distinct interpretations of the original statement lead to different theorems. We could not progress without choosing.
> 
> Which interpretation did you intend?"

**E. Genuine no-clue**
> "We are stuck and unsure what would unblock us. The standard methods listed in §2 all failed in different ways, and we found no unifying pattern. Possible directions include <speculative list>, but we have no preference.
> 
> Could you suggest a starting point or share your intuition about the problem?"

## 6. Status Label

This report results in: **HANDED_OFF**

When the user supplies new information, EvoMath restarts at the appropriate phase:
- New conceptual ingredient → restart at Phase 3 with the ingredient as a given claim
- Counterexample confirmation → REFUTED (record the counterexample)
- Counterexample refutation → restart Phase 2 with the failed case as additional constraint to handle
- Interpretation chosen → restart at Phase 0 with the chosen interpretation
- New starting point → restart Phase 2 with that angle

## 7. Phase 6 Follow-up (automatic, internal)

After this Handoff Report is issued, **Phase 6 runs automatically** to perform IVE classification on the recorded failures and update L2 Strategy Memory (and possibly L3 Pattern Library). The reflection log is internal; it does NOT change this report.

The user does NOT need to act on Phase 6 output — it is the agent's record of what it learned from this problem. If the user is curious, the Phase 6 reflection log is available alongside this report.
````

## Anti-Patterns (Phase 5)

- ❌ Padding the report to look longer or more thorough
- ❌ Hiding failure behind technical jargon
- ❌ Recommending the user "double-check the algebra" when the issue is conceptual
- ❌ Labeling a partially proved result as PROVED with caveats — use HANDED_OFF instead
- ❌ Listing methods you didn't actually try
- ❌ Manufacturing a "core insight" claim when the proof is technical assembly
- ❌ Asking 6 questions at once — pick the one that most unblocks
- ❌ Writing the user a proof outline as if to teach them; this is a question, not a lecture
- ❌ Returning no final status after a timeout or tool/model error when partial progress exists
- ❌ Re-running the whole problem inside Deep Mode

## Honesty Rules

- If only 2 methods were tried, list 2 — do not invent a third.
- If a method "almost worked", say what was missing precisely.
- If you suspect the original statement is false but cannot prove it, say so under "Empirical Observations" and ask for confirmation.
- If you don't know what to ask the user, use template **E** explicitly.
- If a Phase-1 candidate counterexample exists but was not verified, say "candidate, not verified" — never call it a counterexample.

## Comparison: HANDED_OFF vs CONJECTURED

Both are honest non-PROVED outcomes. Use them differently:

- **HANDED_OFF** when there is a specific question the user can answer to unblock progress. Phase 5 was triggered by a termination rule.
- **CONJECTURED** when partial reasoning supports the claim but no termination rule fired (e.g., Phase 4 has not been reached, or it has reached but with insufficient evidence to award PROVED yet).

If unsure, prefer HANDED_OFF — it forces a clear next step.
