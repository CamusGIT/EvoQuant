# Figure Design

## Pipeline Figure

### Core Principle

> The pipeline figure is for highlighting novelty, not for making readers understand. The Method text is what makes readers understand.

The pipeline figure's primary purpose is to **highlight novelty**, not to explain the method. The Method text handles explanation; the figure handles visual impact.

### Design Rules

1. **Differentiate from prior work**: The pipeline figure must look visually different from previous methods' figures. If it looks the same, readers assume no novelty.
   > The method figure is critical. The pipeline figure must look different from previous methods — otherwise readers will assume there is no novelty.

2. **Highlight novel modules**: If the overall pipeline is standard, zoom into and emphasize the novel module(s).
   > If the overall pipeline (from input to output) is not very novel, emphasize the novel module in the pipeline figure.

3. **Consider small-figure alternative**: Instead of one big pipeline figure, use several focused small figures for each novel module. Trade-off: may reduce visual impact.
   > An alternative is to draw several focused small figures instead of one big figure, though this may reduce the paper's visual impact.

4. **Simplify standard components**: Don't spend visual real estate on well-known components (encoders, decoders, standard layers). Show them compactly.

5. **Clear information flow**: Arrows and connections should be unambiguous. The reader should immediately see what flows where.

### Good vs. Bad Examples

When evaluating your pipeline figure, ask:
- Does it look distinct from prior work in this area?
- Can a reader identify the novel parts at a glance?
- Is the visual quality professional?

---

## Teaser Figure (Figure 1)

The teaser is typically the first figure in the paper, placed at the top of page 1.

### Purpose
- Show the key result at a glance
- Immediately capture the reader's attention
- Demonstrate the method's capability visually

### Design Tips
- **Result-focused**: Show what the method achieves, not how it works
- **Compelling**: Choose the most impressive result
- **Comparative**: If possible, show your result vs. baseline side-by-side
- **Self-contained caption**: The caption should let readers understand the figure without reading the paper
- **High resolution**: Visual quality directly affects first impressions

---

## Table Design

### Iterative Improvement Process

Transform tables step by step:

1. **Caption above** — Always place the caption above the table, not below
2. **Remove vertical lines** — Delete all vertical lines; do not connect vertical and horizontal lines
3. **Use booktabs** — Replace `\hline` with `\toprule`, `\midrule`, `\bottomrule`
4. **Minimize lines** — Only use horizontal rules to separate header from body and to mark major groups
5. **Add color** — Highlight best results (red/bold) and second-best (blue/underline)

### Additional Table Tips

- Use `↑` / `↓` arrows after metric names to indicate direction (higher/lower is better)
- Align decimal points for easy comparison
- Keep tables compact — avoid excessive whitespace
- Place single-column tables in the right column (matches reading habit: eyes start upper-left)

---

## Overall Visual Quality

> The key to receiving good reviews: make the paper beautiful and polished.

Three pillars of visual quality:
1. **Beautiful figures**: Professional pipeline figure and teaser
2. **Clean tables**: Booktabs formatting, color highlights, no clutter
3. **Neat typography**: Consistent formatting, proper spacing, no overfull boxes

Visual quality creates a positive first impression that influences the entire review process.
