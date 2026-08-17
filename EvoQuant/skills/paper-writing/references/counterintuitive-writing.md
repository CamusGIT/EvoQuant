# Counterintuitive Writing Tactics

Use these tactics to improve reviewer confidence when paper quality is already "good enough."

## Tactic 1: Lower the Verbal Temperature

Replace high-risk language:
- Avoid: "significantly outperforms all methods in all settings"
- Prefer: "improves performance under matched protocols on benchmarks A/B and stress setting C"

Counterintuitive effect: conservative language often yields higher reviewer trust and fewer "overclaim" objections.

**Before/After Example:**
- Before: "Our method significantly outperforms all existing methods in all settings."
- After: "Our method improves PSNR by 1.2 dB under matched protocols on benchmarks A and B (Tab. 1)."

## Tactic 2: Declare Scope Boundaries Explicitly

Add one sentence in Introduction and Conclusion:
- "Our method targets [setting S]; behavior outside this regime is discussed in limitations."

This reduces reviewer fear that hidden assumptions are being masked.

## Tactic 3: Mechanism Before Metrics

In Introduction and Method:
1. State challenge.
2. State observation/mechanism.
3. State design.
4. Then report metric gains.

If metrics come first, reviewers may perceive the method as benchmark chasing.

## Tactic 4: Use a Claim-Evidence Thread

For each core claim, use an explicit evidence anchor in prose:
- "As quantified in Table 2..."
- "Figure 4 shows this robustness trend..."

Do not leave claims unanchored.

## Tactic 5: Keep One "Anchor Figure"

Design one high-information figure that combines:
- Main comparison
- Hard subset or stress condition
- At least one qualitative panel

A strong anchor figure is often more persuasive than multiple fragmented visuals.

## Tactic 6: Delete the Most Impressive Unsupported Sentence

Before submission, intentionally remove one "great sounding" sentence if it lacks direct evidence.

Counterintuitive effect: acceptance odds improve when unsupported claims are removed, even if prose appears less aggressive.

## Tactic 7: Use Failure as Competence Signal

Include one representative failure case with brief diagnosis:
- "Failure occurs when [condition], likely due to [reason]."

This signals technical maturity and reduces "authors hide weaknesses" reviewer sentiment.

## Quick Pre-Submission Pass (10 Minutes)

1. Highlight every claim sentence in Abstract + Introduction.
2. Write `T/F` next to each sentence:
   - `T`: has direct table/figure evidence
   - `F`: no direct evidence
3. Rewrite or delete every `F`.
