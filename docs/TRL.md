# Technology readiness (evidence-based)

**Level: TRL 4.** TRL 5 is not claimed. The new evidence is a simulated benchmark. There is no field network and no operational trial.

Numbers below are the study script's output rounded to three decimals. Full precision is in [research/results.json](../research/results.json), which `python research/run_study.py --check` regenerates.

## Simulated benchmark (BattLeDIM L-Town)

L-Town is the EPANET model that generated the BattLeDIM SCADA series (Vrachimis et al., 2020, [doi:10.5281/zenodo.4017659](https://doi.org/10.5281/zenodo.4017659)). This is a **simulated benchmark**, not a field dataset. The configuration file lists 33 labeled leaks: 14 start in 2018 and 19 start in 2019. Pressures are the 33 simulated sensors, every five minutes, in metres.

The score of an hour is the largest absolute hourly-mean pressure change across those sensors. The change at a five-minute slot is the pressure minus the median of the same slot on the previous 14 days. Each sensor is divided by the MAD of its 2018 hourly means outside leak-emergence windows. An emergence window runs from the published start to the published peak, and is at least 24 hours.

Two rules were fixed before the 2019 scores were used:

- Simple threshold: alert when the score exceeds 3.
- Calibrated threshold: alert when the score exceeds the split-conformal 0.90 quantile of the 2018 hours outside emergence windows. That quantile is 5.697. The calibration set has 2401 hours.

2019 has 8760 hours. 6694 of them (rate 0.764) meet an emergence window, because several incipient leaks keep their published peak months after they start. Hour-level precision has to be read against that rate.

| Rule | Precision | Recall | False-alarm rate on 2019 hours outside the windows | False-alarm rate on 2018 calibration hours |
|---|---|---|---|---|
| Simple threshold (3) | 0.800 | 0.793 | 0.642 | 0.365 |
| Conformal quantile (5.697) | 0.835 | 0.402 | 0.258 | 0.100 |

The conformal rule holds the 0.10 false-alarm target on the 2018 hours it was fit to (0.100). On 2019 hours outside the windows the rate is 0.258, so the calibration does not carry to the evaluation year. It is the stricter of the two rules: hour-level recall falls from 0.793 to 0.402, and precision rises only from 0.800 to 0.835. Both precisions sit close to the 0.764 onset rate.

Counted as events, the simple rule alerts inside the first 24 hours of all 19 leaks that start in 2019, and the conformal rule does so for 18 of 19 (0.947): 8 of 9 abrupt leaks and all 10 incipient leaks. The median delay among conformal detections is 0.792 hours. At a false-alarm rate of 0.642, or even 0.258, a 24-hour window is expected to contain an alarm whether or not the leak moved the pressure. Those event counts are not evidence of detection skill.

The linearised-grid localiser was not applied to L-Town. This study does not localise a pipe.

## Synthetic grid

The synthetic study is unchanged and is still produced by the same script. The scenarios come from the same linear model the localiser uses, so the accuracy is optimistic.

8 of the unit tests cover that path. `research/run_study.py` (8x8 grid, 1000 test leaks per setting):

| Sensors | Top-1 | Top-3 | Mean hop error | Baseline top-1 | Conformal coverage (target 0.90) | Mean set size |
|---|---|---|---|---|---|---|
| 4 | 0.370 | 0.649 | 1.413 | 0.052 | 0.885 | 5.749 |
| 8 | 0.675 | 0.888 | 0.565 | 0.113 | 0.921 | 2.426 |
| 12 | 0.828 | 0.941 | 0.324 | 0.173 | 0.913 | 1.400 |

With demand noise three times larger than the model assumes, coverage fell to 0.475 / 0.517 / 0.576 (4 / 8 / 12 sensors). Re-calibrating on 100 shifted scenarios restored it (0.917 / 0.898 / 0.912) at the cost of larger sets (23.628 / 12.369 / 9.742 nodes).

## Not claimed

- TRL 5. There is no operational trial and no field pressure series.
- A field result. BattLeDIM is a simulated benchmark.
- Localisation of L-Town pipes, or an EPANET inverse model.
- A false-alarm guarantee on 2019. The conformal rule's evaluation false-alarm rate is 0.258 against a 0.10 target.
- Methods that are the subject of a patent filing. The benchmark comparison is the residual score, the predeclared threshold, and the split-conformal quantile. A patent attorney has not reviewed this text, and no article is submitted.
