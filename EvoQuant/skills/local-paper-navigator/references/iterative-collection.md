# Iterative Collection (Branch 3 State Machine)

Read this only when the user wants **comprehensive coverage** of a topic across the local papers library. For one-shot "find me papers about X", stay in SKILL.md Branch LIST.

## Why a state machine

Collection is iterative: each search round informs the next (which gaps to fill, which seeds to expand). Without explicit states, agents either stop too early (under-collection) or loop forever (over-collection).

## States

```
S1 DECOMPOSE → S2 MULTI_SEARCH → S3 CROSSREF_EXPAND → S4 GAP_CHECK → S5 FINALIZE
                     ↑                                         │
                     └───── (gap found, targeted search) ────┘
```

---

## S1 — DECOMPOSE

**Goal:** Identify 3-5 sub-topics within the user's query, generate 4-6 variant queries.

**Action:**
1. List sub-topics along these axes (pick what fits):
   - Empirical vs. theoretical
   - Mechanism vs. condition
   - Method-keyword variants ("factor mining" / "alpha generation" / "signal construction")
   - Adjacent formulations ("portfolio optimization" / "asset allocation")
2. Write 4-6 queries, at least one per sub-topic.

**Exit:** ≥3 sub-topics named AND ≥4 queries written → S2.

---

## S2 — MULTI_SEARCH

**Goal:** Run searches across different query formulations to build the initial pool.

**Action:**
1. For each query from S1:
   ```bash
   python scripts/local_search.py --query "<q>" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
   ```
2. Deduplicate by `paperId`.
3. Filter by title + tldr relevance. Reject if tldr is off-topic.

**Output:** `pool[]` of candidates with wiki fields.

**Exit:** ≥3 strongly relevant papers in pool → S3. If <3, run 1-2 more targeted queries.

---

## S3 — CROSSREF_EXPAND

**Goal:** Use cross-reference search to find papers keyword search cannot reach.

**Action:** Rank pool by relevance to the user's query. Pick top 3 as seeds, prefer seeds from *different sub-topics* for diversity.

1. **Related** on the most-relevant seed:
   ```bash
   python scripts/xref_search.py --paper-id <seed1> --direction related --limit 15 --output /tmp/pool.jsonl --append
   ```
2. **Shared-keywords** on top 2 seeds:
   ```bash
   python scripts/xref_search.py --paper-id <seed1> --direction shared-keywords --limit 15 --output /tmp/pool.jsonl --append
   python scripts/xref_search.py --paper-id <seed2> --direction shared-keywords --limit 15 --output /tmp/pool.jsonl --append
   ```
3. **Shared-method** on 1-2 diverse seeds:
   ```bash
   python scripts/xref_search.py --paper-id <seedN> --direction shared-method --limit 15 --output /tmp/pool.jsonl --append
   ```
4. **Similarity** with diverse seeds:
   ```bash
   python scripts/similar_papers.py --positive <seed1>,<seed2>,<seed3> --limit 15 --output /tmp/pool.jsonl --append
   ```

**Output:** `pool[]` expanded by cross-referenced papers, still deduplicated.

**Exit:** All 4 search calls completed → S4.

---

## S4 — GAP_CHECK

**Goal:** Audit coverage against the sub-topics from S1.

**Action:**
1. Count papers in `pool[]` per sub-topic from S1.
2. For each sub-topic with **0-1 papers**, run one targeted `local_search` for the gap.
3. If the targeted search returns ≥2 new relevant papers → optionally one more `similar_papers` on the new finds.

**Output:** Final `pool[]`.

**Exit:** Every sub-topic from S1 has ≥2 papers, OR you ran one targeted search per gap → S5.

---

## S5 — FINALIZE

**Goal:** Apply quality filter, take top N, return.

**Action:**
1. Sort by relevance (semantic match to user goal, judged by title + tldr).
2. Apply profile-specific filter:

| Profile | Recency | Source | Target N |
|---|---|---|---|
| **Survey** | include older work | all sources | up to all |
| **Ideation** | bias toward recent | all sources | 30-50 |
| **User-specified N** | match user request | match user signals | user-specified |

3. Output as ranked table.
4. Hand off based on user intent:
   - Survey report → `research-survey`
   - Idea generation → `research-ideation`
   - User just wanted a list → done.

**Exit:** Table delivered. Skill terminates.

---

## Failure escape hatches

- **All searches return <3 results:** The topic may not be in the local papers library. Accept and report what was found.
- **Pool > 200 candidates after S3:** Over-searched. Tighten relevance filter, prefer recent papers, advance to S5.
