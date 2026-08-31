#!/usr/bin/env python3
"""Static, Persian-labelled catalogue of spreads/traditions used to build
menus. Keys must match engine.SPREADS exactly — this module intentionally
does not invent new spreads (per tarot/SKILL.md: "هیچ اسپردی را پیش‌فرض
نگذار... حدس نزن")."""

from __future__ import annotations

SPREAD_META: dict[str, dict] = {
    "one-card": {"emoji": "🃏", "label": "یک کارت", "desc": "یک کارت، یک پیام روشن."},
    "yes-no": {"emoji": "✅", "label": "آره یا نه", "desc": "پاسخ کوتاه به یک پرسش بله/خیر."},
    "three-ppf": {"emoji": "⏳", "label": "گذشته، حال، آینده", "desc": "روند یک موضوع در سه بازه."},
    "three-situation": {"emoji": "🧭", "label": "وضعیت، مانع، توصیه", "desc": "تحلیل عملی یک وضعیت."},
    "three-choice": {"emoji": "⚖️", "label": "مقایسه‌ی دو گزینه", "desc": "سنجش دو مسیر پیش‌رو."},
    "three-mbs": {"emoji": "🧘", "label": "ذهن، بدن، روح", "desc": "نگاهی کل‌نگر به حال درونی."},
    "five-cross": {"emoji": "➕", "label": "صلیب پنج‌کارتی", "desc": "بررسی عمیق‌تر یک موضوع."},
    "relationship-five": {"emoji": "💞", "label": "رابطه (۵ کارت)", "desc": "پویایی میان تو و طرف مقابل."},
    "horseshoe": {"emoji": "🐴", "label": "نعل اسبی (۷ کارت)", "desc": "مسیر کامل از گذشته تا پیامد محتمل."},
    "celtic-cross": {"emoji": "✝️", "label": "صلیب سلتی (۱۰ کارت)", "desc": "جامع‌ترین اسپرد کلاسیک."},
    "beytoote-ten": {"emoji": "🔟", "label": "اسپرد ده‌کارتی", "desc": "روایت گسترده از وضعیت زندگی."},
    "year-ahead": {"emoji": "📅", "label": "سال پیش رو (۱۲ ماه)", "desc": "نمای کلی دوازده ماه آینده."},
}

CATEGORIES: dict[str, dict] = {
    "quick": {"label": "🔹 فال‌های سریع", "spreads": ["one-card", "yes-no"]},
    "three": {"label": "🔹 اسپردهای سه‌کارتی", "spreads": ["three-ppf", "three-situation", "three-choice", "three-mbs"]},
    "five": {"label": "🔹 اسپردهای پنج‌کارتی", "spreads": ["five-cross", "relationship-five"]},
    "deep": {"label": "🔹 اسپردهای عمیق", "spreads": ["horseshoe", "celtic-cross", "beytoote-ten"]},
    "year": {"label": "🔹 سال پیش رو", "spreads": ["year-ahead"]},
}

TRADITION_META: dict[str, dict] = {
    "rws": {"label": "🎴 رایدر-وایت (استاندارد)"},
    "major-only": {"label": "🌟 فقط آرکانای بزرگ"},
    # "marseille" intentionally omitted: no legitimate structured Marseille
    # meanings dataset was found (searched — only card scans exist
    # publicly, not per-card interpretations). Add it back only once a
    # real, sourced Marseille dataset is wired in — never relabel RWS data.
}

SUIT_FA: dict[str, str] = {
    "wands": "عصا",
    "cups": "جام",
    "swords": "شمشیر",
    "pentacles": "سکه",
}
