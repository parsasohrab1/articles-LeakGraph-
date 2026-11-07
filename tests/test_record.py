import json
from pathlib import Path

from leakgraph.record import registration_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_registration_card_matches_the_results_file():
    payload = json.loads((ROOT / "research" / "results.json").read_text(encoding="utf-8"))
    card = (ROOT / "docs" / "REGISTRATION.md").read_text(encoding="utf-8")
    assert card == registration_markdown(payload["battledim"])
    assert "بنچ‌مارک شبیه‌سازی‌شده" in card
    assert "ارسال نشده" in card
    assert "nrwleak" in card
    assert payload["battledim"]["doi"] in card
