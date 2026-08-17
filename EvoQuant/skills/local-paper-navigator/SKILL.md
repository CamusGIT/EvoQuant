---
name: local-paper-navigator
description: "Find and read papers from local markdown/wiki corpus. Disambiguate ambiguous queries, search by keyword + abstract + full-text, judge by author-graded rubric, and read with L1/L2/L3 strategy. Use when: find papers in local corpus, search wiki, read a local report, keyword search across extracted knowledge. Do NOT use for: online paper search (use paper-navigator), survey reports (use research-survey), idea generation (use research-ideation)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: quant-research-team
  version: '1.0.0'
  tags: [local, search, rubric, reading]
---

# Local Paper Navigator

Find and read papers from local markdown/wiki corpus. Route by **intent**, judge by **author-graded rubric**.

```
        User
         │
         ▼
   ┌── Router ──┐
   │            │
   ▼            ▼
 POINT      LIST/ITERATIVE
 (1 paper)   (rubric + 2–3 rounds)
```

The agent does relevance judgment — no LLM-as-judge is called. You author the rubric, you triage each paper, you sort.

## Setup

Scripts at `/skills/local-paper-navigator/scripts/`. Run via `python /skills/local-paper-navigator/scripts/<name>.py`.

No API keys required for local scripts. `find_code.py` requires optional API keys for online code search.

| Env var | Used by | Notes |
|---|---|---|
| `PAPER_NAV_WORKSPACE_DIR` | All scripts | Root directory containing `wiki/`, `markdown/`, `manifest.jsonl`. Default: current directory |
| `GITHUB_TOKEN` | `find_code.py` | Higher rate limits for GitHub API (optional) |
| `HF_TOKEN` | `find_code.py` | Higher rate limits for HuggingFace API (optional) |

---

## Five Red Lines (always)

1. **Track history.** Don't re-run a query you already ran. Empty result → change angle, not synonyms.
2. **Search a gap, not a vibe.** Every query maps to one missing piece of information. No stacked-keyword bags.
3. **One query = one concept.** Split comparisons (`A vs B`), multi-property asks, and multi-year spans into separate calls.
4. **Never hallucinate.** Every fact (title, source, year, content) comes from a tool result or the wiki record.
5. **Quote-or-zero.** When you claim a paper meets a criterion, quote a ≤80-char span from its tldr / abstract / wiki fields. No quote → that criterion scores 0.

---

## Router

| Branch | User signal | Cadence | Output |
|---|---|---|---|
| **POINT** | Title quoted, paperId, "read this paper" | 1 call | Paper Card |
| **LIST** (default) | "find papers about X", "is there a paper that …?", "papers satisfying A and B" | 2 rounds + optional patch | Shortlist with per-criterion evidence |
| **ITERATIVE** | "survey of X", "30+ papers on Y", called from `research-ideation` | up to 3 rounds, breadth-first | Ranked table (hand off to research-survey for the report) |

**Default to LIST when unsure.** Don't add `survey` / `review` to LIST queries — it down-ranks the canonical originals the user wants.

Ambiguous query (project nickname, codename, single capitalized word with zero hits) → run `local_search` exact match first, then `xref_search` for related terms to resolve identifiers, then re-route.

---

## POINT branch (known paper)

| Input | Command | Output |
|---|---|---|
| paperId (SHA-256) | `python scripts/fetch_paper.py --paper-id <ID> --metadata-only` | Paper Card + reading notes |
| Title quoted | `python scripts/match_by_title.py --title "<title>"` (add `--fallback-search` for partial titles) | Paper Card |

**Paper Card:**

```
📄 **<Title>**
Source: <Source> | Year: <Y> | ID: <paperId>
TLDR: <one sentence>
```

Stop here. Do not chain to cross-reference expansion unless asked.

---

## LIST / ITERATIVE branch — 6 steps

### Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch.

### Step 2: Author the RUBRIC (via `think_tool`)

Emit a structured block before any search. It persists across rounds and every later step references it.

```
RUBRIC for "<user query verbatim>"
Branch: LIST | ITERATIVE
Criteria (2–4, atomic, weights sum to ≈1.0):
  C1 [w=0.45] <what the paper MUST do/be — one sentence>
  C2 [w=0.35] <...>
  C3 [w=0.20] <...>
Named entities to preserve verbatim: [<ent1>, <ent2>, ...]
Angle tags (3–5 sub-topic axes): [<tag1>, <tag2>, <tag3>]
Disqualifiers: [<auto-reject if abstract shows this>]
```

Rules:
- **Criteria** atomic (one condition each), weighted, non-redundant.
- **Named entities** = proper-noun / technical-term anchors from the user's query. Every entity appears verbatim in ≥1 query across Rounds 1+2.
- **Angle tags** = sub-topic axes (`method`, `task`, `domain`, …). No two queries in one round share a tag.
- **Disqualifiers** = "specifically X, **not** Y" exclusions. Tripping a disqualifier scores 0 on the related criterion.

### Step 3: Search — Probe-then-Refine

**Do not author all queries upfront.** Round 1 surfaces named entities Round 2 needs.

**Round 1 — Probe** (2 parallel queries):
- `Q-broad` — canonical phrasing of the topic (angle: `general`)
- `Q-narrow` — a specific mechanism / sub-question / method (angle: tagged)

```bash
python scripts/local_search.py --query "<Q-broad>" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
python scripts/local_search.py --query "<Q-narrow>" --limit 15 --sort-by relevance --output /tmp/pool.jsonl --append
```

`--output --append` auto-dedupes by `paperId` across rounds (built into the scripts), so a paper found by two queries is written once. Read `/tmp/pool.jsonl` to inspect (Step 4 triage).

From Round 1 titles + tldrs, lift:
- recurring **named entities** (algorithm / benchmark / model names),
- **angle gaps** (Step-2 tags not seen),
- vocabulary from **adjacent communities**.

**Round 2 — Refine** (2–3 parallel queries):

| Tier | Count | Shape |
|---|---|---|
| Method / mechanism | 1–2 | Sub-mechanism on an uncovered angle tag |
| Named-entity | 1 | Entity verbatim from Round 1 results + a modifier |

```bash
python scripts/local_search.py --query "<refine 1: method, angle X>" --limit 15 --output /tmp/pool.jsonl --append
python scripts/local_search.py --query "<refine 2: method, angle Y>" --limit 15 --output /tmp/pool.jsonl --append
```

**Cross-reference expansion** (ITERATIVE, or LIST after ≥3 strong seeds):
```bash
python scripts/xref_search.py --paper-id <SEED> --direction related --limit 15 --output /tmp/pool.jsonl --append
python scripts/xref_search.py --paper-id <SEED> --direction shared-method --limit 15 --output /tmp/pool.jsonl --append
python scripts/similar_papers.py --positive <SEED1>,<SEED2> --limit 15 --output /tmp/pool.jsonl --append
```

**Round 3 — Patch** (only if Step 5 gate says CONTINUE). One targeted query on the remaining gap.

**Per-query rules:**
- 4–7 words typical (up to 9 OK); <3 over-recalls, >9 dilutes ranking.
- English only.
- Bare entity names, no `paper` / `report`.
- No two queries in one round may share >60% of content tokens.

### Step 4: Triage — PERFECT / GOOD / WEAK / IRREL

After every round, classify each new paper. Emit a `think_tool` block:

```
TRIAGE round=<n>  query="<q>"
  PERFECT (k): <paperId> "<title-≤60>" Y=<year> · [C1✓ C2✓ C3✓]
                evidence C1: "<≤80-char quote>"
                evidence C2: "<≤80-char quote>"
                evidence C3: "<≤80-char quote>"
  GOOD    (k): <paperId> "<title>" Y=<year> · [C1✓ C2~ C3✗]
                evidence C1: "<quote>"
  WEAK    (k): <paperId> "<title>" Y=<year> · [C1~ C2✗ C3✗]
  IRREL   (k): <paperId> "<title>"
```

| Tier | Required mask | Quotes |
|---|---|---|
| `PERFECT` | every high-weight criterion `✓`, no `✗` anywhere | one ≤80-char quote per criterion |
| `GOOD` | every high-weight (`w ≥ 0.3`) at least `~`, no `✗` on any high-weight | one quote per `✓` criterion |
| `WEAK` | one high-weight `✗` or only low-weight hits | none |
| `IRREL` | misses every high-weight or trips a disqualifier | none — drop from later rounds |

`✓` = tldr/abstract clearly supports. `~` = partial/inferable. `✗` = no support or contradicts.

**Snippet upgrade** for borderline papers (abstract silent on a criterion): search wiki body fields for evidence:
```bash
python scripts/snippet_search.py --query "<criterion phrase>" \
  --paper-ids "<paperId1>,<paperId2>,..." --limit 50
```

### Step 5: Saturation Gate

Read the across-round pool from Step 4, apply the table, take the action.

**LIST branch after Round 1:**

| Pool | Action |
|---|---|
| ≥1 PERFECT | **STOP** → Step 6 |
| 0 PERFECT, ≥2 GOOD | **CONTINUE → Round 2** |
| 0 PERFECT, <2 GOOD | **CONTINUE → Round 2**, plus ≥1 query on a *new* angle |

**LIST branch after Round 2:**

| Pool | Action |
|---|---|
| ≥1 new PERFECT, all high-weight criteria covered | **STOP** → Step 6 |
| ≥1 new PERFECT, but a high-weight criterion still has 0 PERFECT | **CONTINUE → Round 3 patch** |
| 0 new PERFECT+GOOD *and* Round 1 had 0 PERFECT | **STOP and re-decompose** — criteria are wrong |
| Empty recall on every Round 2 query | **STOP** — topic not in corpus |

**ITERATIVE branch:** keep searching while any angle tag has 0 PERFECT+GOOD. Stop when every angle tag has ≥2 PERFECT+GOOD.

**Round caps:** LIST 2+1, ITERATIVE 3, POINT 1.

**The gate is mechanical** — do not skip rounds because "the results look right".

### Step 6: Rerank and Output

**Gather:** every PERFECT and GOOD from across all rounds (dedup by `paperId`, keep stronger mask). Add WEAK only if PERFECT+GOOD < 3 (fallback fill). Drop IRREL.

**Score** each criterion 0 / 0.25 / 0.5 / 0.75 / 1.0:

| Score | Meaning |
|---|---|
| `1.0` | quote directly satisfies the criterion |
| `0.75` | strong implication (one inference from quote) |
| `0.5` | partial — topic match, not the specific condition |
| `0.25` | adjacent — same field, off-criterion |
| `0` | no quoted evidence, contradicts, or trips a disqualifier |

**Compute** `weighted_total = Σ (criterion_score × criterion_weight)` ∈ [0, 1]. Sort DESC by `weighted_total`, tie-break by `year` DESC.

**Tier the output:**

| Tier | `weighted_total` | Use |
|---|---|---|
| Primary | ≥ 0.7 | The answer. Eligible for top-K. |
| Secondary | 0.5 – 0.7 | "May also be relevant"; never promoted to Primary. |
| Drop | < 0.5 | Exclude. |

**K to return:**

| Question shape | K |
|---|---|
| "Exactly N papers" | N (pad with Secondary only if Primary < N) |
| "Is there a paper that …?" / "Recommend a paper" | 1–2 (bold top-1) |
| "Find papers about …" | 3–5 |
| "Survey of …" / ITERATIVE | ≤ 10 Primary (hard cap) |

**Output formats:**

LIST (shortlist with evidence):
```
**Primary answer (weighted_total = 0.92):**
- **<paperId[:12]>** "<Title>" — <Source>, <Year>
  - C1 (0.45): "<quote>" → 1.0
  - C2 (0.35): "<quote>" → 1.0
  - C3 (0.20): "<quote>" → 0.5

**May also be relevant:**
- <paperId[:12]> "<Title>" — total 0.62; missed C2.
```

ITERATIVE (ranked table):
```
| # | Title | Source | Year | Score |
|---|-------|--------|------|-------|
| 1 | …    | …      | 2026 | 0.88  |
```

POINT: Paper Card (above).

**Pre-output checklist (mandatory):**

- [ ] **Pool gathered** from every Step-5 triage block across all rounds, deduped by `paperId`, IRREL excluded.
- [ ] **weighted_total computed** for every candidate.
- [ ] **Sorted** DESC by `weighted_total` → `year`.
- [ ] **Every Primary paper has ≥1 evidence quote per high-weight criterion** (quote-or-zero rule, Red Line 5).
- [ ] **Ranked output is Primary-only and ≤ K**.

If any box is unchecked, return to Step 6 — do not output.

---

## Reading Strategy

After identifying papers, read them at the appropriate depth:

| Level | Goal | When | Command |
|---|---|---|---|
| **L1 Technical** | Fully understand method — able to reimplement | Papers you will directly build upon | `python scripts/fetch_paper.py --paper-id <ID> --reading-level L1 --full-stdout` |
| **L2 Analytical** | Understand motivation + design + key results | Most survey/ideation papers | `python scripts/fetch_paper.py --paper-id <ID> --reading-level L2` |
| **L3 Contextual** | Know what it is and where it fits | Quick scanning | `python scripts/fetch_paper.py --paper-id <ID> --metadata-only` |

**L1** reads the full markdown source. **L2** reads the complete wiki record (including strategy, method, experiment, result). **L3** reads only metadata (title, year, source, tldr, abstract).

Details in `references/reading-strategy.md`.

---

## Tool Cheat Sheet

| Need | Script | Notes |
|---|---|---|
| Keyword search | `local_search.py` | Searches wiki JSONL by token overlap |
| Title → record | `match_by_title.py` | Substring match; `--fallback-search` for fuzzy |
| Cross-reference | `xref_search.py` | `--direction related/shared-keywords/shared-method` |
| Similar papers | `similar_papers.py` | Seed-based keyword-overlap similarity |
| Body-text snippets | `snippet_search.py` | Wiki fields first, then markdown fallback with context |
| Fetch full text | `fetch_paper.py` | L1=markdown, L2=wiki, L3=metadata; `--reading-level` flag |
| Literature report | `literature_report.py` | Generates report from local wiki data |
| Saturation gate | `saturation.py` | JSONL log of per-round yields; `estimate` returns STOP/CONTINUE |
| Find code (online) | `find_code.py` | Search GitHub + HuggingFace for paper implementations (requires `GITHUB_TOKEN`, `HF_TOKEN`) |
| Find code (local) | `code_repo_search.py` | Search code-repo for local implementations |

All discovery scripts: `--limit N`, `--json`, `--output FILE`, `--append`; accept SHA-256 paperId. `--output --append` auto-dedupes by `paperId` across rounds.

All scripts run locally. No rate limits. No API keys needed.

---

## References

| File | Read when |
|---|---|
| `references/search-principles.md` | Per-query rules, gap diagnosis |
| `references/disambiguation.md` | Query is a project nickname / codename |
| `references/reading-strategy.md` | L1 / L2 / L3 reading framework |
| `references/output-formats.md` | Paper Card / Reading-Notes templates |
| `references/iterative-collection.md` | 5-state machine for ITERATIVE branch |

---

## Hand off to

| Goal | Skill |
|---|---|
| Survey report | `research-survey` |
| Idea generation | `research-ideation` |
| Baseline code audit | `experiment-pipeline` |
| Extract new PDFs | `quant-paper-extractor` |
