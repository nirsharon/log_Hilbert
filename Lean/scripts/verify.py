"""Build the Lean library and audit every exported declaration's axioms."""

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def main():
    source = (ROOT / "LogHilbert.lean").read_text(encoding="utf-8")
    if re.search(r"\b(sorry|admit|axiom|native_decide)\b", source):
        raise SystemExit("Proof source contains a prohibited placeholder or axiom mechanism")
    declarations = re.findall(
        r"(?m)^(?:@\[[^\n]*?\]\s*)?(?:noncomputable\s+)?"
        r"(?:def|abbrev|theorem)\s+([A-Za-z_][A-Za-z0-9_']*)", source
    )
    expected = {f"LogHilbert.{name}" for name in declarations}
    audit = (ROOT / "Audit.lean").read_text(encoding="utf-8")
    actual = set(re.findall(r"#print axioms ([\w.]+)", audit))
    if actual != expected:
        raise SystemExit(f"Audit declaration mismatch: missing={expected-actual}; extra={actual-expected}")

    subprocess.run(["lake", "build"], cwd=ROOT, check=True)
    result = subprocess.run(
        ["lake", "env", "lean", "-DwarningAsError=true", "Audit.lean"],
        cwd=ROOT, check=True, capture_output=True, text=True
    )
    print(result.stdout, end="")
    groups = re.findall(r"depends on axioms:\s*\[([^\]]*)\]", result.stdout)
    used = {name.strip() for group in groups for name in group.split(",") if name.strip()}
    if not used.issubset(ALLOWED_AXIOMS):
        raise SystemExit(f"Unexpected axioms: {sorted(used-ALLOWED_AXIOMS)}")
    if "sorryAx" in result.stdout or "sorryAx" in result.stderr:
        raise SystemExit("Unproved-placeholder dependency detected")
    print(f"Checked {len(expected)} declarations; axioms: {sorted(used)}")


if __name__ == "__main__":
    main()
