# Search Principles

Rules for effective searching over the local papers library (cards + markdown via `paper_search` / `paper_read` / `paper_section`).

## Query Design Rules

1. **One concept per query.** Split comparisons, multi-property asks, and multi-year spans into separate calls.
2. **4–7 words typical.** <3 over-recalls, >9 dilutes ranking.
3. **Bare entity names.** No `paper` / `report` / `study` filler words.
4. **English preferred.** Chinese terms work but may have lower token-overlap scores. Use both if unsure.
5. **No stacked-keyword bags.** Every query maps to one missing piece of information.

## Multi-Field Search Strategy

The `local_search.py` script searches across multiple wiki JSONL fields with different weights:

| Field | Weight | Why |
|-------|--------|-----|
| `title` | 2× | Highest signal — paper title directly encodes topic |
| `keywords` | 2× | Curated terms that capture synonymous vocabulary |
| `tldr` | 1× | One-sentence core finding |
| `abstract` | 1× | Broader context and approach |
| `source` | 1× | Organization/firm |

**Tip:** For method-focused searches, use `xref_search.py --direction shared-method` which weights the `method` and `strategy` fields more heavily.

## Probe-then-Refine Pattern

Round 1: Broad query + narrow query → surface entities and gaps.
Round 2: Refine queries using entities from Round 1 → fill gaps.
Round 3 (if needed): Patch remaining gaps with targeted search.

This pattern works because:
- Different communities use different terms for the same idea
- A single query misses relevant work
- Round 1 results inform Round 2 vocabulary

## Gap Diagnosis

After a round returns few results, diagnose the gap type:

| Gap Type | Signal | Fix |
|----------|--------|-----|
| **Vocabulary drift** | Different community's term for same concept | Try synonyms from the field's terminology |
| **Dead end** | No papers in the library cover this sub-topic | Accept the gap, note it in output |
| **Over-specific** | Query too narrow | Broaden to the parent concept |
| **Library limit** | Topic exists but not in the papers library | Accept the gap; suggest adding more papers |

## Domain Terminology

When searching across sub-fields, be aware of terminology drift:

| Quant Concept | Common Variants |
|---|---|
| Factor returns | alpha, excess return, risk premium |
| Portfolio optimization | asset allocation, rebalancing, weight optimization |
| Risk model | risk factor, risk decomposition, risk exposure |
| Backtesting | empirical analysis, out-of-sample test, historical simulation |
| Machine learning | deep learning, neural network, AI-based |

Use multiple variants in separate queries to maximize recall.
