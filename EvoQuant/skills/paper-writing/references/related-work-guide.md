# Related Work Guide

## Three-Step Process

### Step 1: List Related Papers

> List all papers closely related to your method. This is the most important step — missing key references can lead to rejection.

This is the most important step. Missing key references can lead to rejection.

- List all papers closely related to your **method/technique**
- Include papers that solve the **same or similar task**
- Include papers that use the **same core technique** in different domains
- Check recent publications (last 2-3 years) in top venues
- Check papers cited by your baselines

### Step 2: Determine Topics

> Determine the topics for Related Work based on your research direction and algorithm techniques.

Group the listed papers into 2-4 topics based on:
- Research direction / task categories
- Algorithm families / technical approaches
- Each topic becomes a subsection or paragraph in Related Work

**Example topics for a 3D reconstruction paper:**
- Neural Radiance Fields
- Multi-view Stereo
- Dynamic Scene Reconstruction

### Step 3: Organize and Write

> Organize the Related Work writing plan based on the papers listed in the first two steps.

For each topic:
1. **Opening sentence**: What this line of work addresses
2. **Survey key methods**: Chronological or grouped by approach
3. **Position our work**: How our method relates to or differs from this line of work

---

## Writing Pattern per Topic

```latex
\paragraph{Topic Name.}
% Opening: What this line of research addresses
[Brief introduction to the topic and its goal.]

% Survey: Key methods in chronological or logical order
[Method A]~\cite{a} proposed [approach]. [Method B]~\cite{b} extended this by [improvement].
More recently, [Method C]~\cite{c} achieved [result] through [technique].

% Position: How our work relates
Unlike [previous approaches], our method [key difference].
% OR: Our work builds on [Method X] but differs in [specific aspect].
```

---

## Common Pitfalls

- **Missing key references**: The most dangerous issue — some reviewers reject papers for this alone
- **Too short**: A paragraph per topic is the minimum; very thin Related Work suggests unfamiliarity with the field
- **No positioning**: Simply listing methods without explaining how your work differs
- **Outdated references**: Only citing old papers while missing recent advances
- **Too many topics**: 2-4 focused topics are better than 6+ scattered ones

---

## Tips

- Write Related Work at **Step 7** (after Method and Experiments are mostly done) — by then you have a clear picture of what's truly related
- When in doubt about whether to include a paper, include it — it's better to over-cite than to miss something
- Use Related Work to **highlight what makes your approach unique** — every topic paragraph should implicitly contrast with your method
- Keep Related Work concise but comprehensive — typically 0.5-1 column in a conference paper
