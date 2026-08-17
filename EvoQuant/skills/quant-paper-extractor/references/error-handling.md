# Error Handling

Graceful degradation rules adapted from AutoSci's /ingest error-handling philosophy: a partial result that preserves well-shaped data is more useful than a clean abort that leaves nothing.

## PDF Conversion Failures

| Failure | Action |
|---------|--------|
| All 3 extraction tiers fail (pymupdf4llm, pymupdf, pypdf) | Log error, set status=`pdf_error`, skip to next file. Do not create empty markdown. |
| PDF is encrypted/password-protected | Same as above. Log "encrypted PDF" as error message. |
| PDF contains only images (no text layer) | Mark as `pdf_error` with message "no text layer". Recommend OCR preprocessing. |
| Markdown output < 500 chars | Set status=`markdown_short`. Log warning. Still attempt extraction but flag as likely incomplete. |

## Extraction Failures

| Failure | Action |
|---------|--------|
| Empty required field after first attempt | Retry once with a more targeted extraction prompt. If still empty, write `""` and add `_warnings: ["empty_field: <fieldname>"]`. |
| No section headings found for a body field | Read the full document with character budget. If still not found, write `""` for that field. Do not fabricate. |
| JSONL validation fails after extraction | Set manifest status=`validation_failed`. Log the specific validation errors. The agent can re-extract manually. |
| If information is not explicitly found in the document | Return empty string. Do not infer. |

## Incremental Processing Errors

| Failure | Action |
|---------|--------|
| Manifest file corrupted or missing | Run `manifest.py rebuild` to reconstruct from filesystem state. |
| Markdown file exists but no JSONL | Re-extract from the existing markdown. No need to re-convert the PDF. |
| JSONL exists but validation fails | Do not overwrite automatically. Log the error and let the agent decide whether to re-extract. |
| SHA-256 collision (two different PDFs produce same hash) | Append `_2`, `_3` suffix to the second paperId. Set status=`collision_resolved`. This is extremely rare. |

## When to Stop vs. Continue

**Stop immediately:**
- No source can be read at all (all tiers fail)
- SHA-256 collision with a different source PDF (not just a duplicate)
- The markdown directory cannot be created (permissions error)

**Continue with warning:**
- One file fails extraction (skip it, process the rest)
- Markdown is short (< 500 chars) — extraction may be incomplete
- A single required field is empty after retry — flag it and continue
- A validation check fails on word limits — the data is still useful, just verbose

## Guiding Principle

> A partial extraction that preserves well-shaped data for some fields is more useful than a clean abort that leaves nothing. Empty fields can be filled later by re-extraction. Fabricated fields cannot be detected post-hoc.
