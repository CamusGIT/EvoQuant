# Introduction Templates

The Introduction follows a standard structure:
1. Introduce the **task** and its application
2. Discuss **previous methods** and their **technical challenges**
3. Present **our pipeline/contributions**
4. Highlight **technical advantages** and new insights

> **Thinking process** (reverse-engineer then forward-write):
> - Reverse: (1) What is the technical problem? (2) What are our contributions? (3) Benefits and insights? (4) How to lead into the challenge?
> - Forward: (1) Task → (2) Previous methods → challenge → (3) Our contributions → (4) Technical advantages and insights

---

## Template Selection Guide

Use these tables to choose the right template version for each part.

**Part 1 — Introducing the Task:**

| Your Situation | Choose |
|----------------|--------|
| Task is unfamiliar to most readers | Version 1 (Niche Task) |
| Task is well-known in the community | Version 2 (Well-Known Task) |
| Paper spans general field → specific setting | Version 3 (General to Specific) — Recommended |
| Challenge is the main hook; task obvious from title | Version 4 (Jump to Challenge) |

**Part 2 — Technical Challenges:**

| Your Situation | Choose |
|----------------|--------|
| Methods have evolved through generations; you address remaining gap | Version 1 (Evolutionary Challenges) |
| You revive a classical idea with modern techniques | Version 2 (Traditional Insight Endorsement) |
| New task with no established methods; multiple requirements | Version 3 (Novel Task) |

**Part 3 — Introducing Our Pipeline:**

| Your Situation | Choose |
|----------------|--------|
| Single core contribution with several advantages | Version 1 (Single Contribution + Teaser) |
| Two distinct, separable contributions | Version 2 (Two Contributions + Teaser) |
| Building on an established pipeline; proposing a new module | Version 3 (Extension of Previous Pipeline) |
| A key observation directly motivates the method | Version 4 (Observation-Driven) |

---

## Part 1: Introducing the Task (4 Versions)

### Version 1 — Niche Task

When the task is not well-known, explain what it is first, then its application.

```latex
% Version 1: The task is niche — explain it first.
% Task description (2-3 sentences explaining what the task is).
% Application of the task.
```

Use this when readers likely have not encountered this specific task before.

### Version 2 — Well-Known Task

When the task is familiar (e.g., object detection, image segmentation), jump directly to the application.

```latex
% Version 2: The task is well-known — go straight to the application.
% Application directly (no need to explain what the task is).
```

### Version 3 — General to Specific (Recommended)

> Recommended: Start with the general task application, then narrow to the specific task setting.

Start broad, then narrow down to the specific setting of this paper.

```latex
% Version 3 (Recommended): General to specific.
% Introduce general task/field and its broad application.
% Then narrow to the specific task setting of this paper.
```

This is the most versatile approach and works for most papers.

### Version 4 — Jump to Challenge via Previous Methods

Skip the task introduction entirely and lead into the challenge through previous methods.

```latex
% Version 4: Jump to challenge through previous methods.
% Directly introduce previous methods and their limitations,
% which naturally frames the task context.
```

Best when the task is obvious from the title and the challenge is the main hook.

---

## Part 2: Technical Challenges of Previous Methods (3 Versions)

### Version 1 — Existing Task, Evolutionary Challenges

For established tasks where methods have evolved over time.

```latex
% Version 1: Existing task — show method evolution leading to our challenge.
% Traditional methods: [describe approach] → [limitation]
% Recent methods (group 1): [describe approach] → [remaining limitation]
% Recent methods (group 2): [describe approach] → [remaining limitation]
% Our challenge: [the specific gap we address]
```

Structure: traditional methods → recent methods 1 → recent methods 2 → our challenge. Each group shows progress but reveals remaining limitations.

### Version 2 — Traditional Insight Endorsement

Leverage a validated traditional insight and apply it in a new context.

```latex
% Version 2: Endorse a traditional insight and extend it.
% Traditional methods used [insight/technique] which was effective because [reason].
% However, recent methods abandoned this in favor of [new approach].
% We argue that the traditional insight still holds and propose to [combine/extend].
```

This works well when you revive a classical idea with modern techniques.

### Version 3 — Novel Task with Multiple Requirements

For new tasks that don't have established methods.

```latex
% Version 3: Novel task — list multiple requirements/challenges.
% This task requires addressing several challenges:
% (1) Challenge A: [description]
% (2) Challenge B: [description]
% (3) Challenge C: [description]
% Existing methods from related fields cannot handle all these simultaneously.
```

---

## Part 3: Introducing Our Pipeline (4+ Versions)

### Version 1 — Single Contribution with Advantages + Teaser

```latex
% Version 1: Single core contribution with multiple advantages.
% In this paper, we propose [method name], which [core contribution in one sentence].
% [Method name] has several appealing properties:
% (1) [Advantage 1]: [explanation]
% (2) [Advantage 2]: [explanation]
% (3) [Advantage 3]: [explanation]
% As shown in Figure 1, [describe teaser figure result].
```

### Version 2 — Two Contributions + Teaser

```latex
% Version 2: Two distinct contributions.
% We propose [method name] for [task].
% Our first contribution is [contribution 1], which [advantage].
% Our second contribution is [contribution 2], which [advantage].
% As illustrated in Figure 1, our method achieves [key result].
```

### Version 3 — Extension of Previous Pipeline

When building on an established pipeline and proposing a new module.

```latex
% Version 3: Based on previous pipeline, propose new module.
% In this paper, we propose [method name] for [task].
% Inspired by previous methods [X, Y], [method name] takes [input]
% and [how it processes].
% Our key innovation is introducing [novel module] for [purpose],
% as illustrated in Figure 1.
% We observe that [key structural property of the problem],
% and [novel module] is naturally suited for this structure.
% [Novel module] encodes not only [local features] but also
% [relational features], enabling effective [high-level reasoning].
```

### Version 4 — Observation-Driven Contribution

When a key observation leads to the proposed method.

```latex
% Version 4: Key observation drives the contribution.
% We observe that [key observation about the problem/data].
% Based on this observation, we propose [method/module] that [leverages the observation].
% This design has the advantage of [technical advantage].
```

---

## Anti-Patterns (What NOT to Do)

### Do NOT write: naive solution → our improvement

> Never present a naive solution first and then describe our improvement on top of it. This framing makes the work appear as a minor incremental improvement. Even if the contribution is incremental, never present it this way.

**Bad example:**
```
A straightforward approach would be to [naive solution]. However, this has [problem].
To address this, we propose [our improvement on top of naive solution].
```

This framing makes the work appear as a minor incremental improvement (a "4-point paper"). Even if the contribution is incremental, never present it this way.

**Instead:** Present the contribution as a principled solution to a fundamental challenge, motivated by a clear insight.

---

## Scope Boundary Statement

After the contribution paragraph, consider adding a scope boundary sentence (see counterintuitive-writing Tactic 2). This reduces reviewer fear of hidden assumptions.

```latex
% Scope boundary (optional, 1 sentence after contributions):
We note that our method targets [specific setting/regime]; behavior
outside this scope is discussed in Section~\ref{sec:limitations}.
```

---

## Contribution Paragraph Checklist

When writing the contribution paragraph (usually the last paragraph before "The remainder of this paper..."):

- [ ] Each contribution is clearly stated
- [ ] Technical advantages are explicit (not just "we propose X")
- [ ] New insights or observations are highlighted
- [ ] Every contribution has experimental support later in the paper
- [ ] The teaser figure is referenced to visually demonstrate the key result
