---
name: quant-paper-extractor
description: "Convert quantitative research report PDFs to markdown, then extract structured knowledge (paperId, title, year, source, keywords, tldr, abstract, strategy, method, experiment, result) into JSONL paper cards. Writes into the repo corpus (corpus/raw, corpus/markdown, corpus/cards) and refreshes context_brief.md + index.jsonl. Use when: adding quant research PDFs to the knowledge base, extracting structured data from reports. Do NOT use for: academic paper search (use paper-navigator), idea generation (use research-ideation), literature surveys (use research-survey)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: quant-research-team
  version: '1.0.0'
  tags: [quant, pdf-extraction, structured-data, jsonl, batch-processing]
---

# Quant Paper Extractor

Batch-convert quantitative research report PDFs (量化研究研报) to structured JSONL paper cards. Two-phase pipeline writing into the repo corpus:

```
corpus/raw/{paperId}.pdf
      │
      ▼ Phase 1: PDF → Markdown (pdf_to_markdown.py)
corpus/markdown/{paperId}.md
      │
      ▼ Phase 2: Markdown → card (agent-driven extraction)
corpus/cards/{paperId}.jsonl
      │
      ▼ Phase 3: refresh derived artifacts
corpus/context_brief.md + corpus/index.jsonl
```

## Setup

Scripts at `scripts/`. Run via `python scripts/<name>.py` from this skill's
directory. Dependencies: `pip install -e .`.

## Pre-conditions

The corpus lives at the repo root (`corpus/`; override with
`EVOSCIENTIST_CORPUS_DIR`). Resolve it once and reuse:

```bash
CORPUS=$(python -c "from EvoQuant.corpus.paths import resolve_corpus_dir; print(resolve_corpus_dir())")
```

Layout (all three layers share the paperId join key):

```
$CORPUS/raw/       ← PDFs, renamed to {paperId}.pdf (see Red Line 8)
$CORPUS/markdown/  ← auto-created; converted markdown
$CORPUS/cards/     ← auto-created; extracted JSONL cards
$CORPUS/manifest.jsonl  ← processing-state ledger
```

**Legacy layouts are dead.** `rawpaper/`, `markdown/`, `wiki/` in a
workspace are deprecated — if you meet them, point the user at
`python -m EvoQuant.corpus.migrate` instead of writing there.

`markdown/` is auto-created by Phase 1; create the cards dir up front:

```bash
mkdir -p "$CORPUS/cards"
```

## Phase 1: PDF → Markdown

Run the conversion script (fully automated, no LLM needed):

```bash
python scripts/pdf_to_markdown.py \
  --rawpaper-dir "$CORPUS/raw" \
  --markdown-dir "$CORPUS/markdown" \
  --manifest-path "$CORPUS/manifest.jsonl"
```

This script:
1. Scans all `.pdf` files in the raw dir (any filename — the hash is the identity)
2. Computes SHA-256 hash of each PDF's binary content → `paperId`
3. **Incremental skip**: if `markdown/{paperId}.md` already exists, skip
4. Extracts text via **three-tier fallback**:
   - `pymupdf4llm.to_markdown()` — native Markdown output (best quality)
   - `pymupdf.open()` → `page.get_text()` — plain text with page headers
   - `pypdf.PdfReader()` → `page.extract_text()` — last resort
5. Hard-truncates at 120,000 characters
6. Writes structured Markdown to `markdown/{paperId}.md`
7. Updates `manifest.jsonl` with status

Read the script's stdout for per-file success/failure reports.

## Phase 2: Markdown → JSONL

The agent (you) performs the extraction reasoning. The `extract.py` script prepares context and validates output.

### Step 2.1: List unextracted markdowns

```bash
python scripts/manifest.py list \
  --manifest-path "$CORPUS/manifest.jsonl" --status markdown_done
```

Also check `markdown_short` status files. For each file without a corresponding `cards/{paperId}.jsonl`:

### Step 2.2: Prepare extraction context

```bash
python scripts/extract.py prepare \
  --markdown-file "$CORPUS/markdown/{paperId}.md"
```

This outputs:
- `MODE: single-pass` or `MODE: two-pass`
- The markdown content (truncated to 120,000 chars)
- Section locator with heading tags (for two-pass mode)
- Field template from `assets/jsonl-record-template.json`

### Step 2.3: Extract fields (agent-driven)

Read the `prepare` output, then use `think_tool` to reason through the extraction following the rules below.

**Read `references/field-definitions.md`** for detailed field specs, word limits, and evidence rules.

**Read `references/quant-report-structure.md`** for section-heading heuristics and terminology glossary.

**For two-pass mode**, read `references/two-pass-extraction.md` for the detailed protocol:
- **Pass 1** (first ~8,000 chars): Extract `paperId`, `title`, `year`, `source`, `tldr`, `abstract`, `keywords`
- **Pass 2** (targeted sections via section locator): Extract `strategy`, `method`, `experiment`, `result`

### Step 2.4: Write the JSONL record

Write a single JSON line to `$CORPUS/cards/{paperId}.jsonl` via `write_file` (or `python -c` if write_file's sandbox can't reach the corpus root).

Each record must have exactly these 11 fields:

| Field | Type | Word Limit | Description |
|-------|------|-----------|-------------|
| paperId | str | N/A | SHA-256 of PDF binary content |
| title | str | ≤30 | title of the report |
| year | int | 4 digits | Publication year |
| source | str | ≤10 | Source organization |
| keywords | list[str] | 3-8 | Quant finance keywords from the document |
| tldr | str | ≤40 | One-sentence core finding |
| abstract | str | ≤150 | Concise summary: question + approach + conclusion. |
| strategy | str | ≤300 | Strategy description + evidence citation |
| method | str | ≤300 | Methodology + evidence citation |
| experiment | str | ≤300 | Experimental setup + evidence citation |
| result | str | ≤200 | Key metrics + evidence citation |

### Step 2.5: Validate

```bash
python scripts/extract.py validate \
  --record "$CORPUS/cards/{paperId}.jsonl"
```

If validation fails, fix the record and re-validate.

### Step 2.6: Update manifest

After successful validation, the manifest is updated automatically. Alternatively, rebuild from filesystem:

```bash
python scripts/manifest.py rebuild \
  --rawpaper-dir "$CORPUS/raw" \
  --markdown-dir "$CORPUS/markdown" \
  --wiki-dir "$CORPUS/cards" \
  --manifest-path "$CORPUS/manifest.jsonl"
```

## Phase 3: Refresh derived artifacts & verify

After all cards are written, refresh the derived index/brief so the runtime
tools see the new papers, then validate the whole cards directory:

```bash
python -m EvoQuant.corpus.refresh
python scripts/extract.py validate \
  --wiki-dir "$CORPUS/cards" --manifest-path "$CORPUS/manifest.jsonl"
```

`refresh` is a full recompute over cards/ (milliseconds) — cheap to run
after every card, and the derived files can never drift.

Then report:

```
Extraction complete:
  PDFs scanned:     N
  Markdown created: M (K skipped, already existed)
  JSONL created:    P (Q skipped, already existed)
  Errors:           E
  Warnings:         W (short markdown, empty fields, etc.)
```

## Red Lines (always)

1. **No fabrication.** Every extracted field must be grounded in the source text. If information is not explicitly found, return empty string. Do not infer.
2. **Shape check.** Every JSONL record must have exactly 11 fields, all present and non-null. Empty strings are allowed but flagged.
3. **Word limits.** Strictly enforced per field (see `references/field-definitions.md`).
4. **English only.** All output fields must be in English. Translate Chinese source text.
5. **Incremental.** Never re-process a PDF that already has a markdown file, or a markdown that already has a JSONL.
6. **Quote-or-zero.** The `strategy`, `method`, `experiment`, and `result` fields must each include at least one `[source: "..."]` inline evidence citation. No citation → flag warning.
7. **If information is not explicitly found, return empty string.** Do not infer.
8. **One join key.** After a PDF is processed, rename it in `$CORPUS/raw/` to `{paperId}.pdf` (the hash) — raw/, markdown/, cards/ must stay keyed identically. The original filename survives in manifest `sourcePdf`.
9. **Write only inside the corpus.** Never create `rawpaper/`, `markdown/`, or `wiki/` in a workspace — that layout is deprecated (see AGENT.md).

## Error Handling

Read `references/error-handling.md` for full details. Summary:

- PDF extraction fails → skip, status=`pdf_error`, continue
- Markdown too short (< 500 chars) → warn, attempt extraction, flag as likely incomplete
- Empty required field → retry once; if still empty, write `""`, flag in `_warnings`
- Validation failure → log errors, do not overwrite, let agent decide
- Partial failure → continue with next file, do not roll back

## References

| File | Read when |
|------|-----------|
| `references/field-definitions.md` | Understanding field types, word limits, and evidence rules |
| `references/quant-report-structure.md` | Understanding quant report structure and terminology |
| `references/two-pass-extraction.md` | Long document extraction protocol |
| `references/error-handling.md` | Failure modes and recovery |

## Assets

| File | Use |
|------|-----|
| `assets/jsonl-record-template.json` | Template for a single JSONL record |
| `assets/extraction-prompt.md` | Extraction rules and prompt template |

## Hand off to

| Goal | Skill |
|------|-------|
| Find academic papers | `paper-navigator` |
| Research ideation | `research-ideation` |
