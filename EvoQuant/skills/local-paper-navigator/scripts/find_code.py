#!/usr/bin/env python3
"""Find code implementations for papers via local code-repo + online (HuggingFace + GitHub).

Searches code-repo/ first (local), then HuggingFace Papers API and GitHub
(online). Returns combined, deduplicated results sorted by (is_official, stars).

DO NOT search for papers online — only for code implementations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from utils import get_papers_dir, match_score, tokenize

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HF_API = "https://huggingface.co/api"
GITHUB_API = "https://api.github.com/search/repositories"

RETRY_ATTEMPTS = 5
RETRY_DELAYS = [3, 6, 12, 24, 48]


# ---------------------------------------------------------------------------
# HTTP helpers (simplified, self-contained)
# ---------------------------------------------------------------------------


def _hf_headers() -> dict:
    token = os.environ.get("HF_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _github_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _request_with_retry(
    client: httpx.Client,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    follow_redirects: bool = True,
) -> dict | list | None:
    """Make HTTP request with retry on 429/5xx."""
    for delay in RETRY_DELAYS:
        try:
            resp = client.get(
                url, params=params, headers=headers, follow_redirects=follow_redirects
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 500, 502, 503, 504):
                import time

                time.sleep(delay)
                continue
            return None
        except (httpx.HTTPError, httpx.NetworkError):
            import time

            time.sleep(delay)
            continue
    return None


def _strip_arxiv_version(arxiv_id: str) -> str:
    """Strip version suffix from arXiv ID (e.g. '2203.02155v5' → '2203.02155')."""
    import re

    return re.sub(r"v\d+$", "", arxiv_id)


# ---------------------------------------------------------------------------
# Local code-repo search
# ---------------------------------------------------------------------------


def _find_local(
    title: str | None = None,
    paper_id: str | None = None,
    workspace_dir: Path | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search code-repo/ for local implementations matching a paper."""
    wd = workspace_dir or get_papers_dir()
    code_repo_dir = wd / "code-repo"
    if not code_repo_dir.is_dir():
        return []

    results = []
    query_tokens = tokenize(title or "") if title else set()

    for meta_file in sorted(code_repo_dir.glob("*/meta.json")):
        try:
            with open(meta_file, encoding="utf-8") as f:
                meta = json.loads(f.read())
        except (json.JSONDecodeError, OSError):
            continue

        # Match by paper_id
        if paper_id and meta.get("anchor_paper_id", "").startswith(paper_id[:12]):
            results.append(_local_repo_to_dict(meta, meta_file.parent))
            continue

        # Match by title (token overlap)
        if title:
            anchor_title = meta.get("anchor_paper_title", "")
            method_name = meta.get("method_name", "")
            score = (
                match_score(anchor_title, query_tokens)
                + match_score(method_name, query_tokens) * 2
            )
            if score > 0:
                results.append((_local_repo_to_dict(meta, meta_file.parent), score))

    # Sort by token match score if title-based, then truncate
    if title and results:
        scored = [(r, s) for r, s in results if isinstance(s, int)]
        unscored = [r for r in results if not isinstance(r, tuple)]
        scored.sort(key=lambda x: x[1], reverse=True)
        results = [r for r, _ in scored] + unscored

    return results[:limit]


def _local_repo_to_dict(meta: dict, repo_path: Path) -> dict:
    """Convert local code-repo meta.json to result dict."""
    return {
        "url": str(repo_path),
        "stars": 0,
        "framework": meta.get("framework", meta.get("language", "")),
        "is_official": False,
        "description": meta.get("description", "")[:150],
        "source": "local",
        "local_path": str(repo_path),
        "method_name": meta.get("method_name", ""),
        "anchor_paper_id": meta.get("anchor_paper_id", ""),
        "anchor_paper_title": meta.get("anchor_paper_title", ""),
    }


# ---------------------------------------------------------------------------
# Online search (HuggingFace + GitHub)
# ---------------------------------------------------------------------------


def _find_via_hf(
    client: httpx.Client, arxiv_id: str | None = None, title: str | None = None
) -> dict | None:
    """Find paper's GitHub repo via HuggingFace Papers API."""
    headers = _hf_headers()

    if arxiv_id:
        arxiv_id = arxiv_id.strip().replace("ArXiv:", "").replace("arxiv:", "")
        for prefix in [
            "https://arxiv.org/abs/",
            "http://arxiv.org/abs/",
            "https://arxiv.org/pdf/",
            "http://arxiv.org/pdf/",
        ]:
            if arxiv_id.startswith(prefix):
                arxiv_id = arxiv_id[len(prefix) :].removesuffix(".pdf")
        arxiv_id = _strip_arxiv_version(arxiv_id)

        data = _request_with_retry(
            client,
            f"{HF_API}/papers/{arxiv_id}",
            headers=headers,
            follow_redirects=True,
        )
        if data and data.get("githubRepo"):
            return {
                "url": data["githubRepo"],
                "stars": data.get("githubStars", 0),
                "framework": "",
                "is_official": True,
                "description": data.get("title", "")[:150],
                "source": "online",
                "local_path": None,
            }

    if title:
        data = _request_with_retry(
            client,
            f"{HF_API}/papers/search",
            params={"q": title, "limit": 3},
            headers=headers,
            follow_redirects=True,
        )
        results = data if isinstance(data, list) else []
        for item in results:
            paper = item.get("paper", item)
            if paper.get("githubRepo"):
                return {
                    "url": paper["githubRepo"],
                    "stars": paper.get("githubStars", 0),
                    "framework": "",
                    "is_official": True,
                    "description": paper.get("title", "")[:150],
                    "source": "online",
                    "local_path": None,
                }

    return None


def _find_via_github(client: httpx.Client, query: str, limit: int = 5) -> list[dict]:
    """Search GitHub for paper implementations."""
    params = {
        "q": f"{query} implementation",
        "per_page": min(limit, 30),
        "sort": "stars",
        "order": "desc",
    }
    data = _request_with_retry(
        client,
        GITHUB_API,
        params=params,
        headers=_github_headers(),
        follow_redirects=True,
    )
    repos = []
    for r in data.get("items", [])[:limit]:
        repos.append(
            {
                "url": r.get("html_url", ""),
                "stars": r.get("stargazers_count", 0),
                "framework": r.get("language", "unknown"),
                "is_official": False,
                "description": (r.get("description") or "")[:150],
                "source": "online",
                "local_path": None,
            }
        )
    return repos


# ---------------------------------------------------------------------------
# Combined search
# ---------------------------------------------------------------------------


def find_code(
    title: str | None = None,
    paper_id: str | None = None,
    limit: int = 5,
    workspace_dir: Path | None = None,
) -> list[dict]:
    """Find code repos for a paper: local code-repo first, then online."""
    repos: list[dict] = []

    # 1. Local code-repo
    local_results = _find_local(title, paper_id, workspace_dir, limit)
    repos.extend(local_results)

    # 2. Online (HF + GitHub)
    with httpx.Client(timeout=30) as client:
        search_query = title or paper_id or ""
        if search_query:
            hf_repo = _find_via_hf(client, arxiv_id=paper_id, title=title)
            if hf_repo:
                repos.append(hf_repo)
            gh_repos = _find_via_github(client, search_query, limit)
            repos.extend(gh_repos)

    # Deduplicate by URL
    seen_urls = {r["url"] for r in repos}
    deduped = []
    for r in repos:
        if r["url"] not in seen_urls:
            continue
        deduped.append(r)
        seen_urls.discard(r["url"])  # keep first, remove from seen

    # Sort: local first, then official, then by stars
    deduped.sort(
        key=lambda r: (r["source"] == "local", r["is_official"], r["stars"]),
        reverse=True,
    )
    return deduped[:limit]


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_repo(r: dict, idx: int) -> str:
    url = r.get("url", "")
    stars = r.get("stars", 0)
    framework = r.get("framework", "unknown")
    is_official = r.get("is_official", False)
    source = r.get("source", "online")
    desc = r.get("description", "")[:150]

    source_tag = " 📦 **Local**" if source == "local" else ""
    official_tag = " 🏷️ **Official**" if is_official else ""
    framework_str = f" | Framework: {framework}" if framework else ""

    return (
        f"{idx}. [{url}]({url}){official_tag}{source_tag}\n"
        f"   ⭐ {stars:,}{framework_str}\n"
        f"   {desc}\n"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Find code implementations via local code-repo + online (HuggingFace + GitHub)"
    )
    parser.add_argument("--title", "-t", help="Paper title to search")
    parser.add_argument(
        "--paper-id", "-p", help="Paper ID (SHA-256 prefix or arXiv ID)"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=5, help="Max repos (default 5)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="Papers root (default: <repo>/papers; EVOSCIENTIST_PAPERS_DIR overrides)",
    )
    args = parser.parse_args()

    if not args.title and not args.paper_id:
        print("Error: --title or --paper-id required", file=sys.stderr)
        sys.exit(1)

    workspace_dir = Path(args.workspace_dir).resolve() if args.workspace_dir else None

    repos = find_code(args.title, args.paper_id, args.limit, workspace_dir)

    if not repos:
        query = args.title or args.paper_id
        print(f"No code found for '{query}'", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(repos, indent=2))
        return

    query = args.title or args.paper_id
    print(f"# Code Implementations: {query}\n")
    print(f"Found **{len(repos)}** repositories\n")
    for i, r in enumerate(repos, 1):
        print(format_repo(r, i))


if __name__ == "__main__":
    main()
