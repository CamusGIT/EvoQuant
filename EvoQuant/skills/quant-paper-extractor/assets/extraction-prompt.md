# Extraction Prompt Template

Use this template when extracting structured information from a quantitative research report markdown file. Follow the workflow defined in SKILL.md.

## Instructions

You are extracting structured information from a **quantitative research report** (量化研究研报) that has been converted from PDF to Markdown. Your output must be a single JSONL record with exactly 11 fields.

## Rules

1. **English only.** All output fields must be in English. Translate any Chinese source text using standard quantitative finance terminology (see `references/quant-report-structure.md` for terminology glossary).

2. **No fabrication.** If information is not explicitly found in the document, return empty string (`""`) or empty list (`[]`). Do not infer, guess, or fabricate any information.

3. **Evidence grounding.** For the four body fields (`strategy`, `method`, `experiment`, `result`), every factual claim must include an inline evidence citation in the format: `[source: "quoted or paraphrased text from document"]`. This is the "quote-or-zero" rule.

4. **Word limits.** Strictly enforced:
   - title: ≤ 30 words
   - source: ≤ 10 words
   - tldr: ≤ 40 words
   - abstract: ≤ 150 words
   - strategy: ≤ 300 words
   - method: ≤ 300 words
   - experiment: ≤ 300 words
   - result: ≤ 200 words

5. **Numeric evidence for result.** The `result` field must contain at least one specific numeric metric (return %, Sharpe ratio, drawdown %, etc.) that appears in the document.

6. **If information is not explicitly found, return empty string.** Do not infer.

## Extraction Process

### Single-pass (markdown ≤ 50,000 chars)
Read the entire document and extract all 11 fields.

### Two-pass (markdown > 50,000 chars)
- **Pass 1** (first ~8,000 chars): Extract `paperId`, `title`, `year`, `source`, `tldr`, `abstract`, `keywords`
- **Pass 2** (targeted sections): Extract `strategy`, `method`, `experiment`, `result`

## Output Format

Write a single JSON line to the wiki/ directory. Example:

```json
{"paperId":"a1b2c3d4...","title":"Factor Momentum in A-Share Market","year":2024,"source":"CITIC Securities","keywords":["factor momentum","A-share","alpha decay"],"tldr":"Factor momentum generates 15.2% annualized return with Sharpe 1.8 in A-share market from 2010-2024.","abstract":"This study investigates...","strategy":"Long-short factor momentum strategy... [source: \"构建多空组合\"]","method":"Cross-sectional regression... [source: \"采用排序法构建因子收益\"]","experiment":"Data: Wind database, 2010-2024... [source: \"回测区间2010年1月\"]","result":"Annualized return 15.2%, Sharpe 1.8, max drawdown 8.3%... [source: \"年化收益15.2%\"]"}
```

## Shape Check (before writing)

Before writing the JSONL record, verify:
- [ ] All 11 fields are present and non-null
- [ ] No extra fields (except `_warnings`)
- [ ] `paperId` matches the markdown filename stem
- [ ] `year` is a 4-digit integer
- [ ] `keywords` has 3–8 items
- [ ] Word limits are respected for all fields
- [ ] Body fields (`strategy`, `method`, `experiment`, `result`) each have at least one `[source: "..."]` citation
- [ ] `result` includes at least one numeric metric from the document
