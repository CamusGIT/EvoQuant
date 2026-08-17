# Per-Phase Output Schemas

## Table of Contents

- [Phase 0 — Intake Card](#phase-0--intake-card)
- [Phase 1 — Empirical Report](#phase-1--empirical-report)
- [Phase 2 — Candidate Slate](#phase-2--candidate-slate)
- [Phase 3 — Decomposition Result](#phase-3--decomposition-result)
- [Phase 4 — Audit Report](#phase-4--audit-report)
- [Phase 5 — Handoff Report](#phase-5--handoff-report)
- [Phase 6 — Reflection Log](#phase-6--reflection-log)
- [Memory State Schema (L1 / L2 / L3)](#memory-state-schema-l1--l2--l3)
- [Cross-Phase: Compressed Summary Schema](#cross-phase-compressed-summary-schema)
- [Final Output to User](#final-output-to-user)
- [Optional LaTeX Source Output (Final Format)](#optional-latex-source-output-final-format)
- [Schema Versioning](#schema-versioning)

**When to read which section**:
- Implementing a single phase: read the schema for that phase only.
- Writing the final user-facing artifact: read "Final Output to User" + relevant Phase 4/5/6 schema.
- Persisting memory between problems: read "Memory State Schema".

---

All schemas are YAML for clarity. Phase outputs that flow downstream MUST conform to State Compression: structured conclusions only, no raw traces.

Every phase output MUST include the phase ledger:

```yaml
phase-ledger:
  phase: 0 | 1 | 2 | 3 | 4 | 5 | 6
  status: completed | stopped | escalated
  key-output: <one-line result>
  methods-used: [<short method names only>]
  remaining-gap: <one-line gap, or null>
  next-phase: <phase number or "final">
```

## Phase 0 — Intake Card

See `intake-checklist.md` for the full schema and examples.

## Phase 1 — Empirical Report

```yaml
type: <copied from Intake Card>
test-domain: <e.g., "n ∈ {1, ..., 200}, integers only">
excluded-degenerate-cases:
  - <e.g., "n = 0 (trivial)", "matrices with rank < n">
computation-mode: exact | approximate
phase-budget:
  scripts-written: <int>
  tool-calls-used: <int>
  budget-exhausted: true | false
exact-arithmetic-tools-used:
  - <e.g., "fractions.Fraction", "math.comb", "sympy.Rational">
approximate-arithmetic-flags:
  used: true | false
  precision: <if used, e.g., "float64", "decimal 50 digits">
  used-for: <e.g., "rough sanity check, not for counterexample search">
patterns-found:
  - description: <e.g., "value is always positive when n is odd">
    domain-of-validity: <e.g., "verified for n ∈ [1, 199] odd">
    confidence: low | medium | high
counterexample-status: none | candidate | verified-by-hand
counterexamples:
  - case: <e.g., "n = 7, x = 1/3">
    verification: exact | approximate
    claim-violated: <which claim or sub-claim from the Intake Card>
claims-data-cannot-support:
  - <e.g., "Cannot conclude anything for n > 200 from this data">
  - <e.g., "Continuous-x cases are untested">
heuristic-hypotheses:
  - <e.g., "The bound is tight at n = 7; tightness pattern unclear elsewhere">
compressed-summary:
  - <one-line description of what Phase 2 needs to know>
```

## Phase 2 — Candidate Slate

```yaml
goal: <subgoal id, or "root" if attacking the original claim directly>
techniques-selected:
  - method-name: <e.g., "induction-on-n">
    rationale: <one-line reason for selection>
candidates:
  - id: c1
    technique: <method-name>
    score: 0-7
    is_sound: true | false
    revision-count: <0 or 1>
    same-route-stall: true | false
    fatal_flaws:
      - issue-class: <one of the 20>
        severity: FATAL | CRITICAL | MAJOR | MINOR
        location: <step ref>
        description: <one sentence>
    gaps:
      - location: <step ref>
        missing: <one sentence>
        local: true | false
        fixable: true | false
    counterexample-attempted: true | false
    counterexample-found: true | false
revision-rounds:
  - round: 1
    score-progression: [3, 4]   # before, after
    converged: true | false
selected-for-downstream:
  - <list of candidate ids whose proofs flow to Phase 3 or Phase 4>
phase-2-completeness:
  required-techniques: 5
  techniques-attempted: <int>
  stopped-early-reason: verified-counterexample | is_sound-found | none
compressed-summary:
  - "method <name>: <one-line success or failure summary>"
```

## Phase 3 — Decomposition Result

```yaml
invariant-object: <single organizing quantity or structure>
invariant-rationale: <why this is the right invariant>
subclaims:
  - id: g1
    statement: <claim>
    feasibility: PROVABLE | WEAKEN | NOT_JUSTIFIED
    depends-on: [<subclaim ids>]
    step-class: identity | proposition | approximation | interpretation
    evidence: <Phase 2 candidate id, or "pending", or "fallback-best-effort">
    proven-by: <method-name, if proven>
dependency-dag:
  edges:
    - [<from-id>, <to-id>]
  topological-order: [g1, g2, g3, ...]
  cycles-detected: true | false
  fallback-applied: true | false   # if cycles existed and were broken
weakening-recommendations:
  - subclaim: <id>
    weaker-form: <statement>
    cost: <what is lost — e.g., "result holds only for n ≥ 100">
synthesis-status:
  attempted: true | false
  successful: true | false
  fallback-text-concatenation: true | false
compressed-summary: <one-paragraph summary of the decomposition>
```

## Phase 4 — Audit Report

```yaml
overall-verdict: PASS | WARN | FAIL
verifier-isolation:
  thinking-stripped: true | false        # reasoning traces removed before verifier saw proof
  other-verifiers-hidden: true | false   # this verifier did not see other reviewers' verdicts
  reviewer-independence: independent-contexts | serial-isolated-contexts | unavailable
asymmetric-vote:
  reviewer-count-launched: <int>
  reviewer-count-needed: 4               # for HOLDS confirmation
  holds: <int>
  hole-found: <int>
  outcome: confirmed | refuted | inconclusive
  pigeonhole-exit-triggered: true | false  # stopped early because outcome was decided
persistent-reviewer:
  this-is-iteration: <int, 1 for first pass>
  same-reviewer-as-previous-iteration: true | false   # true for iterations 2+ on the same proof
named-pattern-screen:
  P4-open-problem-reduction: not-detected | detected
  P5-hypothesis-bypass: not-detected | detected
  P6-divergent-series: not-detected | detected
  P18-tautology: not-detected | detected
  P40-overly-clean: not-detected | detected
issues:
  - issue-class: <one of the 20>
    named-pattern: <P-number from L3 pattern library, or null>
    failure-type: implementation | fundamental | unclassified   # set by Phase 6 IVE
    severity: FATAL | CRITICAL | MAJOR | MINOR
    location: <step ref>
    description: <one sentence>
    recommendation: <fix or escalation>
    counterexample-final-attempt:
  performed: true | false
  distinct-cases-count: <int>             # must be >= 4 for PROVED
  cases-tried:
    - <e.g., "n = 1, 2, 3", "boundary at x = 0", "degenerate triangle">
  found: true | false
  case: <if found, full counterexample term>
core-insight-status:
  type: A | B
  # A: single core insight exists
  # B: technical assembly with no single core
  detail: <if A: "Key step is X because Y"; if B: "Relies on coordination of a, b, c">
restatement-drift-check:
  performed: true | false
  drifts-found:
    - location: <e.g., "abstract vs main theorem statement">
      type: conditional-loss | scope-change | quantifier-loss | constant-divergence
      severity: <FATAL/CRITICAL/MAJOR/MINOR>
final-status: PROVED | REFUTED | CONJECTURED | HANDED_OFF
```

## Phase 5 — Handoff Report

See `handoff-template.md` for the full structure.

## Phase 6 — Reflection Log

Phase 6 runs unconditionally after Phase 4 or Phase 5. Its output is a reflection log that records updates to L2 (Strategy Memory) and L3 (Pattern Library). The log does NOT modify the user-facing artifact.

```yaml
phase-6-reflection:
  triggered-by: phase-4-proved | phase-4-refuted | phase-5-handoff | phase-4-with-earlier-failures
  ese:
    performed: true | false
    winning-technique-extracted: <description, or null if not applicable>
    strategy-updates:
      - strategy-id: <id>
        action: created | promoted | usage-incremented | demoted
        before-state: <e.g., "provisional, success-count=2">
        after-state: <e.g., "confident, success-count=3, success-rate=1.0">
        rationale: <one line>
  ive:
    performed: true | false
    failures-classified:
      - failure-id: <id from L1 negative memory>
        location: <step ref>
        classification: implementation | fundamental | unclassified
        rationale: <one line>
        action-on-l1: <e.g., "severity set to dead-end">
        action-on-l2: <e.g., "negative entry added to strategy memory for number-theory">
    new-patterns-proposed:
      - pattern-id: P<n>
        name: <short label>
        diagnostic: <one line>
        cross-type-evidence: [<problem-types where this fundamental signature was observed>]
  memory-state-after-phase-6:
    memory-persisted: true | false
    storage-location: <e.g., ".evomath/session-memory.json", or null>
    proposed-memory-updates-only: true | false
    l1-positive-count: <int>      # for this problem only
    l1-negative-count: <int>      # for this problem only
    l2-strategies-count: <int>    # cumulative across session
    l2-confident-count: <int>
    l3-patterns-count: <int>      # cumulative across session
    l3-new-this-phase: <int>      # patterns added in this Phase 6 run
```

Schema for the structured fields (in addition to the prose template):

```yaml
trigger-source: phase-1 | phase-2 | phase-3 | phase-4 | runtime | fallback-exhausted
failure-mode: NOT_JUSTIFIED | RECURSION_DEPTH_EXCEEDED | CIRCULAR_DEPENDENCY | NO_PROGRESS_OVER_2_ROUNDS | SINGLE_METHOD_STALL | PHASE_BUDGET_EXHAUSTED | REQUIRED_ARTIFACT_MISSING | UNRESOLVABLE_AMBIGUITY | FATAL_IRREPARABLE | TOOL_OR_MODEL_LIMIT | FALLBACK_EXHAUSTED
deep-mode:
  attempted: true | false                 # MUST be true before Handoff per the prerequisite rule
  target: <subgoal id or step ref>
  methods-tried:
    - <e.g., "exhaustive n ∈ [1, 10]", "symbolic verification">
  result: succeeded | refuted | partial-progress | failed
  notes: <what was learned or eliminated>
methods-attempted: [<list of methods from Phase 2/3>]
partial-progress:
  proved-subclaims: [<ids>]
  refuted-subclaims: [<ids>]
  weakened-form: <if applicable, the weaker statement that is provable>
question-template: A | B | C | D | E       # which template from handoff-template.md
question-text: <the actual question to user>
final-status: HANDED_OFF
```

## Memory State Schema (L1 / L2 / L3)

The full state of EvoMath's three-layer memory at any phase boundary:

```yaml
memory:
  l1-working-memory:                  # per-problem; reset at problem boundary
    positive-memory: [...]            # see claim-memory.md for entry schema
    negative-memory: [...]
    candidate-counterexamples: [...]
  l2-strategy-memory:                 # per-problem-type; session-scoped unless persisted
    strategies:
      - id: <s-NT-001 etc.>
        problem-type: <one of 10>
        technique-summary: <string>
        success-rate: 0.0–1.0
        usage-count: <int>
        success-count: <int>
        failure-count: <int>
        status: provisional | confident | confident-negative
        source-problems: [<ids>]
  l3-pattern-library:                 # global; session-scoped unless persisted; conservative additions only
    patterns:
      - id: P<n>
        name: <string>
        diagnostic: <string>
        severity-guidance: <string>
        generic-classes-mapped-to: [<class numbers>]
        observed-in-types: [<problem-types>]
        discovery-trail: [{problem-id, problem-type, failure-summary}, ...]
```

## Cross-Phase: Compressed Summary Schema

Each phase outputs a `compressed-summary` field. This is what flows into the next phase's prompt context. Raw traces stay out.

```yaml
phase: 0 | 1 | 2 | 3 | 4 | 5
key-conclusions:
  - <single fact, claim, or counterexample>
proven-or-refuted:
  - id: <subclaim id or root>
    status: <one of 5 states>
failures-summary:
  - "method <name>: failed at <step> due to <reason>"
artifacts-saved:
  # only if runtime offers a scratchpad / log file
  - location: <path>
    contents: <type>
do-not-pass-downstream:
  - <list of items deliberately dropped: full code logs, dead-end traces, full rejected candidate text, etc.>
```

## Final Output to User

After Phase 4 (success path) or Phase 5 (handoff path), the final user-facing output should contain:

```yaml
original-statement: <as user provided>
output-mode: Proof | Refutation | Audit-Report | Handoff-Report | Exploratory-Report
final-status: PROVED | REFUTED | VERIFIED_NUMERICALLY | CONJECTURED | HANDED_OFF
proof-or-report: <full text, formatted for human reading; see output-formats.md for LaTeX/markdown specifics>
audit-summary: <if PROVED — Phase 4 verdict + remaining MAJOR/MINOR issues that did not block PROVED>
proved-self-check-checklist:               # MANDATORY when final-status == PROVED
  full-proof-text-exists: true
  every-step-justified: true
  no-shielding-language: true
  phase-4-audit-clean: true                # 0 FATAL + 0 CRITICAL
  asymmetric-vote-passed: true             # 4 HOLDS, 0 HOLE FOUND
  counterexample-cases-tried-at-least-4: true
  cited-claims-in-proved-memory: true
  provenance-annotations-present: true | not-applicable
  inline-uncertainty-markers-on-borderline-claims: true
caveats:
  - <e.g., "Numerical verification only on n ≤ 200">
  - <e.g., "Counterexample candidate at n = 41 not verified due to runtime limit; recommend external check">
```

## Optional LaTeX Source Output (Final Format)

For `output-mode: Proof`, the default final artifact is Markdown with provenance annotations. LaTeX source is optional unless the user requested it or the runtime can compile it. See `output-formats.md` for the full specification, but the schema-level summary for optional LaTeX is:

```yaml
latex-source:
  document-class: article | amsart
  preamble: <required packages; at minimum amsmath, amsthm, marginnote>
  body:
    - theorem-statement: <as parsed in Phase 0>
    - proof-text: <with inline \marginnote{} calls>
  provenance-annotations:
    - location: <line or step ref>
      content: <e.g., "P2-c1 (induction), score 7, P4 audit: 0 FATAL">
      provenance:
        phase: <0|1|2|3|4>
        candidate-or-subclaim-id: <ref>
        counterexample-attempted: true | false
  inline-uncertainty-markers:
    - location: <step ref>
      label: PROVED | VERIFIED_NUMERICALLY | CONJECTURED
      detail: <e.g., "VERIFIED_NUMERICALLY for n ≤ 100, not proved beyond">
```

## Schema Versioning

If schemas evolve in future revisions, every output should include:

```yaml
evomath-schema-version: <semver, e.g., "1.0.0">
```

This allows downstream consumers (other tools, the user, or future EvoMath revisions) to detect format mismatches.
