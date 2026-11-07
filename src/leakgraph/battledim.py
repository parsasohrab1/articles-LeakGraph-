"""BattLeDIM L-Town pressure residuals and leak detection.

L-Town is the EPANET network used to simulate the BattLeDIM benchmark
(doi:10.5281/zenodo.4017659). The series are simulated SCADA, not field
measurements. Labels are the leakage list in the dataset configuration.

The score is the largest absolute hourly-mean pressure change across the
pressure sensors, each divided by its own scale. The change at a 5-minute
slot is the pressure minus the median of that slot on the previous 14 days.
The scale is the MAD of 2018 hourly means outside leak-emergence windows.
A simple rule alerts above 3. A calibrated rule alerts above the
split-conformal 0.90 quantile of those 2018 windows. Neither rule is a
localisation method.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise

import numpy as np

ALPHA = 0.10
SIMPLE_THRESHOLD = 3.0
BASELINE_DAYS = 14
SAMPLES_PER_HOUR = 12
MIN_EMERGENCE = np.timedelta64(24, "h")
EVAL_START = np.datetime64("2019-01-01T00")
EVAL_END = np.datetime64("2020-01-01T00")
MAD_SCALE = 1.4826

_LEAK_RE = re.compile(
    r"^-\s*(p\d+)\s*,\s*"
    r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*,\s*"
    r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*,\s*"
    r"([0-9.]+)\s*,\s*"
    r"(incipient|abrupt)\s*,\s*"
    r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*$"
)


@dataclass(frozen=True)
class Leak:
    link_id: str
    start: np.datetime64
    end: np.datetime64
    diameter_m: float
    leak_type: str
    peak: np.datetime64


def _timestamp(text: str) -> np.datetime64:
    return np.datetime64(text.replace(" ", "T"), "m")


def parse_leak_configuration(text: str) -> list[Leak]:
    """Leak rows from dataset_configuration.yaml. One row per labeled leak."""
    leaks: list[Leak] = []
    in_leaks = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("leakages:"):
            in_leaks = True
            continue
        if not in_leaks:
            continue
        if not line.startswith("-"):
            if line:
                break
            continue
        if line.startswith("- #"):
            continue
        match = _LEAK_RE.match(line)
        if match is None:
            raise ValueError(f"unparsed leak line: {line}")
        link, start, end, diameter, leak_type, peak = match.groups()
        leaks.append(
            Leak(
                link,
                _timestamp(start),
                _timestamp(end),
                float(diameter),
                leak_type,
                _timestamp(peak),
            )
        )
    if not leaks:
        raise ValueError("no leaks found in the configuration")
    return leaks


def parse_pressure_sensors(text: str) -> list[str]:
    sensors: list[str] = []
    grabbing = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("pressure_sensors:"):
            grabbing = True
            continue
        if not grabbing:
            continue
        if line.startswith("- "):
            sensors.append(line[2:].strip())
        elif line:
            break
    if not sensors:
        raise ValueError("no pressure sensors in the configuration")
    return sensors


def emergence_end(leak: Leak) -> np.datetime64:
    """End of the labeled emergence window.

    The window runs from the published start to the published peak, and is
    at least 24 hours. Abrupt leaks peak at the start, so their window is
    the 24-hour floor.
    """
    return max(leak.peak, leak.start + MIN_EMERGENCE)


def in_any_window(stamps: np.ndarray, leaks: list[Leak]) -> np.ndarray:
    mask = np.zeros(stamps.shape[0], dtype=bool)
    times = stamps.astype("datetime64[m]")
    for leak in leaks:
        end = emergence_end(leak).astype("datetime64[m]")
        mask |= (times >= leak.start) & (times < end)
    return mask


def read_pressure_csv(path, expected_sensors: list[str] | None = None):
    """Semicolon-separated SCADA pressures. Decimals use a comma."""
    times: list[str] = []
    rows: list[list[float]] = []
    with open(path, encoding="utf-8") as handle:
        sensors = handle.readline().strip().split(";")[1:]
        if expected_sensors is not None and sensors != expected_sensors:
            raise ValueError(f"pressure columns differ from the configuration in {path}")
        for line in handle:
            if not line.strip():
                continue
            parts = line.strip().split(";")
            times.append(parts[0])
            rows.append([float(item.replace(",", ".")) for item in parts[1:]])
    stamps = np.array([value.replace(" ", "T") for value in times], dtype="datetime64[m]")
    values = np.asarray(rows, dtype=float)
    if values.ndim != 2 or values.shape[0] != stamps.shape[0]:
        raise ValueError(f"could not read pressures from {path}")
    if not np.isfinite(values).all():
        raise ValueError(f"non-finite pressure in {path}")
    return stamps, values, sensors


def assert_regular_five_minutes(stamps: np.ndarray) -> None:
    if stamps.shape[0] < 2:
        raise ValueError("pressure series is empty")
    step = np.diff(stamps.astype("datetime64[m]").astype(np.int64))
    if not np.all(step == 5):
        raise ValueError("pressure series is not a regular 5-minute grid")


def change_residuals(stamps: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Pressure minus the trailing 14-day median of the same 5-minute slot.

    The current sample is not in its own baseline. The first 14 days are NaN.
    """
    n, k = values.shape
    residual = np.full((n, k), np.nan)
    ring = np.full((288, BASELINE_DAYS, k), np.nan)
    position = np.zeros(288, dtype=int)
    filled = np.zeros(288, dtype=int)
    minutes = stamps.astype("datetime64[m]").astype(np.int64)
    slots = (minutes % (24 * 60)) // 5
    for index in range(n):
        slot = int(slots[index])
        if filled[slot] >= BASELINE_DAYS:
            residual[index] = values[index] - np.median(ring[slot], axis=0)
        ring[slot, position[slot]] = values[index]
        position[slot] = (position[slot] + 1) % BASELINE_DAYS
        if filled[slot] < BASELINE_DAYS:
            filled[slot] += 1
    return residual


def _mad_sigma(samples: np.ndarray) -> float:
    samples = samples[np.isfinite(samples)]
    if samples.size < 24:
        raise ValueError("not enough calibration hours to scale a sensor")
    center = np.median(samples)
    sigma = MAD_SCALE * float(np.median(np.abs(samples - center)))
    if not np.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("pressure scale is zero")
    return sigma


def build_hourly(stamps: np.ndarray, values: np.ndarray, leaks: list[Leak]):
    """Return hour starts, scores, and whether the hour meets an emergence window."""
    assert_regular_five_minutes(stamps)
    residual = change_residuals(stamps, values)
    inside = in_any_window(stamps, leaks)
    hours = stamps.astype("datetime64[h]")
    cuts = np.flatnonzero(np.diff(hours.astype(np.int64))) + 1
    bounds = np.concatenate(([0], cuts, [stamps.shape[0]]))
    kept_hours: list[np.datetime64] = []
    means: list[np.ndarray] = []
    onset: list[bool] = []
    for left, right in pairwise(bounds):
        block = residual[left:right]
        if block.shape[0] != SAMPLES_PER_HOUR or not np.isfinite(block).all():
            continue
        kept_hours.append(hours[left])
        means.append(block.mean(axis=0))
        onset.append(bool(np.any(inside[left:right])))
    if not means:
        raise ValueError("no complete hours after the baseline burn-in")
    hour_arr = np.array(kept_hours, dtype="datetime64[h]")
    mean_arr = np.vstack(means)
    onset_arr = np.array(onset, dtype=bool)
    calibration = (hour_arr < EVAL_START) & ~onset_arr
    if int(calibration.sum()) < 24:
        raise ValueError("fewer than 24 leak-free 2018 hours")
    sigma = np.array([_mad_sigma(mean_arr[calibration, j]) for j in range(mean_arr.shape[1])])
    score = np.max(np.abs(mean_arr) / sigma, axis=1)
    return hour_arr, score, onset_arr


def conformal_upper(scores: np.ndarray, alpha: float = ALPHA) -> float:
    """Split-conformal upper quantile. Alerts use a strict exceedance.

    The rank is ceil((n + 1) * (1 - alpha)). If that rank is n + 1, no finite
    threshold can keep the calibration exceedance rate at alpha, and the
    return value is +inf.
    """
    ordered = np.sort(np.asarray(scores, dtype=float))
    n = int(ordered.size)
    if n == 0:
        raise ValueError("no calibration scores")
    rank = int(np.ceil((n + 1) * (1.0 - alpha)))
    if rank > n:
        return float("inf")
    return float(ordered[rank - 1])


def write_leaks(path, leaks: list[Leak]) -> None:
    lines = ["link_id,start,end,peak,diameter_m,leak_type"]
    for leak in leaks:
        lines.append(
            f"{leak.link_id},{leak.start},{leak.end},{leak.peak},"
            f"{leak.diameter_m:.10g},{leak.leak_type}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hourly(path, hours: np.ndarray, scores: np.ndarray, onset: np.ndarray) -> None:
    lines = ["timestamp,score,onset"]
    for hour, score, flag in zip(hours, scores, onset, strict=True):
        stamp = str(np.datetime64(hour, "m"))
        lines.append(f"{stamp},{float(score):.10g},{int(flag)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_leaks(path) -> list[Leak]:
    leaks: list[Leak] = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().strip().split(",")
        expected = ["link_id", "start", "end", "peak", "diameter_m", "leak_type"]
        if header != expected:
            raise ValueError(f"unexpected leak header: {header}")
        for line in handle:
            if not line.strip():
                continue
            link, start, end, peak, diameter, leak_type = line.strip().split(",")
            leaks.append(
                Leak(link, _timestamp(start), _timestamp(end), float(diameter), leak_type, _timestamp(peak))
            )
    if not leaks:
        raise ValueError(f"no leaks in {path}")
    return leaks


def load_hourly(path):
    hours: list[np.datetime64] = []
    scores: list[float] = []
    onset: list[bool] = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().strip()
        if header != "timestamp,score,onset":
            raise ValueError(f"unexpected hourly header: {header}")
        for line in handle:
            if not line.strip():
                continue
            stamp, score, flag = line.strip().split(",")
            hours.append(np.datetime64(stamp, "h"))
            scores.append(float(score))
            onset.append(flag == "1")
    if not hours:
        raise ValueError(f"no hours in {path}")
    return np.array(hours), np.asarray(scores, dtype=float), np.asarray(onset, dtype=bool)


def _ratio(numerator: int, denominator: int):
    if denominator == 0:
        return None
    return numerator / denominator


def _rates(alert: np.ndarray, positive: np.ndarray) -> dict:
    alert = np.asarray(alert, dtype=bool)
    positive = np.asarray(positive, dtype=bool)
    tp = int(np.sum(alert & positive))
    fp = int(np.sum(alert & ~positive))
    fn = int(np.sum(~alert & positive))
    tn = int(np.sum(~alert & ~positive))
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "false_alarm_rate": _ratio(fp, fp + tn),
    }


def _first_hit(leak: Leak, hours: np.ndarray, alert: np.ndarray, end: np.datetime64):
    hour_end = hours + np.timedelta64(1, "h")
    overlap = (hours < end) & (hour_end > leak.start) & alert
    found = np.flatnonzero(overlap)
    if found.size == 0:
        return False, None
    delay = (hours[found[0]] - leak.start) / np.timedelta64(1, "h")
    return True, float(max(0.0, delay))


def _events(leaks: list[Leak], hours: np.ndarray, alert: np.ndarray) -> dict:
    delays: list[float] = []
    n = n_window = n_24 = 0
    by_type = {
        "abrupt": {"n": 0, "detected_within_24h": 0, "detected_in_emergence_window": 0},
        "incipient": {"n": 0, "detected_within_24h": 0, "detected_in_emergence_window": 0},
    }
    for leak in leaks:
        if leak.start < EVAL_START or leak.start >= EVAL_END:
            continue
        n += 1
        hit_window, delay = _first_hit(leak, hours, alert, emergence_end(leak))
        hit_24, _ = _first_hit(leak, hours, alert, leak.start + MIN_EMERGENCE)
        n_window += int(hit_window)
        n_24 += int(hit_24)
        if delay is not None:
            delays.append(delay)
        bucket = by_type[leak.leak_type]
        bucket["n"] += 1
        bucket["detected_within_24h"] += int(hit_24)
        bucket["detected_in_emergence_window"] += int(hit_window)
    typed = {}
    for name, bucket in by_type.items():
        count = bucket["n"]
        typed[name] = {
            "n": count,
            "detected_within_24h": _ratio(bucket["detected_within_24h"], count),
            "detected_in_emergence_window": _ratio(bucket["detected_in_emergence_window"], count),
        }
    return {
        "n": n,
        "detected_within_24h": _ratio(n_24, n),
        "detected_in_emergence_window": _ratio(n_window, n),
        "n_detected_within_24h": n_24,
        "n_detected_in_emergence_window": n_window,
        "median_delay_hours": None if not delays else float(np.median(delays)),
        "by_type": typed,
    }


def evaluate_detection(hours, scores, onset, leaks: list[Leak]) -> dict:
    """Compare the predeclared threshold with the 2018 conformal threshold on 2019."""
    hours = np.asarray(hours)
    scores = np.asarray(scores, dtype=float)
    onset = np.asarray(onset, dtype=bool)
    order = np.argsort(hours.astype("datetime64[h]").astype(np.int64))
    hours, scores, onset = hours[order], scores[order], onset[order]
    calibration = (hours < EVAL_START) & ~onset
    evaluation = hours >= EVAL_START
    if int(calibration.sum()) == 0 or int(evaluation.sum()) == 0:
        raise ValueError("calibration or evaluation hours are missing")
    conformal = conformal_upper(scores[calibration], ALPHA)
    rules = {"simple_threshold": SIMPLE_THRESHOLD, "conformal": conformal}
    hour_level = {}
    events = {}
    calibration_false_alarm = {}
    for name, threshold in rules.items():
        hour_level[name] = _rates(scores[evaluation] > threshold, onset[evaluation])
        events[name] = _events(leaks, hours[evaluation], scores[evaluation] > threshold)
        calibration_false_alarm[name] = float(np.mean(scores[calibration] > threshold))
    n_2018 = sum(1 for leak in leaks if leak.start < EVAL_START)
    n_2019 = sum(1 for leak in leaks if EVAL_START <= leak.start < EVAL_END)
    return {
        "nature": (
            "BattLeDIM L-Town is an EPANET hydraulic simulation published as a "
            "benchmark. These are not field measurements."
        ),
        "benchmark": "simulated",
        "doi": "10.5281/zenodo.4017659",
        "license": "CC-BY-4.0",
        "n_leaks": len(leaks),
        "n_leaks_2018": n_2018,
        "n_leaks_2019": n_2019,
        "n_hours": int(hours.shape[0]),
        "n_calibration_hours": int(calibration.sum()),
        "n_evaluation_hours": int(evaluation.sum()),
        "n_evaluation_onset_hours": int(np.sum(onset[evaluation])),
        "evaluation_onset_rate": float(np.mean(onset[evaluation])),
        "alpha": ALPHA,
        "simple_threshold": SIMPLE_THRESHOLD,
        "conformal_threshold": None if not np.isfinite(conformal) else conformal,
        "baseline_days": BASELINE_DAYS,
        "minimum_emergence_hours": 24,
        "calibration_false_alarm_rate": calibration_false_alarm,
        "hour_level_2019": hour_level,
        "events_2019": events,
    }
