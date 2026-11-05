"""Leak-localisation study on synthetic scenarios (linearised network; not field data).

Usage: python research/run_study.py --out research/results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from leakgraph.localize import (
    Model,
    calibrate_threshold,
    candidate_set,
    nearest_sensor_baseline,
    posterior,
)
from leakgraph.network import choose_sensors, grid_network
from leakgraph.simulate import make_scenarios


def evaluate(model, res, nodes, thr):
    post = np.array([posterior(model, r) for r in res])
    top = np.argsort(-post, axis=1)
    hops = model.net.hops
    top1 = float(np.mean(top[:, 0] == nodes))
    top3 = float(np.mean([n in t[:3] for n, t in zip(nodes, top, strict=True)]))
    herr = float(np.mean([hops[t[0] + 1, n + 1] for n, t in zip(nodes, top, strict=True)]))
    base = np.array([nearest_sensor_baseline(model.net, model.sensors, r) for r in res])
    b1 = float(np.mean(base == nodes))
    bh = float(np.mean([hops[b + 1, n + 1] for n, b in zip(nodes, base, strict=True)]))
    sets = [candidate_set(p, thr) for p in post]
    cov = float(np.mean([n in s for n, s in zip(nodes, sets, strict=True)]))
    return {"top1": top1, "top3": top3, "mean_hop_error": herr, "baseline_top1": b1,
            "baseline_mean_hop_error": bh, "conformal_coverage": cov,
            "mean_set_size": float(np.mean([len(s) for s in sets]))}, post


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/results.json")
    a = ap.parse_args()
    out: dict = {"note": "synthetic scenarios on a linearised 8x8 grid network", "runs": {}}
    net = grid_network(8, seed=0)
    for k in (4, 8, 12):
        model = Model(net, choose_sensors(net, k, seed=0), sigma=0.01, demand_sd=0.02,
                      leak_scale=1.0)
        cal_r, cal_n, _ = make_scenarios(model, 500, seed=11)
        pc = np.array([posterior(model, r) for r in cal_r])
        thr = calibrate_threshold(pc, cal_n, 0.1)
        te_r, te_n, _ = make_scenarios(model, 1000, seed=12)
        same, _ = evaluate(model, te_r, te_n, thr)
        sh_r, sh_n, _ = make_scenarios(model, 1000, seed=13, demand_sd=0.06)
        shifted, _ = evaluate(model, sh_r, sh_n, thr)
        rc_r, rc_n, _ = make_scenarios(model, 100, seed=14, demand_sd=0.06)
        pr = np.array([posterior(model, r) for r in rc_r])
        thr2 = calibrate_threshold(pr, rc_n, 0.1)
        recal, _ = evaluate(model, sh_r, sh_n, thr2)
        out["runs"][f"sensors_{k}"] = {"same_conditions": same, "demand_noise_x3": shifted,
                                       "recalibrated_on_100_shifted": recal, "threshold": thr}
    Path(a.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
