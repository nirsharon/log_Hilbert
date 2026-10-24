# Validation environment

The source was checked using the official Lean 4.19.0 Linux binary and Mathlib
`v4.19.0`, commit `c44e0c8ee63ca166450922a373c7409c5d26b00b`. The Lean binary
and kernel were not edited. The commands in `../README.md` are the normal setup
and check procedure; no host-specific setup utility is needed in this repository.

On the original validation host, process PID namespace and procfs numbering
were different. A small libc executable-path compatibility wrapper redirected
Lean's own-process `/proc/<getpid()>/exe` lookup to `/proc/self/exe`. It changed
no proof, elaboration or kernel function. Archive extraction also used
`TAR_OPTIONS=--no-same-owner` because restoring distributor ownership IDs was
unsupported on that host.

The initial mathematical cache was obtained from upstream cache routines after
an optional editor-asset download failed. No Mathlib theorem source was changed.
The final project passed standard `lake build` and the project's full axiom
audit. The relocated `Lean/` directory is checked again during repository
packaging. Its mathematical source and pinned dependency files are unchanged.
