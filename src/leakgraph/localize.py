"""Bayesian leak localisation and split-conformal candidate sets."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .network import Network


@dataclass
class Model:
    net: Network
    sensors: list[int]
    sigma: float          # sensor noise (head units)
    demand_sd: float      # sd of unmodelled nodal demand fluctuations
    leak_scale: float     # prior scale of leak flow

    def signatures(self) -> np.ndarray:
        """(k, nodes): head drop at each sensor per unit leak at each node."""
        return self.net.R[self.sensors, :]

    def noise_cov(self) -> np.ndarray:
        rs = self.net.R[self.sensors, :]
        k = len(self.sensors)
        return self.sigma**2 * np.eye(k) + self.demand_sd**2 * rs @ rs.T


def posterior(model: Model, residual: np.ndarray) -> np.ndarray:
    """Posterior over leak nodes given head drops at the sensors (uniform prior).

    residual ~ N(0, S + tau^2 a_j a_j^T) under 'leak at j' with flow ~ N(0, tau^2)... we use the
    positive-flow likelihood by profiling over q >= 0 with a Gaussian prior, which reduces to a
    closed form through the Sherman-Morrison identity."""
    s = model.noise_cov()
    s_inv = np.linalg.inv(s)
    a = model.signatures()                       # (k, m)
    tau2 = model.leak_scale**2
    si_r = s_inv @ residual
    logp = np.empty(a.shape[1])
    for j in range(a.shape[1]):
        aj = a[:, j]
        sa = s_inv @ aj
        denom = 1.0 + tau2 * float(aj @ sa)
        quad = float(residual @ si_r) - tau2 * float(aj @ si_r) ** 2 / denom
        logp[j] = -0.5 * quad - 0.5 * np.log(denom)
    logp -= logp.max()
    p = np.exp(logp)
    return p / p.sum()


def estimate_flow(model: Model, residual: np.ndarray, node: int) -> float:
    """Least-squares leak flow at `node` (generalised least squares, clipped at 0)."""
    s_inv = np.linalg.inv(model.noise_cov())
    a = model.signatures()[:, node]
    return max(0.0, float(a @ s_inv @ residual) / float(a @ s_inv @ a))


def nearest_sensor_baseline(net: Network, sensors: list[int], residual: np.ndarray) -> int:
    """Baseline: the node closest (in hops) to the sensor with the largest head drop."""
    s = sensors[int(np.argmax(residual))]
    # node ids are shifted by one relative to graph indices (reservoir removed)
    return int(s)


def calibrate_threshold(posteriors: np.ndarray, truth: np.ndarray, alpha: float) -> float:
    """Split-conformal threshold on the score 1 - p(true node)."""
    scores = 1.0 - posteriors[np.arange(len(truth)), truth]
    k = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    return float(np.sort(scores)[min(k, len(scores)) - 1])


def candidate_set(post: np.ndarray, threshold: float) -> np.ndarray:
    """Nodes whose score is within the calibrated threshold."""
    return np.nonzero(1.0 - post <= threshold)[0]


def repair_priority(post: np.ndarray, flows: np.ndarray) -> np.ndarray:
    """Order candidate nodes by posterior probability times estimated leaked flow."""
    return np.argsort(-(post * flows))
