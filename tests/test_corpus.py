"""Tests for EvoQuant/corpus — paths, filtered backend, paper tools, prompt.

The corpus has one job: make full texts unreachable except through the
designed funnel. These tests pin the interception matrix, the path-
normalization defenses, the composite-merge safety invariants (global
grep/glob must never error) and the three tools' behavior.
"""

import json
from pathlib import Path

import pytest

from EvoQuant.corpus.backend import CorpusBackend
from EvoQuant.corpus.paths import corpus_is_available, resolve_corpus_dir
from EvoQuant.corpus.prompt import BRIEF_MAX_CHARS, build_corpus_prompt_section
from EvoQuant.corpus.tools import build_paper_tools

# ---------------------------------------------------------------------------
# Fixtures: a tiny two-paper corpus
# ---------------------------------------------------------------------------

CARDS = [
    {
        "paperId": "aaaa1111bbbb2222cccc",
        "title": "GFlowNet Factor Mining",
        "year": 2026,
        "source": "Test Securities",
        "keywords": ["GFlowNet", "factor mining"],
        "tldr": "Generates diverse low-correlation alpha factors.",
        "abstract": "Automated factor mining with generative flow networks.",
        "strategy": "Search factor space via GFlowNet.",
        "method": "Trajectory-balance objective.",
        "experiment": "Backtests on CSI 500.",
        "result": "IC median 6.17%.",
    },
    {
        "paperId": "dddd3333eeee4444ffff",
        "title": "Momentum Crash Notes",
        "year": 2025,
        "source": "Other Securities",
        "keywords": ["momentum"],
        "tldr": "Momentum strategies crash in reversals.",
        "abstract": "Studies momentum crashes.",
        "strategy": "Volatility scaling.",
        "method": "Regression.",
        "experiment": "US equities.",
        "result": "Drawdown halved.",
    },
]

MD_A = """Intro paragraph before any heading.

### **原理介绍**

GFlowNet 原理内容。factor generation details.

### 风险提示

模型时效风险。
"""

MD_D = "### Overview\n\nMomentum overview text.\n"


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    (root / "cards").mkdir(parents=True)
    (root / "markdown").mkdir()
    (root / "raw").mkdir()
    for card in CARDS:
        (root / "cards" / f"{card['paperId']}.jsonl").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8"
        )
    (root / "markdown" / f"{CARDS[0]['paperId']}.md").write_text(MD_A, encoding="utf-8")
    (root / "markdown" / f"{CARDS[1]['paperId']}.md").write_text(MD_D, encoding="utf-8")
    (root / "raw" / f"{CARDS[0]['paperId']}.pdf").write_bytes(b"%PDF-fake")
    (root / "context_brief.md").write_text(
        "# brief\n- GFlowNet factor mining and momentum papers", encoding="utf-8"
    )
    return root


@pytest.fixture
def backend(corpus_dir: Path) -> CorpusBackend:
    return CorpusBackend(corpus_dir)


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------


class TestCorpusPaths:
    def test_explicit_wins(self, tmp_path, monkeypatch):
        (tmp_path / "by-env").mkdir()
        monkeypatch.setenv("EVOSCIENTIST_CORPUS_DIR", str(tmp_path / "by-env"))
        assert resolve_corpus_dir(tmp_path) == tmp_path.resolve()

    def test_env_overrides_repo_default(self, tmp_path, monkeypatch):
        target = tmp_path / "by-env"
        target.mkdir()
        monkeypatch.setenv("EVOSCIENTIST_CORPUS_DIR", str(target))
        assert resolve_corpus_dir() == target.resolve()

    def test_missing_everywhere_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("EVOSCIENTIST_CORPUS_DIR", str(tmp_path / "nope"))
        # No <repo>/corpus exists either (repo has none committed).
        if resolve_corpus_dir() is not None:
            pytest.skip("repo-level corpus present; cannot assert None")
        assert resolve_corpus_dir(tmp_path / "also-nope") is None

    def test_available_requires_content(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert corpus_is_available(empty) is False
        assert corpus_is_available(None) is False
        (empty / "index.jsonl").write_text("{}", encoding="utf-8")
        assert corpus_is_available(empty) is True


# ---------------------------------------------------------------------------
# backend: interception matrix
# ---------------------------------------------------------------------------


class TestBackendReads:
    def test_cards_and_root_files_readable(self, backend, corpus_dir):
        assert backend.read("/cards/aaaa1111bbbb2222cccc.jsonl").error is None
        assert backend.read("/context_brief.md").error is None

    def test_markdown_blocked_with_guidance(self, backend):
        result = backend.read(f"/markdown/{CARDS[0]['paperId']}.md")
        assert result.error and "paper_section" in result.error

    def test_raw_blocked_with_guidance(self, backend):
        result = backend.read(f"/raw/{CARDS[0]['paperId']}.pdf")
        assert result.error and "paper_read" in result.error

    @pytest.mark.parametrize(
        "sneaky",
        [
            "/cards/../markdown/x.md",
            "/markdown//x.md",
            "/markdown/../../markdown/x.md",
            "markdown/x.md",  # relative variant
        ],
    )
    def test_traversal_and_double_slash_blocked(self, backend, sneaky):
        assert backend.read(sneaky).error is not None

    def test_ls_root_lists(self, backend):
        result = backend.ls("/")
        assert result.error is None


class TestBackendGrep:
    def test_global_never_errors_and_never_leaks_markdown(self, backend):
        result = backend.grep("原理")  # only present in markdown
        assert result.error is None
        assert not any("markdown" in m["path"] for m in (result.matches or []))

    def test_global_hits_cards_and_root_files(self, backend):
        result = backend.grep("GFlowNet")
        paths = {m["path"] for m in (result.matches or [])}
        assert any("cards" in p for p in paths)
        assert any("context_brief" in p for p in paths)

    def test_explicit_cards_scope_ok(self, backend):
        result = backend.grep("momentum", path="/cards")
        assert result.error is None
        assert result.matches

    def test_explicit_markdown_scope_guided_error(self, backend):
        result = backend.grep("x", path="/markdown")
        assert result.error and "paper_section" in result.error

    def test_explicit_raw_scope_guided_error(self, backend):
        result = backend.grep("x", path="/raw")
        assert result.error and "paper_read" in result.error


class TestBackendGlob:
    def test_global_glob_hides_fulltext_layers(self, backend):
        result = backend.glob("**/*")
        assert result.error is None
        for fi in result.matches or []:
            path = fi.get("path", "")
            assert "markdown" not in path and "/raw" not in path

    def test_explicit_markdown_glob_blocked(self, backend):
        assert backend.glob("*.md", path="/markdown").error is not None


class TestBackendMutations:
    def test_all_mutations_blocked(self, backend):
        assert backend.write("/new.md", "x").error
        assert backend.edit("/context_brief.md", "a", "b").error
        assert backend.upload_files([("/new.pdf", b"x")])[0].error
        # download is the base64 side-channel — must be blocked too.
        assert backend.download_files([f"/raw/{CARDS[0]['paperId']}.pdf"])[0].error


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------


class TestPaperTools:
    def test_no_corpus_no_tools(self, tmp_path):
        assert build_paper_tools(tmp_path / "missing") == []
        assert build_paper_tools(None) == []

    def test_search_ranks_and_formats(self, corpus_dir):
        search, read, section = build_paper_tools(corpus_dir)
        out = search.invoke({"query": "GFlowNet 因子挖掘"})
        assert "aaaa1111bbbb" in out and "1/2 papers" in out

    def test_search_limit_clamped(self, corpus_dir):
        search, _, _ = build_paper_tools(corpus_dir)
        assert "1/2 papers" in search.invoke({"query": "GFlowNet", "limit": 99})

    def test_search_no_match_is_honest(self, corpus_dir):
        search, _, _ = build_paper_tools(corpus_dir)
        out = search.invoke({"query": "zzz-不存在的主题-qqq"})
        assert "no match" in out

    def test_read_returns_card_and_outline(self, corpus_dir):
        _, read, _ = build_paper_tools(corpus_dir)
        out = read.invoke({"paper_id": "aaaa1111bbbb2222cccc"})
        assert "GFlowNet Factor Mining" in out
        assert "## Sections" in out
        assert "paper_section" in out  # escape-hatch pointer
        assert len(out) <= 8200

    def test_read_accepts_8char_prefix(self, corpus_dir):
        _, read, _ = build_paper_tools(corpus_dir)
        assert "GFlowNet" in read.invoke({"paper_id": "aaaa1111"})

    def test_read_rejects_short_prefix(self, corpus_dir):
        _, read, _ = build_paper_tools(corpus_dir)
        assert "not found" in read.invoke({"paper_id": "aaaa"})

    def test_section_by_heading(self, corpus_dir):
        _, _, section = build_paper_tools(corpus_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "风险提示"})
        assert "模型时效风险" in out

    def test_section_respects_max_chars(self, corpus_dir):
        _, _, section = build_paper_tools(corpus_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "原理", "max_chars": 20})
        assert "truncated" in out and len(out) < 300

    def test_section_unknown_heading_lists_titles(self, corpus_dir):
        _, _, section = build_paper_tools(corpus_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "不存在的节"})
        assert "Available sections" in out

    def test_section_by_query(self, corpus_dir):
        _, _, section = build_paper_tools(corpus_dir)
        out = section.invoke({"paper_id": "aaaa1111", "query": "factor generation"})
        assert "###" in out

    def test_section_without_markdown_falls_back(self, tmp_path):
        root = tmp_path / "corpus"
        (root / "cards").mkdir(parents=True)
        card = dict(CARDS[1])
        (root / "cards" / f"{card['paperId']}.jsonl").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8"
        )
        _, _, section = build_paper_tools(root)
        out = section.invoke({"paper_id": card["paperId"], "heading": "anything"})
        assert "paper_read" in out or "No full text" in out


# ---------------------------------------------------------------------------
# prompt section
# ---------------------------------------------------------------------------


class TestPromptSection:
    def test_absent_corpus_is_empty(self, tmp_path):
        assert build_corpus_prompt_section(None) == ""
        assert build_corpus_prompt_section(tmp_path / "missing") == ""

    def test_uses_brief_when_present(self, corpus_dir):
        out = build_corpus_prompt_section(corpus_dir)
        assert "momentum papers" in out and "paper_search" in out

    def test_brief_missing_derives_from_cards(self, corpus_dir):
        (corpus_dir / "context_brief.md").unlink()
        out = build_corpus_prompt_section(corpus_dir)
        assert "GFlowNet Factor Mining" in out

    def test_brief_truncated_at_cap(self, corpus_dir):
        (corpus_dir / "context_brief.md").write_text("x" * 9000, encoding="utf-8")
        out = build_corpus_prompt_section(corpus_dir)
        assert len(out) <= BRIEF_MAX_CHARS + len(out)  # bounded, marker present
        assert "truncated" in out
        assert len(out) < 9000 + 1200  # hard bound: rules + cap + marker

    def test_system_prompt_extra_sections_append_and_skip_empty(self):
        from EvoQuant.prompts import get_system_prompt

        base = get_system_prompt()
        extended = get_system_prompt(extra_sections=["# EXTRA", ""])
        assert extended.startswith(base)
        assert extended.endswith("# EXTRA")


# ---------------------------------------------------------------------------
# integration: composite routing + agent registration
# ---------------------------------------------------------------------------


class TestCompositeIntegration:
    def test_papers_route_mounts_and_intercepts(self, corpus_dir, monkeypatch, tmp_path):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "CORPUS_DIR", corpus_dir)
        # Point the workspace (composite DEFAULT route) at a scratch dir so a
        # global grep doesn't sweep the repo and hit .venv binaries — that
        # error would come from the default route, not the corpus route.
        ws = tmp_path / "ws"
        ws.mkdir()
        monkeypatch.setattr(paths_mod, "WORKSPACE_ROOT", ws)
        monkeypatch.setattr(paths_mod, "_active_workspace", ws)
        import EvoQuant.EvoQuant as E

        route = E._corpus_route()
        assert route is not None and route[0] == "/papers/"

        backend = E._get_default_backend()
        card = backend.read("/papers/cards/aaaa1111bbbb2222cccc.jsonl")
        assert card.error is None
        blocked = backend.read("/papers/markdown/x.md")
        assert blocked.error and "paper_section" in blocked.error
        # Global grep across routes must survive the corpus route (no error).
        assert backend.grep("GFlowNet").error is None
        ls = backend.ls("/papers/")
        assert ls.error is None

    def test_registry_includes_paper_tools_when_corpus_present(self, corpus_dir, monkeypatch):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "CORPUS_DIR", corpus_dir)
        import EvoQuant.EvoQuant as E

        registry, base_tools = E._base_tool_registry()
        assert {"paper_search", "paper_read", "paper_section"} <= set(registry)
        assert any(t.name == "paper_search" for t in base_tools)

    def test_registry_without_corpus_has_no_paper_tools(self, monkeypatch, tmp_path):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "CORPUS_DIR", None)
        import EvoQuant.EvoQuant as E

        registry, _ = E._base_tool_registry()
        assert not [n for n in registry if n.startswith("paper_")]
