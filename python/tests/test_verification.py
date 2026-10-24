"""Mathematical consistency checks independent of the displayed decimal values."""

import unittest

import numpy as np
from scipy.linalg import expm
from scipy.spatial import cKDTree

from log_hilbert_verification.geometry import (
    heisenberg_experiment, karcher_experiment, lambda_distortion,
    metric_errors, sharpness_experiment, symmetric_exp,
)
from log_hilbert_verification.numerics import (
    KernelModel, evaluation_points, interpolation_system, kernel_matrix,
    target_log, to_symmetric, training_grid,
)


class NumericalVerificationTests(unittest.TestCase):
    def test_publication_midpoints_are_off_all_training_grids(self):
        resolution = 128
        points = evaluation_points(resolution)
        interior = points[:resolution**2]
        self.assertEqual(len(np.unique(points, axis=0)), resolution**2+4*resolution)
        for level in range(2, 8):
            distances, _ = cKDTree(training_grid(level)).query(interior)
            self.assertGreater(float(distances.min()), 1e-14)

    def test_matrix_coordinates_are_frobenius_orthonormal(self):
        values = np.random.default_rng(7).normal(size=(13, 6))
        np.testing.assert_allclose(np.linalg.norm(values, axis=1),
                                   np.linalg.norm(to_symmetric(values), axis=(1, 2)), rtol=2e-15)

    def test_symmetric_exponential_matches_general_matrix_exponential(self):
        matrices = to_symmetric(np.random.default_rng(11).normal(size=(5, 6)))
        np.testing.assert_allclose(symmetric_exp(matrices), np.array([expm(x) for x in matrices]),
                                   rtol=1e-13, atol=1e-13)

    def test_sparse_evaluation_has_no_explicit_support_boundary_zeros(self):
        centers = training_grid(3)
        matrix = kernel_matrix(centers, cKDTree(centers), .5)
        self.assertTrue(np.all(matrix.data > 0))
        self.assertEqual(int(np.diff(matrix.indptr).max()), 45)

    def test_interpolation_fits_all_six_components(self):
        centers = training_grid(3)
        term, _ = interpolation_system(centers, .5, target_log(centers), 3)
        np.testing.assert_allclose(term.evaluate(centers), target_log(centers), rtol=1e-11, atol=2e-12)

    def test_ridge_normalization_matches_physical_kernel(self):
        centers, radius, ridge = training_grid(2), .5, .01
        data = target_log(centers)
        term, _ = interpolation_system(centers, radius, data, 2, solver="cholesky", ridge=ridge)
        a0 = kernel_matrix(centers, cKDTree(centers), radius).toarray()
        physical_coefficients = np.linalg.solve(a0/radius**2+ridge*np.eye(len(centers)), data)
        np.testing.assert_allclose(term.coefficients, physical_coefficients/radius**2,
                                   rtol=2e-13, atol=2e-13)

    def test_fixed_kernel_nested_residual_correction_telescopes(self):
        terms = []
        for level in (2, 3, 4):
            centers = training_grid(level)
            residual = target_log(centers)-KernelModel(tuple(terms), "test", level-1).evaluate(centers)
            term, _ = interpolation_system(centers, .5, residual, level, solver="cholesky")
            terms.append(term)
        single, _ = interpolation_system(centers, .5, target_log(centers), 4, solver="cholesky")
        points = evaluation_points(17)
        np.testing.assert_allclose(KernelModel(tuple(terms), "test", 4).evaluate(points),
                                   single.evaluate(points), rtol=2e-12, atol=2e-12)

    def test_principal_spd_metric_comparisons(self):
        generator = np.random.default_rng(19)
        truth, approximation = generator.normal(size=(50, 6)), generator.normal(size=(50, 6))
        errors, distortion, frobenius_bound = metric_errors(truth, approximation)
        self.assertTrue(np.all(errors[:, 1]+1e-10 >= errors[:, 0]))
        self.assertTrue(np.all(errors[:, 1] <= distortion*errors[:, 0]+1e-10))
        self.assertTrue(np.all(errors[:, 2] <= frobenius_bound+1e-10))
        self.assertEqual(float(lambda_distortion(0.)), 1.)

    def test_sharpness_family_approaches_the_bound(self):
        for row in sharpness_experiment():
            if row['epsilon'] == .0001:
                self.assertAlmostEqual(row['measured_ratio'], row['limiting_bound'], delta=2e-6)

    def test_karcher_example_has_the_claimed_quadratic_coefficient(self):
        row = karcher_experiment()[-1]
        self.assertAlmostEqual(row['distance_over_t_squared'], row['limiting_coefficient'], delta=2e-6)

    def test_nonabelian_heisenberg_left_affinity(self):
        result = heisenberg_experiment()
        self.assertLess(result['bch_error'], 1e-13)
        self.assertLess(result['left_equivariance_error'], 1e-13)


if __name__ == "__main__":
    unittest.main()
