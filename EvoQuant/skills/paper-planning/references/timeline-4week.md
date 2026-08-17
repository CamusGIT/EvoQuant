# 4-Week Writing Timeline

## Overview

Start writing **at least 1 month** before the deadline. This timeline ensures every section gets adequate drafting and revision time, and that advisors have enough time to review.

> Start writing at least one month before the deadline.

---

## Week-by-Week Schedule

### Week 4 (4 weeks before deadline)

**Focus: Story + Introduction + Experiment Planning**

- [ ] Organize the paper's story:
  - Core contribution(s)
  - Each module's motivation
  - Key technical advantages
- [ ] List all planned experiments:
  - Comparison experiments (baselines, datasets, metrics)
  - Ablation studies (what to ablate, what tables to produce)
- [ ] Write Introduction first draft
- [ ] Begin running comparison experiments

**Deliverable**: Introduction draft + experiment plan

### Week 3 (3 weeks before deadline)

**Focus: Method + Pipeline Figure**

- [ ] Finalize the pipeline figure sketch
- [ ] Confirm pipeline is settled (or mark unsettled parts with `\todo{}`)
- [ ] Write Method first draft
  - Even if some details are unsettled, write the framework with placeholders
- [ ] Continue running experiments

> **Critical deadline**: By end of Week 3, send Introduction + Method draft to advisor for review.
> Critical: By end of Week 3, you must send the Introduction and Method drafts to your advisor — otherwise the advisor likely will not have enough time to finish reviewing the paper.

**Deliverable**: Introduction + Method draft → advisor

### Week 2 (2 weeks before deadline)

**Focus: Experiments + Abstract + Related Work**

- [ ] Write Experiments first draft (comparison + ablation + demos)
- [ ] Write Abstract first draft
- [ ] Write Related Work first draft
- [ ] Incorporate advisor feedback on Introduction + Method
- [ ] Finalize most experiments

**Deliverable**: Complete first draft of all sections

### Week 1 (last week before deadline)

**Focus: Polish Everything**

- [ ] Revise all sections based on self-review and advisor feedback
- [ ] Finalize pipeline figure and teaser figure
- [ ] Polish tables (booktabs, colors, captions)
- [ ] Run remaining demos
- [ ] Choose paper title
- [ ] Final review pass (use `paper-review` skill checklist)
- [ ] Check formatting, references, supplementary material
- [ ] Submit

**Deliverable**: Final camera-ready paper

---

## Submission Progress Tracking Template

Use this table to track progress across team members:

| Section | Owner | Status | Notes |
|---------|-------|--------|-------|
| Introduction | | | |
| Method | | | |
| Experiments | | | |
| Related Work | | | |
| Abstract | | | |
| Pipeline Figure | | | |
| Teaser Figure | | | |
| Tables | | | |
| Supplementary | | | |

**Status legend**: Not started / In progress / Draft done / Under review / Final

---

## Key Milestones

| Milestone | Deadline | Why It Matters |
|-----------|----------|---------------|
| Story + experiment plan | T-4 weeks | Foundation for everything |
| Intro + Method → advisor | T-3 weeks | Advisor needs time to review and iterate |
| All sections drafted | T-2 weeks | Allows full-paper review and integration |
| Final polish complete | T-2 days | Buffer for unexpected issues |
| Submission | T-0 | Done! |

---

## Experiment Dependency Chain

Training and experiments have dependencies — plan them in order:

```
Week 4          Week 3          Week 2          Week 1
  |               |               |               |
  v               v               v               v
[Train model] → [Run comparisons] → [Run ablations] → [Run demos]
                      |                   |
                      v                   v
               [Comparison table]   [Ablation tables]
                                          |
                                          v
                                   [Design-choice tables]
```

Start training as early as possible (Week 4); comparison experiments depend on a trained model; ablations depend on comparison setup; demos and polish come last.

---

## Tips

- **Advisor review is the bottleneck**: Get drafts to your advisor as early as possible
- **Experiments run in parallel**: Start experiments in Week 4; don't wait for writing to finish
- **Use `\todo{}`**: Mark uncertain parts with `\todo{}` rather than blocking progress
- **Iterate, don't perfectionist-block**: A rough draft that exists is better than a perfect draft that doesn't
- **Reserve 2 days before deadline**: For unexpected issues (formatting, missing references, last-minute experiments)
