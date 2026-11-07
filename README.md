# articles-LeakGraph-

Leak detection on a water-network benchmark, with a synthetic localisation study kept separate.
The Water (MDPI) special issue on smart water management is recorded in
[docs/JOURNAL_FIT.md](docs/JOURNAL_FIT.md). No article is submitted from this branch.
The BattLeDIM comparison uses a pressure-residual score, a predeclared threshold, and a
split-conformal quantile. It does not describe a localisation algorithm.

**Maturity: TRL 4** ([docs/TRL.md](docs/TRL.md)). BattLeDIM L-Town is an EPANET hydraulic
simulation and is reported here as a **simulated benchmark**, not as field data. On the
2019 hours the predeclared threshold has recall **0.793** and a false-alarm rate **0.642**.
The conformal threshold, fit on 2018 leak-free hours, has recall **0.402** and a
false-alarm rate **0.258**. The 2018 false-alarm rate of that rule is **0.100**. Full
precision is in [research/results.json](research/results.json).

- `data/leaks.csv` — 33 labeled leaks from the Zenodo configuration (14 in 2018, 19 in 2019)
- `data/hourly_scores.csv` — hourly residual scores from the 33 simulated pressure sensors
- `src/leakgraph/battledim.py` — loader and the two detection rules
- `src/leakgraph/network.py`, `localize.py`, `simulate.py` — synthetic linearised-grid study
- `research/fetch_battledim.py` rebuilds the snapshot; `research/run_study.py` writes `results.json`

BattLeDIM is Vrachimis et al., Zenodo, [doi:10.5281/zenodo.4017659](https://doi.org/10.5281/zenodo.4017659), CC-BY-4.0.

The basket card for article registration and achievements is [docs/REGISTRATION.md](docs/REGISTRATION.md) (product id `nrwleak`). It is regenerated from `research/results.json`. The article status on that card is unsubmitted.

```bash
pip install -e ".[dev]"
python research/fetch_battledim.py
python -m ruff check src tests research
python -m pytest -q
python research/run_study.py --check
```
