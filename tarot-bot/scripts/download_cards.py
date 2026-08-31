#!/usr/bin/env python3
"""Download public-domain 1909 Waite-Smith scans."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "cards"
UA = "tarot-bot/1.0 (educational; public-domain 1909 scans)"

MAJORS = [
    "RWS_Tarot_00_Fool.jpg",
    "RWS_Tarot_01_Magician.jpg",
    "RWS_Tarot_02_High_Priestess.jpg",
    "RWS_Tarot_03_Empress.jpg",
    "RWS_Tarot_04_Emperor.jpg",
    "RWS_Tarot_05_Hierophant.jpg",
    "RWS_Tarot_06_Lovers.jpg",
    "RWS_Tarot_07_Chariot.jpg",
    "RWS_Tarot_08_Strength.jpg",
    "RWS_Tarot_09_Hermit.jpg",
    "RWS_Tarot_10_Wheel_of_Fortune.jpg",
    "RWS_Tarot_11_Justice.jpg",
    "RWS_Tarot_12_Hanged_Man.jpg",
    "RWS_Tarot_13_Death.jpg",
    "RWS_Tarot_14_Temperance.jpg",
    "RWS_Tarot_15_Devil.jpg",
    "RWS_Tarot_16_Tower.jpg",
    "RWS_Tarot_17_Star.jpg",
    "RWS_Tarot_18_Moon.jpg",
    "RWS_Tarot_19_Sun.jpg",
    "RWS_Tarot_20_Judgement.jpg",
    "RWS_Tarot_21_World.jpg",
]


def dest_for_id(i: int) -> Path:
    return OUT / f"{i:02d}.jpg"


def urls_for(i: int) -> list[str]:
    ia = "https://archive.org/download/pents-13"
    if i <= 21:
        name = MAJORS[i]
        return [f"{ia}/{name}", f"https://commons.wikimedia.org/wiki/Special:FilePath/{name}"]
    suit_idx, rank = divmod(i - 22, 14)
    suits = ["Wands", "Cups", "Swords", "Pents"]
    suit = suits[suit_idx]
    n = rank + 1
    return [f"{ia}/{suit}{n:02d}.jpg", f"https://commons.wikimedia.org/wiki/Special:FilePath/{suit}{n:02d}.jpg"]


def fetch(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
        if len(data) < 2000 or "html" in ctype.lower():
            return False
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    for i in range(78):
        dest = dest_for_id(i)
        if dest.is_file() and dest.stat().st_size > 2000:
            ok += 1
            continue
        for url in urls_for(i):
            if fetch(url, dest):
                ok += 1
                print(f"ok {i:02d} {url}")
                break
        else:
            print(f"FAIL {i:02d}", file=sys.stderr)
    print(f"have {ok}/78")
    return 0 if ok == 78 else 1


if __name__ == "__main__":
    sys.exit(main())
