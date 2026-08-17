---
name: quant-paper-extractor
description: "Convert quantitative research report PDFs to markdown, then extract structured knowledge (paperId, title, year, source, keywords, tldr, abstract, strategy, method, experiment, result) into JSONL files. Use when: processing quant research PDFs, building a quant knowledge base, extracting structured data from reports, or dropping PDFs into rawpaper/. Do NOT use for: academic paper search (use paper-navigator), idea generation (use research-ideation), literature surveys (use research-survey)."
allowed-tools: "write_file edit_file read_file think_tool execute"
metadata:
  author: quant-research-team
  version: '1.0.0'
  tags: [quant, pdf-extraction, structured-data, jsonl, batch-processing]
---

# Quant Paper Extractor

Batch-convert quantitative research report PDFs (量化研究研报) to structured JSONL records. Two-phase pipeline: PDF → Markdown → JSONL.

```
rawpaper/*.pdf
      │
      ▼ Phase 1: PDF → Markdown (pdf_to_markdown.py)
markdown/{sha256}.md
      │
      ▼ Phase 2: Markdown → JSONL (agent-driven extraction)
wiki/{sha256}.jsonl
```

## Setup

Scripts at `scripts/`. Run via `python scripts/<name>.py`.

Install dependencies:

```bash
pip install -e .
```

## Pre-conditions

Working directory must contain these sibling directories:

```
rawpaper/    ← user places PDF files here
markdown/    ← auto-created; stores converted markdown files
wiki/        ← auto-created; stores extracted JSONL files
```

Create `markdown/` and `wiki/` if they don't exist:

```bash
mkdir -p markdown/ wiki/
```

A `manifest.jsonl` file will be created at the working directory root to track processing state.

## Phase 1: PDF → Markdown

Run the conversion script (fully automated, no LLM needed):

```bash
python scripts/pdf_to_markdown.py \
  --rawpaper-dir rawpaper/ \
  --markdown-dir markdown/ \
  --manifest-path manifest.jsonl
```

This script:
1. Scans all `.pdf` files in `rawpaper/`
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
  --manifest-path manifest.jsonl --status markdown_done
```

Also check `markdown_short` status files. For each file without a corresponding `wiki/{paperId}.jsonl`:

### Step 2.2: Prepare extraction context

```bash
python scripts/extract.py prepare \
  --markdown-file markdown/{paperId}.md
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

Write a single JSON line to `wiki/{paperId}.jsonl` via `write_file`.

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
  --record wiki/{paperId}.jsonl
```

If validation fails, fix the record and re-validate.

### Step 2.6: Update manifest

After successful validation, the manifest is updated automatically. Alternatively, rebuild from filesystem:

```bash
python scripts/manifest.py rebuild \
  --rawpaper-dir rawpaper/ \
  --markdown-dir markdown/ \
  --wiki-dir wiki/ \
  --manifest-path manifest.jsonl
```

## Phase 3: Verify & Report

After all files are processed, validate the entire wiki directory:

```bash
python scripts/extract.py validate \
  --wiki-dir wiki/ --manifest-path manifest.jsonl
```

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
