# Two-Pass Extraction Protocol

For markdown documents exceeding 50,000 characters, use the two-pass extraction protocol. For shorter documents, use single-pass.

## When to Use

| Mode | Condition | Method |
|------|-----------|--------|
| **Single-pass** | Markdown ≤ 50,000 chars | Read entire document, extract all 11 fields |
| **Two-pass** | Markdown > 50,000 chars | Split into two targeted reads |

The mode is determined by `extract.py prepare`, which outputs `MODE: single-pass` or `MODE: two-pass`.

## Single-Pass Protocol

1. Agent reads the full markdown content (truncated to 120,000 chars by `extract.py`)
2. Agent fills all 11 fields in one pass using `think_tool` for structured reasoning
3. Agent writes the JSONL record via `write_file`
4. Agent validates with `extract.py validate`

## Two-Pass Protocol

### First Pass — Header Fields (~8,000 chars)

**Read:** First ~8,000 characters of the markdown.

**Rationale:** Cover page, executive summary, and abstract are always in the first few pages. At ~2,500–3,000 chars per page of extracted text, 8,000 chars covers the first 3 pages comfortably.

**Extract these fields:**
- `paperId` — already known from the filename
- `title` — from cover page or first heading
- `year` — from cover page date or footer
- `broker` — from cover page logo/header/footer
- `tldr` — from executive summary (核心观点/投资要点)
- `abstract` — from the summary/abstract section
- `keywords` — from document keywords or inferred from the summary

**Rules:**
- Translate Chinese to English
- If a field is not explicitly found, return empty string. Do not infer.
- Store partial results (these will be combined with second-pass results)

### Second Pass — Body Fields (targeted sections)

**Read:** The section locator output from `extract.py prepare` identifies section headings with their line numbers and category tags (STRATEGY, METHOD, EXPERIMENT, RESULT).

**Locate sections** using the heading heuristics from `references/quant-report-structure.md`:
- **strategy** → headings tagged `STRATEGY`
- **method** → headings tagged `METHOD`
- **experiment** → headings tagged `EXPERIMENT`
- **result** → headings tagged `RESULT`

**Extract these fields:**
- `strategy` — from the strategy section
- `method` — from the methodology section
- `experiment` — from the backtesting section
- `result` — from the results section

**If a section is not found:**
- Check adjacent sections (the report may use non-standard headings)
- Read the section before and after any matched heading for context
- If still not found, write `""` and flag in `_warnings`. Do not fabricate.

**Character budget:** Total input to the agent must not exceed 120,000 chars. If second-pass sections exceed 112,000 chars (leaving room for first-pass context), prioritize in order: **method > experiment > result > strategy** (method is hardest to reconstruct from summary alone).

**Evidence rule:** Each of the four body fields must include at least one inline evidence citation: `[source: "quoted or paraphrased text"]`.

### Assembly

1. Combine first-pass and second-pass results into the complete 11-field record
2. Write the JSONL file via `write_file`
3. Run `extract.py validate` to verify
4. Update manifest status

## Edge Cases

- **No section headings found:** The report may use non-standard formatting. Fall back to reading the full document with a character budget, extracting body fields from context.
- **Multiple sections of the same category:** Combine them into one field, with evidence from each section.
- **Sections in unexpected order:** Quant reports sometimes put results before methodology. Follow the content, not the order.
- **Very short sections (< 200 chars):** The section may be a heading only, with content in the next section. Read the following section as well.
