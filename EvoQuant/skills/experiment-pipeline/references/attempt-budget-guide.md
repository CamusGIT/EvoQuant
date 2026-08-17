# Attempt Budget Guide

Rationale for each stage's attempt budget, adjustment rules, and early termination criteria. The paper defines N_E^s as the maximum number of attempts for stage s, with N_E^1=20, N_E^2=12, N_E^3=12, N_E^4=18. The budget system exists to force systematic thinking — when you know attempts are limited, each one becomes an experiment designed to maximize information.

## Budget Rationale

### Stage 1: Initial Implementation — 20 Attempts (N_E^1=20)

**Why 20?** Initial implementation is the most unpredictable stage. Papers omit critical details, code has version-specific dependencies, and evaluation protocols may differ subtly. 20 attempts gives enough room to find working code and debug the setup while still imposing discipline.

**Breakdown**:
- Attempts 1-3: Initial runs with reported settings
- Attempts 4-8: Debugging data pipeline and evaluation code
- Attempts 9-14: Resolving framework/version differences
- Attempts 15-18: Fine-tuning to match reported metrics
- Attempts 19-20: Final verification with multiple seeds

### Stage 2: HP Tuning — 12 Attempts (N_E^2=12)

**Why 12?** Hyperparameter tuning has diminishing returns. The first few attempts cover the high-impact parameters (learning rate, batch size). Beyond 12 attempts, you're either tuning parameters that don't matter or the problem is deeper than hyperparameters.

**Breakdown**:
- Attempts 1-4: Coarse learning rate search
- Attempts 5-7: Batch size and loss weight exploration
- Attempts 8-10: Regularization and fine-tuning
- Attempts 11-12: Stability verification (3 seeds)

### Stage 3: Proposed Method — 12 Attempts (N_E^3=12)

**Why 12?** If your core idea is sound, 12 systematic attempts should be enough to get it working. If not, the problem is likely fundamental, not engineering. This budget prevents the common trap of endlessly tweaking a flawed approach.

**Breakdown**:
- Attempts 1-3: Incremental component integration
- Attempts 4-6: Initial training and debugging
- Attempts 7-9: Optimization and comparison
- Attempts 10-12: Verification and edge cases

### Stage 4: Ablation — 18 Attempts (N_E^4=18)

**Why 18?** A method with 4-5 components needs at least one leave-one-out experiment per component (4-5), plus interaction tests (2-3), plus verification runs (3-4). That's 9-12 minimum, with 6-9 attempts for investigation and additional tests.

**Breakdown**:
- Attempts 1-5: Leave-one-out for each component
- Attempts 6-8: Interaction effects for key component pairs
- Attempts 9-11: Substitution tests for strongest components
- Attempts 12-15: Additive ablation for paper story
- Attempts 16-18: Verification and edge cases

## Budget Adjustment Rules

Budgets are defaults, not laws. Adjust when the situation warrants it:

### When to Increase Budget

| Situation | Adjustment | Justification |
|-----------|------------|---------------|
| Novel or poorly documented baseline | Stage 1: +5-10 | No reference implementation to compare against |
| From-scratch reproduction (no usable source code) | Stage 1: +10-20; total cap 82-92 | Must implement entire baseline framework; paper omits engineering details; milestones needed |
| From-scratch with many [IMPLICIT] markers (>5) | Stage 1: +15-25; add 2-3 days to timeline | Knowledge gaps require external search + empirical validation |
| Complex method with 6+ components | Stage 4: +6-12 | More components = more ablation experiments |
| Multiple datasets to validate | Stage 3: +3-5 per dataset | Each dataset needs independent verification |
| Multi-objective optimization | Stage 2: +3-5 | Pareto front requires more exploration |

### When to Decrease Budget

| Situation | Adjustment | Justification |
|-----------|------------|---------------|
| Well-documented baseline with official code | Stage 1: -5-10 | Should reproduce quickly |
| Simple method with 1-2 components | Stage 4: -6-10 | Fewer components to ablate |
| M_E has relevant strategies from prior cycles | Stage 2: -3-5 | Start from known-good ranges |
| Clear early signal (positive or negative) | Any stage: -3-5 | Don't burn budget confirming what you already know |

### Maximum Total Budget

A full pipeline run should not exceed **62 total attempts** (20+12+12+18) in Adapt mode, or **82-92 total attempts** (30-40+12+12+18) in From-Scratch mode. If you find yourself exceeding the From-Scratch cap, step back and assess whether the baseline choice itself is viable — consider switching to a baseline with available source code.

## Early Termination Criteria

**Stop before budget exhaustion when**:

### Gate Clearly Met
The gate condition is satisfied well before the budget runs out. Don't run more experiments just because you have budget remaining. Move to the next stage.

### Gate Clearly Unachievable
Evidence from systematic attempts makes clear that the gate cannot be met with the current approach:
- **Stage 1**: Consistent >20% gap after 10+ attempts with different debugging strategies → may need to find a different baseline or implementation
- **Stage 2**: No configuration produces stable training after 8 attempts → likely a deeper issue than hyperparameters
- **Stage 3**: Method consistently underperforms baseline after 8+ varied attempts → trigger IVE classification
- **Stage 4**: Removing a component consistently improves results → the component hurts performance, rethink the method

### Diminishing Returns
Each attempt provides less new information than the previous one. If attempts 7, 8, and 9 all produce similar results with different changes, the system is telling you something — the current axis of variation doesn't matter.

## What to Do When Budget Is Exhausted

If the budget runs out without meeting the gate:

1. **Document the trajectory** — What was tried, what results were obtained, what patterns emerged
2. **Classify the situation**:
   - **Nearly there** (within 80% of gate): Request a small budget extension (3-5 attempts)
   - **Stuck on a specific issue**: Load `experiment-craft` for the 5-step diagnostic flow
   - **No progress despite systematic attempts**: Escalate to `evo-memory` IVE or revisit research direction
3. **Feed into `evo-memory`** — Even exhausted budgets produce valuable data about what doesn't work

## Connection to evo-memory

Budget patterns are themselves learnable:

- **If Stage 1 consistently takes >15 attempts**: Record "initial implementations in [domain] require careful data pipeline verification" in M_E debugging strategies
- **If Stage 2 resolves quickly with M_E guidance**: This validates the stored strategies — increase confidence
- **If any stage exhausts budget without executable code, or Stage 3 method underperforms baseline**: This triggers IVE — the most important evolution mechanism
- **If Stage 4 reveals unexpected component interactions**: Record these in M_E for future architecture decisions
