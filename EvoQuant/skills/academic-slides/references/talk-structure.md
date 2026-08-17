# Talk Structure

Two standard structures for academic presentations, plus a section-by-section guide.

---

## Structure A: Problem-Driven (Standard)

Use this when your audience shares your research background. Start from the research goal and work toward your solution.

```
1. Research goal / big picture
2. Applications and motivation
3. Related work → challenges (build the problem progressively)
   ├─ Related work 1 → what it achieved
   ├─ Challenge remaining from related work 1
   ├─ Related work 2 → solved that challenge
   └─ New challenge from related work 2 (= what YOUR work solves)
4. Summary slide: "This talk addresses [challenges]"
5. Work 1: Task setup → Challenge → Core idea → Method → Results
6. Work 2: (same pattern, if presenting multiple works)
7. Summary and contributions
8. Future work / open questions
```

**Key principle**: Related work is not a literature survey. It is a narrative device that progressively builds toward YOUR problem. Each related work you mention should solve one thing and leave one thing unsolved — the unsolved thing is what your work addresses.

---

## Structure B: Application-Driven (Alternative)

Use this when your audience is interdisciplinary or industry-focused. Start from a compelling application and extract the research question from it.

```
1. Start from a compelling application scenario
2. Extract the research goal from the scenario
3. Related work → challenges (same progressive build)
4. Present research content (method + results)
5. Surface the underlying scientific questions
6. Summary and future directions
```

**Key difference**: Structure A starts abstract (goal → application), Structure B starts concrete (application → goal). Structure B is more engaging for non-experts because they immediately see why the work matters.

**When to choose B over A**: When more than half the audience is outside your specific subfield, or when the application is more memorable than the technique.

---

## Section-by-Section Guide

### Opening Slide

- Your name, talk title, affiliation, date
- One key visual (optional but effective — a figure from your best result)
- Keep it clean; don't crowd with logos unless required by the venue

### Motivation (1-2 slides max)

Answer: **"Why should the audience care?"**

- Start with a concrete example, not an abstract definition
- Show a real-world scenario where the problem matters
- Avoid starting with "In recent years, X has attracted increasing attention" — it is generic and forgettable

### Related Work (2-4 slides)

**This is NOT a literature survey.** It is a narrative that builds to YOUR problem.

For each related work you present:
1. Show what it achieved (briefly, 1-2 sentences)
2. Show what it cannot do (the remaining challenge)
3. Transition: this remaining challenge motivates the next step (or your work)

**Common mistake**: Listing 10 related works with one bullet each. Instead, pick 2-3 that form a logical progression toward your problem.

### Method (4-8 slides)

- **Start with the pipeline figure** — show the big picture before zooming in
- Then zoom into each novel component, one slide each
- Standard components (backbone, loss function, data pipeline) get at most one shared slide
- For each component, explain: (1) what it does, (2) why it's needed, (3) how it differs from the obvious approach

**Common mistake**: Showing the pipeline figure from the paper at full resolution. Paper figures are designed for 300 DPI print at small size — they rarely work on screen. Redesign for projection.

### Results (3-5 slides)

- **Lead with your most impressive result**, not chronological order
- Quantitative: show the comparison table with your method highlighted
- Qualitative: side-by-side comparisons (yours vs. baselines)
- One ablation slide if it tells a clear story — otherwise, relegate to backup

**Rule**: If a result slide needs more than 10 seconds of explanation, it's too complex. Simplify or split.

### Summary (1-2 slides)

- 3-5 bullet points maximum
- Reiterate key contributions — assume the audience has forgotten the details
- No new information in the summary

### Future Work (1 slide)

- 1-2 concrete, exciting directions
- Avoid vague promises ("We plan to extend this to other domains")
- Good future work slides make the audience want to collaborate with you

### Thank You / Q&A Slide

- Contact information (email, website)
- Optional: QR code to paper/code/demo
- Keep visible during Q&A so the audience can note your contact info

---

## Materials Checklist

Before making slides, gather all materials:

- [ ] Paper PDF / manuscript
- [ ] All figures (high-resolution, editable if possible)
- [ ] Key result tables (re-formatted for slides, not paper layout)
- [ ] Pipeline / architecture diagrams
- [ ] Demo videos or GIFs (if applicable)
- [ ] Related work figures (with attribution — always credit the source)
- [ ] Failure case examples (for backup slides)

---

## Multi-Work Presentations

When presenting multiple works in one talk (e.g., thesis defense, invited talk):

- All works must share a coherent research direction — don't present a disconnected list
- Use a single motivation section that sets up the entire arc
- Between works, add a 1-slide transition: "Work 1 solved X, but Y remains — this motivates Work 2"
- Allocate time proportionally: more time for the most important/recent work
- A single unified summary at the end, not separate summaries per work
