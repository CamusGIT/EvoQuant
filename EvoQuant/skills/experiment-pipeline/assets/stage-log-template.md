# Stage Log: Stage [N] — [Stage Name]

## Stage Info

- **Pipeline**: [Project/experiment name]
- **Stage**: [1: Initial Implementation | 2: Hyperparameter Tuning | 3: Proposed Method | 4: Ablation]
- **Budget**: [N] attempts (default: [20/12/12/18])
- **Gate Condition**: [What must be true to advance]
- **Start Date**: [YYYY-MM-DD]

## Attempt Log

| # | Hypothesis | Code Changes | Configuration | Result | Analysis | Gate Met? |
|---|-----------|-------------|--------------|--------|----------|-----------|
| 1 | [What you expected and why] | [Summary of what was modified] | [Changed params or "Same as #N"] | [Metrics + observations] | [Confirmed/refuted? What learned?] | [ ] |
| 2 | | | | | | [ ] |
| 3 | | | | | | [ ] |

*Add rows as needed. This table is the quick-reference stage trajectory log — save to `/experiments/<project>/stageN_name/trajectory.md`. For detailed per-attempt write-ups (e.g., for evo-memory ESE extraction), use the expanded markdown format in [code-trajectory-logging.md](../references/code-trajectory-logging.md).*

## Gate Assessment

- **Gate condition**: [Restate the condition]
- **Current best result**: [Best metric achieved]
- **Met?**: [ ] Yes / [ ] No
- **If not met**: [ ] Continue (attempts remaining) / [ ] Load experiment-craft / [ ] Escalate to evo-memory

## Key Observations

- [Pattern 1 observed across attempts]
- [Pattern 2 observed across attempts]
- [Anything surprising or counterintuitive]

## Lessons Learned

- [What worked and why]
- [What didn't work and why]
- [Reusable strategies identified — tag with [Reusable] for evo-memory ESE]

## Next Stage Preparation

- [ ] Gate condition verified
- [ ] Results documented and saved to `/experiments/<project>/stageN_name/`
- [ ] Trajectory log completed
- [ ] Key artifacts ready for next stage
