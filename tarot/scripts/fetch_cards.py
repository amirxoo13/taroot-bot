#!/usr/bin/env python3
"""Download the 78-card Tarotoo MIT dataset into references/cards.json."""
from pathlib import Path
import urllib.request

URL = "https://raw.githubusercontent.com/Tarotoo-com/tarotoo-tarot-dataset/main/data/cards.json"
DEST = Path(__file__).resolve().parents[1] / "references" / "cards.json"

def main() -> int:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "taroot-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    DEST.write_bytes(data)
    print(f"wrote {DEST} ({len(data)} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
