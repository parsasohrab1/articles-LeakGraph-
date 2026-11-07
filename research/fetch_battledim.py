"""Download BattLeDIM L-Town pressures and write the detection snapshot.

The snapshot is a simulated hydraulic benchmark, not field data. Raw SCADA
files stay in data/raw and are not committed. Outputs:

    data/dataset_configuration.yaml
    data/leaks.csv
    data/hourly_scores.csv
    data/manifest.json

Usage: python research/fetch_battledim.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leakgraph.battledim import (
    build_hourly,
    parse_leak_configuration,
    parse_pressure_sensors,
    read_pressure_csv,
    write_hourly,
    write_leaks,
)

RECORD = "https://zenodo.org/records/4017659/files/"
FILES = {
    "dataset_configuration.yaml": "48486401f5b4d0447023f5ce5d242c52",
    "2018_SCADA_Pressures.csv": "d389d8541350c19ff0bfc6b80f246d35",
    "2019_SCADA_Pressures.csv": "5ea1e46d3f2f0a89a3f98d6fd39a851d",
}


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(name: str, dest: Path) -> None:
    expected = FILES[name]
    if dest.exists() and _md5(dest) == expected:
        print(f"kept {name}")
        return
    url = RECORD + name + "?download=1"
    print(f"downloading {name}")
    urllib.request.urlretrieve(url, dest)
    got = _md5(dest)
    if got != expected:
        raise SystemExit(f"md5 mismatch for {name}: {got} != {expected}")


def main() -> None:
    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        _download(name, raw / name)
    config_text = (raw / "dataset_configuration.yaml").read_text(encoding="utf-8")
    leaks = parse_leak_configuration(config_text)
    sensors = parse_pressure_sensors(config_text)
    frames = []
    for year in (2018, 2019):
        stamps, values, _ = read_pressure_csv(raw / f"{year}_SCADA_Pressures.csv", sensors)
        frames.append((stamps, values))
    stamps = np_concatenate_time(frames)
    values = np_concatenate_values(frames)
    hours, scores, onset = build_hourly(stamps, values, leaks)
    data = ROOT / "data"
    shutil.copyfile(raw / "dataset_configuration.yaml", data / "dataset_configuration.yaml")
    write_leaks(data / "leaks.csv", leaks)
    write_hourly(data / "hourly_scores.csv", hours, scores, onset)
    manifest = {
        "nature": (
            "BattLeDIM L-Town is an EPANET hydraulic simulation. "
            "This snapshot is a simulated benchmark, not field data."
        ),
        "doi": "10.5281/zenodo.4017659",
        "license": "CC-BY-4.0",
        "citation": (
            "Vrachimis, S. G., Eliades, D. G., Taormina, R., Ostfeld, A., Kapelan, Z., "
            "Liu, S., Kyriakou, M. S., Pavlou, P., Qiu, M., and Polycarpou, M. (2020). "
            "Dataset of BattLeDIM: Battle of the Leakage Detection and Isolation Methods. "
            "Zenodo. https://doi.org/10.5281/zenodo.4017659"
        ),
        "pressure_files_md5": FILES,
        "n_pressure_sensors": len(sensors),
        "pressure_sensors": sensors,
        "n_leaks": len(leaks),
        "n_hours": int(hours.shape[0]),
        "score": (
            "max over sensors of the absolute hourly-mean 14-day change residual, "
            "scaled by the 2018 leak-free MAD"
        ),
    }
    (data / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"leaks {len(leaks)} hours {hours.shape[0]}")


def np_concatenate_time(frames):
    stamps = np.concatenate([item[0] for item in frames])
    step = np.diff(stamps.astype("datetime64[m]").astype(np.int64))
    if not np.all(step == 5):
        raise SystemExit("2018 and 2019 pressures do not form one 5-minute grid")
    return stamps


def np_concatenate_values(frames):
    return np.concatenate([item[1] for item in frames], axis=0)


if __name__ == "__main__":
    main()
