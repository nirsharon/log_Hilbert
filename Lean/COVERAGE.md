# Formal verification coverage

This is a partial formalization of `multiscale_log_hilbert_v5.tex`, whose exact
SHA-256 fingerprint is recorded in `verification/snapshot.json`.
All 46 included Lean definitions and lemmas pass the Lean 4.19.0 checker and
the axiom audit. This does **not** verify all proofs in the manuscript.

An abstract result assumes the paper's stated bijection/Hilbert-space setup.
It does not independently prove that a named manifold or matrix construction
satisfies that setup. A conditional recurrence theorem assumes its one-step
bound explicitly; it does not prove the analytic estimates leading to it.

| Manuscript result | Status in this package | Checked declarations or remaining work |
| --- | --- | --- |
| Proposition 2.5, transported Hilbert structure | Abstract result checked | `chartNormedGroup`, `chartModule`, `chartInnerProductSpace`, `chartLinearIsometry`, `transportedHilbert_complete`. Particular manifold/chart examples are not instantiated. |
| Proposition 3.1, transference | Abstract result checked | `transference`, `transference_norm`, `liftLinear`, `lift_idempotent`, `lift_norm_bound`, `functionChart`. Analytic function-space constructions are not independently developed. |
| Lemma 3.2, Sobolev/Moser smoothness | Not formalized | Fractional Sobolev spaces on the domain, tame composition estimates, cutoff/tubular extensions, and the C^k interpolation argument. No Lean conclusion about the disputed sigma dependence is claimed. |
| Theorem 3.3, sharp SPD metric comparison | Not formalized | Matrix log/exp differential estimates in the relevant norms, the affine-invariant distance and path-length argument, and sharpness. Numerical checks are not a substitute. |
| Theorem 3.4, invariant Lie-group metrics | Not formalized | Lie exponential differential, invariant Riemannian lengths, and compact-range inverse estimates. |
| Theorem 3.5, Riemannian/Hadamard comparison | Not formalized | Curvature assumptions, Rauch comparison and distance/path arguments. |
| Corollary 3.6, natural-metric error transfer | Not formalized | The preceding metric comparisons, eigenvalue perturbation and the uniform-constant Lq integration argument. |
| Theorem 4.1, kernel interpolation and penalized least squares | Not formalized | RKHS construction, strict kernel positivity, representer theorem, projection identification and coefficient equations. |
| Theorem 4.3, single-scale errors | Not formalized | Sobolev sampling inequalities and scalar kernel estimates, including their vector-valued extension. |
| Proposition 5.1, multilevel conjugacy | Abstract result checked | `iterate_conjugacy`, `residual_conjugacy`, `correction_conjugacy`, `commuting_diagram`. No linearity of the level operators is required. |
| Theorem 5.2, fixed-kernel telescoping | Hilbert projection argument checked; kernel instantiation pending | `telescoping`, `nested_projection_absorption`, `orthogonal_telescoping`. Theorem 4.1 must still identify the paper's kernel interpolants with these projections; the claimed error estimates require Theorem 4.3. |
| Theorem 5.3, scaled multilevel convergence | Not formalized; supporting recurrence checked | `geometric_recurrence` and `geometric_recurrence_tendsto` check only a generic scalar implication. Native-space bounds, sampling, fill-distance power identities, and the paper's contraction hypotheses remain to be formalized. |
| Proposition 6.1, sparsity/conditioning | Not formalized | Packing estimates and eigenvalue bounds for kernel matrices. |
| Proposition 6.2, computational complexity | Not formalized | A computational cost model, data-structure assumptions and asymptotic operation counts. |
| Theorem 7.1, compact groups | Not formalized | Theorem 3.4, principal-chart retention and compact inverse estimates. |
| Proposition 7.2, cubic Karcher comparison | Not formalized; positive-radius clarification needed | Existence/uniqueness, Hessian comparison, BCH remainder and cancellation, and the final metric estimate. |
| Proposition 7.3, quadratic comparison and sharp example | Not formalized; positive-radius clarification needed | Recentring isometries, uniform Taylor bounds, the preceding cubic result, and the explicit SPD asymptotic calculation. |
| Lemma B.1, scaled native norms | Not formalized | Fourier/native norm equivalence, restriction/minimal extensions and Stein's extension operator. |

Other checked supporting statements include transported addition identities,
metric completeness, the ordered residual-operator identity, vanishing
interpolation residuals, and weighted affine equivariance. They do not complete
the unformalized numbered results listed above. The manifold examples and other
unnumbered claims are also outside a claim of full verification.

## Boundary clarification

With the paper's open-ball convention, at r=0 the balls B(e,2r) and
B(exp(X0),2*c_R*r) are empty. Thus the existence of a minimizer in those balls
cannot be asserted, even for a single zero-spread datum. This elementary fact
is checked by `no_minimizer_at_zero_radius`. Require `0 < r` in Propositions
7.2 and 7.3, or state the zero-spread case separately. The suggested wording is recorded in `UNVERIFIED.md`. This finding is a statement-level clarification and is not
a verification or refutation of the positive-radius analytic estimates.

## What remains before a full verification claim

Priority is Lemma 3.2 and Theorem 3.3, followed by the kernel/native-space and
sampling results needed for Theorem 5.3. The Lie/Riemannian and Karcher analyses
must then be formalized against actual geometric definitions. Replacing these
steps by hypotheses would produce conditional results and would not complete
the requested verification of the paper.
