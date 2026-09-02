---
name: research-ideation
description: "Quant-focused research ideation pipeline: scope selection (3 stages) → anchor-first literature grounding → single-core idea generation → iterative refinement → ELO tournament ranking (Final = N+R+C−D) → update evo-memory → user selects direction → expand into manuscript-quality proposal. Optimized for incremental, anchor-first contributions. Use when: user wants to find a quant research direction, brainstorm ideas within a scope stage, evaluate idea novelty, design a novel solution anchored to an existing paper, rank/compare research ideas, or generate a research proposal. Do NOT use for finding/searching/reading papers (use local-paper-navigator), literature survey reports (use research-survey), or planning a paper (use paper-planning)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: quant-research-team
  version: '3.0.0'
  tags: [core, research, ideation, tournament, proposal, quant, anchor-first, incremental]
---

# Research Ideation

From research goal to ranked ideas and a detailed proposal.

```
Step 0: Load evo-memory (M_I)
    ↓
Step 1: Define Scope & Goal
    ↓
Step 2: Literature Grounding (MUST use local-paper-navigator scripts)
    ↓
Step 3: Generate Ideas (3 Anchor Papers × Innovator persona)
    ↓
Step 4: Refine Ideas (3 tracks × N iterations)
    ↓
Step 5: ELO Tournament → Present Top-3 to User
    ↓
Step 6: Update evo-memory (IDE)
    ↓
User Selects
    ↓
Step 7: Expand into Proposal
    ↓
Step 8: Validate and Iterate
```

## When to Use

- User wants to find a research direction or brainstorm research ideas within a specific quant scope stage
- User wants to evaluate whether an idea is novel or worth pursuing
- User wants to rank or compare multiple research ideas
- User wants to generate a research proposal from an idea anchored to an existing paper

**Note**: This pipeline is optimized for quantitative research where incremental, anchor-first contributions are preferred over architectural redesigns.

## When NOT to Use

- **Finding/reading papers** → use `local-paper-navigator`
- **Literature survey report** → use `research-survey`
- **Planning a paper (story design, experiment plan)** → use `paper-planning`

---

## Step 0: Load Prior Knowledge from evo-memory

**Before any ideation begins**, load Ideation Memory (M_I) from prior research cycles:

1. Read M_I at `/memory/ideation-memory.md` (refer to `evo-memory` skill)
2. Select the **top-2 entries** (k_I=2) most relevant to the user's current goal by comparing each entry's Summary and Retrieval Tags against the goal
3. **Feasible directions** from prior cycles → use as seeds in Step 3 (incorporate as candidate anchor directions alongside new ones, within the same scope stage)
4. **Unsuccessful directions** marked as fundamental failures → use during idea pruning in Step 4 (prune any idea that matches a fundamental failure pattern)
5. If M_I doesn't exist yet (first cycle), skip this step

This step prevents repeating known dead ends and builds on prior successes across research cycles.

## Step 1: Define Research Scope & Goal

### Research Scope

The long-term objective of this continual research program is to incrementally improve the quantitative research pipeline through publishable contributions in one of three core stages:

| Stage | Focus |
|-------|-------|
| **Alpha Factor Research** | Discover and validate economically meaningful alpha factors grounded in financial theory and empirical evidence |
| **Alpha Generation Methodology** | Develop more effective methods for discovering, generating, and evolving alpha factors automatically |
| **Portfolio Strategy Research** | Develop methods that transform one or multiple alpha signals into robust, diversified, and executable investment portfolios under realistic trading constraints. |

Each research session **MUST** focus on exactly one of the three stages above.

**Hard constraints:**
- The objective is not to redesign the entire pipeline, but to produce the **smallest publishable improvement** within a single stage.
- The proposed contribution should introduce **one primary innovation**, treating the remaining components as fixed background.
- Improvements should be **incremental rather than architectural**.

### Research Goal

Within the chosen scope stage, define a concrete goal. Ask: "What is the smallest improvement that would be publishable in this stage?"

The goal should be narrow enough to complete in one research cycle, yet significant enough to advance the field.

## Step 2: Literature Grounding (via local-paper-navigator)

**Invoke `local-paper-navigator`** to collect relevant papers from the local papers library. Do NOT skip this step or substitute with general knowledge — ideas must be grounded in real papers.

**CRITICAL: All paper discovery in this step MUST use the `local-paper-navigator` skill and its scripts (local_search, xref_search, similar_papers, snippet_search, etc.). Using WebSearch, WebFetch, or any generic web search tool for finding papers is PROHIBITED.** Generic web search returns blog posts, news articles, and low-quality results — only local-paper-navigator provides the local search, cross-reference, and keyword-similarity infrastructure needed for literature grounding.

### Build Challenge-Insight Tree

From the collected papers, construct a **challenge-insight tree** — a many-to-many mapping between technical challenges and the insights/techniques that address them:

- **Extract challenges**: From each paper, what technical problem does it solve?
- **Extract insights**: What technique or key idea does it use?
- **Map connections**: Which insights address which challenges?

**How this drives ideation**:
- Challenges with few insights → **unsolved problem** (candidate for Step 3)
- Insights not yet applied to a challenge → **cross-domain transfer opportunity** (candidate for Step 4)
- Challenges with many insights → well-studied, avoid unless you have a fundamentally new angle

Also generate a condensed **literature review synthesis** as context for idea generation (for full surveys use `research-survey`).

See `references/literature-tree.md` for construction methodology.

**Execution rule**: Do NOT generate ideas without real paper grounding. The tree must reference actual papers with titles, sources, and findings. Paper search MUST go through `local-paper-navigator` — never use WebSearch/WebFetch as a shortcut.

## Step 3: Generate Ideas

Generate 3 initial research ideas, each anchored to a specific paper from the literature grounding (Step 2), grounded in the literature.

### Three Personas

| Persona | Focus |
|---------|-------|
| **Innovator** | Novelty & creativity — groundbreaking, high-risk/high-reward |
| **Pragmatist** | Difficulty-aware — realistic scope, minimal resource requirements |
| **Critic** | Scientific value — advances understanding, rigorous |

### Anchor-First Principle

Every proposal **MUST** be anchored to one **Anchor Paper** — a specific paper from the literature grounding (Step 2) that serves as the primary methodological foundation.

- **≥70% of the proposed method** must be inherited from the Anchor Paper.
- The remaining ≤30% constitutes the innovation contribution.
- Prioritize **extending an existing framework**, not redesigning the entire system.
- The Anchor Paper's method is the baseline; the proposal's innovation is the delta above that baseline.

When generating ideas in Step 3, each idea must explicitly state:
- **Anchor Paper**: [title + paperId]
- **Inherited components**: [what is kept from the anchor, ≥70%]
- **Innovation delta**: [what is changed/added, ≤30%]

### Single-Core Innovation

Each proposal may introduce **at most 1 core innovation point** (maximum 2 if tightly related — sharing the same mechanism or directly causally linked).

Innovation should come from **refinement of existing methods** — improvement, replacement, or extension — not from horizontal concatenation of unrelated methods or modules.

**Disallowed**: Combining technique A from paper X + technique B from paper Y where A and B address different problems and are not causally linked.

**Allowed**: Replacing paper X's optimization method with a more effective variant; extending paper X's factor mining pipeline with one additional module; adding one constraint to paper X's portfolio construction.

### Process

1. Analyze literature + challenge-insight tree → select **3 candidate Anchor Papers** (one per direction)
2. Generate one idea per Anchor Paper using **Innovator** persona
3. Each idea must follow **Path 1 (Focused Contribution)**: single new component; clean hypothesis
   - Path 2 (System Contribution) is **PROHIBITED** under the single-core innovation constraint
4. Each idea must specify Anchor Paper, inherited components (≥70%), and innovation delta (≤30%)

### Idea Format

```
# Research Idea: [Concise Title]

## Anchor Paper
- **Anchor Paper**: [title + paperId]
- **Inherited components**: [what is kept from the anchor, ≥70%]
- **Innovation delta**: [what is changed/added, ≤30%]

## Core Idea
[One paragraph: the proposal + which research direction it addresses + how the innovation delta extends the anchor]

## Validation Plan
[Concrete experiment outline. Datasets must be chosen from what is actually
available — run `quant-experiment-runtime`'s `discover_data.py --code-repo code-repo`
to list offline data packages, and use `local-paper-navigator` to recover the
paper's tested scope; plan around the intersection, scoped by the paper's test
range + budget + necessity (not the dataset's maximum coverage). Then: baselines,
metrics. See `references/proposal-extension.md` Section 4.]

## Baseline Feasibility
- **Anchor Paper source code**: [available at URL / ❌ no usable code]
- **Implementation mode (preliminary — for difficulty scoring)**: [Adapt / From-Scratch / Hybrid]
- **Difficulty correction**: [base score + adjustment = corrected score, e.g., 3+4=7 if From-Scratch]
```

## Step 4: Refine Ideas

Run 3 parallel refinement tracks — one per initial idea. Each track uses all 3 personas.

```
For each track:
  For N=3 iterations:
    1. Evaluate current best idea (novelty, difficulty, relevance, clarity, anchor-coherence)
    2. All 3 personas generate refined versions based on evaluation
    3. Pick the best refinement as seed for next iteration
  Track champion = best idea across iterations
```

### 5 Evolution Strategies

1. **Enhancement through Grounding**: Strengthen with literature citations
2. **Improving Coherence**: Fix logical flaws in the mechanism
3. **Inspiration and Combination**: Combine with a different concept from literature
4. **Simplification**: Strip down to a clean, testable hypothesis
5. **Literature-Driven Pivot**: Abandon the mechanism; propose a new approach from literature

**Critical rule**: If evaluation says the approach is a dead-end, the persona MUST pivot — refinement is not restricted to patching.

### Refinement Constraints

- Each refinement iteration **MUST** preserve the Anchor Paper as the methodological foundation. Pivoting to a different anchor paper is allowed, but adding new unrelated components is **PROHIBITED**.
- If refinement adds a second innovation point, it must be **tightly related** to the first (same mechanism or direct causal link).
- The 5 Evolution Strategies must operate within the anchor-first frame:
  - **Enhancement through Grounding** → strengthen the innovation delta with additional evidence
  - **Improving Coherence** → fix logical flaws within the inherited + innovation structure
  - **Inspiration and Combination** → combine with a concept **from the Anchor Paper's domain**, not an unrelated domain
  - **Simplification** → strip the innovation delta to its essential mechanism
  - **Literature-Driven Pivot** → replace the innovation delta with a better approach from literature, keeping the anchor foundation

### Logical Cohesion Principles

- **Too many variables** → Focus via Subtraction: isolate the most promising variable
- **Disconnected components** → Justify via Strong Correlation: build explicit causal links

## Step 5: ELO Tournament → Present Top-3

Rank all track champions through pairwise comparison, then **present the top-3 to the user for selection**.

### Four Dimensions

| Dimension | What It Measures |
|-----------|-----------------|
| **Novelty** | How different from existing published work? (scored 1-10; higher = more novel) |
| **Difficulty** | Total implementation effort (1-10; higher=harder). **Includes baseline reproduction cost** — if any baseline requires from-scratch reproduction (no source code), add +3-5. Difficulty measures TOTAL effort, not just the innovation delta. See `references/baseline-feasibility.md` |
| **Relevance** | Does this address an important problem aligned with the goal? (scored 1-10; higher = more relevant) |
| **Clarity** | Is the idea well-defined enough to start immediately? (scored 1-10; higher = clearer) |

### Final Score Formula

**Final = Novelty + Relevance + Clarity − Difficulty**

- Novelty, Relevance, Clarity are **additive** (higher is better).
- Difficulty is **subtractive** (higher difficulty reduces the final score).
- Same final score → **lower Difficulty wins** (difficulty serves as tiebreaker).

### Tournament

- **Starting Elo**: 1500 | **K-factor**: 32
- Compare ideas pairwise → update Elo → sort by final score
- See `references/elo-ranking-guide.md` for rubric and formula

### Present Top-3 to User

After the tournament, present the top-3 ideas with **both** a comparison table and the **full refined idea** for each. This ensures the user sees the concrete, actionable version of each idea — not just a summary.

#### Part 1: Comparison Table

```
## Top-3 Research Ideas (ranked by ELO)

| Rank | Title | Anchor Paper | Innovation Delta | Novelty | Difficulty | Relevance | Clarity | Final | ELO |
|------|-------|-------------|-----------------|---------|------------|-----------|---------|-------|-----|
| 1 | ... | ... | ... | 9 | 3 | 8 | 8 | 22 | 1280 |
| 2 | ... | ... | ... | 7 | 4 | 8 | 7 | 18 | 1240 |
| 3 | ... | ... | ... | 8 | 5 | 9 | 7 | 19 | 1210 |
```

#### Part 2: Full Refined Ideas

For **each** of the top-3, present the refined idea using the same structured format as Step 3, plus a refinement summary:

```
# Refined Idea [Rank]: [Concise Title]

## Anchor Coherence
- Anchor Paper: [title]
- Inherited: [≥70% method description]
- Innovation: [≤30% delta description]
- Coherence check: [Is the innovation tightly integrated with the inherited method?]

## Core Idea
[One paragraph: the refined proposal — this should reflect ALL changes from Step 4 refinement,
not the original Step 3 version]

## Validation Plan
[Concrete experiment outline updated with refinement insights: datasets, baselines, metrics,
key ablations identified during refinement]

## Refinement Summary
[Brief paragraph summarizing what changed from the initial idea and why:
- What was simplified or removed (and why)
- What was added or concretized (and why)
- Which persona drove the most impactful change
- Key risk mitigations added during refinement]
```

**This section is mandatory** — do NOT skip the full refined ideas or collapse them into the comparison table. The user needs to see the complete, refined version to make an informed selection.

#### Part 3: Selection Prompt

```
Which idea would you like to develop into a full proposal? (1/2/3, or combine elements)
```

**After presenting top-3, trigger Step 6 (evo-memory IDE) before finalizing user selection.** The user may:
- Pick one of the top-3
- Ask to combine elements from multiple ideas
- Request modifications before expanding
- Ask to regenerate with different constraints

## Step 6: Update evo-memory

After the tournament and before the user selects, trigger `evo-memory` IDE (Idea Direction Evolution):

1. Save the top-3 directions to `/direction-summary.md`
2. Trigger IDE protocol via `evo-memory` skill with the direction summary
3. Each top direction is added to M_I as a feasible direction with its ELO score
4. Any ideas that were clearly unworkable during refinement (Step 4) are recorded as unsuccessful directions with failure classification (fundamental vs implementation)

This ensures future ideation cycles benefit from what was learned in this cycle.

## Step 7: Expand into Proposal

After the user selects an idea, expand it into a manuscript-quality research proposal. **This is a two-phase process** because different fields require different proposal structures.

### Phase 1: Generate a Domain-Specific Template

Before writing, first generate a proposal template tailored to the user's field:

1. Identify the field from the research goal and literature
2. Start with universal sections (Abstract, Problem, Related Work, Method, Evaluation, Conclusion)
3. Add field-specific sections (e.g., Ethics/IRB for medical research, Safety analysis for chemistry, Statistical power analysis for clinical trials, Ablation design for ML)
4. Adapt terminology to the field's conventions (e.g., "Study Design" in medicine, "Methodology" in social sciences, "Proposed Method" in engineering)

See `assets/proposal-template.md` for the complete field-specific section guide and writing instructions.

### Phase 2: Write the Proposal

Fill the generated template following these universal principles:
- Write for a top-tier reviewer in the field — every claim supported, every design justified
- Avoid variable confusion: clearly isolate the core contribution
- Match the field's rigor standards (math for quantitative fields, protocols for experimental fields, coding schemes for qualitative fields)
- Anticipate skeptical reviewer questions proactively

See `references/proposal-extension.md` for detailed section guidance.

## Step 8: Validate and Iterate

Run experiments on representative data. If the approach fails, return to Step 3 or Step 4 with updated knowledge. See `experiment-craft` for systematic debugging.

---

## Counterintuitive Rules

1. **Problem selection > solution design**: Choosing WHAT to solve matters more than HOW
2. **Pursue new failure cases, not incremental improvements**: Find settings where existing methods break
3. **If a well-established solution exists, switch problems**: Improvement space is too small
4. **Technology is creative combination, not concatenation**: Simple A→B pipelines are not contributions
5. **Quantity before quality in generation**: Generate many candidates before evaluating any
6. **Difficulty is subtractive**: A brilliant but difficult idea scores lower than a solid but easy one — research cycles are finite
7. **Anchor-first, not free-form**: Extending an existing framework is always preferred over designing a new one from scratch
8. **One innovation, not three**: The smallest publishable improvement beats the most ambitious redesign
9. **The tournament finds surprises**: Trust rankings over gut feeling

---

## Dependency: local-paper-navigator

All paper discovery goes through `local-paper-navigator`. This skill does not search for papers itself. **Using WebSearch, WebFetch, or any generic search tool to find papers is PROHIBITED** — these tools cannot access the local papers library. Always use `local-paper-navigator` and its scripts (local_search, xref_search, similar_papers, snippet_search, etc.) for all paper discovery needs in Steps 2, 3, and 4.

| Step | Requires local-paper-navigator for |
|------|------------------------------|
| Step 2 | Collect 30-50 relevant papers for literature tree construction |
| Step 3 | Verify no well-established solution exists for selected problems |
| Step 4 | Cross-domain search for transferable techniques during refinement |

## evo-memory Integration

| When | Action | Details |
|------|--------|---------|
| **Step 0** (before ideation) | **Read M_I** | Load `/memory/ideation-memory.md`, select top-2 relevant entries, use feasible directions as seeds, avoid fundamental failures |
| **Step 6** (after tournament) | **Write M_I via IDE** | Save top-3 directions with ELO scores as feasible; save dead-end ideas as unsuccessful with failure classification |

## Handoff

| To | When | Key Artifacts |
|----|------|---------------|
| `paper-planning` | Proposal complete (Step 7) → plan paper structure | `/research-proposal.md`, `/direction-summary.md` |
| `experiment-pipeline` | Proposal complete (Step 7) → start experiments | `/research-proposal.md`, `/direction-summary.md` |
| `evo-memory` | After tournament (Step 6) → update Ideation Memory via IDE protocol | `/direction-summary.md` |

---

## References & Assets

| Topic | File |
|-------|------|
| Literature tree construction | `references/literature-tree.md` |
| Problem selection framework | `references/problem-selection.md` |
| Solution design methodology | `references/solution-design.md` |
| Tree expansion rules | `references/tree-search-protocol.md` |
| ELO formula & rubric | `references/elo-ranking-guide.md` |
| Proposal section guidance | `references/proposal-extension.md` |
| Baseline feasibility assessment | `references/baseline-feasibility.md` |
| Idea candidate template | `assets/idea-candidate-template.md` |
| Ranking scorecard | `assets/ranking-scorecard-template.md` |
| Direction summary | `assets/direction-summary-template.md` |
| Proposal example (E-FNO) | `assets/proposal-template.md` |
