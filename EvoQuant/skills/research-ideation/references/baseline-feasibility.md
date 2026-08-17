# Baseline Feasibility Assessment

Guidance for annotating every baseline's source code availability and correcting
Difficulty Score. Applied during Step 3 (idea generation) and Step 7 (proposal
expansion).

**Scope of this assessment**: here we only judge **feasibility and difficulty**
— does code exist, how hard would reproduction be, what does that do to the
Difficulty Score and the ELO ranking. This is *not* the final implementation
plan. The authoritative per-baseline Implementation Mode decision and the
audit document live in `experiment-pipeline` Stage 1
(`/experiments/<project>/stage1_baseline/source-code-audit.md`), which carries this
assessment forward and only re-checks when stale. Keep the two stages
non-duplicative: ideation scores feasibility; pipeline decides mode and acts.

## Baseline Feasibility Table

For each baseline, fill this table (use `local-paper-navigator`'s `find_code.py` and `code_repo_search.py` to check availability):

| Baseline | Source Code? | Source | Impl Mode (preliminary) | LOC Est | Time Est | Difficulty Adj |
|----------|-------------|--------|---------------------------|---------|----------|---------------|
| B1: [method] | ✅/❌/⚠️ | URL or N/A | Adapt/From-Scratch/Hybrid | [realistic] | [realistic] | +0/+3-5/+1-2 |

**Implementation Mode (preliminary — for difficulty scoring only)**:
- **Adapt**: Reliable official or community code exists. Only minor modifications needed → no Difficulty adjustment.
- **From-Scratch**: No usable code. Must implement entire method from paper description → Difficulty +3-5 (+3 if one baseline, +5 if the PRIMARY/anchor baseline is from-scratch).
- **Hybrid**: Partial code exists (core algorithm available, data/eval pipeline missing) → Difficulty +1-2.

**When any baseline is From-Scratch**, the proposal MUST include:
1. A **Reproduction Milestone Plan** breaking the baseline into independently testable milestones (data pipeline → algorithm skeleton → training loop → evaluation)
2. A **Knowledge Gap Assessment** listing key implementation details the paper omits and how they will be resolved
3. A **corrected Difficulty Score** that accounts for from-scratch implementation effort, not just the innovation delta
4. A **corrected LOC estimate** using ×5-10 multiplier on the paper's claimed LOC (papers report core modification LOC only)
5. A **corrected time estimate** using ×2-3 multiplier on the paper's claimed timeline

**Example**: If the proposal claims Difficulty=3, ~250 LOC, 4 weeks, but the anchor baseline (GFlowNet) has no source code and requires from-scratch reproduction (~2500-5000 LOC), the corrected assessment should be: Difficulty=7, ~2500-5000 LOC, 6-8 weeks.
