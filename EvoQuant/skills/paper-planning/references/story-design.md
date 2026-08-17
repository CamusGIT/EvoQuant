# Story Design

## What is a Paper's "Story"?

The story is the logical narrative connecting problem → insight → method → results. A strong story makes the paper feel inevitable: given the problem, the proposed solution is the natural response.

## The Reverse-then-Forward Method

### Phase 1: Reverse Engineering

Start from your method and work backwards:

1. **Technical problem**: What specific challenge does our method solve?
   - Be precise: not "task X is hard" but "existing methods cannot handle [specific aspect] efficiently"

2. **Contributions**: What are our concrete technical contributions?
   - List 2-3 specific, verifiable contributions
   - Each should be a concrete technical novelty, not a vague claim

3. **Benefits and insights**: What advantages does our approach provide? What new understanding?
   - Technical advantages (speed, accuracy, generalization)
   - New insights about the problem domain

4. **Challenge framing**: How do we set up the challenge so our contribution feels necessary?
   - What do previous methods do? Where do they fall short?
   - How does this naturally lead to our contribution?

### Phase 2: Forward Writing

Now write the Introduction following this forward flow:

1. **Task**: Introduce the task and its importance
2. **Previous methods → Challenge**: Survey prior work and reveal the gap
3. **Our contributions**: Present our solution as a natural response to the challenge
4. **Technical advantages**: Explain why our approach is effective

---

## Starting with the Pipeline Figure

> Start by drawing a pipeline figure sketch — this forces you to clarify the overall method before writing.

Drawing the pipeline figure sketch is the **first concrete step** in story design:

1. **Sketch the full pipeline** from input to output
2. **Identify novel modules** — mark which parts are new vs. standard
3. **Determine module motivations** — for each novel module, write one sentence on *why*
4. **Map to subsections** — each major module becomes a Method subsection
5. **Extract the story** — the novel modules and their motivations form the core narrative

### Pipeline Sketch Checklist

- [ ] Input and output are clearly defined
- [ ] All major processing steps are shown
- [ ] Novel modules are visually distinguished from standard components
- [ ] Each novel module has a one-line motivation
- [ ] The information flow is unambiguous (arrows/connections)

---

## Articulating Core Contributions

### How to Write Contribution Statements

Good contribution statements are:
- **Specific**: Name the technique, not just "a novel method"
- **Verifiable**: Can be confirmed by reading the paper
- **Advantageous**: State the benefit, not just what was done

**Bad**: "We propose a novel method for [task]."
**Good**: "We introduce [specific technique] for [specific purpose], which naturally [specific advantage tied to problem structure]."

### Template for Contribution Paragraph

```
Our contributions are summarized as follows:
(1) We propose [specific technique] for [specific purpose], which [specific advantage].
(2) We introduce [specific technique] that [specific capability], enabling [specific benefit].
(3) Extensive experiments on [datasets] demonstrate that our method achieves [specific improvement] over state-of-the-art methods.
```

---

## Module Motivation Mapping

This table implements the **three-element system** from [method-templates.md](../../paper-writing/references/method-templates.md): each row captures the module design, motivation, and technical advantage that will become one Method subsection.

For each module in the pipeline, fill in this table:

| Module | What it does | Why it's needed | Technical advantage |
|--------|-------------|-----------------|---------------------|
| Module A | [function] | [challenge it addresses] | [why it works well] |
| Module B | [function] | [challenge it addresses] | [why it works well] |
| Module C | [function] | [challenge it addresses] | [why it works well] |

This table directly maps to:
- **Introduction**: Contributions paragraph
- **Method**: Subsection structure (motivation → design → advantages per module)
- **Experiments**: Ablation study design (remove each module to verify necessity)

---

## Common Story Anti-Patterns

1. **No clear challenge**: Proposing a solution without establishing why it's needed
2. **Incremental framing**: "Method A has problem P; we add module M to fix it" — makes work seem minor
3. **Disconnected contributions**: Multiple contributions that don't form a coherent narrative
4. **Missing insight**: Technical contribution without explaining *why* it works — feels arbitrary
5. **Overclaiming**: Story promises more than experiments deliver
