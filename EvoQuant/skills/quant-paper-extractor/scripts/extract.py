#!/usr/bin/env python3
"""Extract preparation and validation for quant-paper-extractor.

This script does NOT call an LLM. It:
  1. Prepares extraction context from a markdown file (prepare subcommand)
  2. Validates JSONL records against the field schema (validate subcommand)

The actual LLM extraction reasoning is performed by the Claude agent itself,
guided by the SKILL.md workflow and the extraction-prompt.md template.

Usage:
  # Prepare extraction context for a markdown file
  python scripts/extract.py prepare --markdown-file markdown/abc123.md [--max-chars 120000]

  # Validate a single JSONL record
  python scripts/extract.py validate --record wiki/abc123.jsonl

  # Validate all JSONL files in wiki/
  python scripts/extract.py validate --wiki-dir wiki/ --manifest-path manifest.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add scripts/ to path for manifest import
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SINGLE_PASS_THRESHOLD = 50_000  # chars
FIRST_PASS_CHARS = 8_000
MAX_CHARS_DEFAULT = 120_000
MIN_MD_CHARS = 500

# Field word limits
FIELD_LIMITS = {
    "title": 30,
    "source": 10,
    "tldr": 40,
    "abstract": 150,
    "strategy": 300,
    "method": 300,
    "experiment": 300,
    "result": 200,
}

REQUIRED_FIELDS = [
    "paperId",
    "title",
    "year",
    "source",
    "keywords",
    "tldr",
    "abstract",
    "strategy",
    "method",
    "experiment",
    "result",
]

# Section-heading patterns for quant research reports (Chinese + English)
SECTION_PATTERNS = {
    "strategy": re.compile(
        r"(策略|投资策略|组合构建|交易策略|信号构建|portfolio|signal.?construct)",
        re.IGNORECASE,
    ),
    "method": re.compile(
        r"(方法|模型|因子|因子构建|方法论|回归|机器学习|methodology|model|factor.?construct)",
        re.IGNORECASE,
    ),
    "experiment": re.compile(
        r"(回测|实证|数据|样本|样本区间|回测设计|backtest|empirical|data|sample)",
        re.IGNORECASE,
    ),
    "result": re.compile(
        r"(结果|表现|收益|超额|绩效|夏普|回撤|result|performance|return|drawdown)",
        re.IGNORECASE,
    ),
}

# Template path
TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "jsonl-record-template.json"
)


# ---------------------------------------------------------------------------
# Prepare mode
# ---------------------------------------------------------------------------


def prepare_context(markdown_file: str, max_chars: int = MAX_CHARS_DEFAULT) -> None:
    """Read a markdown file and output extraction context for the agent.

    Determines single-pass vs two-pass mode and outputs:
    - MODE indicator
    - Section locator (headings + line numbers for two-pass)
    - Content (truncated to max_chars)
    - Field template
    """
    with open(markdown_file, encoding="utf-8") as f:
        content = f.read()

    total_chars = len(content)
    paper_id = Path(markdown_file).stem

    # Determine mode
    if total_chars <= SINGLE_PASS_THRESHOLD:
        print("MODE: single-pass")
        print(f"PAPER_ID: {paper_id}")
        print(f"TOTAL_CHARS: {total_chars}")
        print()
        # Output full content (truncated)
        if total_chars > max_chars:
            content = (
                content[:max_chars]
                + f"\n\n---\n*[Truncated at {max_chars} characters]*"
            )
        print(content)
    else:
        print("MODE: two-pass")
        print(f"PAPER_ID: {paper_id}")
        print(f"TOTAL_CHARS: {total_chars}")
        print()

        # First pass: first 8,000 chars
        first_pass = content[:FIRST_PASS_CHARS]
        print("=== FIRST PASS (cover/summary) ===")
        print(first_pass)
        print()

        # Section locator: find headings that match quant report sections
        print("=== SECTION LOCATOR ===")
        lines = content.split("\n")
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            # Match markdown headings or plain-text section headings
            is_heading = (
                stripped.startswith("#")
                or re.match(r"^[一二三四五六七八九十]+[、.]", stripped)
                or re.match(r"^\d+[\.、]\s", stripped)
            )
            if is_heading:
                tags = []
                for category, pattern in SECTION_PATTERNS.items():
                    if pattern.search(stripped):
                        tags.append(category.upper())
                tag_str = f"  <-- {', '.join(tags)}" if tags else ""
                print(f"L {i:5d}: {stripped[:100]}{tag_str}")
        print()

        # Remaining content (truncated to budget)
        remaining_budget = (
            max_chars - FIRST_PASS_CHARS - 2000
        )  # leave room for locator output
        if remaining_budget > 0:
            remaining = content[FIRST_PASS_CHARS:]
            if len(remaining) > remaining_budget:
                remaining = remaining[:remaining_budget] + "\n\n---\n*[Truncated]*"
            print("=== REMAINING CONTENT ===")
            print(remaining)
        print()

    # Output field template
    print("=== FIELD TEMPLATE ===")
    template = load_template()
    if template:
        print(json.dumps(template, indent=2, ensure_ascii=False))
    else:
        # Fallback inline template
        print(
            json.dumps(
                {
                    "paperId": paper_id,
                    "title": "",
                    "year": 0,
                    "source": "",
                    "keywords": [],
                    "tldr": "",
                    "abstract": "",
                    "strategy": "",
                    "method": "",
                    "experiment": "",
                    "result": "",
                },
                indent=2,
                ensure_ascii=False,
            )
        )


def load_template() -> dict | None:
    """Load the JSONL record template from assets/."""
    try:
        with open(TEMPLATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Validate mode
# ---------------------------------------------------------------------------


def count_words(text: str) -> int:
    """Count words in a string (handles both English and Chinese)."""
    if not text:
        return 0
    # Chinese characters count as one word each
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    # Remove Chinese chars, then count English words
    english_text = re.sub(r"[一-鿿]", " ", text)
    english_words = len(english_text.split())
    return chinese_chars + english_words


def validate_record(record: dict, paper_id_from_filename: str = "") -> list[str]:
    """Validate a single JSONL record. Returns a list of error messages.

    An empty list means the record is valid.
    """
    errors: list[str] = []

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: {field}")
        elif record[field] is None:
            errors.append(f"Field is null: {field}")

    # 2. No extra fields (allow _warnings for metadata)
    extra = set(record.keys()) - set(REQUIRED_FIELDS) - {"_warnings"}
    if extra:
        errors.append(f"Unexpected fields: {extra}")

    # 3. paperId matches filename
    if paper_id_from_filename and record.get("paperId") != paper_id_from_filename:
        errors.append(
            f"paperId mismatch: record={record.get('paperId')}, filename={paper_id_from_filename}"
        )

    # 4. year is a 4-digit integer
    year = record.get("year")
    if year is not None:
        if not isinstance(year, int) or year < 1900 or year > 2100:
            errors.append(f"year must be a 4-digit integer, got: {year}")

    # 5. keywords is a list of 3-8 strings
    kw = record.get("keywords")
    if kw is not None:
        if not isinstance(kw, list):
            errors.append(f"keywords must be a list, got: {type(kw).__name__}")
        elif len(kw) < 3 or len(kw) > 8:
            errors.append(f"keywords must have 3-8 items, got {len(kw)}")

    # 6. Word limits
    for field, limit in FIELD_LIMITS.items():
        value = record.get(field, "")
        if isinstance(value, str) and value:
            wc = count_words(value)
            if wc > limit:
                errors.append(f"{field} exceeds word limit: {wc} > {limit}")

    # 7. Empty required field warnings (not errors, but worth flagging)
    for field in [
        "title",
        "source",
        "tldr",
        "abstract",
        "strategy",
        "method",
        "experiment",
        "result",
    ]:
        value = record.get(field)
        if value == "" or value == []:
            errors.append(f"WARNING: empty required field: {field}")

    return errors


def validate_single_record(record_path: str) -> bool:
    """Validate a single JSONL record file. Returns True if valid."""
    paper_id = Path(record_path).stem
    with open(record_path, encoding="utf-8") as f:
        line = f.readline().strip()
    if not line:
        print(f"ERROR: empty file {record_path}")
        return False

    try:
        record = json.loads(line)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {record_path}: {e}")
        return False

    errors = validate_record(record, paper_id)
    if errors:
        print(f"VALIDATION FAILED: {record_path}")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print(f"VALID: {record_path}")
        return True


def validate_all(wiki_dir: str, manifest_path: str = "") -> int:
    """Validate all JSONL files in wiki/. Returns count of invalid files."""
    if not os.path.isdir(wiki_dir):
        print(f"wiki directory not found: {wiki_dir}", file=sys.stderr)
        return 1

    jsonl_files = sorted(Path(wiki_dir).glob("*.jsonl"))
    if not jsonl_files:
        print("No JSONL files found in wiki/", file=sys.stderr)
        return 0

    valid = 0
    invalid = 0
    for jf in jsonl_files:
        if validate_single_record(str(jf)):
            valid += 1
        else:
            invalid += 1

    print(
        f"\nValidation summary: {valid} valid, {invalid} invalid out of {len(jsonl_files)} total"
    )
    return invalid


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Extract preparation and validation for quant-paper-extractor"
    )
    sub = parser.add_subparsers(dest="command")

    # prepare
    prep = sub.add_parser(
        "prepare", help="Prepare extraction context for a markdown file"
    )
    prep.add_argument(
        "--markdown-file", required=True, help="Path to the markdown file"
    )
    prep.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS_DEFAULT,
        help=f"Max characters to output (default {MAX_CHARS_DEFAULT})",
    )

    # validate
    val = sub.add_parser("validate", help="Validate JSONL records")
    val.add_argument("--record", help="Validate a single JSONL record file")
    val.add_argument("--wiki-dir", help="Validate all JSONL files in this directory")
    val.add_argument(
        "--manifest-path", default="", help="Manifest path (for status updates)"
    )

    args = parser.parse_args()

    if args.command == "prepare":
        if not os.path.exists(args.markdown_file):
            print(f"Error: file not found: {args.markdown_file}", file=sys.stderr)
            sys.exit(1)
        prepare_context(args.markdown_file, args.max_chars)

    elif args.command == "validate":
        if args.record:
            ok = validate_single_record(args.record)
            sys.exit(0 if ok else 1)
        elif args.wiki_dir:
            n_invalid = validate_all(args.wiki_dir, args.manifest_path)
            sys.exit(n_invalid)
        else:
            print("Error: specify --record or --wiki-dir", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
