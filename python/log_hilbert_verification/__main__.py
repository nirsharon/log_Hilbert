"""Command-line entry point; use one BLAS thread unless explicitly overridden."""

import os

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

from .reproduce import main

main()
