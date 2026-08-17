# Source Code Audit: [Project Name]

Date: [date]

> This file is the **authoritative Implementation Mode decision** for the
> pipeline. It carries forward the baseline-feasibility assessment from the
> `research-ideation` proposal (which scored feasibility/difficulty) and only
> re-checks baselines whose assessment is stale or that were added during
> refinement. Do not redo the literature-era search from scratch.

## Baseline Code Availability

| Baseline | Paper Title | Paper ID | Local Code-repo? | Online Code? | Impl Mode | Source URL |
|----------|-------------|----------|------------------|-------------|-----------|------------|
| B1 | | | ✅/❌ | ✅/❌ | Adapt/FS/Hybrid | |
| B2 | | | ✅/❌ | ✅/❌ | Adapt/FS/Hybrid | |
| B3 | | | ✅/❌ | ✅/❌ | Adapt/FS/Hybrid | |
| B4 | | | ✅/❌ | ✅/❌ | Adapt/FS/Hybrid | |

## Audit Commands Run

(Only for baselines re-checked here; others inherited from the proposal.)

- `python EvoQuant/skills/local-paper-navigator/scripts/find_code.py --title "..."`
- `python EvoQuant/skills/local-paper-navigator/scripts/code_repo_search.py --query "..."`
- `python EvoQuant/skills/local-paper-navigator/scripts/code_repo_search.py --paper-id <ID>`

## Decision

**Implementation mode (per baseline)**: [Adapt / From-Scratch / Hybrid — one per baseline]

**Justification**: [why this mode was chosen — e.g., "No official repo, no community implementation with >50 stars, local code-repo empty → From-Scratch"]

**Budget adjustment**: [e.g., "Stage 1 budget increased from ≤20 to ≤35 for From-Scratch reproduction"]
