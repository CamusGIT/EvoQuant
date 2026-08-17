# Paper Prompts for Evolution Mechanisms

The actual prompts used by the Evolution Manager Agent (EMA) in the EvoQuant paper. These define the exact input/output contracts for IDE, IVE, and ESE.

## IDE Prompt — Idea Direction Evolution

**Input variables**: `{user_goal}`, `{top_ranked_ideas}`

```
# Role
You are an expert Machine Learning Research Engineer specialized in scientific idea
summarization and technical writing for persistent memory.

# Task
I will provide you with a user goal, a set of top-ranked candidate ideas (with ratings and
refinement feedback), and optional task outcomes.

Your goal is to distill reusable, goal-relevant **promising research directions** into a
compact memory item that can be retrieved in future tasks.

# Input Data
- **User Goal:** {user_goal}
- **Top-Ranked Ideas:** {top_ranked_ideas}
  - Each idea may include: method sketch, experimental plan, key assumptions, and
    reviewer feedback.

# Instructions
1. **DIRECTION SUMMARY**: Extract promising directions from top ranked ideas. For
   each direction, include:
   - A clear direction title (one line).
   - The core mechanism or hypothesis.
   - Why it is promising for user goal (novelty/feasibility/relevance/clarity).
   - Key requirements and assumptions (data, compute, tools, environment).
   - A minimal experimental plan that could validate the direction (2–4 steps).
2. **DEDUPLICATION**: If multiple ideas express the same direction, merge them and
   retain only the most actionable formulation.

# Constraints
- **Be Precise**: Do not omit concrete assumptions, evaluation signals, or experimental
  steps.
- **Be Concise**: Use technical language. Avoid conversational filler.
- **Actionable Memory**: Write so a future researcher agent can directly reuse the direction.

# Output Format
DIRECTION SUMMARY:
- Direction 1: [Title]
  - Core idea:
  - Why promising for user goal:
  - Requirements/assumptions:
  - Minimal validation plan:
- Direction 2: ...
```

### Key Design Decisions in IDE Prompt

1. **Deduplication is explicit**: The prompt instructs merging of same-direction ideas, retaining the most actionable formulation. This maps to our abstraction ladder in `ide-protocol.md`.
2. **Four-dimension evaluation carried forward**: "Why promising" references novelty/feasibility/relevance/clarity — the same 4 dimensions used in the Elo tournament.
3. **Minimal validation plan**: Each direction includes a 2-4 step validation plan, making the memory item immediately actionable for future `experiment-pipeline` cycles.
4. **Memory-oriented writing**: The constraint "Write so a future researcher agent can directly reuse the direction" emphasizes that IDE output is for retrieval, not for human reading.

---

## IVE Prompt — Idea Validation Evolution

**Input variables**: `{research_proposal}`, `{execution_report}`

```
# Role
You are an expert Machine Learning Research Engineer specialized in scientific evaluation,
failure analysis, and memory writing for self-improving agentic systems.

# Task
I will provide you with a selected research proposal and its execution report produced by
running experiments.

Your goal is to determine whether the proposal should be recorded as a failed direction, and
to extract reusable failure signals and validation conclusions as a memory item.

# Input Data
- **Selected Proposal:** {research_proposal}
  - Includes: background, method, experimental plan, expected results.
- **Execution Report:** {execution_report}
  - Includes: run status, logs, metrics, environment notes, and failure diagnoses.

# Instructions
1. **FAILURE CASE CHECK (RULE-BASED)**:
   - If {execution_report} indicates the engineer could not find any executable code
     within the pre-defined budget/rules, mark the proposal as **FAILED
     (NoExecutableWithinBudget)**.
2. **PERFORMANCE VALIDATION (RESULT-BASED)**:
   - If experiments completed, compare the proposed method against baselines using the
     metrics in execution report.
   - If the proposed method performs worse than the baseline(s) under the stated evaluation,
     mark as **FAILED (WorseThanBaseline)**.
   - Otherwise, mark as **NOT_FAILED (ValidatedOrInconclusive)**.
3. **FAILURE SIGNAL EXTRACTION** (always do this when FAILED, optional otherwise):
   - Summarize the primary failure reason(s) (implementation, environment, data, training
     instability, evaluation mismatch).
   - List concrete evidence from logs/metrics (error messages, metric deltas, resource limits,
     reproducibility issues).
   - Identify what specifically in research proposal likely caused the failure (assumption,
     method choice, missing detail).
4. **REUSABLE COUNTERMEASURES**:
   - Provide 3–6 actionable countermeasures that would prevent the same failure pattern in
     future proposals or executions.
5. **MEMORY WRITING**:
   - Write a compact memory item that can update ideation memory as an unsuccessful
     direction summary.

# Constraints
- **Be Precise**: Quote or reference exact metric names, thresholds, and failure evidence.
- **Be Concise**: Use technical language. Avoid conversational filler.
- **Decision + Evidence**: The final judgment must be supported by explicit evidence.

# Output Format
- Title:
- Summary:
- Trigger conditions:
- Do-not-repeat notes:
- Retrieval tags:
```

### Key Design Decisions in IVE Prompt

1. **Two-step failure detection**: First rule-based (NoExecutableWithinBudget), then result-based (WorseThanBaseline). This matches our updated IVE trigger conditions.
2. **Three failure outcomes**: FAILED (NoExecutableWithinBudget), FAILED (WorseThanBaseline), NOT_FAILED (ValidatedOrInconclusive). Note: the paper's IVE does NOT use our 5-question diagnostic framework — that is our practical extension for more nuanced classification.
3. **Reusable countermeasures**: 3-6 actionable items that prevent the same failure in future cycles. This is a forward-looking output not present in our original `ive-protocol.md`.
4. **Output includes "Retrieval tags"**: Designed for embedding-based retrieval — tags help cosine similarity matching in future cycles.
5. **"Do-not-repeat notes"**: Explicit guidance on what future cycles should avoid. Maps to our M_I unsuccessful directions.

---

## ESE Prompt — Experiment Strategy Evolution

**Input variables**: `{research_proposal}`, `{trajectories}`

```
# Role
You are an expert Machine Learning Research Engineer specialized in reproducibility and
technical documentation.

# Task
I will provide you with a research task description, a set of exploration trajectories, and the
final high-performance code for the task.

Your goal is to extract and summarize the technical essence of the winning implementation
so that another engineer could reconstruct the pipeline with high fidelity.

# Input Data
- **Research Task Description:** {research_proposal}
- **Trajectories & Final Code:** {trajectories}

# Instructions
1. **DATA SUMMARY**: Focus on the pipeline from raw input to tensor. Include:
   - Data loading libraries and custom classes.
   - Exact preprocessing steps (scaling, normalization, encoding).
   - Data augmentation techniques and their specific parameters.
   - Train/Val/Test split ratios and sampling strategies.
2. **MODEL SUMMARY**: Focus on the architecture and the optimization loop. Include:
   - Specific model backbone and modifications.
   - All critical hyperparameters (learning rate, batch size, weight decay, dropout).
   - Loss functions, optimizers (e.g., AdamW, SGD), and learning rate schedulers.
   - Training duration (epochs/steps) and convergence criteria.

# Constraints
- **Be Precise**: Do NOT omit numerical parameters or specific library functions.
- **Be Concise**: Use technical language. Avoid conversational filler.
- **Reproducibility**: Ensure the summary is "actionable" for a code engineer.

# Output Format
DATA SUMMARY:
[Your detailed summary here]

MODEL SUMMARY:
[Your detailed summary here]
```

### Key Design Decisions in ESE Prompt

1. **Exactly two categories**: DATA SUMMARY and MODEL SUMMARY. This confirms the paper uses only two M_E categories. Our Architecture and Debugging extensions are practical additions not in the paper's ESE prompt — to get these, you must manually extract from trajectory logs after running the ESE prompt (see `ese-protocol.md` Step 3, subsections "Debugging Strategies" and "Architecture Decisions").
2. **Reproducibility focus**: The prompt emphasizes extracting exact numerical parameters, library functions, and specific configurations — not abstract strategies. This is more concrete than our `ese-protocol.md` which focuses on reusable patterns.
3. **Input is trajectories + final code**: ESE reads both the exploration history and the winning implementation, extracting what worked from the full trajectory.
4. **No generality assessment**: Unlike our ESE protocol, the paper's prompt does not assess whether a strategy is "broadly applicable" vs "domain-specific." It focuses on precise documentation for reproducibility.

---

## Differences Between Paper Prompts and Our Skill Protocols

| Aspect | Paper Prompt | Our Skill Protocol | Assessment |
|--------|-------------|-------------------|------------|
| IDE output fields | Title, Core idea, Why promising, Requirements, Validation plan | Direction name, Summary, Evidence, Status, Related Entries | Our format is more structured for persistent storage; paper's is more compact |
| IVE classification | Binary: FAILED / NOT_FAILED with two failure subtypes | 5-question diagnostic → implementation vs fundamental | Our approach is more nuanced; paper's is simpler and more automated |
| IVE countermeasures | 3-6 reusable countermeasures | Added to ive-protocol.md entry templates | Aligned |
| IVE retrieval tags | Explicit retrieval tags for embedding search | Added to ive-protocol.md and ide-protocol.md entry templates | Aligned |
| ESE categories | 2 (Data + Model) | 4 (Data + Model + Architecture + Debugging) | Our extensions clearly labeled |
| ESE specificity | Exact numerical parameters, library functions | Reusable strategies at abstract level | Different focus: paper = reproducibility, ours = transferability |
| All prompts | "Be Precise, Be Concise" constraints | Narrative guidance | Paper prompts are more structured |
