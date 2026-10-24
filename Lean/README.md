# Lean verification

**This is a partial formalization, not a verification of the entire paper.**
The mathematical source contains 46 checked definitions and lemmas for the
transported Hilbert structure, abstract transference, conjugacy, projection
telescoping and supporting algebra. In particular, Lemma 3.2 and the sharp SPD
metric theorem are not yet formalized.

There are two independent directories at the repository root:
`Lean/` for formal proofs and `python/` for numerical experiments and figures.
Neither contains the manuscript or a document build system.

## Reproduce the Lean checks

Install Lean using the [official instructions](https://lean-lang.org/install/).
Git and Python 3 are also needed. From the repository root:

```bash
cd Lean
elan toolchain install leanprover/lean4:v4.19.0
lake update
lake exe cache get
python3 scripts/verify.py
```

Lean 4.19.0 and Mathlib `v4.19.0` are pinned for reproducibility. The first setup
downloads dependencies and their compiled cache, requiring several GB of disk
space. Later checks reuse that installation.

The verification script runs `lake build`, checks that the audit includes every
exported definition/theorem, then checks `Audit.lean` with warnings treated as
errors. It rejects unproved placeholders and any axiom outside the standard
classical foundations `propext`, `Classical.choice` and `Quot.sound`.

## Scope and files

- `LogHilbert.lean`: the checked mathematical source.
- `Audit.lean`: an axiom-dependency audit of all 46 definitions and lemmas.
- `COVERAGE.md`, `coverage.csv`: status of all 18 numbered manuscript results.
- `UNVERIFIED.md`: the 15 results still needing complete verification, with priorities and completion criteria.
- `scripts/verify.py`: the repeatable build and audit.
- `verification/`: audit output, source/dependency fingerprints and validation-host notes.

The abstract results checked are Proposition 2.5 (transported Hilbert space),
Proposition 3.1 (transference and inherited linearity/idempotence/norm bounds),
and Proposition 5.1 (multilevel conjugacy). The Hilbert-space projection
argument of Theorem 5.2 is checked, but its kernel/RKHS instantiation and error
consequences remain pending. Generic recurrence lemmas check conditional
scalar bounds, not the analytic hypotheses needed for Theorem 5.3.

The chart is a genuine bijection. Its smoothness and the existence of named
matrix logarithms are separate geometric facts. Lean level indices start at
zero: `Q 0` is the first operator, so the telescoping statement uses
`iterate ... (n+1) = P n b`.

The stored audit and fingerprints document a successful check of this source.
Rerun the verification after changing a proof. The number of Lean declarations
is not the number of verified paper theorems. Numerical tests in `../python/`
do not replace missing formal proofs.

## Missing results and submission

Keep the missing results explicitly marked in `UNVERIFIED.md`. A missing Lean
proof is not evidence that a written theorem is false. Mathematical claims in
the paper still need complete written proofs or precise citations. Do not
describe the manuscript as fully Lean-verified.

Prioritize the Sobolev composition lemma (3.2), the sharp SPD comparison (3.3),
and the analytic/kernel results needed for multilevel convergence (4.1, B.1,
4.3, 5.2, 5.3). The detailed list explains which parts are already checked and
which foundations remain to be supplied. Unverified results have not been
silently inserted as axioms.

Propositions 7.2 and 7.3 also need a positive radius `0 < r`, or a separate
zero-radius case: the stated open ball containing the minimizer is empty at
r=0. This statement-level clarification is checked by
`no_minimizer_at_zero_radius`; the positive-radius estimates remain unverified.
