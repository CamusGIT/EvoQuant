# Thorough Mode — multi-round rubric search

Optional deep protocol for LIST/ITERATIVE questions ("survey of X", "find
papers satisfying A and B", calls from research-ideation). The default
single-pass loop in SKILL.md is enough for most questions; escalate here
when coverage matters more than latency.

Everything below uses the native tools (`paper_search` / `paper_read` /
`paper_section`) — no scripts required.

## Router

| Branch | User signal | Cadence | Output |
|---|---|---|---|
| **POINT** | Title quoted, paperId, "read this paper" | 1 read | Paper Card |
| **LIST** (default) | "find papers about X", "is there a paper that …?", "papers satisfying A and B" | 2 rounds + optional patch | Shortlist with per-criterion evidence |
| **ITERATIVE** | "survey of X", "30+ papers on Y", called from `research-ideation` | up to 3 rounds, breadth-first | Ranked table (hand off to research-survey for the report) |

**Default to LIST when unsure.** Don't add `survey` / `review` to LIST queries — it down-ranks the canonical originals the user wants.

Ambiguous query (project nickname, codename, single capitalized word with zero hits) → exact-match `paper_search` first, then a second query on related terms to resolve identifiers, then re-route.

## Round structure — Probe-then-Refine

**Do not author all queries upfront.** Round 1 surfaces named entities Round 2 needs.

**Round 1 — Probe** (2 queries):
- `Q-broad` — canonical phrasing of the topic (angle: `general`)
- `Q-narrow` — a specific mechanism / sub-question / method (angle: tagged)

From Round 1 rows, lift:
- recurring **named entities** (algorithm / benchmark / model names),
- **angle gaps** (rubric tags not seen),
- vocabulary from **adjacent communities**.

**Round 2 — Refine** (2–3 queries):

| Tier | Count | Shape |
|---|---|---|
| Method / mechanism | 1–2 | Sub-mechanism on an uncovered angle tag |
| Named-entity | 1 | Entity verbatim from Round 1 results + a modifier |

**Round 3 — Patch** (only if the saturation gate says CONTINUE). One targeted query on the remaining gap.

**Per-query rules:**
- 4–7 words typical (up to 9 OK); <3 over-recalls, >9 dilutes ranking.
- English or Chinese both work (cards match Chinese titles via titleCn).
- Bare entity names, no `paper` / `report`.
- No two queries in one round may share >60% of content tokens.
- Track queries across rounds; never re-run one verbatim.

## Step 1: Parse intent

State in one sentence: the **research object** (specific technique / concept) and the **constraints** (domain, task, recency, exclusions). Confirm the router branch.

## Step 2: Author the RUBRIC (via `think_tool`)

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

## Step 3: Search

Run the probe/refine queries above via `paper_search` (one call per query,
`limit` 8–15). Pool results by deduping on paperId across rounds.

## Step 4: Triage — PERFECT / GOOD / WEAK / IRREL

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

**Card upgrade** for borderline papers (card silent on a criterion): `paper_read` the paperId, and if a summary field still doesn't settle it, `paper_section` with a `query` aimed at the criterion phrase — quote from the returned section.

## Step 5: Saturation Gate

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

## Step 6: Rerank and Output

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

POINT: Paper Card (see `output-formats.md`).

**Pre-output checklist (mandatory):**

- [ ] **Pool gathered** from every Step-5 triage block across all rounds, deduped by `paperId`, IRREL excluded.
- [ ] **weighted_total computed** for every candidate.
- [ ] **Sorted** DESC by `weighted_total` → `year`.
- [ ] **Every Primary paper has ≥1 evidence quote per high-weight criterion** (quote-or-zero rule, Red Line 5).
- [ ] **Ranked output is Primary-only and ≤ K**.

If any box is unchecked, return to Step 6 — do not output.
