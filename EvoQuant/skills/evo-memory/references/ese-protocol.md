# ESE Protocol — Experiment Strategy Evolution

Step-by-step process for extracting reusable strategies from successful experiment pipelines and storing them in Experimentation Memory (M_E). ESE turns individual successes into accumulated wisdom for future cycles.

## When to Trigger

ESE runs after `experiment-pipeline` succeeds — all 4 stages complete and all gate conditions met. This means the full pipeline produced validated results, and the code trajectory logs contain a complete record of what worked.

## Step-by-Step Process

### Step 1: Run the Paper's ESE Prompt

The paper's ESE prompt (in [paper-prompts.md](paper-prompts.md)) is the primary extraction mechanism. Reason through it step by step before manual strategy extraction:

1. Read the ESE prompt from `paper-prompts.md`
2. Fill in the variables:
   - `{research_proposal}` ← the content of `/research-proposal.md`
   - `{trajectories}` ← concatenated trajectory logs from all 4 stages (see Step 2 below for file paths) plus the final working code from `/experiments/<project>/stage3_method/` (or `/experiments/<project>/stage4_ablation/` if ablation modified the implementation)
3. Reason through the filled prompt step by step
4. The output contains two sections:
   - **DATA SUMMARY** → maps to our "Data Processing Strategies" section in M_E
   - **MODEL SUMMARY** → maps to our "Model Training Strategies" section in M_E
5. Our Architecture and Debugging strategy sections (the last two subsections of Step 3 below) are populated by manual extraction AFTER the prompt run — the paper's ESE does not cover these categories

Use the prompt output as the foundation for Steps 3-6 below, supplementing with manual extraction for the extension categories.

### Step 2: Gather Trajectory Logs

Read all four stage trajectory logs:
- `/experiments/<project>/stage1_baseline/trajectory.md`
- `/experiments/<project>/stage2_tuning/trajectory.md`
- `/experiments/<project>/stage3_method/trajectory.md`
- `/experiments/<project>/stage4_ablation/trajectory.md`

Also read the cross-stage summary at `/experiments/<project>/trajectory-summary.md` if available.

### Step 3: Identify What Worked

Scan the logs for patterns that contributed to success. Focus on entries tagged `[Reusable]` first, then look for implicit patterns.

The paper's ESE prompt (see [paper-prompts.md](paper-prompts.md)) outputs exactly two sections: **DATA SUMMARY** (raw input → tensor pipeline) and **MODEL SUMMARY** (architecture + optimization loop). We extend with two additional practical categories. **Four categories to look for**:

#### Data Processing Strategies
- Which preprocessing steps were critical?
- Did data augmentation help? Which types?
- Were there data quality issues that required specific handling?
- Any data splitting or sampling strategies that mattered?

**Example extraction**: "In Stage 1, attempt 3 revealed that the baseline's reported preprocessing was incomplete — median filtering before normalization was critical for training stability with noisy sensor data."

→ **M_E entry**: "Median filter before normalization for noisy sensor data reduces training instability."

#### Model Training Strategies
- Which hyperparameter ranges worked?
- Which learning rate schedules were effective?
- Were there training tricks that made the difference? (warmup, gradient clipping, weight initialization)
- Which optimizer settings were important?

**Example extraction**: "In Stage 2, cosine annealing with warm restarts (T_0=10, T_mult=2) consistently outperformed linear decay and step decay across all 3 seeds."

→ **M_E entry**: "Cosine annealing with warm restarts (T_0=10, T_mult=2) for transformer fine-tuning on datasets with <50K samples."

#### Debugging Strategies
- Which diagnostic approaches resolved failures fastest?
- Were there failure patterns that were quickly identified using specific techniques?
- Any counterintuitive debugging insights?

**Example extraction**: "In Stage 3, attempt 5, the method appeared to fail — but the issue was evaluation, not training. Switching from batch-level to sample-level metric computation revealed the method was actually performing well."

→ **M_E entry**: "When method appears to underperform: verify evaluation granularity (batch vs sample) before concluding method failure."

#### Architecture Decisions
- Which design choices were key to performance?
- Did architecture modifications interact with training in important ways?
- Were there architecture anti-patterns that wasted attempts?

**Example extraction**: "In Stage 4, ablation showed that residual connections in the new module were essential — without them, gradients vanished after layer 12. Other components showed marginal impact."

→ **M_E entry**: "Residual connections are critical for any module inserted deeper than 10 layers in transformer architectures."

### Step 4: Assess Generality

For each identified pattern, classify its generality:

| Generality Level | Description | Example |
|-----------------|-------------|---------|
| **Broadly applicable** | Works across domains and architectures | "Learning rate warmup for 10% of total steps" |
| **Domain-specific** | Works for a class of problems | "For point cloud data, random rotation augmentation improves generalization" |
| **Highly specific** | Works for this exact setup | "ResNet-50 on CIFAR-10 needs LR=0.1" |

**Rule**: Store broadly applicable and domain-specific strategies. Highly specific strategies are only worth storing if the exact setup is likely to recur.

### Step 5: Check for Existing Entries

Read `/memory/experiment-memory.md` and check:

- **Exact match**: Same strategy already stored → update evidence with new cycle data and date
- **Contradicting entry**: New evidence contradicts existing strategy → add the new evidence as a note. Do NOT delete the old entry yet — wait for a third data point to resolve the contradiction
- **Related entry**: Similar strategy in a different context → add as a separate entry, cross-reference the related one
- **New strategy**: No existing entry → append to the appropriate section

### Step 6: Write M_E Entries

For each new or updated strategy:

```markdown
### [Strategy Name]

- **Category**: Data Processing | Model Training | Debugging | Architecture
- **Context**: [When to apply this strategy — domain, scale, conditions]
- **Strategy**: [What to do — specific, actionable guidance]
- **Evidence**: [Cycle N, Stage S, Attempt A — what happened]
- **Generality**: Broadly applicable | Domain-specific | Highly specific
- **Confidence**: Single observation | Confirmed (N cycles) | Contradicted
- **Related Entries**: [Cross-references to other M_E entries]
- **Date Added**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]
```

### Step 7: Write Evolution Report

Generate a report at `/memory/evolution-reports/cycle_N_ese.md`:
- How many strategies were extracted
- Which categories they fall into
- Which are broadly applicable (highest value)
- Any contradictions with existing M_E entries
- Expected impact on future `experiment-pipeline` cycles

## Extraction Quality Guidelines

### Write for the Future Reader

The reader of M_E is a future version of you (or a different researcher) starting a new experiment pipeline. They need:
1. **When to apply**: Clear context conditions (not just "this works" but "this works WHEN...")
2. **What to do**: Specific, actionable steps (not just "tune LR" but "try LR in [1e-4, 5e-4] with cosine schedule")
3. **Why it works**: Brief explanation of the principle (helps judge applicability)

### Avoid Overfitting to One Cycle

A strategy observed once is a hypothesis. A strategy confirmed across 2+ cycles is reliable. When writing entries from a single cycle:
- Mark as "single observation" in the evidence
- Don't state the strategy as a universal rule
- Update confidence when the same pattern appears in future cycles

### Capture Negative Results Too

"This approach did NOT work in this context" is valuable information. If a commonly recommended technique failed, record it:
- "Batch normalization in the custom module caused training instability for this architecture (contrary to standard practice). Layer normalization worked."
- This prevents future cycles from wasting attempts on the same failed approach.

## Example: Full ESE Extraction

**Successful pipeline**: Contrastive pruning for vision-language models, all 4 stages complete.

**Extracted strategies**:

1. **Data Processing**: "For vision-language datasets, align image-text pairs by semantic similarity score before training — random pairing causes contrastive loss to diverge."
   - Category: Data Processing
   - Generality: Domain-specific (multi-modal)
   - Evidence: Cycle 5, Stage 1, Attempt 4

2. **Model Training**: "Separate learning rates for vision and language encoders (10x lower for language) when fine-tuning pre-trained multi-modal models."
   - Category: Model Training
   - Generality: Domain-specific (multi-modal fine-tuning)
   - Evidence: Cycle 5, Stage 2, Attempts 3-5

3. **Debugging**: "When contrastive loss plateaus: visualize the embedding space — collapsed representations indicate the temperature parameter is too high."
   - Category: Debugging
   - Generality: Broadly applicable (any contrastive learning)
   - Evidence: Cycle 5, Stage 3, Attempt 7

4. **Architecture**: "Pruning ratios should be asymmetric across modality-specific layers — vision layers tolerate more pruning than language layers in VL models."
   - Category: Architecture
   - Generality: Domain-specific (multi-modal pruning)
   - Evidence: Cycle 5, Stage 4, Ablation results
