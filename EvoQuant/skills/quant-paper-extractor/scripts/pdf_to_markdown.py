#!/usr/bin/env python3
"""Convert PDFs in rawpaper/ to structured Markdown files in markdown/.

For each PDF:
  1. Compute SHA-256 hash of binary content → paperId
  2. Skip if markdown/{paperId}.md already exists (incremental)
  3. Extract text via three-tier fallback: pymupdf4llm → pymupdf → pypdf
  4. Write structured Markdown to markdown/{paperId}.md
  5. Update manifest.jsonl with status

Output Markdown format preserves page boundaries and tables, which is
critical for the two-pass extraction in Phase 2.

Usage:
  python pdf_to_markdown.py \\
    --rawpaper-dir rawpaper/ \\
    --markdown-dir markdown/ \\
    --manifest-path manifest.jsonl
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add scripts/ to path for manifest import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import append_entry, compute_paper_id, is_processed, make_entry

# ---------------------------------------------------------------------------
# Three-tier PDF extraction
# ---------------------------------------------------------------------------

MAX_CHARS = 120_000
MIN_CHARS = 500  # Below this, extraction likely failed


def _extract_pymupdf4llm(pdf_path: str) -> str | None:
    """Tier 1: pymupdf4llm — native Markdown output, best for LLM consumption."""
    try:
        import pymupdf4llm

        md_text = pymupdf4llm.to_markdown(pdf_path)
        if md_text and len(md_text.strip()) >= MIN_CHARS:
            return md_text
    except ImportError:
        print("  pymupdf4llm not available, trying next tier", file=sys.stderr)
    except Exception as e:
        print(f"  pymupdf4llm failed: {e}", file=sys.stderr)
    return None


def _extract_pymupdf(pdf_path: str) -> str | None:
    """Tier 2: pymupdf (fitz) — plain text with page headers."""
    try:
        import pymupdf

        doc = pymupdf.open(pdf_path)
        parts: list[str] = []
        parts.append(f"**Total Pages:** {len(doc.pages)}\n")
        for i, page in enumerate(doc.pages, start=1):
            text = page.get_text("text")
            if text and text.strip():
                parts.append(f"## Page {i}\n\n{text}")
            else:
                parts.append(f"## Page {i}\n\n*(No text content on this page)*")
        doc.close()
        result = "\n\n---\n\n".join(parts)
        if result and len(result.strip()) >= MIN_CHARS:
            return result
    except ImportError:
        print("  pymupdf not available, trying next tier", file=sys.stderr)
    except Exception as e:
        print(f"  pymupdf failed: {e}", file=sys.stderr)
    return None


def _extract_pypdf(pdf_path: str) -> str | None:
    """Tier 3: pypdf — last resort."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        parts: list[str] = []
        parts.append(f"**Total Pages:** {len(reader.pages)}\n")
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                parts.append(f"## Page {i}\n\n{text}")
            else:
                parts.append(f"## Page {i}\n\n*(No text content on this page)*")
        result = "\n\n---\n\n".join(parts)
        if result and len(result.strip()) >= MIN_CHARS:
            return result
    except ImportError:
        print("  pypdf not available", file=sys.stderr)
    except Exception as e:
        print(f"  pypdf failed: {e}", file=sys.stderr)
    return None


def extract_pdf(pdf_path: str) -> tuple[str, str]:
    """Try all three extraction tiers. Returns (markdown, tier_used).

    Falls through tiers until one succeeds. Returns ("", "none") if all fail.
    """
    for tier_name, extractor in [
        ("pymupdf4llm", _extract_pymupdf4llm),
        ("pymupdf", _extract_pymupdf),
        ("pypdf", _extract_pypdf),
    ]:
        result = extractor(pdf_path)
        if result:
            # Truncate if too long
            if len(result) > MAX_CHARS:
                result = (
                    result[:MAX_CHARS]
                    + f"\n\n---\n*[Truncated at {MAX_CHARS} characters]*"
                )
            return result, tier_name

    return "", "none"


# ---------------------------------------------------------------------------
# Table formatting (for pymupdf/pypdf tiers that don't handle tables natively)
# ---------------------------------------------------------------------------


def format_table_as_markdown(table: list[list]) -> str:
    """Format a table as Markdown pipe syntax."""
    if not table or not table[0]:
        return ""
    lines: list[str] = []
    header = table[0]
    lines.append("| " + " | ".join(str(cell) if cell else "" for cell in header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in table[1:]:
        lines.append(
            "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main conversion logic
# ---------------------------------------------------------------------------


def convert_pdf(
    pdf_path: str,
    markdown_dir: str,
    manifest_path: str,
    dry_run: bool = False,
) -> dict:
    """Convert a single PDF to markdown. Returns a status dict."""
    filename = os.path.basename(pdf_path)
    paper_id = compute_paper_id(pdf_path)
    md_path = os.path.join(markdown_dir, f"{paper_id}.md")

    # Check if already converted
    if is_processed(manifest_path, paper_id):
        return {"paperId": paper_id, "status": "skipped", "file": filename}

    if dry_run:
        return {"paperId": paper_id, "status": "dry_run", "file": filename}

    # Extract
    markdown_content, tier_used = extract_pdf(pdf_path)

    if not markdown_content:
        # All tiers failed
        entry = make_entry(
            paper_id,
            filename,
            status="pdf_error",
            error_message="All extraction tiers failed",
        )
        append_entry(manifest_path, entry)
        return {
            "paperId": paper_id,
            "status": "pdf_error",
            "file": filename,
            "error": "All extraction tiers failed",
        }

    # Add header
    full_md = f"# {filename}\n\n**Total Pages:** see content | **SHA-256:** `{paper_id}`\n\n---\n\n{markdown_content}"

    # Write
    os.makedirs(markdown_dir, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    # Determine status
    is_short = len(markdown_content) < MIN_CHARS
    status = "markdown_short" if is_short else "markdown_done"

    # Update manifest
    entry = make_entry(
        paper_id,
        filename,
        markdown_path=md_path,
        status=status,
        error_message="Markdown < 500 chars" if is_short else None,
    )
    append_entry(manifest_path, entry)

    return {
        "paperId": paper_id,
        "status": status,
        "file": filename,
        "tier": tier_used,
        "chars": len(markdown_content),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDFs in rawpaper/ to Markdown in markdown/"
    )
    parser.add_argument(
        "--rawpaper-dir", required=True, help="Directory containing PDF files"
    )
    parser.add_argument(
        "--markdown-dir", required=True, help="Output directory for Markdown files"
    )
    parser.add_argument("--manifest-path", required=True, help="Path to manifest.jsonl")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without converting",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed progress"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.rawpaper_dir):
        print(
            f"Error: rawpaper directory not found: {args.rawpaper_dir}", file=sys.stderr
        )
        sys.exit(1)

    os.makedirs(args.markdown_dir, exist_ok=True)

    # Scan for PDFs
    pdf_files = sorted(Path(args.rawpaper_dir).glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in rawpaper/", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF file(s) in {args.rawpaper_dir}/\n")

    # Process each PDF
    results = {"converted": 0, "skipped": 0, "short": 0, "error": 0}
    for pdf_file in pdf_files:
        result = convert_pdf(
            str(pdf_file), args.markdown_dir, args.manifest_path, args.dry_run
        )
        status = result["status"]
        if status == "skipped":
            results["skipped"] += 1
            if args.verbose:
                print(f"  SKIP  {result['file']} (already processed)")
        elif status == "pdf_error":
            results["error"] += 1
            print(f"  ERROR {result['file']} — {result.get('error', 'unknown')}")
        elif status == "markdown_short":
            results["short"] += 1
            print(
                f"  WARN  {result['file']} — markdown only {result['chars']} chars (tier: {result.get('tier', '?')})"
            )
        elif status == "dry_run":
            print(f"  DRY   {result['file']} → {result['paperId'][:12]}...")
        else:
            results["converted"] += 1
            print(
                f"  OK    {result['file']} → {result['paperId'][:12]}... ({result['chars']} chars, tier: {result.get('tier', '?')})"
            )

    # Summary
    print("\nConversion summary:")
    print(f"  Converted: {results['converted']}")
    print(f"  Skipped:   {results['skipped']}")
    print(f"  Short:     {results['short']}")
    print(f"  Errors:    {results['error']}")


if __name__ == "__main__":
    main()
