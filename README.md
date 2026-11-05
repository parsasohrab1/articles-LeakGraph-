# articles-LeakGraph-

Leak localisation in water distribution networks with calibrated uncertainty. Product for the
water-management special issue (Water, MDPI: "Looking into the Future of Smart Water Management by AI").

**Maturity: TRL 4 on synthetic scenarios** ([docs/TRL.md](docs/TRL.md)). No field data yet.

- `src/leakgraph/network.py` linearised pipe network, response matrix, sensor placement
- `src/leakgraph/localize.py` Bayesian posterior over leak nodes, split-conformal candidate sets, repair priority
- `src/leakgraph/simulate.py` synthetic scenarios
- `research/run_study.py` study, `research/results.json` output; `tests/` 8 tests
- Docs: [BRS](docs/BRS.md) · [SRS](docs/SRS.md) · [TRL](docs/TRL.md)

```bash
pip install -e ".[dev]" && python -m pytest -q && python research/run_study.py
```
