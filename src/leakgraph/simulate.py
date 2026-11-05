"""Synthetic leak scenarios on a linearised network (labelled synthetic, not field data)."""

from __future__ import annotations

import numpy as np

from .localize import Model


def make_scenarios(model: Model, n: int, seed: int, demand_sd: float | None = None,
                   sigma: float | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (residuals (n, k), true leak nodes (n,), true flows (n,))."""
    rng = np.random.default_rng(seed)
    net = model.net
    m, k = net.nodes, len(model.sensors)
    nodes = rng.integers(0, m, n)
    flows = rng.lognormal(np.log(model.leak_scale), 0.5, n)
    rs = net.R[model.sensors, :]
    dsd = model.demand_sd if demand_sd is None else demand_sd
    sig = model.sigma if sigma is None else sigma
    res = np.empty((n, k))
    for i in range(n):
        demand = rng.normal(0.0, dsd, m)
        res[i] = flows[i] * rs[:, nodes[i]] + rs @ demand + rng.normal(0.0, sig, k)
    return res, nodes, flows
