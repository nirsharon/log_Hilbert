# Results still needing complete Lean verification

**Unverified here means not fully checked in this Lean project. It does not
classify the written result as true or false.** Of the 18 numbered results,
three abstract results are checked (2.5, 3.1, 5.1), and 15 need further work.
Theorem 5.2 already has a checked projection proof, and Theorem 5.3 has checked
generic recurrence lemmas; their full manuscript statements remain pending.
Examples and other unnumbered assertions are not all formalized either.

## Recommended approach

1. Keep mathematical claims supported by complete written proofs or precise
   references. Treat complete Lean formalization as a separate project rather
   than a prerequisite for submission. The current package should be described
   as a formalization of the algebraic core only.
2. Prioritize 3.2 and 3.3 because the former is a crucial regularity input and
   the latter is a central geometric contribution. Next connect the checked
   algorithms to kernel interpolation and establish the analytic inputs to 5.3.
3. Reuse existing Mathlib theorems where their hypotheses and conclusions
   match exactly. Keep standard results imported from the literature distinct
   from new paper-specific arguments. Missing results must not be postulated
   and then reported as proved. Any conditional intermediate statement should
   state its remaining hypotheses explicitly.
4. Track one task per result below. A task is complete only when the original
   hypotheses/conclusion have been matched, all dependencies are accounted for,
   the project builds and the axiom audit passes.

## Pending results

| Result | Missing formalization or completion criterion | Priority |
| --- | --- | --- |
| **Lemma 3.2: pulled-back smoothness / Moser estimate** | Formalize or import the correct Sobolev composition estimate, with its constant depending on the bounded range rather than the high Sobolev norm. Establish both chart directions, cutoff/tubular extension and the C^k statement. The questioned dependence on sigma is not Lean-verified. | First |
| **Theorem 3.3: sharp SPD metric comparison** | Define the relevant matrix log/exp, norms and affine-invariant distance; prove differential and path-length estimates, the lower bound and sharpness of the upper constant. Numerical examples do not prove the inequality or sharpness. | First |
| **Theorem 3.4: invariant metrics on Lie groups** | Prove the exponential differential formula, the invariant-length bounds, the bi-invariant constant-one result and the compact-range lower comparison. | Geometric extensions |
| **Theorem 3.5: local and Hadamard comparison** | Supply the curvature/Rauch comparison and the path/distance arguments under the stated radius and convexity hypotheses. | Geometric extensions |
| **Corollary 3.6: error transfer to natural metrics** | Apply the geometric comparisons with rigorously uniform constants; include eigenvalue perturbation and the Lq argument. The abstract norm identity in Proposition 3.1 does not prove these comparisons. | After metric comparisons |
| **Theorem 4.1: kernel interpolation and penalized least squares** | Construct the RKHS setting and verify positive Gram matrices, representer/minimum-norm assertions, projection identification and the regularized coefficient equations. | Analytic backbone |
| **Theorem 4.3: single-scale errors** | Supply the scalar Sobolev sampling/approximation bounds and their vector-valued extension with the claimed constants and orders. | Analytic backbone |
| **Theorem 5.2: fixed-kernel telescoping, full kernel statement** | Instantiate the already checked nested orthogonal projections with the paper's RKHS interpolants using 4.1, and transfer the error estimates using 4.3. The abstract telescoping proof itself is checked. | Analytic backbone |
| **Theorem 5.3: multilevel convergence with scaled kernels** | Prove that the actual residuals satisfy the native-space and sampling bounds; derive the stated contraction factor, L2/L-infinity estimates, rates and natural-metric consequences. The checked scalar recurrence is conditional on its one-step bound. | Analytic backbone |
| **Proposition 6.1: sparsity and level-independent conditioning** | Prove the packing count and kernel-matrix eigenvalue estimates, including the lower spectral bound and scaling argument. | After kernel theory |
| **Proposition 6.2: computational complexity** | Choose a computational cost model and formalize the data-structure assumptions, operation/memory counts and asymptotic bounds. | Later |
| **Theorem 7.1: compact groups** | Establish the required global exponential distance bound, retention in the principal chart and the compact inverse comparison. | After Lie metrics |
| **Proposition 7.2: cubic Karcher comparison** | Prove existence/uniqueness, Hessian comparison, the BCH remainder, cancellations and the final distance bound. Clarify the positive-radius assumption first. | Karcher analysis |
| **Proposition 7.3: quadratic comparison and sharp example** | Prove recentering isometries, uniform Taylor estimates, the preceding cubic input and the explicit SPD asymptotic coefficient. Clarify the positive-radius assumption first. | Karcher analysis |
| **Lemma B.1: scaled native-space norms** | Establish Fourier/native norm equivalence, restriction/minimal-extension facts and the extension operator with the required L2 and Sobolev bounds. | Analytic backbone |

## Immediate statement clarification

For Proposition 7.2, use `0 < r <= r_0`. For Proposition 7.3, require
`0 < r <= r_1` in addition to the data-spread bound. Alternatively, state the
zero-spread case separately. At r=0 the relevant open ball is empty, so it
cannot contain the claimed minimizer. This wording correction does not itself
verify the positive-radius analytic estimates.
