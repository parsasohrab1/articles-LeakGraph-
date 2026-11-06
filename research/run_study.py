"""Synthetic localisation study plus the BattLeDIM simulated-benchmark detection study.

BattLeDIM L-Town is an EPANET hydraulic simulation, not field data.
The benchmark block is computed from data/hourly_scores.csv and data/leaks.csv.

Usage:
    python research/fetch_battledim.py
    python research/run_study.py --out research/results.json
    python research/run_study.py --check
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leakgraph.battledim import evaluate_detection, load_hourly, load_leaks
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


def synthetic() -> dict:
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
    return out


def battledim() -> dict:
    data = ROOT / "data"
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    hours, scores, onset = load_hourly(data / "hourly_scores.csv")
    leaks = load_leaks(data / "leaks.csv")
    if len(leaks) != manifest["n_leaks"] or int(hours.shape[0]) != manifest["n_hours"]:
        raise SystemExit("snapshot does not match data/manifest.json; rerun fetch_battledim.py")
    result = evaluate_detection(hours, scores, onset, leaks)
    result["n_pressure_sensors"] = manifest["n_pressure_sensors"]
    return result


def build() -> dict:
    return {"synthetic": synthetic(), "battledim": battledim()}


def _same(left, right) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
        return math.isclose(left, right, rel_tol=1e-6, abs_tol=1e-6)
    return left == right


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "research" / "results.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fresh = build()
    path = Path(args.out)
    if args.check:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if not _same(saved, fresh):
            raise SystemExit("results.json does not match a fresh run")
        print("results.json matches a fresh run")
        return
    path.write_text(json.dumps(fresh, indent=2) + "\n", encoding="utf-8")
    bench = fresh["battledim"]
    simple = bench["hour_level_2019"]["simple_threshold"]
    conformal = bench["hour_level_2019"]["conformal"]
    print(
        f"leaks {bench['n_leaks']} "
        f"simple_recall {simple['recall']} simple_precision {simple['precision']} "
        f"conformal_recall {conformal['recall']} conformal_precision {conformal['precision']} "
        f"conformal_threshold {bench['conformal_threshold']}"
    )


if __name__ == "__main__":
    main()
