# Counterintuitive Review Protocol

Use this protocol after the draft is complete and before the final submission pass.

## Phase 1: Reject-First Summary

Write this first, in reviewer tone:

```
This paper should be rejected because:
1) ...
2) ...
3) ...
```

Do not write positives yet. This surfaces high-risk weaknesses quickly.

## Phase 2: Novelty Stress Test

Apply this question to the core idea:
- "Could a capable PhD in this subfield derive this idea in one afternoon after reading top related papers?"

**Before/After Example:**
- Before: "We propose a novel attention mechanism that achieves superior performance."
- After: "We show that axis-aligned decomposition of 3D attention reduces memory from O(N^3) to O(N) while preserving reconstruction quality within 0.3 dB (Tab. 2)."

If answer is "likely yes", do one of:
1. Narrow the claim scope.
2. Emphasize non-obvious mechanism or theoretical justification.
3. Reframe contribution around robustness/efficiency/setting realism rather than novelty rhetoric.

## Phase 3: Claim-Evidence Audit

Create a short table:

| Claim ID | Claim Sentence | Evidence (Tab/Fig/Section) | Verdict |
|---|---|---|---|
| C1 |  |  | supported / weak / unsupported |
| C2 |  |  | supported / weak / unsupported |

Rule:
- `unsupported`: delete or rewrite claim immediately
- `weak`: weaken wording and add qualifier

## Phase 4: Trust Scorecard (Counterintuitive Priority)

Score each item from 0-2:
- Fairness of baseline comparison
- Reproducibility details
- Honest limitations
- Failure case transparency
- Statistical soundness

If total `< 7/10`, do not submit yet even if top-line numbers look strong.

## Phase 5: Kill-Switch Conditions

Trigger a "no-submit" decision if any condition holds:
1. More than 20% claims in Abstract/Introduction are unsupported.
2. At least one obvious recent baseline is missing without explanation.
3. Core contribution has no direct ablation.
4. Main gain appears only on easy subsets.

### Domain-Specific Kill-Switch Thresholds

| Domain | Typical Kill-Switch Signal |
|--------|--------------------------|
| Vision | Main metric (PSNR/mAP) gain < 0.1 dB / 0.3% on standard split; no qualitative improvement visible |
| NLP | Accuracy/F1 gain < 0.5% without statistical significance test; core baseline missing (e.g., GPT-4) |
| Systems | Throughput gain < 5% with added complexity; no latency or memory comparison |

## Phase 6: Prebuttal Draft

Draft one-line responses for likely attacks before submission:
- "novelty limited"
- "missing baseline"
- "not robust"
- "unclear motivation"

Counterintuitive effect: writing prebuttal early improves paper structure and reduces review surprises.
