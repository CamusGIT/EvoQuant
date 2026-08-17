# Code Trajectory Logging

A structured format for recording every attempt across all pipeline stages. Code trajectory logs serve two purposes: they help you track progress within a single pipeline run, and they feed into `evo-memory`'s Experiment Strategy Evolution (ESE) mechanism for cross-cycle learning.

## Logging Format

Each attempt produces one log entry with five fields:

### Entry Structure

```markdown
## Attempt [N] — Stage [S]: [Stage Name]

**Hypothesis**: [What you expect to happen and why]
**Code Changes**: [Summary of what was modified — key changes, not a full diff]
**Configuration**: [Any changed hyperparameters, data settings, or environment details]
**Result**: [Metrics + observations]
**Analysis**: [Hypothesis confirmed or refuted? What did you learn?]
```

### Field Guidelines

**Hypothesis**: Be specific. "Try a smaller learning rate" is too vague. "Reducing LR from 1e-3 to 1e-4 should prevent the oscillation seen in Attempt 3, based on the gradient norm analysis" gives actionable context.

**Code Changes**: Summarize the intent, not the diff. "Added gradient clipping (max_norm=1.0) to the optimizer step" is more useful than listing line numbers. Include the file and function modified if relevant.

**Configuration**: Only record what CHANGED from the previous attempt. If you're using the same config, note "Same as Attempt N" and only list the delta.

**Result**: Include both quantitative metrics (the numbers) and qualitative observations (what you noticed). "Accuracy: 82.3% (up from 79.1%). Training curve now converges smoothly without oscillation. Loss drops consistently for the first 50 epochs then plateaus."

**Analysis**: This is the most important field. Connect the result back to the hypothesis. If confirmed, state what this means for the next step. If refuted, hypothesize why and what this implies about the underlying cause.

## Example Trajectory Log Entry

```markdown
## Attempt 4 — Stage 1: Initial Implementation

**Hypothesis**: The 5% accuracy gap from the paper is caused by different data
augmentation. The paper mentions "standard augmentation" but their code applies
random erasing (p=0.5) which is not mentioned in the paper text.

**Code Changes**: Added RandomErasing(p=0.5, scale=(0.02, 0.33)) to the training
transform pipeline in data/transforms.py.

**Configuration**: Same as Attempt 3, plus RandomErasing.

**Result**: Accuracy: 93.8% (paper reports 94.1%). Gap reduced from 5% to 0.3%.
Training curve now matches the shape shown in the paper's Figure 3.

**Analysis**: Hypothesis confirmed. Random erasing was the missing augmentation.
0.3% remaining gap is within expected variance (paper reports ±0.4%). Gate condition
met — proceeding to Stage 2.
```

## How Logs Feed Into evo-memory

After a successful pipeline run, `evo-memory`'s ESE mechanism reads the trajectory logs and extracts reusable patterns. To make your logs useful for ESE:

### Write for Extraction

Ask yourself: "If a future researcher saw only this log entry, could they extract a reusable strategy?"

**Good for extraction**: "Learning rate warmup for 10% of total steps prevented early divergence. Without warmup, loss spiked in the first 500 steps and never recovered."

**Bad for extraction**: "Changed LR schedule. Results improved." — Too vague to be reusable.

### Tag Reusable Patterns

When you discover something that might generalize, mark it explicitly:

```markdown
**Analysis**: Hypothesis confirmed. **[Reusable]** For transformer fine-tuning on
small datasets (<10K samples), cosine annealing with warm restarts consistently
outperforms linear decay. This is the third time this pattern has appeared across
different domains.
```

The `[Reusable]` tag helps ESE identify high-value patterns during extraction.

### Categories for ESE

When writing analysis, think about which M_E category the insight falls into. The paper's ESE jointly summarizes two core categories (data processing and model training). We extend with architecture and debugging for comprehensive coverage:

| Category | Source | Example Insight |
|----------|--------|----------------|
| Data Processing Strategies | Paper (core) | "Median filter before normalization reduces noise-related instability" |
| Model Training Strategies | Paper (core) | "AdamW with weight decay 0.01 works better than Adam for this architecture" |
| Architecture Strategies | Extension | "Residual connections are critical for modules inserted deeper than 10 layers in transformers" |
| Debugging Strategies | Extension | "When validation loss increases while training loss decreases, check for data leakage before assuming overfitting" |

## Trajectory Log File Organization

### Per-Stage Logs

Each stage maintains its own trajectory log:
```
/experiments/<project>/stage1_baseline/trajectory.md
/experiments/<project>/stage2_tuning/trajectory.md
/experiments/<project>/stage3_method/trajectory.md
/experiments/<project>/stage4_ablation/trajectory.md
```

### Cross-Stage Summary

After completing all stages (or when the pipeline terminates), create a summary:
```
/experiments/<project>/trajectory-summary.md
```

The summary should highlight:
- Total attempts per stage (actual vs budget)
- Key turning points (which attempts broke through or revealed important information)
- Reusable patterns identified (tagged entries from individual logs)
- Failed hypotheses worth remembering (to avoid repeating in future cycles)

## Anti-Patterns

### Don't Log Mechanically

A log that reads "Attempt 1: tried X, didn't work. Attempt 2: tried Y, didn't work. Attempt 3: tried Z, worked." is useless for ESE. Each entry should explain WHY you tried what you tried, and WHY you think the result happened.

### Don't Skip Failed Attempts

Failed attempts are often more informative than successful ones. They narrow the search space and reveal what DOESN'T work. Log every attempt, especially failures.

### Don't Retroactively Edit

Log results as they happen, not after you know the answer. Retroactive editing introduces hindsight bias and makes the trajectory misleading for ESE extraction.
