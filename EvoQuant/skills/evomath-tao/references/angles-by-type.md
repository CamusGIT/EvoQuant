# Starting Angles by Problem Type

For each of the 10 types, ~8 standard angles. In Phase 2, **select the top-5** that are most relevant and mutually distinct — do not enumerate all 8. Each selection is one candidate; running 5 candidates with diverse machinery beats running 8 mutual variants.

---

## Competition

### algebra
1. **Factoring / completing the square** — algebraic identities, quadratic forms, sum/difference of cubes
2. **Substitution** — variable change, trig substitution, telescoping sums
3. **Symmetry exploitation** — swap variables, use symmetric polynomials (e_k, p_k, h_k)
4. **Inequalities** — AM-GM, Cauchy-Schwarz, rearrangement, Chebyshev, Jensen
5. **Generating functions** — for sequences, recursions, partition counting
6. **Functional equation tricks** — substitute x→0, x→1, x→-x; injectivity; surjectivity; fixed points
7. **Induction** — strong, structural, backward, or generalized
8. **Polynomial root analysis** — Vieta's formulas, discriminant, rational root theorem, resultants

### geometry
1. **Auxiliary lines / circles** — angle bisectors, perpendiculars, midpoint circles, nine-point circle
2. **Coordinate geometry** — pick origin & axes, compute everything algebraically
3. **Trigonometric identities** — law of sines, law of cosines, sum-to-product
4. **Inversive / projective transformations** — when ratios or cross-ratios are involved
5. **Vector / complex number method** — for collinearity, concurrency, similarity
6. **Area chase** — equate areas computed two different ways
7. **Power of a point / radical axis** — for circle problems and tangents
8. **Spiral similarity / homothety** — for similar-triangle structures across configurations

**Olympiad geometry dispatch rule**:
- For circle/tangent/orthocentre problems, the default top-5 must include: coordinate/vector setup, angle/cyclic chase, power/radical-axis, inversion or projection, and spiral similarity/homothety.
- Coordinate geometry gets at most two symbolic attempts. If the algebra grows without producing a compact identity or a verified equivalence, mark it as a same-route stall and move to another geometry technique.
- Numerical exploration may suggest claims, but the Phase 2 candidate must state a synthetic or algebraic proof target explicitly (for example, "prove O lies on line L", "show power equality", or "show tangent by radius perpendicular").
- A tangent goal should be normalized to at least two equivalent tests before Phase 2 scoring: radius perpendicular to tangent line, power-of-point equality, directed angle equality, or discriminant-one-contact in coordinates.

### number-theory
1. **Modular arithmetic** — pick smart moduli (small primes, n itself, factors of constants)
2. **Prime factorization / valuations** — vp(n), lifting-the-exponent (LTE)
3. **CRT (Chinese Remainder Theorem)** — combine independent congruences
4. **Pigeonhole on residue classes** — when finiteness of classes matters
5. **Vieta jumping** — for symmetric Diophantine equations
6. **Quadratic reciprocity** — for prime-residue questions
7. **Bounding / size argument** — show no solution exceeds N, then check finitely many
8. **Fermat's little theorem / Euler's theorem** — for exponent reductions modulo primes / prime powers

### combinatorics
1. **Pigeonhole** — find collision or excess
2. **Double counting** — count one quantity two different ways
3. **Bijection / injection / surjection** — explicit structural correspondence
4. **Extremal principle** — pick smallest/largest object, derive contradiction or property
5. **Probabilistic method** — show positive expectation or non-zero probability of desired structure
6. **Invariant / monovariant** — quantity preserved or strictly decreasing under operations
7. **Coloring / parity** — assign labels to expose hidden constraint
8. **Generating functions / recursion** — for counting and structure questions

---

## Research

### analysis
1. **Triangle inequality + ε/3 trick** — for limit, continuity, and uniform-continuity proofs
2. **Dominated convergence (DCT)** — interchange limit and integral; requires |f_n| ≤ g, ∫g < ∞
3. **Monotone convergence (MCT)** — for monotone non-negative sequences/integrals
4. **Fubini / Tonelli** — interchange order of integration; requires integrability or non-negativity
5. **Compactness arguments** — extract convergent subsequence; use total boundedness or Heine-Borel
6. **Density arguments** — prove on a dense subset, extend by continuity
7. **Approximation by simple/smooth functions** — reduce to special case via density of simple functions
8. **Spectral / functional calculus** — for operator-theoretic problems

### probability
1. **Markov / Chebyshev / Chernoff bounds** — concentration around mean
2. **Borel-Cantelli claims** — almost sure convergence and lim sup events
3. **Coupling** — compare two distributions on the same probability space
4. **Martingale arguments** — optional stopping theorem, martingale convergence
5. **Conditioning / tower property** — decompose expectation via E[X] = E[E[X|F]]
6. **Generating function / characteristic function** — moments, distribution identification
7. **Method of moments** — match moments to identify or bound distribution
8. **Probabilistic construction** — random object with desired property (existence proof)

### optimization
1. **KKT conditions** — first-order necessary conditions for constrained optimization
2. **Lagrangian duality** — primal-dual relationship, weak/strong duality
3. **Convexity exploitation** — local optima are global; Jensen's inequality
4. **Subgradient / proximal methods** — for non-smooth or composite objectives
5. **Smoothness + strong convexity bounds** — convergence rates of first-order methods
6. **LP / SDP relaxation** — when integer programming is hard, relax to convex
7. **Variational inequalities** — for fixed-point and equilibrium characterizations
8. **Min-max duality** — saddle-point analysis, Sion's theorem

### linear-algebra
1. **Spectral decomposition** — eigenvalue/eigenvector basis for symmetric/normal operators
2. **Singular value decomposition (SVD)** — for general (non-square) matrices
3. **Schur complement** — block-matrix manipulation, PSD decomposition
4. **Trace / determinant identities** — invariants under similarity, AM-GM for eigenvalues
5. **Rank-nullity arguments** — dimension counting, kernel/image structure
6. **Operator norms** — for stability, perturbation, and bounding
7. **Matrix inequalities (Loewner order)** — for PSD relations and matrix monotonicity
8. **Polynomial identities of matrices** — Cayley-Hamilton, minimal polynomial, characteristic polynomial

---

## Applied

### graph-theory
1. **Induction on |V| or |E|** — strip a vertex or edge, recurse
2. **Spectral methods (Laplacian eigenvalues)** — for connectivity, expansion, mixing
3. **Probabilistic argument** — random graph, random orientation, random partition
4. **Flow / cut duality** — max-flow = min-cut, integral solutions in bipartite
5. **Coloring / chromatic argument** — for partition or independent set problems
6. **Extremal / Turán-type** — edge maximization under forbidden subgraph constraint
7. **Structural decomposition** — into trees, paths, matchings, expanders
8. **Counting walks / paths via adjacency matrix** — algebraic graph theory, walk-counting

### ML-theory
1. **PAC / VC bounds** — for distribution-free generalization
2. **Rademacher complexity** — data-dependent generalization bounds
3. **Stability arguments** — algorithmic stability → generalization (Bousquet-Elisseeff)
4. **Convergence analysis (gradient descent variants)** — smoothness + strong convexity → linear rate
5. **Information-theoretic bounds** — mutual information between hypothesis and data
6. **NTK / mean-field analysis** — wide-network and infinite-width limits
7. **Margin / Lipschitz arguments** — for robustness and adversarial bounds
8. **Concentration of measure** — for high-dimensional behavior, isoperimetric inequalities

---

## Selection Heuristic for Phase 2

When picking 5 from 8:

1. **Most relevant**: matches the surface structure of the problem
   - Symmetric expression → symmetry exploitation
   - Diophantine → modular arithmetic
   - Inequality → AM-GM / Cauchy
2. **Most distinct**: spans different mathematical machinery
   - Don't pick three angles that are all algebraic; mix algebraic + combinatorial + analytic
3. **Most cheap-to-test**: angles where 5–10 minutes of work tells you if it works
   - Modular arithmetic with small modulus is cheap; spectral decomposition of a 1000×1000 matrix is not
4. **Avoid duplicates**: induction often subsumes "structural decomposition"; pick one, not both
5. **Use Phase 1 hints**: if data shows pattern depends on parity, prioritize parity-aware angles (modular, coloring); if data shows extremal structure, prioritize extremal principle / probabilistic

## When Standard Angles Don't Apply

For research-level or exotic problems where no standard angle fits cleanly:
- Combine angles (e.g., spectral + probabilistic = random matrix theory)
- Look up the area's textbook table of contents and use top-level chapter names as candidate angles
- Phase 5 (Handoff) is appropriate if no angle gives traction within Phase 2's termination limits
