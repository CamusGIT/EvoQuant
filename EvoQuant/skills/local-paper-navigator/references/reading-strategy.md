# Paper Reading Strategy

Guide for structured paper analysis using local wiki and markdown resources.

## 3-Level Reading Framework

### L1: Technical Reading (High effort)

**Goal:** Fully understand the method — able to reimplement it.

**Process:**
1. Read the wiki metadata (title, source, year, keywords, tldr, abstract)
2. Read the full markdown source for detailed methodology:
   ```bash
   python scripts/fetch_paper.py --paper-id <ID> --reading-level L1 --full-stdout
   ```
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
1. Read the complete wiki record (including strategy, method, experiment, result):
   ```bash
   python scripts/fetch_paper.py --paper-id <ID> --reading-level L2
   ```
2. Focus on:
   - What problem does this solve, and why does it matter?
   - What is the key insight / intuition?
   - What are the design choices and why were they made?
   - How does this compare to alternative approaches?
3. Use cross-reference search for context:
   ```bash
   python scripts/xref_search.py --paper-id <ID> --direction shared-method
   ```

**When to use:** Most papers in your literature survey.

### L3: Contextual Reading (Low effort)

**Goal:** Know what it is and where it fits in the landscape.

**Process:**
1. Read metadata only (title, year, source, tldr, abstract):
   ```bash
   python scripts/fetch_paper.py --paper-id <ID> --metadata-only
   ```
2. Note: main contribution, year, source, relation to your work

**When to use:** Quick scanning, staying current with the corpus.

---

## Reading Decision Tree

```
Is this paper directly related to my implementation?
├── Yes → L1 Technical Reading (full markdown)
└── No
    ├── Is it in my research area / related work?
    │   ├── Yes → L2 Analytical Reading (full wiki record)
    │   └── No → L3 Contextual Reading (metadata only)
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
