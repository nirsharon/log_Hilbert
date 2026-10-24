"""SPD distances and independent checks of the comparison constants."""

import numpy as np

from .numerics import to_symmetric


def symmetric_exp(matrix, multiplier=1.):
    values, vectors = np.linalg.eigh(matrix)
    return (vectors*np.exp(multiplier*values)[..., None, :])@np.swapaxes(vectors, -1, -2)


def lambda_distortion(omega):
    x = np.asarray(omega, dtype=float)/2
    return np.divide(np.sinh(x), x, out=np.ones_like(x), where=x != 0)


def metric_errors(truth_log, approximation_log):
    """Return log-Euclidean, affine-invariant, Frobenius errors and bounds."""
    truth = to_symmetric(truth_log)
    approximate = to_symmetric(approximation_log)
    le = np.linalg.norm(truth_log-approximation_log, axis=1)
    a = symmetric_exp(truth)
    b = symmetric_exp(approximate)
    inv_half = symmetric_exp(truth, -.5)
    relative = inv_half@b@inv_half
    eigenvalues = np.linalg.eigvalsh((relative+np.swapaxes(relative, -1, -2))/2)
    if np.min(eigenvalues) <= 0:
        raise FloatingPointError("An SPD distance calculation lost positivity")
    ai = np.linalg.norm(np.log(eigenvalues), axis=1)
    frob = np.linalg.norm(a-b, axis=(1, 2))
    sa, sb = np.linalg.eigvalsh(truth), np.linalg.eigvalsh(approximate)
    omega = np.maximum(sa[:, -1]-sa[:, 0], sb[:, -1]-sb[:, 0])
    distortion = lambda_distortion(omega)
    frob_bound = np.exp(np.maximum(sa[:, -1], sb[:, -1]))*le
    return np.column_stack((le, ai, frob)), distortion, frob_bound


def spd_distance_from_logs(x, y):
    inv_half = symmetric_exp(x, -.5)
    relative = inv_half@symmetric_exp(y)@inv_half
    relative = (relative+relative.T)/2
    return float(np.linalg.norm(np.log(np.linalg.eigvalsh(relative))))


def sharpness_experiment():
    rows = []
    w = np.array([[0., 1.], [1., 0.]])
    for omega in (.5, 2., 4.):
        for epsilon in (.01, .001, .0001):
            a = np.sqrt(omega**2/4-epsilon**2)
            x = np.diag([a, -a])
            y = x+epsilon*w
            ratio = spd_distance_from_logs(x, y)/np.linalg.norm(x-y)
            rows.append(dict(omega=omega, epsilon=epsilon, measured_ratio=ratio,
                             limiting_bound=float(lambda_distortion(omega))))
    return rows


def karcher_experiment():
    rows = []
    x0, w = np.diag([1., -1.]), np.array([[0., 1.], [1., 0.]])
    expected = float((np.sinh(2)-2)/(2*np.sqrt(2)))
    for t in (.1, .03, .01, .003, .001):
        a, b = symmetric_exp(x0+t*w), symmetric_exp(x0-t*w)
        av, aq = np.linalg.eigh(a)
        half = (aq*np.sqrt(av))@aq.T
        inv_half = (aq/np.sqrt(av))@aq.T
        c = inv_half@b@inv_half
        cv, cq = np.linalg.eigh((c+c.T)/2)
        mean = half@((cq*np.sqrt(cv))@cq.T)@half
        inv_reference = symmetric_exp(x0, -.5)
        relative = inv_reference@mean@inv_reference
        distance = np.linalg.norm(np.log(np.linalg.eigvalsh((relative+relative.T)/2)))
        rows.append(dict(t=t, distance=float(distance), distance_over_t_squared=float(distance/t**2),
                         limiting_coefficient=expected))
    return rows


def heisenberg_experiment():
    """Check exact BCH and left equivariance for an affine log-space average."""
    def exp_nilpotent(x):
        return np.eye(3)+x+x@x/2
    def log_unipotent(g):
        n = g-np.eye(3)
        return n-n@n/2
    generator = np.random.default_rng(1234)
    a = np.triu(generator.normal(size=(3, 3)), 1)
    xs = np.triu(generator.normal(size=(3, 3, 3)), 1)
    weights = np.array([.2, .3, .5])
    translated = np.array([log_unipotent(exp_nilpotent(a)@exp_nilpotent(x)) for x in xs])
    bch = np.array([a+x+(a@x-x@a)/2 for x in xs])
    left_mean = exp_nilpotent(np.einsum('i,ijk->jk', weights, translated))
    right_mean = exp_nilpotent(a)@exp_nilpotent(np.einsum('i,ijk->jk', weights, xs))
    return dict(bch_error=float(np.max(np.abs(translated-bch))),
                left_equivariance_error=float(np.linalg.norm(left_mean-right_mean)))
