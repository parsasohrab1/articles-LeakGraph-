from pathlib import Path

import numpy as np
import pytest

from leakgraph.battledim import (
    ALPHA,
    SIMPLE_THRESHOLD,
    change_residuals,
    conformal_upper,
    emergence_end,
    evaluate_detection,
    load_hourly,
    load_leaks,
    parse_leak_configuration,
    parse_pressure_sensors,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = """
leakages:
- # linkID, startTime, endTime, leakDiameter (m), leakType, peakTime
- p257, 2018-01-08 13:30, 2019-12-31 23:55, 0.011843, incipient, 2018-01-25 08:30
- p31,  2018-06-28 10:35, 2018-08-12 17:30, 0.016389, incipient, 2018-08-03 02:45
- p673, 2018-03-05 15:45, 2018-03-23 10:25, 0.022916, abrupt, 2018-03-05 15:45

pressure_sensors:
- n1
- n4

flow_sensors:
- PUMP_1
"""


def test_parser_reads_labeled_leaks_and_sensors():
    leaks = parse_leak_configuration(SAMPLE)
    assert [leak.link_id for leak in leaks] == ["p257", "p31", "p673"]
    assert leaks[1].diameter_m == pytest.approx(0.016389)
    abrupt = leaks[2]
    assert abrupt.leak_type == "abrupt"
    assert emergence_end(abrupt) == abrupt.start + np.timedelta64(24, "h")
    incipient = leaks[0]
    assert emergence_end(incipient) == incipient.peak
    assert parse_pressure_sensors(SAMPLE) == ["n1", "n4"]


def test_parser_rejects_a_broken_leak_line():
    with pytest.raises(ValueError, match="unparsed"):
        parse_leak_configuration("leakages:\n- p1, not-a-date, abrupt\n")


def test_trailing_median_responds_to_a_step_then_settles():
    start = np.datetime64("2018-01-01T00:00")
    count = 40 * 288
    stamps = start + np.arange(count) * np.timedelta64(5, "m")
    values = np.full((count, 1), 10.0)
    step = 20 * 288
    values[step:] = 12.0
    residual = change_residuals(stamps, values)
    assert residual[14 * 288, 0] == pytest.approx(0.0)
    assert residual[step, 0] == pytest.approx(2.0)
    assert residual[step + 14 * 288, 0] == pytest.approx(0.0)


def test_conformal_quantile_holds_on_exchangeable_scores():
    rng = np.random.default_rng(0)
    calibration = rng.normal(size=800)
    evaluation = rng.normal(size=4000)
    threshold = conformal_upper(calibration, ALPHA)
    assert float(np.mean(calibration > threshold)) <= ALPHA + 1e-12
    assert float(np.mean(evaluation > threshold)) < 0.16


def test_detection_counts_a_spike_and_ignores_a_quiet_hour():
    hours = np.array(
        [f"2018-06-01T{hour:02d}" for hour in range(12)] + ["2019-03-01T00", "2019-03-01T01"],
        dtype="datetime64[h]",
    )
    scores = np.array([0.2] * 12 + [0.2, 5.0])
    onset = np.array([False] * 13 + [True])
    leaks = parse_leak_configuration(
        "leakages:\n"
        "- p10, 2019-03-01 01:10, 2019-03-02 00:00, 0.02, abrupt, 2019-03-01 01:10\n"
    )
    result = evaluate_detection(hours, scores, onset, leaks)
    assert result["benchmark"] == "simulated"
    assert result["simple_threshold"] == SIMPLE_THRESHOLD
    simple = result["hour_level_2019"]["simple_threshold"]
    conformal = result["hour_level_2019"]["conformal"]
    assert simple["tp"] == 1 and simple["fp"] == 0 and simple["fn"] == 0
    assert conformal["tp"] == 1 and conformal["fp"] == 0
    assert result["events_2019"]["simple_threshold"]["detected_within_24h"] == 1.0
    assert result["calibration_false_alarm_rate"]["conformal"] <= ALPHA + 1e-12


def test_snapshot_matches_the_configuration_and_covers_both_years():
    config = ROOT / "data" / "dataset_configuration.yaml"
    leaks = load_leaks(ROOT / "data" / "leaks.csv")
    parsed = parse_leak_configuration(config.read_text(encoding="utf-8"))
    assert [(item.link_id, str(item.start), str(item.end), item.leak_type) for item in leaks] == [
        (item.link_id, str(item.start), str(item.end), item.leak_type) for item in parsed
    ]
    assert sum(item.start < np.datetime64("2019-01-01") for item in leaks) == 14
    assert sum(item.start >= np.datetime64("2019-01-01") for item in leaks) == 19
    hours, scores, onset = load_hourly(ROOT / "data" / "hourly_scores.csv")
    assert hours.shape[0] > 1000
    assert np.isfinite(scores).all()
    assert hours[0] < np.datetime64("2018-02-01") and hours[-1] >= np.datetime64("2019-12-01")
    assert set(np.unique(onset)).issubset({False, True})
