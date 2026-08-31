#!/usr/bin/env python3
"""Optional external true-randomness source for card draws.

Uses RANDOM.ORG's legacy HTTP API (no signup, no API key — stable since
1998, sourced from atmospheric radio noise): https://www.random.org/clients/http/api/
`/sequences/` returns a genuine random permutation ("to shuffle a deck of
cards", per their own docs); `/integers/` with min=0 max=1 gives genuine
random bits, used here for reversed/upright.

This is entirely optional and self-contained: any failure (network error,
timeout, malformed response, wrong count) returns None and the caller
falls back to secrets.SystemRandom() — a real tarot reading must never
fail, hang, or block because an external service is slow or down.

(ANU's QRNG API is not used here: their free/no-signup endpoint is
documented as being phased out in favor of a new service that requires a
registered API key, which is a worse fit for a zero-config default.)
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request

logger = logging.getLogger("tarot_bot.truerandom")

_TIMEOUT_SECONDS = 5
_USER_AGENT = "tarot-bot/1.0 (+https://github.com/amirxoo13/taroot-bot)"


def _fetch_plain_lines(url: str, expected_count: int) -> list[str] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                return None
            text = resp.read().decode("utf-8", errors="replace").strip()
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.debug("random.org request failed", exc_info=True)
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) != expected_count:
        logger.debug("random.org returned %d lines, expected %d", len(lines), expected_count)
        return None
    return lines


def fetch_permutation(n: int) -> list[int] | None:
    """A genuine random permutation of 0..n-1 (atmospheric-noise sourced),
    or None if anything went wrong. n must be small (deck size, <= 78)."""
    if n <= 0:
        return []
    url = f"https://www.random.org/sequences/?min=0&max={n - 1}&format=plain&rnd=new"
    lines = _fetch_plain_lines(url, n)
    if lines is None:
        return None
    try:
        perm = [int(x) for x in lines]
    except ValueError:
        return None
    if sorted(perm) != list(range(n)):
        return None
    return perm


def fetch_bits(n: int) -> list[bool] | None:
    """n genuine random booleans (atmospheric-noise sourced), or None on
    any failure."""
    if n <= 0:
        return []
    url = f"https://www.random.org/integers/?num={n}&min=0&max=1&col=1&base=10&format=plain&rnd=new"
    lines = _fetch_plain_lines(url, n)
    if lines is None:
        return None
    if not all(line in ("0", "1") for line in lines):
        return None
    return [line == "1" for line in lines]
