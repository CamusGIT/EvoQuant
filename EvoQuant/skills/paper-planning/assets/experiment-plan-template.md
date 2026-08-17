# Experiment Plan

## Paper Information

- **Paper title**: [Working title]
- **Core contribution(s)**: [List contributions]
- **Target venue**: [Conference/journal]
- **Submission deadline**: [Date]

---

## Filled Example (for reference)

<details>
<summary>Click to expand: example plan for a fictional NeRF paper</summary>

- **Paper title**: SparseNeRF: Temporally Sparse Attention for Dynamic Scene Reconstruction
- **Core contribution(s)**: (1) Sparse temporal attention module, (2) Motion-aware ray sampling
- **Target venue**: CVPR 2026
- **Submission deadline**: 2025-11-14

**Baselines**: 3DGS (SOTA), D-NeRF (dynamic classic), TiNeuVox (fast dynamic)
**Datasets**: D-NeRF synthetic (standard), Nerfies (real-world)
**Metrics**: PSNR ↑, SSIM ↑, LPIPS ↓, FPS ↑

**Core ablation**: Full → w/o sparse attention → w/o motion-aware sampling → w/o both
**Claim mapping**: C1 "outperforms SOTA" → Tab.1 (Done, supported) · C2 "sparse attention reduces compute" → Tab.3 (Running) · C3 "robust to fast motion" → Fig.5 (Planned)

</details>

---

## Comparison Experiments

### Baselines

| # | Method | Source | Why Include |
|---|--------|--------|-------------|
| 1 | | [paper/code link] | [SOTA / classic / related] |
| 2 | | [paper/code link] | [SOTA / classic / related] |
| 3 | | [paper/code link] | [SOTA / classic / related] |

### Datasets

| # | Dataset | Size | Why Include |
|---|---------|------|-------------|
| 1 | | | [standard benchmark] |
| 2 | | | [challenging / real-world] |

### Metrics

| # | Metric | Direction | Standard? |
|---|--------|-----------|-----------|
| 1 | | ↑ / ↓ | Yes / No |
| 2 | | ↑ / ↓ | Yes / No |

---

## Ablation Studies

### Core Contribution Ablation (Big Table)

| # | Configuration | What Changes | Expected Effect |
|---|--------------|--------------|-----------------|
| 1 | Full model (Ours) | — | Best |
| 2 | w/o [Contribution A] | [Remove/replace A] | [Expected degradation] |
| 3 | w/o [Contribution B] | [Remove/replace B] | [Expected degradation] |
| 4 | w/o [Contribution C] | [Remove/replace C] | [Expected degradation] |

### Design Choice Tables (Small Tables)

**Table A: [Module X] design choices**

| Variant | Description | Expected Result |
|---------|-------------|-----------------|
| Default (ours) | [our choice] | Best |
| Alternative 1 | [description] | [expected] |
| Alternative 2 | [description] | [expected] |

**Table B: [Hyperparameter Y] sensitivity**

| Value | Expected Result |
|-------|-----------------|
| [low] | [expected] |
| [default] | Best |
| [high] | [expected] |

---

## Demos / Applications

| # | Scenario | Data | Purpose |
|---|----------|------|---------|
| 1 | | | [showcase upper limit] |
| 2 | | | [real-world application] |
| 3 | | | [cross-domain generalization] |

---

## Claim-to-Experiment Mapping

| Claim ID | Claim Sentence | Evidence (Tab/Fig) | Status | Verdict |
|----------|---------------|-------------------|--------|---------|
| C1 | | [Tab/Fig reference] | Planned / Running / Done | supported / weak / unsupported |
| C2 | | [Tab/Fig reference] | Planned / Running / Done | supported / weak / unsupported |
| C3 | | [Tab/Fig reference] | Planned / Running / Done | supported / weak / unsupported |

---

## Timeline

| Experiment | Start | Expected Completion | Status |
|-----------|-------|-------------------|--------|
| | | | |
| | | | |
| | | | |
