# Abstract

Leak alarms on the BattLeDIM L-Town **simulated benchmark** were compared for 2019. L-Town is an EPANET hydraulic simulation (Vrachimis et al., 2020, doi:10.5281/zenodo.4017659). It is not a field network, and the series are not field measurements.

The published configuration lists 33 labeled leaks, 19 of which start in 2019. Each hour is scored by the largest sensor-wise pressure change against the previous 14 days at the same five-minute slot. A simple rule alerts above a predeclared score of 3. A second rule alerts above the split-conformal 0.90 quantile of the 2018 hours that sit outside the labeled emergence windows. That quantile is 5.697.

On 8760 hours in 2019, of which 0.764 fall inside an emergence window, the simple rule has precision 0.800, recall 0.793, and a false-alarm rate 0.642. The conformal rule has precision 0.835, recall 0.402, and a false-alarm rate 0.258. Its false-alarm rate on the 2018 hours used to set the quantile is 0.100, so the 0.10 target does not hold on the evaluation year. Precision for both rules is close to the 0.764 onset rate. Alarms are also frequent enough that a hit inside 24 hours of a leak start is expected without a leak effect. This note is not submitted. A patent attorney has not reviewed it, and it does not describe a localisation method.

Numbers are rounded from `research/results.json`, which `python research/run_study.py` writes. They were not entered by hand.
