# Experiment Planning

## Why Plan Experiments Early?

Experiment planning should happen **alongside story design** (Week 4 before deadline), not after writing the Method. Early planning:
- Reveals gaps in the proposed method
- Identifies missing baselines before it's too late to run them
- Ensures ablation studies directly support paper claims
- Prevents last-minute scrambling for missing experiments

---

## Comparison Experiments

### Selecting Baselines

> List the comparison experiments you need to run.

**For existing tasks with established methods:**
- Include **current SOTA** methods (must-have)
- Include **recent** methods from top venues (last 2-3 years)
- Include **classic** methods that are widely known in the field
- Ensure baselines are fairly evaluated (same data, same metrics, same protocol)

**For novel tasks without direct baselines:**
- Adapt methods from **related tasks**
- Create **method variants** as baselines (e.g., replace your novel module with standard alternatives)
- Combine existing techniques in **straightforward ways** as a baseline
- Clearly explain and justify each baseline's construction

### Choosing Datasets

- Use **standard benchmarks** for the task (required for comparison with published numbers)
- Add **challenging datasets** to demonstrate the method's limits (for demos)
- Consider **diverse scenarios** that test different aspects of the method
- Verify that baselines have results on these datasets (or can be reproduced)

### Choosing Metrics

- Use **standard metrics** for the task (enables comparison with published work)
- Add metrics that specifically capture your method's advantage
- Include both **quantitative** metrics and **qualitative** visual comparisons
- Use established evaluation protocols (official splits, standard preprocessing)

---

## Ablation Studies

### Part 1: Core Contribution Ablation (Big Table)

Design one comprehensive table that tests each core contribution:

| Configuration | What's Changed | Purpose |
|--------------|----------------|---------|
| Full model | Nothing (ours) | Reference |
| w/o Contribution A | Remove/replace module A | Verify A is necessary |
| w/o Contribution B | Remove/replace module B | Verify B is necessary |
| w/o Contribution C | Remove/replace module C | Verify C is necessary |

- Each row should change **exactly one thing** from the full model
- Include **visualization** alongside the table to show qualitative differences
- Results should clearly show that each contribution matters

### Part 2: Design Choice Tables (Small Tables)

For each pipeline module, create a focused table:

**Table: Effect of [design choice] in Module X**

| Design choice variant | Metric |
|----------------------|--------|
| Choice A (default) | best |
| Choice B | worse |
| Choice C | worse |

Types of small tables:
- **Hyperparameter sensitivity**: Vary key hyperparameters; show performance is stable
- **Input quality**: Test with degraded inputs; show robustness
- **Design alternatives**: Compare your design choice against alternatives; justify your choice
- **Component analysis**: Deeper analysis of a specific module's behavior

---

## Demo Planning

> Applications and demos are critical for the paper's impact.

Demos showcase the method's potential beyond standard benchmarks:

- **More challenging data**: Harder scenes, rare cases, edge cases
- **Real-world applications**: Practical use cases that readers care about
- **Cross-domain generalization**: Does the method work outside the training domain?
- **Failure case analysis**: Honest discussion of when the method struggles (shows maturity)

---

## Experiment-to-Claim Mapping

Every claim in the paper (especially in Abstract and Introduction) must have experimental support.

| Claim ID | Claim Sentence | Evidence (Tab/Fig) | Status | Verdict |
|----------|---------------|-------------------|--------|---------|
| C1 | "Our method outperforms SOTA" | Tab. 1 | Done / Running / Planned | supported / weak / unsupported |
| C2 | "Module A is effective" | Tab. 2 | Done / Running / Planned | supported / weak / unsupported |
| C3 | "Robust to input quality" | Tab. 3 | Done / Running / Planned | supported / weak / unsupported |
| C4 | "Works on challenging scenes" | Fig. 5 | Done / Running / Planned | supported / weak / unsupported |

> Every claim in the paper (especially in the Abstract and Introduction) must be correct and supported by experiments. Some reviewers will reject a paper directly for unsupported claims.

---

## Experiment-to-Figure/Table Assignment Guide

| Experiment Type | Best Presentation Format |
|----------------|------------------------|
| Quantitative comparison (numbers) | Table (booktabs, best in bold) |
| Qualitative comparison (visual) | Figure (side-by-side panels) |
| Performance trend over variable | Line plot |
| Ablation study | Table (one row per configuration) |
| Demo / challenging case | Figure (full-width, high-res) |
| Efficiency comparison | Table or bar chart |

---

## Common Pitfalls in Experiment Planning

1. **Missing important baselines**: Not comparing with well-known recent methods
2. **No ablation studies**: Reviewers will ask "what happens without module X?"
3. **Too few metrics**: Only using one metric when the field has multiple standard ones
4. **Easy-only datasets**: Only testing on simple benchmarks; doesn't prove real effectiveness
5. **Unfair comparison**: Different training data, resolution, or compute budgets
6. **No visual results**: Tables without qualitative comparisons are insufficient
7. **No failure cases**: Hiding failure modes makes the paper seem less trustworthy
