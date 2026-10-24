"""Run the numerical experiments and write CSV and JSON results."""

import argparse
import csv
import heapq
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize

from .geometry import (heisenberg_experiment, karcher_experiment, lambda_distortion,
                       metric_errors, sharpness_experiment)
from .numerics import (KernelModel, build_models, evaluation_points,
                       interpolation_system, target_log, to_symmetric, training_grid)

METRICS = ("log_euclidean", "affine_invariant", "frobenius")


class ErrorRecord:
    def __init__(self):
        self.values = np.zeros(3)
        self.points = np.zeros((3, 2))
        self.seeds = [[] for _ in METRICS]
        self.counter = 0
        self.maximum_ratio = 1.
        self.maximum_distortion = 1.

    def update(self, points, errors, distortion, frobenius_bound):
        tolerance = 2e-10
        if np.any(errors[:, 1]+tolerance < errors[:, 0]):
            raise AssertionError("Affine-invariant lower comparison failed")
        if np.any(errors[:, 1] > distortion*errors[:, 0]+tolerance):
            raise AssertionError("Affine-invariant upper comparison failed")
        if np.any(errors[:, 2] > frobenius_bound+tolerance):
            raise AssertionError("Frobenius comparison failed")
        reliable = errors[:, 0] > 1e-9
        if np.any(reliable):
            self.maximum_ratio = max(self.maximum_ratio, float(np.max(errors[reliable, 1]/errors[reliable, 0])))
        self.maximum_distortion = max(self.maximum_distortion, float(np.max(distortion)))
        for metric in range(3):
            index = int(np.argmax(errors[:, metric]))
            if errors[index, metric] > self.values[metric]:
                self.values[metric] = errors[index, metric]
                self.points[metric] = points[index]
            count = min(8, len(points))
            candidates = np.argpartition(errors[:, metric], -count)[-count:]
            for index in candidates:
                self.counter += 1
                item = (float(errors[index, metric]), self.counter, points[index].copy())
                if len(self.seeds[metric]) < 64:
                    heapq.heappush(self.seeds[metric], item)
                elif item[0] > self.seeds[metric][0][0]:
                    heapq.heapreplace(self.seeds[metric], item)


def sample_models(models, resolution, batch_size):
    """Reuse each multilevel correction across all prefix approximants."""
    points = evaluation_points(resolution)
    records = {(model.scheme, model.level): ErrorRecord() for model in models}
    multilevel = sorted((model for model in models if model.scheme == "multilevel"), key=lambda m: m.level)
    independent = [model for model in models if model.scheme != "multilevel"]
    for first in range(0, len(points), batch_size):
        part = points[first:first+batch_size]
        truth = target_log(part)
        approximation = np.zeros_like(truth)
        for model in multilevel:
            approximation += model.terms[-1].evaluate(part)
            errors, distortion, bound = metric_errors(truth, approximation)
            records[(model.scheme, model.level)].update(part, errors, distortion, bound)
        for model in independent:
            approximation = model.terms[0].evaluate(part)
            errors, distortion, bound = metric_errors(truth, approximation)
            records[(model.scheme, model.level)].update(part, errors, distortion, bound)
    return records


def refine_record(model, record, number_of_starts=4):
    """Find local peaks from strong grid candidates, separately for each metric.

    This improves a sampled maximum. It does not certify a continuum supremum.
    """
    h = 2.**(-model.level)
    values, points = record.values.copy(), record.points.copy()
    for metric in range(3):
        starts = []
        for _, _, candidate in sorted(record.seeds[metric], key=lambda v: v[0], reverse=True):
            if all(np.linalg.norm(candidate-start) >= h/3 for start in starts):
                starts.append(candidate)
            if len(starts) >= number_of_starts:
                break
        normalization = max(record.values[metric], 1e-12)
        def objective(point):
            point = np.asarray(point).reshape(1, 2)
            errors, _, _ = metric_errors(target_log(point), model.evaluate(point))
            return -float(errors[0, metric])/normalization
        for start in starts:
            simplex = np.tile(start, (3, 1))
            for coordinate in range(2):
                step = .2*h if start[coordinate]+.2*h <= 1 else -.2*h
                simplex[coordinate+1, coordinate] += step
            result = minimize(objective, start, method="Nelder-Mead", bounds=[(0., 1.), (0., 1.)],
                              options={"initial_simplex": simplex, "maxiter": 250,
                                       "xatol": 1e-10, "fatol": 2e-10})
            value = -float(result.fun)*normalization
            if value > values[metric]:
                values[metric], points[metric] = value, result.x
    return values, points


def telescoping_experiment(last_level=5):
    points = evaluation_points(97)
    result = {}
    for ridge in (0., .01):
        terms = []
        largest_residual = 0.
        for level in range(2, last_level+1):
            centers = training_grid(level)
            residual = target_log(centers)-KernelModel(tuple(terms), "fixed_multilevel", level-1).evaluate(centers)
            term, stats = interpolation_system(centers, .5, residual, level, solver="cholesky", ridge=ridge)
            terms.append(term)
            largest_residual = max(largest_residual, stats["relative_linear_residual"])
        centers = training_grid(last_level)
        single, _ = interpolation_system(centers, .5, target_log(centers), last_level,
                                         solver="cholesky", ridge=ridge)
        difference = KernelModel(tuple(terms), "fixed_multilevel", last_level).evaluate(points)-single.evaluate(points)
        absolute = float(np.linalg.norm(difference, axis=1).max())
        relative = absolute/float(np.linalg.norm(target_log(points), axis=1).max())
        result["exact" if ridge == 0 else "ridge"] = dict(
            maximum_absolute_difference=absolute, maximum_relative_difference=relative,
            physical_ridge_parameter=ridge, normalized_ridge_parameter=ridge*.5**2,
            largest_relative_linear_residual=largest_residual, last_level=last_level,
        )
    return result


def target_geometry_experiment():
    """Locate the target log-norm and spectral-spread peaks independently."""
    points = evaluation_points(128)
    matrices = to_symmetric(target_log(points))
    spectra = np.linalg.eigvalsh(matrices)
    initial = (np.linalg.norm(matrices, axis=(1, 2)), spectra[:, -1]-spectra[:, 0])
    answer = {}
    for name, values in zip(("maximum_log_frobenius_norm", "maximum_log_condition_number"), initial):
        start = points[int(np.argmax(values))]
        def objective(point):
            b = to_symmetric(target_log(np.asarray(point).reshape(1, 2)))[0]
            if name == "maximum_log_frobenius_norm":
                return -float(np.linalg.norm(b))
            spectrum = np.linalg.eigvalsh(b)
            return -float(spectrum[-1]-spectrum[0])
        result = minimize(objective, start, method="Nelder-Mead", bounds=[(0., 1.), (0., 1.)],
                          options={"xatol": 1e-12, "fatol": 1e-13, "maxiter": 300})
        answer[name] = -float(result.fun)
        answer[name+"_location"] = result.x.tolist()
    answer["metric_distortion_at_maximum_spread"] = float(lambda_distortion(answer["maximum_log_condition_number"]))
    return answer


def legacy_midpoint_experiment(models):
    """Reproduce the two under-resolution checks from the earlier review."""
    multilevel = sorted((m for m in models if m.scheme == "multilevel"), key=lambda m:m.level)
    stationary = max((m for m in models if m.scheme == "stationary"), key=lambda m:m.level)
    rows = []
    for resolution in (97, 193):
        axis = (np.arange(resolution)+.5)/resolution
        x, y = np.meshgrid(axis, axis, indexing="ij")
        points = np.column_stack((x.ravel(), y.ravel()))
        maxima = np.zeros(len(multilevel))
        stationary_maximum = 0.
        for first in range(0, len(points), 512):
            part = points[first:first+512]
            truth = target_log(part)
            approximation = np.zeros_like(truth)
            for j, model in enumerate(multilevel):
                approximation += model.terms[-1].evaluate(part)
                maxima[j] = max(maxima[j], float(np.linalg.norm(truth-approximation, axis=1).max()))
            stationary_maximum = max(stationary_maximum, float(np.linalg.norm(truth-stationary.evaluate(part), axis=1).max()))
        for j, model in enumerate(multilevel):
            rows.append(dict(resolution=resolution, scheme="multilevel", level=model.level,
                             midpoint_maximum_log_error=float(maxima[j])))
        rows.append(dict(resolution=resolution, scheme="stationary", level=stationary.level,
                         midpoint_maximum_log_error=stationary_maximum))
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--max-level", type=int, default=7)
    parser.add_argument("--fixed-max-level", type=int, default=6)
    parser.add_argument("--grids", type=int, nargs="+", default=[256, 512])
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--quick", action="store_true", help="Smoke test; writes only to the explicitly selected output directories")
    arguments = parser.parse_args(argv)
    if arguments.quick:
        arguments.max_level = arguments.fixed_max_level = 4
        arguments.grids = [32, 64]
        if arguments.output == Path("results"):
            parser.error("Use --output with a temporary directory for --quick")
    if arguments.max_level < 3 or min(arguments.grids) < 2**arguments.max_level:
        parser.error("Use max-level >= 3 and midpoint grids resolving the finest training grid")
    if arguments.fixed_max_level < 2 or arguments.batch_size < 1:
        parser.error("fixed-max-level must be at least 2 and batch-size must be positive")
    arguments.grids = sorted(set(arguments.grids))
    if len(arguments.grids) < 2:
        parser.error("At least two distinct evaluation grids are required")
    started = time.monotonic()
    arguments.output.mkdir(parents=True, exist_ok=True)
    models, statistics = build_models(arguments.max_level, arguments.fixed_max_level)
    grid_rows, final_rows, last_refined = [], [], None
    for resolution in arguments.grids:
        print(f"Sampling {resolution} x {resolution} midpoints and {4*resolution} boundary points", flush=True)
        sampled = sample_models(models, resolution, arguments.batch_size)
        refined = {}
        for model in models:
            record = sampled[(model.scheme, model.level)]
            values, points = refine_record(model, record)
            key = (model.scheme, model.level)
            refined[key] = values
            row = dict(scheme=model.scheme, level=model.level, evaluation_resolution=resolution)
            for metric, name in enumerate(METRICS):
                row[f"sampled_{name}"] = float(record.values[metric])
                row[f"refined_{name}"] = float(values[metric])
            grid_rows.append(row)
            if resolution == arguments.grids[-1]:
                row = dict(scheme=model.scheme, level=model.level,
                           **{name: float(values[i]) for i, name in enumerate(METRICS)},
                           log_euclidean_max_x=float(points[0, 0]), log_euclidean_max_y=float(points[0, 1]),
                           maximum_observed_ai_over_log_euclidean=record.maximum_ratio,
                           maximum_distortion_bound=record.maximum_distortion, rate=None)
                final_rows.append(row)
        if last_refined is not None:
            refinement_difference = max(float(np.max(np.abs(refined[k]-last_refined[k])/np.maximum(refined[k], 1e-15)))
                                        for k in refined)
        last_refined = refined
        print(f"Refined finest multilevel log error: {refined[('multilevel',arguments.max_level)][0]:.10e}", flush=True)
    if refinement_difference > 2e-3:
        raise RuntimeError(f"Peak estimates changed by {refinement_difference:.3g}; increase --grids or refinement starts")
    for scheme in ("multilevel", "stationary", "fixed"):
        previous = None
        for row in sorted((row for row in final_rows if row["scheme"] == scheme), key=lambda r:r["level"]):
            if previous is not None:
                row["rate"] = float(np.log2(previous/row["log_euclidean"]))
            previous = row["log_euclidean"]
    summary = dict(
        python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
        configuration=dict(max_level=arguments.max_level, fixed_max_level=arguments.fixed_max_level,
                           evaluation_grids=arguments.grids, cg_relative_tolerance=3e-13,
                           peak_starts=4, metric_comparison_absolute_tolerance=2e-10,
                           kernel_normalization="unit diagonal; ridge converted by delta**2"),
        interpretation="Refined numerical maxima, not certified continuum suprema.",
        largest_refinement_relative_difference=refinement_difference,
        telescoping=telescoping_experiment(min(5, arguments.max_level)),
        target_geometry=target_geometry_experiment(),
        heisenberg=heisenberg_experiment(), elapsed_seconds=time.monotonic()-started,
    )
    write_csv(arguments.output/"convergence.csv", final_rows)
    write_csv(arguments.output/"grid_refinement.csv", grid_rows)
    write_csv(arguments.output/"linear_systems.csv", statistics)
    write_csv(arguments.output/"spd_sharpness.csv", sharpness_experiment())
    write_csv(arguments.output/"karcher_quadratic.csv", karcher_experiment())
    write_csv(arguments.output/"legacy_midpoint_sampling.csv", legacy_midpoint_experiment(models))
    summary["elapsed_seconds"] = time.monotonic()-started
    (arguments.output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote numerical results to {arguments.output}", flush=True)


if __name__ == "__main__":
    main()
