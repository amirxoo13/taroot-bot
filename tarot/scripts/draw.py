#!/usr/bin/env python3
"""Draw or look up RWS cards from references/cards.json. Does not invent meanings."""
from __future__ import annotations
import argparse, json, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS_PATH = ROOT / "references" / "cards.json"
SPREADS = {
    "one-card": 1, "yes-no": 1, "three-ppf": 3, "three-situation": 3,
    "three-choice": 3, "three-mbs": 3, "five-cross": 5, "relationship-five": 5,
    "horseshoe": 7, "celtic-cross": 10, "tree-of-life": 10, "houses-twelve": 12,
    "year-ahead": 12, "beytoote-ten": 10,
}

def load_cards():
    cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
    if not isinstance(cards, list) or len(cards) != 78:
        raise ValueError("expected 78 cards")
    return cards

def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int)
    p.add_argument("--spread", choices=sorted(SPREADS))
    p.add_argument("--seed", type=int)
    p.add_argument("--lookup")
    args = p.parse_args(argv)
    cards = load_cards()
    if args.lookup:
        q = args.lookup.lower()
        hits = [c for c in cards if q in c["name"].lower() or q == str(c["id"])]
        print(json.dumps(hits[0] if hits else {"error": args.lookup}, ensure_ascii=False, indent=2))
        return 0
    count = SPREADS[args.spread] if args.spread else (args.count or 1)
    rng = random.Random(args.seed)
    chosen = rng.sample(cards, count)
    print(json.dumps({"spread": args.spread, "cards": chosen}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
