"""Linearised hydraulic model of a pipe network (DC / resistive approximation).

Heads h satisfy L h = -d for nodal demands d, where L is the weighted graph Laplacian with the
reservoir node grounded. A leak of flow q at node j changes the heads by -q * R[:, j], with
R = inverse of the reduced Laplacian. This is a linearisation of the Hazen-Williams network
equations around one operating point; it is an assumption of the model, not a hydraulic solver.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Network:
    n: int
    conductance: np.ndarray        # (n, n) symmetric, zero diagonal
    hops: np.ndarray               # (n, n) hop distances
    R: np.ndarray                  # (n-1, n-1) response matrix of non-reservoir nodes

    @property
    def nodes(self) -> int:
        return self.n - 1          # node ids 0..n-2 correspond to graph nodes 1..n-1


def grid_network(side: int = 8, seed: int = 0) -> Network:
    """side x side grid; node 0 (corner) is the reservoir. Conductances are random."""
    rng = np.random.default_rng(seed)
    n = side * side
    c = np.zeros((n, n))
    for r in range(side):
        for k in range(side):
            i = r * side + k
            if k + 1 < side:
                c[i, i + 1] = c[i + 1, i] = rng.uniform(0.5, 2.0)
            if r + 1 < side:
                c[i, i + side] = c[i + side, i] = rng.uniform(0.5, 2.0)
    lap = np.diag(c.sum(axis=1)) - c
    reduced = lap[1:, 1:]
    hops = np.full((n, n), np.inf)
    for s in range(n):
        hops[s, s] = 0
        frontier = [s]
        while frontier:
            nxt = []
            for u in frontier:
                for v in np.nonzero(c[u])[0]:
                    if hops[s, v] == np.inf:
                        hops[s, v] = hops[s, u] + 1
                        nxt.append(v)
            frontier = nxt
    return Network(n, c, hops, np.linalg.inv(reduced))


def choose_sensors(net: Network, k: int, seed: int = 0) -> list[int]:
    """Greedy sensor placement: repeatedly add the node that most increases the minimum pairwise
    distance between leak signatures (columns of R restricted to the sensors)."""
    rng = np.random.default_rng(seed)
    cols = net.R.copy()
    chosen: list[int] = [int(rng.integers(net.nodes))]
    while len(chosen) < k:
        best, best_val = None, -1.0
        for cand in range(net.nodes):
            if cand in chosen:
                continue
            sig = cols[chosen + [cand]].T
            d = np.linalg.norm(sig[:, None, :] - sig[None, :, :], axis=2)
            np.fill_diagonal(d, np.inf)
            val = float(np.min(d))
            if val > best_val:
                best, best_val = cand, val
        chosen.append(int(best))
    return chosen
