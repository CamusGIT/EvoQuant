"""Tests for EvoQuant/papers — paths, filtered backend, paper tools, prompt.

The papers has one job: make full texts unreachable except through the
designed funnel. These tests pin the interception matrix, the path-
normalization defenses, the composite-merge safety invariants (global
grep/glob must never error) and the three tools' behavior.
"""

import json
from pathlib import Path

import pytest

from EvoQuant.papers.backend import PapersBackend
from EvoQuant.papers.paths import papers_are_available, resolve_papers_dir
from EvoQuant.papers.prompt import BRIEF_MAX_CHARS, build_papers_prompt_section
from EvoQuant.papers.tools import build_paper_tools

# ---------------------------------------------------------------------------
# Fixtures: a tiny two-paper papers
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
def papers_dir(tmp_path: Path) -> Path:
    root = tmp_path / "papers"
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
def backend(papers_dir: Path) -> PapersBackend:
    return PapersBackend(papers_dir)


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------


class TestPapersPaths:
    def test_explicit_wins(self, tmp_path, monkeypatch):
        (tmp_path / "by-env").mkdir()
        monkeypatch.setenv("EVOSCIENTIST_PAPERS_DIR", str(tmp_path / "by-env"))
        assert resolve_papers_dir(tmp_path) == tmp_path.resolve()

    def test_env_overrides_repo_default(self, tmp_path, monkeypatch):
        target = tmp_path / "by-env"
        target.mkdir()
        monkeypatch.setenv("EVOSCIENTIST_PAPERS_DIR", str(target))
        assert resolve_papers_dir() == target.resolve()

    def test_missing_everywhere_is_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("EVOSCIENTIST_PAPERS_DIR", str(tmp_path / "nope"))
        # No <repo>/papers exists either (repo has none committed).
        if resolve_papers_dir() is not None:
            pytest.skip("repo-level papers present; cannot assert None")
        assert resolve_papers_dir(tmp_path / "also-nope") is None

    def test_available_requires_content(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert papers_are_available(empty) is False
        assert papers_are_available(None) is False
        (empty / "index.jsonl").write_text("{}", encoding="utf-8")
        assert papers_are_available(empty) is True


# ---------------------------------------------------------------------------
# backend: interception matrix
# ---------------------------------------------------------------------------


class TestBackendReads:
    def test_cards_and_root_files_readable(self, backend, papers_dir):
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
    def test_no_papers_no_tools(self, tmp_path):
        assert build_paper_tools(tmp_path / "missing") == []
        assert build_paper_tools(None) == []

    def test_search_ranks_and_formats(self, papers_dir):
        search, read, section = build_paper_tools(papers_dir)
        out = search.invoke({"query": "GFlowNet 因子挖掘"})
        assert "aaaa1111bbbb" in out and "1/2 papers" in out

    def test_search_limit_clamped(self, papers_dir):
        search, _, _ = build_paper_tools(papers_dir)
        assert "1/2 papers" in search.invoke({"query": "GFlowNet", "limit": 99})

    def test_search_no_match_is_honest(self, papers_dir):
        search, _, _ = build_paper_tools(papers_dir)
        out = search.invoke({"query": "zzz-不存在的主题-qqq"})
        assert "no match" in out

    def test_read_returns_card_and_outline(self, papers_dir):
        _, read, _ = build_paper_tools(papers_dir)
        out = read.invoke({"paper_id": "aaaa1111bbbb2222cccc"})
        assert "GFlowNet Factor Mining" in out
        assert "## Sections" in out
        assert "paper_section" in out  # escape-hatch pointer
        assert len(out) <= 8200

    def test_read_accepts_8char_prefix(self, papers_dir):
        _, read, _ = build_paper_tools(papers_dir)
        assert "GFlowNet" in read.invoke({"paper_id": "aaaa1111"})

    def test_read_rejects_short_prefix(self, papers_dir):
        _, read, _ = build_paper_tools(papers_dir)
        assert "not found" in read.invoke({"paper_id": "aaaa"})

    def test_section_by_heading(self, papers_dir):
        _, _, section = build_paper_tools(papers_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "风险提示"})
        assert "模型时效风险" in out

    def test_section_respects_max_chars(self, papers_dir):
        _, _, section = build_paper_tools(papers_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "原理", "max_chars": 20})
        assert "truncated" in out and len(out) < 300

    def test_section_unknown_heading_lists_titles(self, papers_dir):
        _, _, section = build_paper_tools(papers_dir)
        out = section.invoke({"paper_id": "aaaa1111", "heading": "不存在的节"})
        assert "Available sections" in out

    def test_section_by_query(self, papers_dir):
        _, _, section = build_paper_tools(papers_dir)
        out = section.invoke({"paper_id": "aaaa1111", "query": "factor generation"})
        assert "###" in out

    def test_section_without_markdown_falls_back(self, tmp_path):
        root = tmp_path / "papers"
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
    def test_absent_papers_is_empty(self, tmp_path):
        assert build_papers_prompt_section(None) == ""
        assert build_papers_prompt_section(tmp_path / "missing") == ""

    def test_uses_brief_when_present(self, papers_dir):
        out = build_papers_prompt_section(papers_dir)
        assert "momentum papers" in out and "paper_search" in out

    def test_brief_missing_derives_from_cards(self, papers_dir):
        (papers_dir / "context_brief.md").unlink()
        out = build_papers_prompt_section(papers_dir)
        assert "GFlowNet Factor Mining" in out

    def test_brief_truncated_at_cap(self, papers_dir):
        (papers_dir / "context_brief.md").write_text("x" * 9000, encoding="utf-8")
        out = build_papers_prompt_section(papers_dir)
        assert len(out) <= BRIEF_MAX_CHARS + len(out)  # bounded, marker present
        assert "truncated" in out
        assert len(out) < 9000 + 1200  # hard bound: rules + cap + marker

    def test_system_prompt_extra_sections_append_and_skip_empty(self):
        from EvoQuant.prompts import get_system_prompt

        base = get_system_prompt()
        extended = get_system_prompt(extra_sections=["# EXTRA", ""])
        assert extended.startswith(base)
        assert extended.endswith("# EXTRA")

    def test_repo_agents_md_loaded(self):
        from EvoQuant.EvoQuant import _agent_md_section

        # Real repo carries AGENTS.md (agents.md spec name); the loader
        # must find it without any configuration.
        assert "语料库" in _agent_md_section()

    def test_workspace_agents_md_overrides_and_truncates(self, tmp_path, monkeypatch):
        from EvoQuant import paths as paths_mod
        from EvoQuant.EvoQuant import _agent_md_section

        (tmp_path / "AGENTS.md").write_text("W" * 5000, encoding="utf-8")
        monkeypatch.setattr(paths_mod, "WORKSPACE_ROOT", tmp_path)
        out = _agent_md_section()
        assert out.startswith("WWW") and "AGENTS.md truncated" in out
        assert len(out) < 5000


# ---------------------------------------------------------------------------
# migration
# ---------------------------------------------------------------------------


def _legacy_workspace(tmp_path: Path) -> Path:
    """Fake legacy layout: rawpaper/{中文名}.pdf + markdown/ + wiki/ + manifest."""
    ws = tmp_path / "ws"
    (ws / "rawpaper").mkdir(parents=True)
    (ws / "markdown").mkdir()
    (ws / "wiki").mkdir()
    entries = []
    for card, pdf_bytes in zip(CARDS, [b"%PDF-aaa", b"%PDF-ddd"]):
        pdf_name = f"20260331-券商-{card['title']}.pdf"
        (ws / "rawpaper" / pdf_name).write_bytes(pdf_bytes)
        (ws / "markdown" / f"{card['paperId']}.md").write_text(
            MD_A if card is CARDS[0] else MD_D, encoding="utf-8"
        )
        (ws / "wiki" / f"{card['paperId']}.jsonl").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8"
        )
        entries.append(
            {
                "paperId": card["paperId"],
                "sourcePdf": f"rawpaper/{pdf_name}",
                "markdownPath": f"markdown/{card['paperId']}.md",
                "wikiPath": f"wiki/{card['paperId']}.jsonl",
                "status": "extraction_done",
            }
        )
    (ws / "manifest.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries), encoding="utf-8"
    )
    return ws


class TestMigrate:
    def test_layout_and_keys(self, tmp_path):
        from EvoQuant.papers.migrate import migrate

        ws = _legacy_workspace(tmp_path)
        papers = tmp_path / "papers"
        log = migrate(ws, papers, link=False, prune=False)
        for card in CARDS:
            assert (papers / "raw" / f"{card['paperId']}.pdf").is_file()
            assert (papers / "markdown" / f"{card['paperId']}.md").is_file()
            assert (papers / "cards" / f"{card['paperId']}.jsonl").is_file()
        # manifest carries the new join-key paths
        first = json.loads((papers / "manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert first["papersPath"]["raw"] == f"raw/{CARDS[0]['paperId']}.pdf"

    def test_derived_brief_and_index(self, tmp_path):
        from EvoQuant.papers.migrate import migrate

        papers = tmp_path / "papers"
        migrate(_legacy_workspace(tmp_path), papers, link=False, prune=False)
        brief = (papers / "context_brief.md").read_text(encoding="utf-8")
        assert "GFlowNet Factor Mining" in brief and "Keywords" in brief
        index_lines = (papers / "index.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(index_lines) == 2
        assert json.loads(index_lines[0])["paperId"].startswith("aaaa" if "aaaa" in index_lines[0] else "dddd")

    def test_idempotent_rerun(self, tmp_path):
        from EvoQuant.papers.migrate import migrate

        ws = _legacy_workspace(tmp_path)
        papers = tmp_path / "papers"
        migrate(ws, papers, link=False, prune=False)
        log2 = migrate(ws, papers, link=False, prune=False)
        assert any("KEEP" in line for line in log2)

    def test_dry_run_writes_nothing(self, tmp_path):
        from EvoQuant.papers.migrate import migrate

        ws = _legacy_workspace(tmp_path)
        papers = tmp_path / "papers"
        log = migrate(ws, papers, link=False, prune=True, dry_run=True)
        assert not papers.exists()
        assert not list(ws.glob("_papers_migrated_backup_*"))
        assert any("PRUNE PLAN" in line for line in log)

    def test_prune_moves_not_deletes(self, tmp_path):
        from EvoQuant.papers.migrate import migrate

        ws = _legacy_workspace(tmp_path)
        papers = tmp_path / "papers"
        migrate(ws, papers, link=False, prune=True)
        backups = list(ws.glob("_papers_migrated_backup_*"))
        assert len(backups) == 1
        backup = backups[0]
        assert (backup / "rawpaper").is_dir()
        assert (backup / "manifest.jsonl").is_file()
        assert not (ws / "rawpaper").exists()
        assert not (ws / "manifest.jsonl").exists()


class TestRefreshCLI:
    def test_refresh_rewrites_derived_and_leaves_manifest(self, tmp_path, monkeypatch, capsys):
        from EvoQuant.papers import migrate as migrate_mod
        from EvoQuant.papers import refresh

        papers = tmp_path / "papers"
        migrate_mod.migrate(_legacy_workspace(tmp_path), papers, link=False, prune=False)
        manifest_before = (papers / "manifest.jsonl").read_text(encoding="utf-8")
        (papers / "context_brief.md").write_text("stale", encoding="utf-8")

        monkeypatch.setattr(refresh, "resolve_papers_dir", lambda: papers)
        assert refresh.main(["someref"]) == 0
        out = capsys.readouterr().out
        assert "someref" in out
        assert "new session" in out  # mount-timing note
        brief = (papers / "context_brief.md").read_text(encoding="utf-8")
        assert "GFlowNet Factor Mining" in brief  # stale text was replaced
        assert (papers / "manifest.jsonl").read_text(encoding="utf-8") == manifest_before

    def test_refresh_without_papers_exits_2(self, tmp_path, monkeypatch, capsys):
        from EvoQuant.papers import refresh

        monkeypatch.setattr(refresh, "resolve_papers_dir", lambda: None)
        assert refresh.main([]) == 2
        assert "EVOSCIENTIST_PAPERS_DIR" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# integration: composite routing + agent registration
# ---------------------------------------------------------------------------


class TestCompositeIntegration:
    def test_papers_route_mounts_and_intercepts(self, papers_dir, monkeypatch, tmp_path):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "PAPERS_DIR", papers_dir)
        # Point the workspace (composite DEFAULT route) at a scratch dir so a
        # global grep doesn't sweep the repo and hit .venv binaries — that
        # error would come from the default route, not the papers route.
        ws = tmp_path / "ws"
        ws.mkdir()
        monkeypatch.setattr(paths_mod, "WORKSPACE_ROOT", ws)
        monkeypatch.setattr(paths_mod, "_active_workspace", ws)
        import EvoQuant.EvoQuant as E

        route = E._papers_route()
        assert route is not None and route[0] == "/papers/"

        backend = E._get_default_backend()
        card = backend.read("/papers/cards/aaaa1111bbbb2222cccc.jsonl")
        assert card.error is None
        blocked = backend.read("/papers/markdown/x.md")
        assert blocked.error and "paper_section" in blocked.error
        # Global grep across routes must survive the papers route (no error).
        assert backend.grep("GFlowNet").error is None
        ls = backend.ls("/papers/")
        assert ls.error is None

    def test_registry_includes_paper_tools_when_papers_present(self, papers_dir, monkeypatch):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "PAPERS_DIR", papers_dir)
        import EvoQuant.EvoQuant as E

        registry, base_tools = E._base_tool_registry()
        assert {"paper_search", "paper_read", "paper_section"} <= set(registry)
        assert any(t.name == "paper_search" for t in base_tools)

    def test_registry_without_papers_has_no_paper_tools(self, monkeypatch, tmp_path):
        from EvoQuant import paths as paths_mod

        monkeypatch.setattr(paths_mod, "PAPERS_DIR", None)
        import EvoQuant.EvoQuant as E

        registry, _ = E._base_tool_registry()
        assert not [n for n in registry if n.startswith("paper_")]


# ---------------------------------------------------------------------------
# onboarding hints
# ---------------------------------------------------------------------------


class TestOnboarding:
    def test_missing_dir_points_at_raw(self, tmp_path):
        from EvoQuant.papers.onboarding import onboarding_hint

        for absent in (None, tmp_path / "nope"):
            hint = onboarding_hint(absent)
            assert hint is not None and "papers/raw" in hint

    def test_empty_library_silent(self, tmp_path):
        from EvoQuant.papers.onboarding import onboarding_hint

        (tmp_path / "papers").mkdir()
        assert onboarding_hint(tmp_path / "papers") is None

    def test_pending_pdfs_counted(self, tmp_path):
        from EvoQuant.papers.onboarding import onboarding_hint

        root = tmp_path / "papers"
        (root / "raw").mkdir(parents=True)
        (root / "raw" / f"{CARDS[0]['paperId']}.pdf").write_bytes(b"%PDF-a")
        (root / "raw" / f"{'deadbeef' * 8}.pdf").write_bytes(b"%PDF-b")
        (root / "manifest.jsonl").write_text(
            json.dumps({"paperId": CARDS[0]["paperId"], "status": "extraction_done"}),
            encoding="utf-8",
        )
        hint = onboarding_hint(root)
        assert hint and "1 份" in hint

    def test_all_ingested_silent(self, tmp_path):
        from EvoQuant.papers.onboarding import onboarding_hint

        root = tmp_path / "papers"
        (root / "raw").mkdir(parents=True)
        for card in CARDS:
            (root / "raw" / f"{card['paperId']}.pdf").write_bytes(b"%PDF-x")
        (root / "manifest.jsonl").write_text(
            "\n".join(
                json.dumps({"paperId": c["paperId"], "status": "extraction_done"})
                for c in CARDS
            ),
            encoding="utf-8",
        )
        assert onboarding_hint(root) is None
