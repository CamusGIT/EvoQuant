# Paper Reading Strategy

Guide for structured paper analysis over the corpus, using the three native tools. Whole-paper reads are blocked by design — L1 means reading *sections*, not the entire markdown.

## 3-Level Reading Framework

### L1: Technical Reading (High effort)

**Goal:** Fully understand the method — able to reimplement it.

**Process:**
1. Read the card: `paper_read <ID>` (title, source, year, keywords, tldr, abstract, summary fields)
2. Read the relevant full-text sections verbatim, one call per section:
   `paper_section(<ID>, heading="方法")` — or `query=` to pick the best-matching section
3. Study the method and strategy sections in detail:
   - What is the exact formulation / algorithm?
   - What are the inputs, outputs, and intermediate representations?
   - What are the key hyperparameters and design choices?
4. Analyze experiment and result fields:
   - What baselines are compared?
   - What metrics are used and why?
   - Do the results support the claimed contributions?

**When to use:** Papers you will directly build upon.

### L2: Analytical Reading (Medium effort)

**Goal:** Understand the *why* — motivation, design rationale, tradeoffs, key results.

**Process:**
1. Read the complete card: `paper_read <ID>` — the five summary fields plus the section outline usually settle analytical questions.
2. Focus on:
   - What problem does this solve, and why does it matter?
   - What is the key insight / intuition?
   - What are the design choices and why were they made?
   - How does this compare to alternative approaches?
3. For context, run another `paper_search` on the shared method keywords instead of a single paper.

**When to use:** Most papers in your literature survey.

### L3: Contextual Reading (Low effort)

**Goal:** Know what it is and where it fits in the landscape.

**Process:**
1. Read the one-line rows only: `paper_search "<topic>"` (id | year | source | score | title | tldr).
2. Note: main contribution, year, source, relation to your work

**When to use:** Quick scanning, staying current with the corpus.

---

## Reading Decision Tree

```
Is this paper directly related to my implementation?
├── Yes → L1 Technical Reading (paper_read + paper_section per section)
└── No
    ├── Is it in my research area / related work?
    │   ├── Yes → L2 Analytical Reading (paper_read card)
    │   └── No → L3 Contextual Reading (paper_search rows)
    └── Am I just browsing / monitoring?
        └── L3 Contextual Reading
```

---

## Key Questions to Answer for Each Paper

### Core Questions (all levels)

1. **What problem** does this paper address?
2. **What is the key contribution** (in one sentence)?
3. **How novel is this?** (unique keywords vs. shared with other papers)

### Deeper Questions (L1-L2)

4. **What technique** is the core innovation?
5. **What are the tradeoffs** or limitations?
6. **What results** are claimed and what evidence supports them?

### Implementation Questions (L1 only)

7. **How would I reproduce this?** (detailed steps from method + experiment fields)
8. **What could go wrong?** (failure modes, edge cases)
