# Output Formats

EvoMath produces different final artifacts depending on the output mode (set by the user's goal in Phase 0). This document specifies each mode's format, optional LaTeX conventions, provenance annotations, inline uncertainty markers, and the PROVED Self-Check Checklist that must accompany any PROVED output.

## Output Modes (summary)

| Output mode | Triggered by goal | Format |
|---|---|---|
| Proof | `prove` (succeeded to PROVED) | Markdown proof by default; optional LaTeX source with provenance annotations |
| Refutation | `prove` or `refute` reaching REFUTED | Counterexample term + verification log + concise note |
| Audit Report | `audit-existing-proof` | Issue list with severity + recommendations |
| Handoff Report | Phase 5 triggered | Structured wall report (see `handoff-template.md`) |
| Exploratory Report | `theory-building` / `literature-synthesis` | Markdown report by default; optional LaTeX source with inline uncertainty markers |

## Optional LaTeX Source

For `Proof` and `Exploratory Report` modes, the default final artifact is human-readable Markdown. If the user requests LaTeX, or if the runtime can create files and compile LaTeX, the agent may also provide LaTeX source. A compiled PDF is required only when a LaTeX compiler is actually available and was run successfully.

If LaTeX source is produced, use this minimum preamble:

```latex
\documentclass{amsart}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{marginnote}    % for provenance annotations
\usepackage{xcolor}         % for inline uncertainty markers

\newtheorem{theorem}{Theorem}
\newtheorem{claim}[theorem]{Claim}
\newtheorem{corollary}[theorem]{Corollary}

% Custom commands for EvoMath annotations
\newcommand{\evomark}[2]{\textcolor{#1}{[#2]}}
\newcommand{\proved}[0]{\evomark{black}{PROVED}}
\newcommand{\verifiednumerical}[1]{\evomark{orange}{VERIFIED\_NUMERICALLY: #1}}
\newcommand{\conjectured}[0]{\evomark{red}{CONJECTURED}}
\newcommand{\refuted}[1]{\evomark{red}{REFUTED at #1}}
\newcommand{\handedoff}[0]{\evomark{purple}{HANDED\_OFF}}
\newcommand{\provenance}[1]{\marginnote{\footnotesize\textit{#1}}}
```

## Provenance Annotations

Every claim in the proof body that originated from a specific phase or method must be annotated. The annotation links the claim back to its workspace provenance.

**LaTeX format**: `\provenance{<phase>-<id>, <method>, <audit status>}`

**Markdown format**: `[<phase>-<id>, <method>, <audit status>]`

Examples:
```latex
\begin{proof}
By induction on $n$. \provenance{P2-c1, induction, P4 audit: 0 FATAL/CRITICAL}

\textbf{Base case.} For $n = 1$, both sides equal 1. \provenance{P1 exact, n=1 verified}

\textbf{Inductive step.} Assume $S_k = k(k+1)/2$. Then
\[
  S_{k+1} = S_k + (k+1) = \frac{k(k+1)}{2} + (k+1) = \frac{(k+1)(k+2)}{2}. \provenance{P2-c1 step 2; algebraic identity, no hidden assumption}
\]

This completes the induction. \provenance{P4 audit: persistent reviewer iteration 1, 4 HOLDS / 0 HOLE FOUND}
\end{proof}
```

The annotations let a human reviewer trace every claim back to:
- Which phase generated it (P0 / P1 / P2 / P3 / P4)
- Which candidate / subclaim id
- Which method (induction, modular, etc.)
- What audit status it achieved

This is the AI-Co-Mathematician "annotations linking claims to workspace provenance" pattern, adapted for a skill-level output.

## Inline Uncertainty Markers

Inside the proof or report body, claims with non-PROVED status must carry a visible inline marker, such as a LaTeX command or Markdown tag.

**Markers**:
- `\proved` — proved in this document (typically omitted for brevity in a Proof-mode document where the default is PROVED)
- `\verifiednumerical{N≤100}` — verified by exact arithmetic on a finite domain; N and domain stated
- `\conjectured` — supported by data or partial reasoning but not proved
- `\refuted{n=41}` — disproven; reference the counterexample
- `\handedoff` — escalated to user; not resolved in this document

**Usage rule**: in Proof mode, the *default* is PROVED, so `\proved` is rarely needed; instead, mark every step that *deviates* from PROVED status. In Exploratory Report mode, the default is CONJECTURED, so most claims carry the inline marker.

Example in Proof mode:
```latex
\begin{theorem}
For every even integer $N > 2$, there exist primes $p, q$ with $N = p + q$.
\end{theorem}

\noindent\verifiednumerical{N \in [4, 1000]} This holds empirically; cf. literature for verification to $\sim 10^{18}$.

\noindent\conjectured\ A general proof remains open (Goldbach's conjecture, 1742).

\noindent\handedoff\ Standard sieve and density arguments are insufficient for this claim.
```

In a Proof-mode document, the presence of `\conjectured` and `\handedoff` markers would itself trigger downgrade from PROVED — they should not appear in a fully-PROVED proof.

## PROVED Self-Check Checklist (final-output section)

Every final output with `final-status: PROVED` MUST include this checklist, with every box explicitly ticked by the agent. If any box cannot be honestly ticked, the status downgrades.

The checklist has 10 items, matching math-olympiad's pure-reasoning audit. PROVED requires every item to be honestly tickable.

```markdown
## PROVED Self-Check Checklist

- [x] Full step-by-step proof text exists in this document.
- [x] Every non-trivial step has explicit justification (theorem cited, claim proven, or computation shown).
- [x] No instances of "obviously", "clearly", "显然", "易见", or unjustified "WLOG" remain.
- [x] Phase 4 audit ran. Result: 0 FATAL + 0 CRITICAL.
- [x] Asymmetric vote in Phase 4: 4 HOLDS, 0 HOLE FOUND. Reviewers: R1, R2, R3, R4.
- [x] At least 4 distinct counterexample cases tried. Cases tried: n = 1, 2, 10, 100, boundary at n = 0.
- [x] Every cited subclaim is in positive memory at status PROVED.
- [x] Provenance annotations present on every theorem, claim, and proof step in the chosen output format.
- [x] Inline uncertainty markers used on any non-PROVED claim.
- [x] No shielding language remaining: searched and removed "obviously", "clearly", "显然", "易见", unjustified "WLOG".
```

A real example with each box justified by a one-line reference is required for the checklist to count. Pure-tick checklists without references must be rejected at the output stage.

## Audit Report Format (audit-existing-proof goal)

When the user submitted a proof to audit:

```latex
\section*{EvoMath Audit Report}

\textbf{Original proof:} <verbatim, with line numbers added>

\textbf{Audit summary:} <verdict: PASS / WARN / FAIL>

\textbf{Issues found:}

\begin{itemize}
  \item \textbf{Line 12:} \evomark{red}{FATAL} — Hidden assumption (Issue #11). The proof uses continuity of $f$, but the theorem statement does not assume $f$ is continuous.
  \item \textbf{Line 18:} \evomark{orange}{MAJOR} — Overclaim (Issue #16). The conclusion as stated requires $n \geq 2$; the proof only shows it for $n \geq 3$.
\end{itemize}

\textbf{Recommendations:}
\begin{itemize}
  \item Either add continuity hypothesis to the theorem statement, or replace the IVT step with a different argument.
  \item Adjust the theorem statement to "$n \geq 3$", or extend the proof to handle $n = 2$.
\end{itemize}

\textbf{Status:} CONJECTURED (with critical issues identified)
```

## Refutation Format

When the result is REFUTED:

```latex
\section*{EvoMath Refutation Report}

\textbf{Claim:} <original statement>

\textbf{Counterexample:} <the verified counterexample term>

\textbf{Verification:} <exact arithmetic log, contradiction proof, or proof-assistant output>

\textbf{Status:} REFUTED

\textbf{Notes:} <optional — e.g., "The claim holds for n < 41 but fails at n = 41">
```

## Exploratory Report Format

Used for `theory-building` and `literature-synthesis` goals. The format intentionally accommodates incomplete proofs, partial progress, and failed attempts as first-class content.

```latex
\section*{Exploratory Report: <topic>}

\subsection*{Research Question}
<from Phase 0 intake>

\subsection*{Empirical Findings}
\verifiednumerical{<domain>} <observed pattern, with citation to Phase 1 exact-computation log>

\subsection*{Working Conjectures}
\conjectured\ <conjecture 1>
\conjectured\ <conjecture 2>

\subsection*{Proven Subclaims}
\proved\ <subclaim 1 with full proof>
\proved\ <subclaim 2 with full proof>

\subsection*{Failed Explorations (First-Class Content)}
We attempted the following approaches and recorded what was learned:
\begin{itemize}
  \item \textbf{Method A:} <method> — failed because <reason>. Worth noting that...
  \item \textbf{Method B:} <method> — failed because <reason>. The obstruction is...
\end{itemize}

\subsection*{Open Problems Identified}
\handedoff\ <problem 1>: would unblock progress on conjecture X.

\subsection*{Recommended Next Steps}
<for human follow-up>

\subsection*{Status}
\textbf{output-mode:} Exploratory Report. Most claims labeled CONJECTURED. This is a research artifact, not a final proof.
```

## Verifying the Output

Before the agent emits the final output, it should structurally check:

1. **PROVED outputs**: The PROVED Self-Check Checklist is present and all boxes ticked with references.
2. **Provenance annotations**: Every theorem, claim, and key proof step has a provenance note. In LaTeX, use `\provenance{}`; in Markdown, use a compact bracketed note such as `[P2-c1, induction, P4 audit clean]`.
3. **Inline markers**: Any claim weaker than PROVED carries an inline marker.
4. **Status consistency**: The final-status field matches the strongest claim in the document. If the document contains a `\handedoff` marker but final-status says PROVED, the output is malformed.
5. **No raw traces**: No Phase 2 reasoning traces, no dead-end candidate text. Per State Compression rule.

If any of these fail, the output is not ready. Either repair, or downgrade the status.
