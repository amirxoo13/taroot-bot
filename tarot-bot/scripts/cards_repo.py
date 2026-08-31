#!/usr/bin/env python3
"""Cached, read-only access to the tarot dataset and card image files.

Card ids 0-77 map 1:1 onto image files written by download_cards.py
(`{id:02d}.jpg`): 0-21 are the Majors, 22-35 Wands, 36-49 Cups, 50-63
Swords, 64-77 Pentacles — verified directly against the Tarotoo dataset
this bot fetches (see tarot/scripts/fetch_cards.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import engine  # sibling module; reads TAROT_SKILL_DIR/references/cards.json

_CARDS: list[dict] | None = None
_BY_ID: dict[int, dict] | None = None


def all_cards() -> list[dict]:
    """All 78 cards, sorted by id. Loaded once and cached in memory."""
    global _CARDS, _BY_ID
    if _CARDS is None:
        cards = sorted(engine.load_cards(), key=lambda c: int(c["id"]))
        _CARDS = cards
        _BY_ID = {int(c["id"]): c for c in cards}
    return _CARDS


def by_id(card_id: int) -> Optional[dict]:
    all_cards()
    assert _BY_ID is not None
    return _BY_ID.get(int(card_id))


def image_path(card_id: int, assets_dir: Path) -> Optional[Path]:
    """Local path to a card's scan, or None if it hasn't been downloaded
    (download_cards.py can fail per-card on flaky sources; the bot degrades
    to text-only for that specific card rather than crashing)."""
    path = assets_dir / "cards" / f"{int(card_id):02d}.jpg"
    return path if path.is_file() else None
