# Supplementary Material Guide

## Core Principle

> Every claim that supports an accept decision must appear in the main paper. Supplementary provides depth, not defense.

Reviewers may skim or skip supplementary material entirely. Never hide critical evidence there.

---

## What Goes Where

| Content | Main Paper | Supplementary |
|---------|:----------:|:-------------:|
| Core comparison table (SOTA) | **Yes** | — |
| Core ablation table | **Yes** | — |
| Additional ablation variants | — | Yes |
| Implementation details (architecture, hyperparameters) | Brief summary | Full details |
| Proof / derivation of key equation | Statement + intuition | Full proof |
| Extra qualitative results | Best 2–3 examples | Full gallery |
| Failure case analysis | 1 representative case | Extended analysis |
| Dataset details (splits, preprocessing) | 1–2 sentences | Full specification |
| User study protocol and raw data | Summary statistics | Full protocol + data |
| Per-scene / per-category breakdowns | — | Yes |
| Video results (if applicable) | — | Yes (linked) |

**Rule of thumb**: If removing it from the paper would weaken a reviewer's confidence in a core claim, it belongs in the main paper.

---

## Standard Structure

```latex
\appendix

\section{Implementation Details}
% Architecture, hyperparameters, training schedule, hardware

\section{Additional Experiments}
% Extended ablations, per-category breakdowns, sensitivity analysis

\section{Additional Qualitative Results}
% Full visual comparison gallery, failure cases

\section{Proofs}
% Formal derivations referenced in the main text
```

Order by importance — reviewers who read supplementary usually start from the top.

---

## Referencing from Main Paper

Use forward references sparingly and consistently:

```latex
% Good: specific pointer
See Appendix A for full architecture details.
Additional per-scene results are provided in the supplementary (Table S1).

% Bad: vague dump
More details can be found in the supplementary material.
```

- Reference supplementary **at the point of need**, not in a blanket statement at the end.
- Use a consistent prefix (`Table S1`, `Figure S1`) or appendix labels (`Table A.1`) — pick one and stick with it.
- Limit to 3–5 forward references total; more suggests the main paper is incomplete.

---

## Common Mistakes

1. **Hiding a core ablation in supplementary** — Reviewers write "missing ablation" if they don't find it in the main paper, even if it exists in the appendix.
2. **Dumping raw results without commentary** — Supplementary tables still need brief captions explaining what the reader should notice.
3. **No page/size awareness** — Some venues limit supplementary length (e.g., NeurIPS: no limit; CVPR: encouraged but optional). Check venue guidelines.
4. **Orphan references** — Every supplementary section should be referenced from the main paper. Unreferenced sections are effectively invisible.
