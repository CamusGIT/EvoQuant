---
name: local-paper-navigator
description: "Find and read papers from the local research-report corpus (repo corpus/, mounted at /papers/). Three native tools form a reading funnel: paper_search (one line per paper), paper_read (card + section outline), paper_section (one verbatim section — the only full-text access). Use when: find papers in the local corpus, read a local report, compare corpus viewpoints, keyword search across extracted knowledge. Do NOT use for: online paper search (use paper-navigator), survey reports (use research-survey), idea generation (use research-ideation)."
allowed-tools: "think_tool paper_search paper_read paper_section read_file"
metadata:
  author: quant-research-team
  version: '2.0.0'
  tags: [local, search, rubric, reading]
---

# Local Paper Navigator

Find and read papers from the local corpus via the **three native tools**. No scripts, no environment variables — the corpus is already mounted and the tools resolve it themselves.

```
paper_search    L3  one line per paper — find candidates, pick paperIds
      │
paper_read      L2  full card + section outline — understand a paper (one call is enough)
      │
paper_section   L1  ONE verbatim section — the only escape hatch into full text
```

Whole-paper reads are blocked by design (`/papers/markdown/**` and `/papers/raw/**` reject direct reads). A read rejection is the mechanism working, not a failure — descend a level instead.

## Core loop

1. `paper_search(query, limit)` — 1–3 queries, one concept each, dedupe by paperId.
2. `paper_read(paper_id)` — for each candidate that matters. 8+ char paperId prefix works.
3. `paper_section(paper_id, heading|query)` — only when you must quote the full text verbatim.
4. Stop. Cite with the paperId prefix (first 8+ chars).

Empty search → the tool says so honestly. Report "not in corpus" rather than widening into fabrication; try one rephrased query (English ↔ Chinese — cards match Chinese titles) before concluding.

## Reading discipline

| Level | Tool | Payload | When |
|---|---|---|---|
| **L3 Contextual** | `paper_search` | one line/paper | scanning, building a shortlist |
| **L2 Analytical** | `paper_read` | card + outline, ≤8K | understanding a paper's method + findings |
| **L1 Technical** | `paper_section` | one section, ≤16K | reimplementing, verbatim quotation |

Defaults: L3 before L2 before L1. Escalate only when the current level cannot answer the question. Most questions end at L2.

## Five Red Lines (always)

1. **Track history.** Don't re-run a query you already ran. Empty result → change angle, not synonyms.
2. **Search a gap, not a vibe.** Every query maps to one missing piece of information. No stacked-keyword bags.
3. **One query = one concept.** Split comparisons (`A vs B`), multi-property asks, and multi-year spans into separate calls.
4. **Never hallucinate.** Every fact (title, source, year, content) comes from a tool result. Direct reads being rejected is the design — never claim content you couldn't reach.
5. **Quote-or-zero.** When you claim a paper meets a criterion, quote a ≤80-char span from its card or a paper_section result. No quote → that criterion scores 0.

## Typical paths

**POINT** (title quoted / paperId known / "read this"): `paper_read` once → answer. Paper Card format in `references/output-formats.md`. Stop — no expansion unless asked.

**LIST** (default — "find papers about X"): 2–3 `paper_search` calls from different angles → `paper_read` the top few → shortlist with evidence.

**SURVEY** ("survey of X", 30+ papers, called from research-ideation): escalate to **Thorough Mode** — `references/thorough-mode.md` (rubric, triage, saturation gate; still all native tools).

## Legacy scripts (compatibility only)

`scripts/` still work and now default to the corpus root (`--corpus-dir`, or `EVOSCIENTIST_CORPUS_DIR`; `--workspace-dir` is deprecated). The native tools above replaced them for search/read — reach for a script only when it does something the tools don't:

| Need | Script |
|---|---|
| Cross-reference expansion | `xref_search.py`, `similar_papers.py` |
| Literature report scaffold | `literature_report.py` |
| Find code (online/local) | `find_code.py`, `code_repo_search.py` |
| Card-level search fallback | `local_search.py`, `match_by_title.py`, `snippet_search.py` |

## References

| File | Read when |
|---|---|
| `references/thorough-mode.md` | SURVEY / ITERATIVE — multi-round rubric search |
| `references/search-principles.md` | Per-query rules, gap diagnosis |
| `references/disambiguation.md` | Query is a project nickname / codename |
| `references/reading-strategy.md` | L1 / L2 / L3 reading framework |
| `references/output-formats.md` | Paper Card / Reading-Notes templates |
| `references/iterative-collection.md` | 5-state machine for ITERATIVE branch |

## Hand off to

| Goal | Skill |
|---|---|
| Survey report | `research-survey` |
| Idea generation | `research-ideation` |
| Baseline code audit | `experiment-pipeline` |
| Extract new PDFs | `quant-paper-extractor` |
