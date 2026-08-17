# Output Formats

Templates for presenting search results and reading notes.

## Paper Card

Used for POINT branch (single known paper).

```
📄 **<Title>**
Source: <Source> | Year: <Y> | ID: <paperId[:12]>...
TLDR: <one sentence>
```

## Paper Table

Used for LIST/ITERATIVE branch results.

```
| # | Title | Source | Year | Score |
|---|-------|--------|------|-------|
| 1 | <title> | <source> | <year> | 0.88 |
```

For >10 papers, group by sub-topic if obvious clusters exist.

## Reading Notes

When the user asks to read a paper (Branch POINT), use the template at `assets/paper-summary-template.md`.

Reading depth:

| Level | Goal | When | Output length |
|---|---|---|---|
| **L1 Technical** | Can reimplement | Building directly on the paper | Full markdown + wiki |
| **L2 Analytical** | Understand motivation + design + key results | Most survey/ideation papers | Complete wiki record |
| **L3 Contextual** | Know what it is, where it fits | Quick scan | TLDR + abstract |

Details in `reading-strategy.md`.

## Disambiguation Report

Used when the query is ambiguous. Full structure in `disambiguation.md`. Short form:

```
🔍 Disambiguation: "<query>"
├── Resolution: <what the term refers to>
│   ├── Paper: <title> (<source>, <year>)
│   └── Keywords: <keywords>
└── Next: <what you'll search for>
```

## Cross-Reference Summary

After cross-reference search, optionally summarize related papers:

```
🔗 Cross-references for "<Title>" (<paperId[:12]>...):
├── Related: <N> papers share keywords
│   ├── <title1> (shared: factor mining, alpha)
│   └── <title2> (shared: portfolio optimization)
└── Shared method: <M> papers use similar methodology
    ├── <title3> (shared: GFlowNet, reinforcement learning)
    └── <title4> (shared: multi-factor model)
```
