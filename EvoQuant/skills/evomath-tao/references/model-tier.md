# Model-Tier Configuration

EvoMath adapts its budget and rigor parameters to the underlying LLM's tier. This recognition comes from the math-olympiad skill: a small fast model (Haiku) needs more candidates to recover what a strong model (Opus / Sonnet 4.7) gets in fewer tries. Likewise, a strong model deserves more thorough audit passes.

Model tier is set in Phase 0 alongside problem type. The agent should detect or be told the active model and apply the tier's parameters.

## Tier Table

| Parameter | Haiku tier | Sonnet tier | Opus / Sonnet 4.7 tier |
|---|---|---|---|
| **Phase 2 candidates (K)** | 8 | 4 | 3 |
| **Internal-rounds per candidate** | 3 | 5 | 5 |
| **Max external revisions per candidate** | 2 | 2 | 2 |
| **Phase 4 verify passes** | 3 | 5 | 5 + named-pattern screen |
| **Asymmetric vote threshold** | 4 HOLDS / 2 HOLE | 4 HOLDS / 2 HOLE | 4 HOLDS / 2 HOLE |
| **Abstain after consecutive failed revisions** | 2 | 3 | 4 |
| **Presentation pass** (Phase 4 polish) | skip | yes | 2 drafts (clarity + elegance) |
| **Deep Mode tool budget** | 1 call | 2 calls | 2 calls |

## Defaults (when tier is unknown)

Treat the runtime as **Sonnet tier**:
- 4 candidates × 5 internal rounds each
- 5 verify passes in Phase 4
- 1 presentation pass
- Abstain after 3 failed revisions
- 2 Deep Mode tool calls

## Detection Heuristics

| Signal | Inferred tier |
|---|---|
| `claude-haiku-*` / `claude-3-haiku` in model id | Haiku |
| `claude-sonnet-3*` / `claude-sonnet-3.5*` | Sonnet |
| `claude-sonnet-4*` / `claude-sonnet-4.5+` / `claude-opus-*` | Opus / Sonnet 4.7 tier |
| `gemini-2.5-flash` / `gemini-3-flash` | Sonnet tier equivalent |
| `gemini-3-pro` / `gemini-3.1-pro` | Opus tier equivalent |
| `gpt-5-*` / `o1-*` | Opus tier equivalent |
| Unknown / no model id | Sonnet tier (default) |

## Why Differential Parameters

**Haiku tier (8 candidates, 3 rounds)**: small models miss insights but produce candidates cheaply. Compensate breadth with quantity. Skip elegance polishing because output is closer to "raw idea" anyway.

**Sonnet tier (4 candidates, 5 rounds)**: balanced — modest candidate count, more internal refinement per candidate, single polish pass.

**Opus / Sonnet 4.7 tier (3 candidates, 5 rounds + 2 drafts)**: strong models produce few but high-quality candidates. Spend the budget on rigor (named-pattern screen, two presentation drafts). Larger Deep Mode budget because their probe is more likely to find the truth.

## Trade-off

Lowering K below 3 is forbidden — even Opus deserves at least 3 different angles, else the vote degenerates. Raising K above 12 wastes budget — beyond 12 angles, marginal candidate adds noise.

## Auditing Implications

If a candidate at Phase 4 needed ≥ 4 internal rounds AND ≥ 1 external revision AND the model is Haiku tier, the candidate is in the "high-effort borderline" zone. Flag as `borderline-candidate: true` in the Phase 4 audit output; this gives Phase 6 reflection a chance to capture the technique as a provisional L2 strategy if it ultimately succeeds, or a fundamental dead-end if it fails.

## Empirical Anchors

Tier values are anchored to LemmaSearch (the original empirical system) and math-olympiad design notes:

- LemmaSearch ran K=4 with max_revisions=2 and achieved 35/40 on a self-built IMO dataset using Moonshot/vLLM-class models (Sonnet equivalent).
- math-olympiad documents:
  - Haiku: 8 solvers / 3 verify passes / abstain after 2 revise fails / no presentation
  - Sonnet: 4 / 5 / 3 / yes
  - Opus: 3 / 5 + patterns / 4 / 2 drafts

These two systems converged on similar values without coordination, suggesting the tier table reflects genuine empirical reality, not arbitrary parameter choice.
