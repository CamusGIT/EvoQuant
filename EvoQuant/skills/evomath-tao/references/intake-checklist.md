# Phase 0 — Intake Checklist

## Instruction Header (use verbatim)

> "Do not attempt proof, refutation, or solution strategy. Only parse the statement, identify variable domains, assumptions, ambiguities that may change the truth value, degenerate configurations not explicitly included or excluded, division-by-zero, sign conditions, and edge cases at boundaries. Output the Intake Card. Do not start solving."

This header forbids solving but **requires** mathematical semantic checking. You are a parser with full mathematical literacy, not a typist with no intuition.

## Intake Card Schema

```yaml
statement: <the claim, normalized>
type: <one of the 10 types — see Type Classification below>
variable-domain:
  - <variable_name>: <real | integer | positive-integer | rational | complex | function-space | matrix | ...>
assumptions:
  - <each explicit hypothesis from the problem statement>
goal: prove | refute | find-example | audit-existing-proof | theory-building | literature-synthesis
ambiguity-classification:
  blocking-ambiguity:
    - <questions that may change the truth value of the claim>
  assumed-defaults:
    - <questions where a reasonable default exists and execution can continue>
degenerate-cases-policy: included | excluded | unclear
edge-cases-flagged:
  - <division-by-zero risks, infinite-domain edges, boundary behavior, …>
needs-user-input: <true if blocking-ambiguity is non-empty, else false>
declared-defaults:
  - <if continuing on assumed-defaults, list each declaration explicitly>
```

## Branching Rules

| Condition | Action |
|---|---|
| `blocking-ambiguity` non-empty | **STOP**. Present each blocking question to the user. Do not advance to Phase 1. |
| Only `assumed-defaults` non-empty | List each declared default in `declared-defaults`, then continue to Phase 1. |
| Both empty | Continue directly to Phase 1. |
| Parsed structure differs meaningfully from naïve reading | OPTIONAL: present the reformulated statement for user approval before advancing. Recommended when reformulation changes the theorem's scope, quantifier order, or domain. |

## Iterative Refinement

Phase 0 is not strictly one-shot. After the user replies to blocking questions:
1. Re-parse with the new information.
2. Update the Intake Card in place.
3. Check `needs-user-input` again — only continue when it is `false`.
4. If multiple rounds occur, record each user response in a `clarification-history` field for downstream auditability.

This mirrors the "iterative intent refinement" pattern: the perfect prompt is co-created, not front-loaded.

## Goal Type Definitions

| Goal | Meaning | Output mode |
|---|---|---|
| `prove` | Establish the claim with a rigorous proof | Proof (Markdown by default; optional LaTeX source) |
| `refute` | Find a verified counterexample | Refutation |
| `find-example` | Construct a specific witness | Witness + verification |
| `audit-existing-proof` | Review a user-submitted proof for gaps | Audit Report |
| `theory-building` | Develop a framework, conjecture, or definition; no single theorem expected | **Exploratory Report** |
| `literature-synthesis` | Survey existing results, identify connections | **Exploratory Report** |

For `theory-building` and `literature-synthesis`, the pipeline still runs all six phases, but Phase 4 does not require PROVED. The final output is an Exploratory Report (see `output-formats.md`) where most claims may be CONJECTURED with inline uncertainty markers. This is a legitimate research output, not a failure.

## blocking-ambiguity (must ask)

These genuinely change truth value or theorem identity:
- Variable domain unclear and changes truth (e.g., "for all x" — but is x integer, real, or complex?)
- Existence vs uniqueness ambiguous ("show f satisfies P" — find one, or characterize all?)
- Degenerate construction not specified, would yield different theorems
- Two reasonable interpretations of a term, yielding different conclusions
- Hypothesis missing entirely (e.g., "prove f is bounded" with no f given)

## assumed-defaults (declare and continue)

These can be declared without user interaction:
- Standard implicit assumptions (real-valued unless stated; n ≥ 1 for integer indices)
- Conventional notation (log base e in analysis, natural numbers from 1 unless specified)
- Standard regularity assumptions in research-level contexts (continuity, measurability for integrals)
- Type defaults from the field (in number theory, "prime" means rational prime unless stated)

In all cases the declared default MUST appear in `declared-defaults` so downstream phases see it explicitly. Do not silently assume.

## Type Classification (10 types)

### Competition (4)
- **algebra** — polynomials, inequalities, functional equations, sequences, recursions
- **geometry** — Euclidean, projective, vector / coordinate, transformations
- **number-theory** — divisibility, primes, Diophantine equations, modular arithmetic
- **combinatorics** — counting, existence, extremal, structural

### Research (4)
- **analysis** — limits, integrals, measure theory, function spaces, PDEs
- **probability** — random variables, expectations, concentration, stochastic processes
- **optimization** — convex / non-convex, KKT, duality, gradient methods
- **linear-algebra** — eigenvalues, matrix decompositions, operator theory

### Applied (2)
- **graph-theory** — connectivity, coloring, flow, spectral graph theory
- **ML-theory** — generalization bounds, convergence rates, complexity, expressivity

### Multi-type Problems

If the problem genuinely spans types (e.g., probabilistic combinatorics, spectral graph theory):
- Pick the **dominant** type for prompt selection
- Note the secondary type(s) in `assumptions` so Phase 2 can pull angles from both libraries

## Anti-Patterns (Phase 0)

- ❌ Drafting a proof outline ("I'd start with induction on n…")
- ❌ Speculating about which technique will work
- ❌ Adding hypotheses the problem didn't state ("I'll assume continuity")
- ❌ Solving small cases (Phase 1's job)
- ❌ Writing prose paragraphs instead of filling the Card

If you find yourself reasoning toward an answer in Phase 0, stop and refocus on filling the Card structure. The card is for a downstream solver, not a hint to yourself.

## Examples

### Example A — Clean intake (no blocking)

**User**: "Prove that for all positive integers n, n³ - n is divisible by 6."

**Card**:
```yaml
statement: For all positive integers n, n³ - n is divisible by 6
type: number-theory
variable-domain:
  - n: positive-integer
assumptions: []
goal: prove
ambiguity-classification:
  blocking-ambiguity: []
  assumed-defaults: []
degenerate-cases-policy: included  # n = 1 gives 0, divisible by 6 vacuously
edge-cases-flagged: []
needs-user-input: false
declared-defaults: []
```

### Example B — Assumed-default (declare and continue)

**User**: "Prove that the sequence a_n = 1/n converges."

**Card**:
```yaml
statement: The sequence a_n = 1/n converges (to 0 in the standard topology of ℝ)
type: analysis
variable-domain:
  - n: positive-integer
  - a_n: real
assumptions: []
goal: prove
ambiguity-classification:
  blocking-ambiguity: []
  assumed-defaults:
    - "Topology / metric on ℝ assumed standard (Euclidean absolute value)"
    - "Convergence assumed to mean limit exists in ℝ (not extended-real)"
degenerate-cases-policy: included
edge-cases-flagged: []
needs-user-input: false
declared-defaults:
  - "Standard Euclidean topology on ℝ"
  - "Convergence in ℝ, not ℝ̄"
```

### Example C — Blocking (must ask)

**User**: "Prove that f(x) is bounded."

**Card**:
```yaml
statement: f(x) is bounded
type: <unclear — depends on what f is>
variable-domain:
  - x: <unclear>
  - f: <unclear>
assumptions: []
goal: prove
ambiguity-classification:
  blocking-ambiguity:
    - "What is f? No definition was given."
    - "What is the domain of x? Real, integer, complex, function space?"
    - "Bounded above, below, or both?"
  assumed-defaults: []
degenerate-cases-policy: unclear
edge-cases-flagged: []
needs-user-input: true
declared-defaults: []
```

→ **Action**: STOP. Present the three blocking questions. Do not advance to Phase 1.
