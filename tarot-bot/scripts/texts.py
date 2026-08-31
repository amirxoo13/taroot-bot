#!/usr/bin/env python3
"""Centralized Persian UI copy. Keeping every user-facing string in one
place makes tone/wording easy to review and change without touching
handler logic."""

from __future__ import annotations

WELCOME = (
    "🔮 <b>به ربات فال تاروت خوش آمدید</b>\n\n"
    "این ربات بر پایه‌ی سنت رایدر-وایت، مارسی و منابع تاروت، یک خوانش "
    "ساختاریافته از کارت‌ها براتون می‌سازه.\n\n"
    "⚠️ <i>فال تاروت روایت و تأمل است؛ نه تشخیص پزشکی، حکم حقوقی یا "
    "پیش‌بینی قطعی بازار.</i>\n\n"
    "برای شروع، از منوی زیر انتخاب کنید 👇"
)

MAIN_MENU_PROMPT = "منوی اصلی:"

HELP = (
    "📖 <b>راهنما</b>\n\n"
    "/fal — شروع یک فال جدید (اسپرد، سنت و نیت رو خودتون انتخاب می‌کنید)\n"
    "/rooz — یک کارت تصادفی برای امروز\n"
    "/gallery یا /cards — مرور همه‌ی ۷۸ کارت دسته\n"
    "/cancel — لغو فالِ در حال انجام\n"
    "/help — همین راهنما\n\n"
    "⚠️ خروجی این ربات جایگزین مشاوره‌ی تخصصی (پزشکی، حقوقی، مالی) نیست."
)

CHOOSE_CATEGORY = "یک دسته از اسپردها رو انتخاب کنید:"
CHOOSE_SPREAD = "کدوم اسپرد رو می‌خواید؟"
CHOOSE_TRADITION = "کدوم سنت تاروت مدنظرتونه؟"
CHOOSE_REVERSALS = "کارت‌های معکوس هم در نظر گرفته بشن؟"
ASK_NIYAT = (
    "اگه نیت یا پرسش خاصی دارید بنویسید (اختیاریه، می‌تونید رد کنید).\n"
    "این متن فقط برای دقیق‌تر شدن خوانش استفاده می‌شه."
)

DRAWING = "🃏 در حال بریدن دسته و کشیدن کارت‌ها…"
INTERPRETING = "✨ در حال نوشتن تفسیر…"
READING_DONE = "پایان خوانش 🔮"

CANCELLED = "❌ فالِ در حال انجام لغو شد."
NOTHING_TO_CANCEL = "چیزی برای لغو کردن در جریان نیست."
GENERIC_ERROR = "⚠️ یک مشکل موقت پیش اومد. دوباره امتحان کنید یا /cancel بزنید."
HF_UNAVAILABLE_NOTE = (
    "\n\n(مدل زبانی موقتاً در دسترس نبود؛ این تفسیر بر پایه‌ی دیتاست کارت‌هاست.)"
)

ROOZ_ASK_MORE = "می‌خواید یک فال کامل‌تر هم بگیرید؟"


def confirm_summary(spread_label: str, tradition_label: str, reversals: bool, niyat: str) -> str:
    lines = [
        "🔎 <b>خلاصه‌ی انتخاب شما</b>",
        f"اسپرد: {spread_label}",
        f"سنت: {tradition_label}",
        f"کارت معکوس: {'بله' if reversals else 'خیر'}",
    ]
    if niyat:
        lines.append(f"نیت: {niyat}")
    lines.append("")
    lines.append("آماده‌اید؟")
    return "\n".join(lines)


def rooz_header(name_fa: str, name_en: str, orientation_fa: str) -> str:
    return f"🌞 <b>کارت امروز شما</b>\n{name_fa} ({name_en}) — {orientation_fa}"


def gallery_header(total: int, page: int, total_pages: int) -> str:
    return (
        f"🃏 گالری کارت‌ها ({total} کارت) — صفحه {page + 1} از {total_pages}\n"
        "برای دیدن جزئیات، روی کارت بزنید:"
    )
