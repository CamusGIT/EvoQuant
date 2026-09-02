"""The library system-prompt section: what the library holds, how to read it.

Injected ONCE at agent build time (static concatenation), not per-turn —
per-turn injection would sit after the volatile tail and kill the prompt
cache prefix (deepagents shares the cached prefix across turns).

Budget discipline: the whole section is capped at ~4.6K chars (brief ≤4K +
rules), asserted by tests — the system prompt already carries seven
sections before this one.
"""

from __future__ import annotations

from pathlib import Path

from .tools import _load_cards

#: Hard cap on the injected brief (chars).
BRIEF_MAX_CHARS = 4000

_RULES = """# Papers Library

A local library of quantitative research reports is mounted read-only at
/papers/ and exposed through three tools — this is the ONLY supported way
to consult it:

- paper_search(query) — one line per paper; find candidate paperIds first
- paper_read(paper_id) — the paper's card (tldr, abstract, per-topic
  summaries, section outline); one call per paper is enough
- paper_section(paper_id, heading) — one section verbatim, for quotes

Hard rules:
1. Search before you read: start from paper_search, never from ls /papers/.
2. One paper_read per paperId — re-reading a card you already have is a
   discipline error.
3. Direct reads of /papers/markdown/** and /papers/raw/** are rejected by
   design, not a malfunction — use paper_section for verbatim text.
4. Cite papers by the first 8+ chars of their paperId (plus title), so
   claims stay traceable to a card.

## Papers overview (context_brief)
"""


def _brief_from_cards(papers_dir: Path) -> str:
    """Regenerate a brief on the fly when context_brief.md is missing."""
    cards = _load_cards(papers_dir)
    if not cards:
        return ""
    cards = sorted(cards, key=lambda c: str(c.get("year", "")), reverse=True)
    lines = []
    for c in cards[:20]:
        tldr = str(c.get("tldr", "")).replace("\n", " ")[:200]
        lines.append(
            f"## {c.get('title', '(untitled)')} ({c.get('year', '?')}, "
            f"{c.get('source', '?')})\n- id: {str(c.get('paperId', ''))[:12]} — {tldr}"
        )
    if len(cards) > 20:
        lines.append(
            f"(+{len(cards) - 20} more — use paper_search to discover them)"
        )
    return "\n".join(lines)


def build_papers_prompt_section(papers_dir: str | Path | None) -> str:
    """Build the library prompt section; empty string when the library is absent.

    Prefers the curated ``context_brief.md``; falls back to a cards-derived
    brief (extraction may have outgrown the file). The brief is truncated
    at BRIEF_MAX_CHARS so the section stays a bounded add-on.
    """
    if not papers_dir:
        return ""
    root = Path(papers_dir)
    brief_path = root / "context_brief.md"
    brief = ""
    if brief_path.is_file():
        try:
            brief = brief_path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            brief = ""
    if not brief:
        brief = _brief_from_cards(root)
    if not brief:
        return ""
    if len(brief) > BRIEF_MAX_CHARS:
        brief = brief[:BRIEF_MAX_CHARS] + "\n...[brief truncated]"
    return _RULES + brief
