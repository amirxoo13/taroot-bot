#!/usr/bin/env python3
"""Draw cards from the sibling tarot skill dataset and build a reading pack."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

MAJOR_FA = {
    0: "احمق",
    1: "جادوگر",
    2: "کاهنهٔ اعظم",
    3: "امپراتریس",
    4: "امپراتور",
    5: "هیروفانت",
    6: "عشاق",
    7: "ارابه",
    8: "قدرت",
    9: "گوشه‌نشین",
    10: "چرخ بخت",
    11: "عدالت",
    12: "مرد حلق‌آویز",
    13: "مرگ",
    14: "اعتدال",
    15: "شیطان",
    16: "برج",
    17: "ستاره",
    18: "ماه",
    19: "خورشید",
    20: "داوری",
    21: "جهان",
}

SUIT_FA = {
    "wands": "عصا",
    "cups": "جام",
    "swords": "شمشیر",
    "pentacles": "سکه",
}

RANK_FA = {
    "ace": "آس",
    "two": "دو",
    "three": "سه",
    "four": "چهار",
    "five": "پنج",
    "six": "شش",
    "seven": "هفت",
    "eight": "هشت",
    "nine": "نه",
    "ten": "ده",
    "page": "صفحه",
    "knight": "شوالیه",
    "queen": "ملکه",
    "king": "شاه",
}

SPREADS: dict[str, list[str]] = {
    "one-card": ["پیام"],
    "yes-no": ["پاسخ"],
    "three-ppf": ["گذشته", "حال", "آینده اگر روند بماند"],
    "three-situation": ["وضعیت", "مانع", "توصیه"],
    "three-choice": ["گزینهٔ آ", "گزینهٔ ب", "معیار"],
    "three-mbs": ["ذهن", "بدن", "روح"],
    "five-cross": ["موضوع", "گذشته", "آینده", "شالوده", "بهترین مسیر ممکن"],
    "relationship-five": ["تو", "دیگری", "رابطه", "چالش", "مسیر"],
    "horseshoe": ["گذشته", "حال", "آیندهٔ نزدیک", "نگرش", "محیط", "مانع", "پیامد محتمل"],
    "celtic-cross": ["وضع حاضر", "چالش روی آن", "آگاهانه", "ناخودآگاه / شالوده", "گذشتهٔ نزدیک", "آیندهٔ نزدیک", "خود پرسشگر", "محیط", "امید یا ترس", "پیامد محتمل"],
    "beytoote-ten": ["پرسشگر", "وضعیت حاضر", "گذشتهٔ نزدیک", "گذشتهٔ دورتر", "هدف", "آیندهٔ نزدیک", "نگرش", "محیط", "امید یا ترس", "نتیجه"],
    "year-ahead": [f"ماه {i}" for i in range(1, 13)],
}

SYSTEM_PROMPT = """تو خوانندهٔ میز تاروت هستی. فقط فارسی بنویس. لحن آرام، نزدیک به جلسهٔ حضوری، بدون لودگی.
فال روایت و تأمل است نه پزشکی، حقوقی، یا پیش‌بینی قطعی بازار.
کارت‌ها از قبل کشیده شده‌اند. نام، جهت، و جایگاه را عوض نکن و کارت جدید نساز.
سنت را از فیلد tradition بخوان. اگر RWS است از meaning و کلیدواژه‌های داده‌شده استفاده کن.
ساختار: یک جملهٔ ورود به میز؛ هر جایگاه با حس تصویر؛ پیوند کارت‌ها مثل جمله؛ یک سؤال آرام در پایان.
وعدهٔ معجزه و دستور جادو نده."""


def skill_dir() -> Path:
    raw = os.environ.get("TAROT_SKILL_DIR", "/home/workdir/.grok/skills/tarot")
    return Path(raw)


def load_cards() -> list[dict]:
    path = skill_dir() / "references" / "cards.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing cards.json: {path}")
    cards = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cards, list) or len(cards) != 78:
        raise ValueError("cards.json must contain 78 objects")
    return cards


def name_fa(card: dict) -> str:
    if card.get("arcana") == "major":
        return MAJOR_FA.get(int(card["id"]), card["name"])
    suit = SUIT_FA.get(str(card.get("suit") or ""), "")
    head = str(card["name"]).split(" of ", 1)[0].lower()
    rank = RANK_FA.get(head, head)
    if rank in ("ملکه", "شاه"):
        return f"{rank} {suit}"
    return f"{rank} {suit}".strip()


def pick_pool(cards: list[dict], tradition: str) -> list[dict]:
    if tradition == "major-only":
        return [c for c in cards if c.get("arcana") == "major"]
    return list(cards)


def draw_spread(
    spread: str,
    *,
    seed: int | None = None,
    reversals: bool = False,
    tradition: str = "rws",
    question: str = "",
) -> dict:
    if spread not in SPREADS:
        raise ValueError(f"unknown spread: {spread}")
    positions = SPREADS[spread]
    cards = pick_pool(load_cards(), tradition)
    rng = random.Random(seed)
    chosen = rng.sample(cards, k=len(positions))
    packed = []
    for pos, card in zip(positions, chosen):
        rev = bool(reversals and rng.choice((True, False)))
        item = {
            "position": pos,
            "id": card["id"],
            "name": card["name"],
            "name_fa": name_fa(card),
            "arcana": card.get("arcana"),
            "suit": card.get("suit"),
            "orientation": "reversed" if rev else "upright",
            "keywords": card.get("keywords_reversed" if rev else "keywords_upright", []),
            "meaning": card.get("meaning_reversed" if rev else "meaning_upright", ""),
            "love": card.get("love_reversed" if rev else "love", ""),
            "career": card.get("career_reversed" if rev else "career", ""),
        }
        if spread == "yes-no":
            item["yes_no"] = card.get("yes_no_reversed" if rev else "yes_no")
        packed.append(item)
    return {
        "spread": spread,
        "positions": positions,
        "tradition": tradition,
        "reversals": reversals,
        "seed": seed,
        "question": question,
        "cards": packed,
    }


def format_fallback(pack: dict) -> str:
    lines = [
        "فال تاروت روایت است نه حکم قطعی.",
        f"اسپرد: {pack['spread']} | سنت: {pack['tradition']}",
    ]
    if pack.get("question"):
        lines.append(f"نیت: {pack['question']}")
    lines.append("")
    for card in pack["cards"]:
        dir_fa = "معکوس" if card["orientation"] == "reversed" else "قائم"
        keys = "، ".join(card.get("keywords") or [])
        lines.append(f"• {card['position']} — {card['name_fa']} ({card['name']}) [{dir_fa}]")
        if keys:
            lines.append(f"  کلید: {keys}")
        if card.get("meaning"):
            lines.append(f"  {card['meaning']}")
        if card.get("yes_no"):
            lines.append(f"  برچسب آره/نه ناشر: {card['yes_no']}")
        lines.append("")
    lines.append("متن بالا از دیتاست است؛ مدل زبانی در دسترس نبود یا فراخوانی نشد.")
    return "\n".join(lines).strip()


def build_messages(pack: dict) -> list[dict]:
    user = {
        "question": pack.get("question") or "",
        "tradition": pack["tradition"],
        "spread": pack["spread"],
        "reversals": pack["reversals"],
        "cards": pack["cards"],
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--spread", default="three-ppf", choices=sorted(SPREADS))
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--reversals", action="store_true")
    p.add_argument("--tradition", default="rws", choices=("rws", "marseille", "major-only"))
    p.add_argument("--question", default="")
    args = p.parse_args()
    pack = draw_spread(
        args.spread,
        seed=args.seed,
        reversals=args.reversals,
        tradition=args.tradition,
        question=args.question,
    )
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
