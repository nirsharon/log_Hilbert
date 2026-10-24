"""Save the verified convergence data as PNG, JPG and vector PDF figures.

Run from the repository's python/ directory:
    python scripts/plot_convergence.py

For a separately downloaded script and CSV:
    python plot_convergence.py --input convergence.csv --output-dir figures

Requires Matplotlib. No LaTeX installation or numerical recomputation is needed.
"""

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Also works on servers without a display.
import matplotlib.pyplot as plt


SCHEMES = (
    ("multilevel", "Multilevel, scaled"),
    ("stationary", "Single scale, scaled"),
    ("fixed", "Single scale, fixed"),
)


def read_results(path):
    """Read the CSV's log-Euclidean errors, sorted by refinement level."""
    series = {name: {} for name, _ in SCHEMES}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"scheme", "level", "log_euclidean"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns {sorted(required)}")
        for row in reader:
            name = row["scheme"]
            level, error = int(row["level"]), float(row["log_euclidean"])
            if name not in series or level < 0 or not math.isfinite(error) or error <= 0:
                raise ValueError(f"Invalid convergence row: {row}")
            if level in series[name]:
                raise ValueError(f"Duplicate row for {name} at level {level}")
            series[name][level] = error
    if any(not points for points in series.values()):
        raise ValueError("CSV must contain data for all three schemes")
    return {name: sorted(points.items()) for name, points in series.items()}


def save_figure(input_path, output_dir, formats, dpi, width=6.4, height=3.4,
                font_size=14):
    """Export a compact figure with larger text and standard curve styling."""
    series = read_results(input_path)
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(width, height))
    for name, label in SCHEMES:
        points = series[name]
        # The dyadic grids have h_j = 2**(-j) / sqrt(2).
        inverse_h = [math.sqrt(2) * 2**level for level, _ in points]
        errors = [error for _, error in points]
        ax.loglog(inverse_h, errors, "o-", label=label)
    ax.set_xlabel(r"Inverse fill distance, $1/h_j$", fontsize=font_size)
    ax.set_ylabel("Max. log-Euclidean error", fontsize=font_size)
    ax.tick_params(axis="both", labelsize=font_size - 2)
    ax.legend(fontsize=font_size - 2)
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        for extension in dict.fromkeys(formats):
            output = output_dir / f"convergence.{extension}"
            options = {"pil_kwargs": {"quality": 95}} if extension == "jpg" else {}
            fig.savefig(output, dpi=dpi, **options)
            print(f"Saved {output}")
    finally:
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/convergence.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("figures"))
    parser.add_argument("--formats", nargs="+", choices=("png", "jpg", "pdf"),
                        default=["png", "jpg", "pdf"])
    parser.add_argument("--dpi", type=int, default=600,
                        help="Raster resolution; PDF curves and text remain vector graphics")
    parser.add_argument("--width", type=float, default=6.4, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=3.4, help="Figure height in inches")
    parser.add_argument("--font-size", type=float, default=14,
                        help="Axis-label size in points; ticks and legend are 2 points smaller")
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    if min(args.width, args.height) <= 0 or args.font_size <= 2:
        parser.error("Figure dimensions must be positive and --font-size must exceed 2")
    save_figure(args.input, args.output_dir, args.formats, args.dpi,
                args.width, args.height, args.font_size)


if __name__ == "__main__":
    main()
