"""The target, compactly supported kernel, and interpolation operators.

Symmetric matrices are stored in a Frobenius-orthonormal basis.  The kernel
matrices have unit diagonal.  For interpolation this gives exactly the same
functions as delta**(-d) * phi(distance/delta).  A physical ridge parameter
lambda is converted to lambda * delta**d before solving the normalized system.
"""

from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.sparse import eye as sparse_eye
from scipy.sparse.linalg import LinearOperator, cg, eigsh
from scipy.spatial import cKDTree


def target_log(points):
    """Return B(x) in the basis (E11,E22,E33,(E12+E21)/sqrt(2),...)."""
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    x, y = points[:, 0], points[:, 1]
    return np.column_stack((
        np.sin(2*np.pi*x), np.cos(2*np.pi*y), x-y,
        np.sqrt(2)*0.5*np.cos(np.pi*x*y),
        np.sqrt(2)*0.3*np.sin(np.pi*(x+y)),
        np.sqrt(2)*0.4*x*y,
    ))


def to_symmetric(values):
    values = np.asarray(values, dtype=float)
    out = np.zeros(values.shape[:-1]+(3, 3))
    out[..., 0, 0], out[..., 1, 1], out[..., 2, 2] = np.moveaxis(values[..., :3], -1, 0)
    out[..., 0, 1] = out[..., 1, 0] = values[..., 3]/np.sqrt(2)
    out[..., 0, 2] = out[..., 2, 0] = values[..., 4]/np.sqrt(2)
    out[..., 1, 2] = out[..., 2, 1] = values[..., 5]/np.sqrt(2)
    return out


def training_grid(level):
    axis = np.linspace(0, 1, 2**level+1)
    x, y = np.meshgrid(axis, axis, indexing="ij")
    return np.column_stack((x.ravel(), y.ravel()))


def evaluation_points(resolution):
    """Cell midpoints plus the entire boundary, including each corner once.

    Interior points are off all training grids when resolution is a power of
    two at least 2**max_level.  Boundary points intentionally include data sites.
    """
    axis = (np.arange(resolution)+0.5)/resolution
    x, y = np.meshgrid(axis, axis, indexing="ij")
    interior = np.column_stack((x.ravel(), y.ravel()))
    edge = np.arange(resolution)/resolution
    boundary = np.vstack((
        np.column_stack((edge, np.zeros_like(edge))),
        np.column_stack((np.ones_like(edge), edge)),
        np.column_stack((1-edge, np.ones_like(edge))),
        np.column_stack((np.zeros_like(edge), 1-edge)),
    ))
    return np.vstack((interior, boundary))


def wendland_c2(radius):
    radius = np.asarray(radius)
    return np.maximum(1-radius, 0)**4 * (4*radius+1)


def kernel_matrix(points, centers_tree, support_radius):
    distances = cKDTree(points).sparse_distance_matrix(
        centers_tree, support_radius, output_type="coo_matrix"
    ).tocsr()
    distances.data[:] = wendland_c2(distances.data/support_radius)
    distances.eliminate_zeros()
    return distances


@dataclass
class KernelTerm:
    centers: np.ndarray
    radius: float
    coefficients: np.ndarray
    level: int

    def __post_init__(self):
        self.tree = cKDTree(self.centers)

    def evaluate(self, points):
        return kernel_matrix(np.asarray(points).reshape(-1, 2), self.tree, self.radius) @ self.coefficients


@dataclass
class KernelModel:
    terms: tuple
    scheme: str
    level: int

    def evaluate(self, points, batch_size=256):
        points = np.asarray(points, dtype=float).reshape(-1, 2)
        out = np.zeros((len(points), 6))
        for first in range(0, len(points), batch_size):
            part = points[first:first+batch_size]
            for term in self.terms:
                out[first:first+batch_size] += term.evaluate(part)
        return out


def interpolation_system(centers, radius, data, level, solver="cg", ridge=0., condition=False):
    """Fit a kernel term; ridge uses the delta**(-2)-normalized RKHS kernel."""
    matrix = kernel_matrix(centers, cKDTree(centers), radius)
    normalized_ridge = ridge*radius**centers.shape[1]
    system = matrix + normalized_ridge*sparse_eye(len(centers), format="csr")
    counts = np.diff(matrix.indptr)
    iterations = []
    if solver == "cholesky":
        dense = system.toarray()
        factor = cho_factor(dense, lower=True, check_finite=False)
        coefficients = cho_solve(factor, data, check_finite=False)
    elif solver == "cg":
        coefficients = np.empty_like(data)
        for column in range(data.shape[1]):
            steps = [0]
            def callback(_):
                steps[0] += 1
            coefficients[:, column], info = cg(
                system, data[:, column], rtol=3e-13, atol=0.,
                maxiter=1000, callback=callback,
            )
            if info != 0:
                raise RuntimeError(f"CG failed at level {level}, component {column}: {info}")
            iterations.append(steps[0])
    else:
        raise ValueError(f"Unknown solver: {solver}")
    relative_residual = np.linalg.norm(system@coefficients-data)/max(np.linalg.norm(data), 1e-300)
    statistics = {
        "level": int(level), "points": int(len(centers)), "radius": float(radius),
        "mean_nnz_per_row": float(np.mean(counts)), "max_nnz_per_row": int(np.max(counts)),
        "relative_linear_residual": float(relative_residual), "solver": solver,
        "cg_max_iterations": max(iterations, default=0), "ridge": float(ridge),
    }
    if condition:
        v0 = np.random.default_rng(107+level).normal(size=len(centers))
        largest = eigsh(matrix, k=1, which="LA", tol=1e-10, v0=v0, return_eigenvectors=False)[0]
        if solver == "cholesky" and ridge == 0:
            inverse = LinearOperator(matrix.shape, matvec=lambda v: cho_solve(factor, v, check_finite=False))
            smallest = eigsh(matrix, k=1, sigma=0., which="LM", OPinv=inverse,
                              tol=1e-10, v0=v0, return_eigenvectors=False)[0]
        else:
            smallest = eigsh(matrix, k=1, which="SA", tol=1e-10, v0=v0,
                              maxiter=10000, return_eigenvectors=False)[0]
        statistics["condition_number_2"] = float(largest/smallest)
    return KernelTerm(centers, radius, coefficients, level), statistics


def build_models(max_level=7, fixed_max_level=6, support_grid_spacings=4., conditions=True):
    """Construct multilevel, stationary, and fixed-radius single-level models."""
    models, statistics, corrections = [], [], []
    for level in range(2, max_level+1):
        centers = training_grid(level)
        data = target_log(centers)
        radius = support_grid_spacings*2.**(-level)
        previous = KernelModel(tuple(corrections), "multilevel", level-1).evaluate(centers)
        term, stats = interpolation_system(centers, radius, data-previous, level, condition=conditions)
        corrections.append(term)
        models.append(KernelModel(tuple(corrections), "multilevel", level))
        statistics.append(dict(stats, scheme="multilevel"))
        stationary, _ = interpolation_system(centers, radius, data, level)
        models.append(KernelModel((stationary,), "stationary", level))
        if level <= fixed_max_level:
            fixed, fixed_stats = interpolation_system(centers, .5, data, level,
                                                      solver="cholesky", condition=conditions)
            models.append(KernelModel((fixed,), "fixed", level))
            statistics.append(dict(fixed_stats, scheme="fixed"))
        print(f"Fitted level {level}: {len(centers)} sites", flush=True)
    return models, statistics
