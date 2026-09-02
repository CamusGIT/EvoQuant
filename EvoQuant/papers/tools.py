"""The paper reading funnel: paper_search / paper_read / paper_section.

These tools ARE the root interface. The ``/papers/`` backend exists to
block raw paths; these three tools are the designed path through the layers:

    paper_search   L3  one line per paper — find candidates, pick paperIds
    paper_read     L2  the full card + section outline — understand a paper
    paper_section  L1  one section verbatim — the only escape hatch into the
                      full text, capped at MAX_SECTION_CHARS

Everything is sized so a sane investigation stays in a few KB of context:
search rows are one-liners, cards are naturally ≤8K, sections are capped.

Scoring is inlined from ``skills/local-paper-navigator/scripts/local_search.py``
(FIELD_WEIGHTS) rather than imported — skill scripts run on ad-hoc sys.paths
and must stay decoupled from the package.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.tools import tool

from .paths import papers_are_available

#: Hard cap on search rows (AutoSci-style top-K constraint).
MAX_SEARCH_LIMIT = 15
#: Hard cap on a single section payload.
MAX_SECTION_CHARS = 16000
#: Shortest paperId prefix accepted for lookup.
MIN_PREFIX_CHARS = 8

# Field name -> weight for relevance scoring (navigator FIELD_WEIGHTS semantics).
# titleCn (the original Chinese title from the markdown, joined in from
# index.jsonl) carries the same weight as title — cards are English-dominant
# and Chinese queries would otherwise miss them entirely.
FIELD_WEIGHTS: dict[str, int] = {
    "title": 2,
    "titleCn": 2,
    "keywords": 2,
    "tldr": 1,
    "abstract": 1,
    "source": 1,
}

_CJK_RE = re.compile(r"[一-鿿]")
_MARK_NOISE_RE = re.compile(r"<mark>\d+</mark>\s*")


def _tokenize(text: str) -> set[str]:
    """Whitespace/punctuation tokens (len>1, lowercased) + CJK bigrams.

    The bigram channel is what makes Chinese queries work: "因子挖掘" and a
    card writing "因子 挖掘" share no whole token, but they share 因子/挖掘.
    """
    tokens = {t for t in re.sub(r"[^\w\s]", " ", text.lower()).split() if len(t) > 1}
    for chunk in re.split(r"[\s\W]+", text):
        if len(chunk) >= 2 and _CJK_RE.search(chunk):
            tokens.update(chunk[i : i + 2] for i in range(len(chunk) - 1))
    return tokens


def _score(record: dict, query_tokens: set[str]) -> float:
    """Weighted token-overlap score (navigator compute_score semantics)."""
    total = 0.0
    for field, weight in FIELD_WEIGHTS.items():
        value = record.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        elif not isinstance(value, str):
            value = str(value) if value else ""
        if value:
            total += len(query_tokens & _tokenize(value)) * weight
    return total


def _load_cards(papers_dir: Path) -> list[dict]:
    """Load one JSON record per cards/*.jsonl file (first non-empty line).

    The index's ``titleCn`` (original Chinese title) is joined in by paperId
    when present, so Chinese queries can find English-dominant cards.
    """
    cards: list[dict] = []
    for path in sorted((papers_dir / "cards").glob("*.jsonl")):
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if isinstance(record, dict):
                    cards.append(record)
                break  # card files are single-record; extras are ignored
        except (OSError, json.JSONDecodeError):
            continue

    title_cn: dict[str, str] = {}
    index_path = papers_dir / "index.jsonl"
    if index_path.is_file():
        try:
            for line in index_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict) and rec.get("titleCn") and rec.get("paperId"):
                    title_cn[str(rec["paperId"])] = str(rec["titleCn"])
        except OSError:
            pass
    if title_cn:
        for card in cards:
            cn = title_cn.get(str(card.get("paperId", "")))
            if cn:
                card.setdefault("titleCn", cn)
    return cards


def _normalize_paper_id(raw: str) -> str:
    """Strip route/file decorations users and agents tend to paste."""
    pid = raw.strip()
    for prefix in ("/papers/cards/", "papers/cards/", "/cards/", "cards/"):
        if pid.startswith(prefix):
            pid = pid[len(prefix) :]
    if pid.endswith(".jsonl") or pid.endswith(".md") or pid.endswith(".pdf"):
        pid = pid.rsplit(".", 1)[0]
    return pid.strip()


def _resolve_paper(papers_dir: Path, raw_id: str) -> tuple[dict, Path] | None | str:
    """Find a card by exact or ≥8-char prefix paperId.

    Returns ``(card, markdown_path)``, ``None`` (not found), or a string
    (ambiguous prefix, listing the candidates).
    """
    cards = _load_cards(papers_dir)
    pid = _normalize_paper_id(raw_id)
    if len(pid) < MIN_PREFIX_CHARS:
        return None
    exact = [c for c in cards if str(c.get("paperId", "")) == pid]
    if exact:
        return _with_markdown(papers_dir, exact[0])
    candidates = [c for c in cards if str(c.get("paperId", "")).startswith(pid)]
    if len(candidates) == 1:
        return _with_markdown(papers_dir, candidates[0])
    if len(candidates) > 1:
        listing = "\n".join(
            f"- {c['paperId'][:12]}  {c.get('title', '')[:60]}" for c in candidates[:5]
        )
        return (
            f"paperId prefix {pid!r} is ambiguous ({len(candidates)} matches). "
            f"Use a longer prefix:\n{listing}"
        )
    return None


def _with_markdown(papers_dir: Path, card: dict) -> tuple[dict, Path]:
    md = papers_dir / "markdown" / f"{card.get('paperId', '')}.md"
    return card, md if md.is_file() else papers_dir / "markdown" / "nonexistent.md"


def _split_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Split markdown on ``### `` headings; drop <mark>page-noise lines."""
    cleaned = _MARK_NOISE_RE.sub("", markdown_text)
    parts = re.split(r"^### +(.+?)\s*$", cleaned, flags=re.M)
    # re.split with one group yields [pre, h1, body1, h2, body2, ...]
    sections: list[tuple[str, str]] = []
    for i in range(1, len(parts) - 1, 2):
        sections.append((parts[i].strip(), parts[i + 1]))
    return sections


def _pick_section(sections: list[tuple[str, str]], heading: str | None, query: str | None):
    """heading match first; else best query-overlap section; else None."""
    if heading:
        wanted = heading.strip().strip("*").lower()
        for title, body in sections:
            if wanted and wanted in title.lower():
                return title, body
        return None
    if query:
        q = _tokenize(query)
        best, best_score = None, -1.0
        for title, body in sections:
            s = len(q & _tokenize(title + " " + body[:2000]))
            if s > best_score:
                best, best_score = (title, body), s
        if best is not None and best_score > 0:
            return best
    return None


def build_paper_tools(papers_dir: str | Path | None) -> list:
    """Build the paper tools bound to ``papers_dir``.

    Returns an empty list when the root is absent — never mount dead
    tools that error on every call; the agent should not even see them.
    """
    if not papers_dir or not papers_are_available(papers_dir):
        return []
    root = Path(papers_dir)
    # Per-tool-instance result cache: an identical (query, limit) asked again
    # returns the stored answer with a [cache] marker instead of rescoring —
    # repeated identical searches are the top retrieval-discipline waste.
    # Lives in this closure (not module level) so each build gets fresh
    # state and tests stay independent.
    _search_cache: dict[tuple[str, int], str] = {}

    @tool(parse_docstring=True)
    def paper_search(query: str, limit: int = 8) -> str:
        """Search the local paper root by keywords; one line per paper.

        Returns up to `limit` papers (max 15), each as one line:
        paperId-prefix | year | source | score | title | tldr. Use it to
        find paperIds, then paper_read for the ones that matter. This is a
        card-level index search — it does not search full texts.

        Args:
            query: Space-separated keywords (Chinese or English), e.g.
                "GFlowNet 因子挖掘".
            limit: Max rows to return (1-15, default 8).

        Returns:
            Ranked one-line-per-paper listing, or an honest "no match"
            message when nothing scores above zero.
        """
        limit = max(1, min(int(limit), MAX_SEARCH_LIMIT))
        key = (query.strip().lower(), limit)
        if key in _search_cache:
            return (
                _search_cache[key]
                + "\n[cache] identical query already answered above — "
                "reuse this result instead of searching again."
            )
        cards = _load_cards(root)
        q = _tokenize(query)
        scored = sorted(
            ((c, _score(c, q)) for c in cards),
            key=lambda pair: (-pair[1], str(pair[0].get("year", ""))),
        )
        hits = [(c, s) for c, s in scored if s > 0][:limit]

        header = f"# paper_search '{query}' -> {len(hits)}/{len(cards)} papers"
        if not hits:
            keywords = sorted(
                {k for c in cards for k in (c.get("keywords") or [])}
            )[:15]
            kw_hint = f"Known keywords include: {', '.join(keywords)}." if keywords else ""
            result = (
                f"{header}\nno match. The root may genuinely not cover this "
                f"topic — say so rather than inventing content. Try broader "
                f"terms, or read /papers/context_brief.md for what exists. {kw_hint}"
            )
        else:
            rows = []
            for c, s in hits:
                tldr = str(c.get("tldr", "")).replace("\n", " ")[:200]
                rows.append(
                    f"{str(c.get('paperId', ''))[:12]} | {c.get('year', '?')} | "
                    f"{c.get('source', '?')} | {s:.0f} | {c.get('title', '?')} | {tldr}"
                )
            result = header + "\n" + "\n".join(rows)
        _search_cache[key] = result
        return result

    @tool(parse_docstring=True)
    def paper_read(paper_id: str) -> str:
        """Read a paper's card: distilled fields + section outline.

        One call is enough to understand a paper: title/year/source,
        keywords, tldr, abstract and the five summary fields, plus an
        outline of the full text (section titles with sizes). Reading this
        twice for the same paperId is a discipline error.

        Args:
            paper_id: paperId from paper_search (an 8+ char prefix works).

        Returns:
            The formatted card and section outline, with a pointer to
            paper_section for verbatim quotes.
        """
        found = _resolve_paper(root, paper_id)
        if isinstance(found, str):
            return found
        if found is None:
            return (
                f"paperId {paper_id!r} not found. Run paper_search first; "
                "the index at /papers/index.jsonl lists every paperId."
            )
        card, md_path = found

        lines = [
            f"# {card.get('title', '(untitled)')}",
            f"id: {card.get('paperId', '')[:24]} | year: {card.get('year', '?')} "
            f"| source: {card.get('source', '?')}",
            f"keywords: {', '.join(str(k) for k in (card.get('keywords') or []))}",
            f"tldr: {card.get('tldr', '')}",
        ]
        for field in ("abstract", "strategy", "method", "experiment", "result"):
            value = card.get(field)
            if value:
                text = str(value).replace("\n", " ")
                lines.append(f"\n## {field}\n{text}")
        lines.append("\n## Sections")
        if md_path.is_file():
            try:
                sections = _split_sections(md_path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                sections = []
            for i, (title, body) in enumerate(sections, 1):
                lines.append(f"{i}. {title} ({len(body)} chars)")
        else:
            lines.append("(full text not available for this paper)")
        lines.append(
            "\nFull text is not bulk-readable by design. For verbatim "
            "content use paper_section(paper_id, heading)."
        )
        return "\n".join(lines)

    @tool(parse_docstring=True)
    def paper_section(
        paper_id: str,
        heading: str | None = None,
        query: str | None = None,
        max_chars: int = 8000,
    ) -> str:
        """Read ONE section of a paper's full text, verbatim.

        The escape hatch into full texts: pass a heading (substring match,
        e.g. "风险提示") or a query (picks the best-matching section).
        Whole-paper reads are blocked — this is the designed way to quote.

        Args:
            paper_id: paperId from paper_search/paper_read (8+ char prefix ok).
            heading: Section title substring to read exactly that section.
            query: Keywords; the best-matching section is returned.
            max_chars: Cap on returned chars (1-16000, default 8000).
        """
        max_chars = max(1, min(int(max_chars), MAX_SECTION_CHARS))
        found = _resolve_paper(root, paper_id)
        if isinstance(found, str):
            return found
        if found is None:
            return f"paperId {paper_id!r} not found. Run paper_search first."
        card, md_path = found
        if not md_path.is_file():
            return (
                f"No full text for {card.get('paperId', '')[:12]}; the card "
                "carries the distilled content (paper_read)."
            )
        try:
            sections = _split_sections(md_path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            return f"Could not read full text: {exc}"
        if not sections:
            return "Full text has no '### ' sections to slice."

        picked = _pick_section(sections, heading, query)
        if picked is None:
            titles = "\n".join(f"- {t}" for t, _ in sections)
            hint = (
                f"No section matches heading {heading!r}."
                if heading
                else "Provide a heading or a query."
            )
            return f"{hint} Available sections:\n{titles}"
        title, body = picked
        body = body.strip()
        if len(body) > max_chars:
            body = body[:max_chars] + f"\n...[truncated, {len(body) - max_chars} chars omitted]"
        return f"### {title} ({len(body)} chars)\n\n{body}"

    return [paper_search, paper_read, paper_section]
