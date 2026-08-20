"""Build contexts.json for ``deepeval generate --method contexts``.

Deterministic curation — no chunking/embedding/retrieval/rerank. The corpus
is small and naturally grouped (one paper or one skill = one self-contained
topic), so each context is assembled by rule:

- One context per paper: the full wiki record (structured精华: title/year/
  source/keywords/tldr/abstract/strategy/method/experiment/result) plus the
  head of the parsed markdown (fuller content, capped so the generation LLM
  stays focused).
- One context per selected project doc / core skill SKILL.md.

Output: tests/evals/contexts.json — a list of contexts, each a list of text
chunks, matching deepeval's documented contexts-file shape:
    [["chunk 1", "chunk 2"], ["another context chunk"]]

Run from the repo root:
    uv run python tests/evals/build_contexts.py
"""

import json
import pathlib
import sys

EVAL_DIR = pathlib.Path(__file__).parent
REPO_ROOT = EVAL_DIR.parent.parent
WS = EVAL_DIR / "fixtures" / "workspace"

WIKI_FIELDS = (
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
)

# Core quant-pipeline skills + project docs. Deliberately excludes skills
# that depend on external services (nano-banana, paper-graph).
DOC_SOURCES = [
    ("project:readme", REPO_ROOT / "README.md"),
    ("project:docs", REPO_ROOT / "docs" / "README.md"),
    ("skill:quant-paper-extractor", REPO_ROOT / "EvoQuant" / "skills" / "quant-paper-extractor" / "SKILL.md"),
    ("skill:local-paper-navigator", REPO_ROOT / "EvoQuant" / "skills" / "local-paper-navigator" / "SKILL.md"),
    ("skill:research-ideation", REPO_ROOT / "EvoQuant" / "skills" / "research-ideation" / "SKILL.md"),
    ("skill:quant-experiment-runtime", REPO_ROOT / "EvoQuant" / "skills" / "quant-experiment-runtime" / "SKILL.md"),
    ("skill:research-survey", REPO_ROOT / "EvoQuant" / "skills" / "research-survey" / "SKILL.md"),
    ("skill:evomath-tao", REPO_ROOT / "EvoQuant" / "skills" / "evomath-tao" / "SKILL.md"),
]

MARKDOWN_HEAD_CHARS = 4000
SKILL_HEAD_CHARS = 6000


def _paper_contexts() -> list[list[str]]:
    manifest = [
        json.loads(line)
        for line in (WS / "manifest.jsonl").read_text().splitlines()
        if line.strip()
    ]
    contexts = []
    for row in manifest:
        wiki_path = WS / row["wikiPath"]
        records = [
            json.loads(line)
            for line in wiki_path.read_text().splitlines()
            if line.strip()
        ]
        chunks = []
        for rec in records:
            lines = [f"[wiki record | paperId {rec.get('paperId', '?')}]"]
            for field in WIKI_FIELDS:
                if rec.get(field):
                    lines.append(f"{field}: {rec[field]}")
            chunks.append("\n".join(lines))
        md_path = WS / row["markdownPath"]
        if md_path.exists():
            md = md_path.read_text(errors="replace")[:MARKDOWN_HEAD_CHARS]
            chunks.append(
                f"[parsed report head | {row['sourcePdf']}]\n{md}"
            )
        contexts.append(chunks)
    return contexts


def _doc_contexts() -> list[list[str]]:
    contexts = []
    for tag, path in DOC_SOURCES:
        if not path.exists():
            print(f"WARNING: missing doc source {path}", file=sys.stderr)
            continue
        text = path.read_text(errors="replace")
        if tag.startswith("skill:"):
            text = text[:SKILL_HEAD_CHARS]
        contexts.append([f"[{tag}]\n{text}"])
    return contexts


def main() -> None:
    contexts = _paper_contexts() + _doc_contexts()
    out = EVAL_DIR / "contexts.json"
    out.write_text(json.dumps(contexts, ensure_ascii=False, indent=1))
    print(
        f"wrote {out}: {len(contexts)} contexts "
        f"({sum(len(c) for c in contexts)} chunks)"
    )


if __name__ == "__main__":
    main()
