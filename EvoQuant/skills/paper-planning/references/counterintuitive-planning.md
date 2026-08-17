# Counterintuitive Planning Playbook

Use this playbook when the goal is not "write faster" but "maximize acceptance probability."

## Rule 1: Start from Rejection, Not from Story

Most teams start by polishing a positive narrative. Start by listing likely rejection reasons first.

Create a rejection-risk table:

| Predicted Rejection Comment | Probability (1-5) | Impact (1-5) | Preemption Experiment / Edit | Owner | Deadline |
|---|---:|---:|---|---|---|
| "Novelty is limited" |  |  | Add novelty-isolation ablation + explicit difference table vs closest work |  |  |
| "Missing baseline X" |  |  | Run baseline X with matched protocol |  |  |
| "Not robust" |  |  | Add stress test / corruption / cross-domain test |  |  |
| "Claim unsupported" |  |  | Add claim-evidence mapping and explicit table references |  |  |

Prioritize by `Probability * Impact`. Execute top risks first.

**Triage order for remedial experiments:**
1. Desk-reject prevention (missing baselines, unsupported claims)
2. Highest risk-score items from the table above
3. Polish experiments (extra demos, visualizations)

## Rule 2: Freeze a Minimal Defensible Claim

Define the smallest claim that survives reviewer attack:
- "Under fair compute and data budgets, method A improves metric M on setting S."

Do not start with universal claims ("works for all", "general", "state-of-the-art across tasks"). Expand claims only after evidence exists.

**Before/After Example:**
- Before: "Our method achieves state-of-the-art performance across all 3D reconstruction tasks."
- After: "Under matched compute budgets, our method improves PSNR by 1.2 dB on indoor scenes (Tab. 1)."

## Rule 3: Design Evidence Before Design Language

Before writing polished prose, complete these checks:
- Can each contribution be removed or replaced in one ablation row?
- Can each claimed advantage be measured by at least one accepted metric?
- Can each key claim be pointed to one table/figure ID?

If any answer is "no", redesign experiment plan first.

## Rule 4: Buy Trust with Honest Weakness

Intentionally include one controlled failure mode:
- Pick one representative failure case.
- Explain why failure happens.
- Show scope boundary where method is not expected to work.

Counterintuitive result: one honest limitation often increases confidence in all other claims.

## Rule 5: Predefine a Fallback Narrative

If final top-line gain is small, pivot to a stronger framing that is already preplanned:
- Better efficiency at similar quality
- Better robustness at similar average score
- Better behavior on hard subsets
- Better practical constraints (memory, latency, annotation need)

Do this before deadline week; do not improvise under time pressure.

### Fallback-Narrative-to-Experiment Mapping

| Fallback Framing | Decisive Experiment |
|-----------------|-------------------|
| Better efficiency at similar quality | Runtime / FLOPs comparison table at matched quality threshold |
| Better robustness at similar average score | Corruption / perturbation / cross-domain stress tests |
| Better behavior on hard subsets | Per-difficulty breakdown table (easy vs. hard splits) |
| Better practical constraints (memory, latency, annotation) | Resource-usage table comparing memory, latency, annotation cost |

## Rule 6: Kill Weak Experiments Early

Delete experiments that are expensive but low-information:
- Repetitive benchmark variants that do not test claims
- Cosmetic visualizations without diagnostic value
- Extra comparisons that are unfair by construction

Reallocate time to decisive experiments that can change reviewer scores.
