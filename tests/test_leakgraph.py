import numpy as np
import pytest

from leakgraph.localize import (
    Model, calibrate_threshold, candidate_set, estimate_flow, posterior, repair_priority,
)
from leakgraph.network import choose_sensors, grid_network
from leakgraph.simulate import make_scenarios


@pytest.fixture(scope="module")
def model():
    net = grid_network(6, seed=1)
    return Model(net, choose_sensors(net, 6, seed=1), sigma=0.01, demand_sd=0.02, leak_scale=1.0)


def test_response_matrix_is_symmetric_positive(model):
    r = model.net.R
    assert np.allclose(r, r.T) and (r > 0).all()


def test_hops_are_symmetric_and_finite():
    net = grid_network(4)
    assert np.isfinite(net.hops).all() and (net.hops == net.hops.T).all()


def test_sensors_unique(model):
    assert len(set(model.sensors)) == len(model.sensors) == 6


def test_posterior_normalised_and_finds_noise_free_leak(model):
    j = 7
    res = 1.0 * model.signatures()[:, j]
    p = posterior(model, res)
    assert abs(p.sum() - 1.0) < 1e-12 and int(np.argmax(p)) == j


def test_flow_estimate_recovers_flow(model):
    j = 3
    res = 2.5 * model.signatures()[:, j]
    assert estimate_flow(model, res, j) == pytest.approx(2.5, rel=1e-6)


def test_conformal_coverage_on_exchangeable_data(model):
    cal_r, cal_n, _ = make_scenarios(model, 400, seed=2)
    te_r, te_n, _ = make_scenarios(model, 400, seed=3)
    pc = np.array([posterior(model, r) for r in cal_r])
    pt = np.array([posterior(model, r) for r in te_r])
    thr = calibrate_threshold(pc, cal_n, 0.1)
    cov = np.mean([n in candidate_set(p, thr) for p, n in zip(pt, te_n, strict=True)])
    assert cov >= 0.85


def test_repair_priority_orders_by_product():
    post = np.array([0.5, 0.3, 0.2])
    flows = np.array([1.0, 3.0, 0.1])
    assert list(repair_priority(post, flows)) == [1, 0, 2]


def test_scenarios_are_seeded(model):
    a = make_scenarios(model, 5, seed=9)
    b = make_scenarios(model, 5, seed=9)
    assert all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))
