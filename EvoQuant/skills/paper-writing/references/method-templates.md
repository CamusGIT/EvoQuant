# Method Templates

## The Three-Element System

Every pipeline module in the Method section must address three elements:

1. **Module Design** — Description of module details
2. **Motivation** — Why the paper uses this module
3. **Technical Advantages** — Why this module works well

> If you used `paper-planning`, the **Module Motivation Mapping table** from story-design already contains these three elements for each module. Import it directly — don't recreate from scratch.

---

## Pre-Writing: Organize Your Thoughts

Before writing the Method section, check if a Module Motivation Mapping table exists from `paper-planning`. If so, use it as your writing plan. Otherwise, answer these questions:

1. What modules does the method have?
2. For each module:
   - What is the workflow? (Module design)
   - Why this module? (Motivation)
   - Why does it work well? (Technical advantages)

**Process:**
1. Answer the three questions for every module → organize as mind map or table
2. Draw pipeline figure sketch
3. Map subsections to pipeline modules
4. For each subsection: plan motivation → module design → technical advantages
5. Write module design first (basic content), then add motivation and technical advantages

If `paper-planning` was used, import the Module Motivation Mapping table from story design — each row becomes one Method subsection (motivation → design → advantages).

---

## Method Overview Template

The Method section should start with an Overview paragraph.

```latex
\section{Method}

% Overview: 1-2 sentences on setting
% Example: Given [specific input data], our task is to [produce specific output].

% 1-2 sentences on core contribution
% Example: Inspired by [prior work], we [core approach description].

% If the pipeline is novel, reference a pipeline figure
% Example: Figure 2 illustrates the overview of our method.

% Section roadmap:
% Section 3.1 describes [module 1].
% Section 3.2 describes [module 2].
% Section 3.3 describes [module 3].
```

**Template:**
```latex
\section{Method}

% Setting (1-2 sentences):
Given [input description], our goal is to [output/task description].

% Core contribution (1-2 sentences):
To this end, we propose [method name], which [core idea in one sentence].
Figure~\ref{fig:pipeline} illustrates the overview of our approach.

% Section roadmap:
In Section~\ref{sec:module1}, we describe [module 1].
Section~\ref{sec:module2} presents [module 2].
Finally, Section~\ref{sec:module3} details [module 3].
```

### Overview Tips

- Keep the overview short (3–5 sentences) for standard pipelines; save detail for subsections.
- Define notation once in the overview (e.g., input $\mathbf{X}$, output $\mathbf{Y}$) and reuse consistently.
- The section-roadmap sentence is optional for methods with only 2 modules — it adds no information.

---

## Method Subsection Template

Each subsection follows the three-element pattern:

```latex
\subsection{Module Name}
\label{sec:module_name}

% 1. MOTIVATION (Why this module?)
% Problem-driven: because X problem exists, we design Y to solve it.
% Typical opening sentences:
%   - "A remaining problem/challenge is ..."
%   - "However, [previous approach] has difficulty in ..."
%   - "To address [challenge], we propose ..."

[Motivation paragraph: explain the problem this module solves.]

% 2. MODULE DESIGN (What does it do?)
% Two parts:
%   (a) Description of specific data structure / network structure
%   (b) Forward process: given X input, step 1 does A, step 2 does B, ..., output Y

[Design paragraph(s): describe the module's structure and forward process.]

% 3. TECHNICAL ADVANTAGES (Why does it work well?)
% Explain the design choices and why they lead to good performance.

[Advantages paragraph: articulate why this design is effective.]
```

### Module Design in Detail

Module design has two parts:

1. **Structure description**: Specific data structure or network architecture
   - What representation is used?
   - What are the key components?
   - How are inputs/outputs formatted?

2. **Forward process description**: Step-by-step operation
   ```
   Given [input X],
   Step 1: [operation] → [intermediate result]
   Step 2: [operation] → [intermediate result]
   Step 3: [operation] → [final output Y]
   ```

### Module Motivation Patterns

Motivation is always problem-driven. Common opening patterns:

- "A remaining problem/challenge is ..."
- "However, [existing methods] have difficulty in ..."
- "Previous methods [approach], which leads to [limitation]..."
- "To handle [specific challenge], we ..."
- "We observe that [observation], which motivates ..."
- "Achieving [goal A] and [goal B] simultaneously is challenging because ..." (dilemma pattern)

---

## Checking if Method is Easy to Understand

Three levels of checking:

### Level 1: Writing Plan

After writing, extract the writing plan from your Method section:
- Does the flow make sense?
- Are subsections in a logical order?
- Does each subsection clearly correspond to a pipeline module?

### Level 2: Paragraph Writing

For each paragraph:
- [ ] Does the first sentence tell readers what this paragraph is about?
- [ ] Does the paragraph convey exactly one message?
- [ ] Is the paragraph self-contained (all concepts defined or referenced)?

### Level 3: Sentence Writing

For each sentence:
- [ ] Is the **motivation** for this sentence clear? (Readers always know *why* they are reading this.)
- [ ] Does it **flow** from the previous sentence?
- [ ] Is **terminology consistent**? (Don't keep changing names for the same concept.)

> Check that the motivation for every sentence is clear — readers should always know why they are reading it.
> Check that sentences flow logically from one to the next.
> Check that terminology is consistent — do not keep changing names for the same concept.

---

## Implementation Details

Implementation details include:
- Network layers and architecture specifics
- Feature vector dimensions
- Coordinate transformations
- Normalization details
- Training hyperparameters

**Placement options:**
1. At the end of the Method section (common)
2. In a dedicated "Implementation Details" subsection
3. In supplementary material (if space is limited)

---

## Common Pitfalls

- **Missing motivation**: Module design without explaining *why* → reviewer feedback: "lacks motivation"
- **Missing forward process**: Only high-level description without step-by-step flow → unclear
- **Inconsistent terminology**: Changing variable names or module names mid-section
- **No pipeline figure reference**: Method text should reference the pipeline figure
- **Overloaded paragraphs**: Mixing multiple concepts in one paragraph
