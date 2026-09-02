"""Corpus: repo-level read-only paper corpus for EvoQuant.

Layout (see AGENT.md at the repo root for the agent-facing contract):

    papers/
      raw/{paperId}.pdf       # original PDFs (gitignored; machine-blocked)
      markdown/{paperId}.md   # full text (machine-blocked; per-section only)
      cards/{paperId}.jsonl   # paper cards — the default reading layer
      context_brief.md        # global overview, injected into the system prompt
      index.jsonl             # derived index (paperId/title/year/source/keywords)
      manifest.jsonl          # extractor state ledger

Agents reach the corpus ONLY through the ``/papers/`` virtual route
(CorpusBackend) and the ``paper_search``/``paper_read``/``paper_section``
tools — never via direct filesystem paths or environment variables.
"""
