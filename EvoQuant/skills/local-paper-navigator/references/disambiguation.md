# Disambiguation

Read this when the user's query looks ambiguous — a project name, codename, module name, or nickname — rather than a paper title or topic.

## Signals of an ambiguous query

- Single-word or 2-word capitalized name (e.g., "QuantaAlpha", "GFlowNet")
- "the X paper" where X looks like a product or code name
- Mix of org name + module ("DeepSeek Engram")
- Zero results from a `local_search` on the literal query

## Resolution steps

1. **Direct local search first:**
   ```bash
   python scripts/local_search.py --query "<exact term>" --limit 5
   ```
   If 1-3 sensible results appear → not ambiguous, return as Paper Card.

2. **Broaden to cross-reference:**
   ```bash
   python scripts/xref_search.py --query "<term>" --direction related --limit 10
   ```
   Papers with shared keywords often clarify what the term refers to.

3. **Try fuzzy title match:**
   ```bash
   python scripts/match_by_title.py --title "<term>" --fallback-search
   ```

4. **Extract identifiers:** From the search results, identify:
   - Actual paper title
   - Source (organization)
   - Related keywords

5. **Re-enter the appropriate branch:**
   - If now have a specific paper → Branch POINT
   - If now have a topic + several related papers → Branch LIST
   - If user wants a survey of all related work → Branch ITERATIVE

## Output: Disambiguation Report

Show the user what was resolved before proceeding:

```
🔍 Disambiguation: "GFlowNet"
├── Resolution: "GFlowNet" is a generative flow network for factor mining
│   ├── Paper: "Low-Correlation Volume-Price Factor Mining Strategy Based on GFlowNet" (Guojin Securities, 2026)
│   └── Keywords: GFlowNet, Factor Mining, Low Correlation, Volume-Price Data
└── Next: searching related factor mining papers
```

## When disambiguation fails

If local search also returns nothing:
- The term may not be in the local wiki corpus — ask the user for source or context
- It may be a typo — try near-spellings or ask user to confirm
- The paper may not have been extracted yet — suggest running `quant-paper-extractor` first

Don't invent a paper. If you can't resolve, say so.
