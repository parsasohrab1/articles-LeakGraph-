"""Rewrite docs/REGISTRATION.md from research/results.json.

Usage: python research/write_registration.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leakgraph.record import registration_markdown


def main() -> None:
    payload = json.loads((ROOT / "research" / "results.json").read_text(encoding="utf-8"))
    text = registration_markdown(payload["battledim"])
    path = ROOT / "docs" / "REGISTRATION.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(path)


if __name__ == "__main__":
    main()
