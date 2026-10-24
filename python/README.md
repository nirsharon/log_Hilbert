# Python numerical verification

Numerical experiments and figure generation for multilevel log-Hilbert kernel
approximation. This directory is independent of the Lean project. It contains
no manuscript, bibliography, LaTeX exporter or document build system.

The experiment compares multilevel residual correction with scaled kernels,
single-scale interpolation with the same scaled kernels, and fixed-radius
interpolation. The target is a smooth 3-by-3 positive definite matrix field,
represented through its symmetric matrix logarithm.

## Install and check

From the repository root:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

On Windows, activate with `.venv\Scripts\activate`. Use Python 3.12.
Pinned dependencies are NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8.
No external data, account or API key is required.

## Reproduce the numerical results

Run from this directory:

```bash
python -m log_hilbert_verification
```

This regenerates the CSV and JSON files in `results/`. It does not generate
any document or LaTeX file. The checked-in full run took about two minutes;
runtime depends on the machine. The largest dense system has 4225 sites, so
several GB of available memory are suitable.

For a quick check that leaves the checked-in results unchanged:

```bash
python -m log_hilbert_verification --quick --output /tmp/log-hilbert-check
```

On Windows, substitute a suitable temporary output directory. The quick mode
requires an explicit output directory and refuses the default `results/` path.

The module entry point sets BLAS thread counts to one unless already set. For
explicit control on Unix-like systems:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m log_hilbert_verification
```

## Generate the figure

From the existing verified CSV, without rerunning the numerical experiments:

```bash
python scripts/plot_convergence.py
```

This writes `figures/convergence.png` and `figures/convergence.jpg` at 600 dpi
(3840 by 2880 pixels), and `figures/convergence.pdf` with vector curves and text.
It uses standard Matplotlib styling, point markers and automatic axes/legend.
The three curves show maximum log-Euclidean error against inverse fill distance,
`1/h_j = sqrt(2) * 2**j`. There is no fitted or reference curve.

Other formats, resolution and output paths are supported:

```bash
python scripts/plot_convergence.py --formats pdf
python scripts/plot_convergence.py --formats png jpg --dpi 1200
python scripts/plot_convergence.py --output-dir /tmp/log-hilbert-figures
```

## Results and interpretation

| File | Contents |
| --- | --- |
| `results/convergence.csv` | Refined maximum-error estimates in log-Euclidean, affine-invariant and Frobenius metrics, locations and measured rates |
| `results/grid_refinement.csv` | Sampled and locally refined maxima at each evaluation resolution |
| `results/linear_systems.csv` | Support radii, condition estimates, sparsity, CG iterations and residuals |
| `results/summary.json` | Configuration, dependency versions, target geometry, telescoping and Heisenberg checks |
| `results/spd_sharpness.csv` | Numerical sharpness family for the metric-distortion bound |
| `results/karcher_quadratic.csv` | Quadratic Karcher comparison and limiting coefficient |
| `results/legacy_midpoint_sampling.csv` | Earlier 97-square and 193-square sampling diagnostics |

The multilevel and stationary schemes use dyadic levels 2 through 7 and support
radius `4 * 2**(-level)`. The fixed-radius scheme uses radius 1/2 through level 6.
It stops there because its dense solves grow substantially in memory and cost.

The multilevel log-Euclidean error decreases approximately as follows:

| Level | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- |
| Error | 1.19e-1 | 3.62e-2 | 1.19e-2 | 3.89e-3 | 1.28e-3 | 4.21e-4 |
| Dyadic rate | | 1.71 | 1.61 | 1.61 | 1.61 | 1.60 |

Errors are estimated from 256-square and 512-square midpoint grids, their
boundaries, and local optimisation from strong candidates for each metric
separately. Interior seeds are off the training grids; boundary points can
include data sites. Agreement between refined estimates is checked. These are
numerical estimates, not certified global suprema or proofs of convergence.
The theorem's non-explicit contraction conditions are not certified by the run.

To add a finer evaluation grid while preserving the checked-in data:

```bash
python -m log_hilbert_verification --grids 256 512 1024 --output results_finer
```

Rates use unrounded errors. Small last-digit differences across numerical
library and BLAS builds are expected. The legacy sampling data are diagnostics
and do not supply the displayed convergence curve.

## Numerical conventions

The symmetric matrix field has six Frobenius-orthonormal coordinates; the
off-diagonal coordinates include a factor of `sqrt(2)`. Interpolation systems
use unit-diagonal Wendland kernel matrices. For physical
`Phi_delta = delta**(-2) * phi`, a physical ridge parameter `lambda` becomes
`lambda * delta**2` in that normalized system. Thus `lambda=0.01` at radius 1/2
means normalized ridge 0.0025.

Scaled systems use CG with relative tolerance `3e-13`; fixed systems use
Cholesky. Stored support-boundary zeros are removed before nonzeros are counted.
SPD metric inequalities are checked at sampled points within the stated
floating-point tolerances. These numerical checks complement the Lean source
in `../Lean/`; they do not extend its formal verification coverage.

## Code layout

- `log_hilbert_verification/numerics.py`: target, kernel, fitting and evaluation.
- `log_hilbert_verification/geometry.py`: metric, sharpness, Karcher and Heisenberg checks.
- `log_hilbert_verification/reproduce.py`: experiments, refinement, CSV and JSON output.
- `scripts/plot_convergence.py`: standard Matplotlib image exports.
- `tests/test_verification.py`: 11 mathematical/numerical checks.

Run commands from this directory so that relative `results/` and `figures/`
paths resolve as documented. The directory can also be installed with
`python -m pip install .`, exposing the `log-hilbert-verify` command.
