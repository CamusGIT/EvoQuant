# Abstract Templates

## Pre-Writing Questions

Before drafting the Abstract, answer these four questions:

1. **Technical problem**: What technical problem do we solve? Why is there no well-established solution? *(Critical)*
2. **Technical contribution**: What is our technical contribution?
3. **Why it works**: Why does our method fundamentally work?
4. **Technical advantage**: What is our technical advantage? What new insight do we provide? *(Critical)*

---

## Version 1: Challenge → Contribution

The simplest structure. Present the technical challenge, then directly describe the contribution in 1-2 sentences.

```latex
% Version 1: challenge -> contribution
% Introduce the technical challenge, then 1-2 sentences on the technical contribution.

% Task. Technical challenge.
% Technical contribution (1-2 sentences).
% Benefits. Experiment.
```

**Structure breakdown:**
1. **Task** (1 sentence): What task/problem this paper addresses
2. **Technical challenge** (1-2 sentences): Why existing methods struggle
3. **Technical contribution** (1-2 sentences): What we propose and how it addresses the challenge
4. **Benefits** (1 sentence): Key advantages of our approach
5. **Experiment** (1 sentence): Summary of experimental validation

---

## Version 2: Challenge → Insight → Contribution (Recommended)

> Recommended: Present the technical challenge, then one sentence on the insight, then 1-2 sentences on the technical contribution.

The insight sentence bridges the gap between the challenge and the solution, showing the reader *why* this approach makes sense.

```latex
% Version 2 (Recommended): challenge -> insight -> contribution
% Introduce the technical challenge, then one sentence on the insight,
% then 1-2 sentences on the technical contribution.

% Task. Technical challenge.
% Insight. (one sentence — the key observation or principle)
% Technical contribution. (1-2 sentences)
% Benefits. Experiment.
```

**Structure breakdown:**
1. **Task** (1 sentence)
2. **Technical challenge** (1-2 sentences)
3. **Insight** (1 sentence): The key observation that motivates our approach
4. **Technical contribution** (1-2 sentences): How we leverage the insight
5. **Benefits** (1 sentence)
6. **Experiment** (1 sentence)

---

## Version 3: Multiple Contributions

When the paper has multiple distinct contributions, describe each with its technical advantage.

```latex
% Version 3: multiple contributions
% Each contribution is described with its technical advantage.

% Task. Technical challenge.
% First, we xxx (technical contribution 1 + advantage).
% Second, we xxx (technical contribution 2 + advantage).
% Experiment.
```

**Structure breakdown:**
1. **Task** (1 sentence)
2. **Technical challenge** (1-2 sentences)
3. **Contribution 1** (1-2 sentences): What it does + why it helps
4. **Contribution 2** (1-2 sentences): What it does + why it helps
5. **Experiment** (1 sentence)

---

## Writing Tips

- Keep the Abstract to **150-250 words** (check venue requirements)
- Every claim in the Abstract must be supported by experiments — unsupported claims (especially in the Abstract and Introduction) can lead to rejection
- The Abstract is written at **Step 9** (near the end) because by then the story is clear and experiments are done
- Avoid vague phrases like "we propose a novel method" without specifying what is novel
- The task sentence should let readers immediately know the paper's domain
