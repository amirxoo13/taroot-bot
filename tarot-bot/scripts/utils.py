#!/usr/bin/env python3
"""Small, dependency-free helpers shared across the bot modules."""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Iterable, Iterator, TypeVar

TELEGRAM_TEXT_LIMIT = 4096
SAFE_CHUNK_LIMIT = 3800  # headroom under Telegram's hard 4096-char limit

T = TypeVar("T")


def chunk_text(text: str, limit: int = SAFE_CHUNK_LIMIT) -> list[str]:
    """Split long text into Telegram-safe pieces, preferring paragraph/line/
    word boundaries so a reading is never cut mid-sentence if avoidable."""
    text = (text or "").strip()
    if not text:
        return [""]
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def daily_seed(user_id: int, day: date | None = None) -> int:
    """Deterministic per-user, per-day seed so /rooz draws the same card
    if called twice in the same day, but differs across users and days."""
    day = day or date.today()
    raw = f"{user_id}:{day.isoformat()}".encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:12], 16)


def chunked(seq: list[T], size: int) -> Iterator[list[T]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]
