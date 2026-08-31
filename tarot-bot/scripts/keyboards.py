#!/usr/bin/env python3
"""Inline keyboard builders. Kept separate from handler logic so the UI
layout can change without touching bot flow/state code."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import catalog
import engine


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔮 شروع فال", callback_data="menu:new_reading")],
        [InlineKeyboardButton("🌞 فال روز", callback_data="menu:rooz")],
        [InlineKeyboardButton("🃏 گالری کارت‌ها", callback_data="gal:page:0")],
        [InlineKeyboardButton("❓ راهنما", callback_data="menu:help")],
    ]
    return InlineKeyboardMarkup(rows)


def categories_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(meta["label"], callback_data=f"cat:{key}")]
        for key, meta in catalog.CATEGORIES.items()
    ]
    rows.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def spreads_menu(category_key: str) -> InlineKeyboardMarkup:
    spreads = catalog.CATEGORIES[category_key]["spreads"]
    rows = []
    for key in spreads:
        meta = catalog.SPREAD_META[key]
        rows.append([InlineKeyboardButton(f"{meta['emoji']} {meta['label']}", callback_data=f"spread:{key}")])
    rows.append([InlineKeyboardButton("🔙 دسته‌بندی‌ها", callback_data="menu:new_reading")])
    return InlineKeyboardMarkup(rows)


def tradition_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(meta["label"], callback_data=f"trad:{key}")]
        for key, meta in catalog.TRADITION_META.items()
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="nav:back_to_spread")])
    return InlineKeyboardMarkup(rows)


def reversals_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔄 بله، با کارت معکوس", callback_data="rev:yes")],
        [InlineKeyboardButton("➡️ نه، فقط قائم", callback_data="rev:no")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="nav:back_to_tradition")],
    ]
    return InlineKeyboardMarkup(rows)


def niyat_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("⏭️ رد کردن، بدون نیت خاص", callback_data="niyat:skip")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="nav:back_to_reversals")],
    ]
    return InlineKeyboardMarkup(rows)


def confirm_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔮 کارت‌ها را بکش", callback_data="confirm:draw")],
        [InlineKeyboardButton("🔙 تغییر انتخاب‌ها", callback_data="nav:back_to_reversals")],
        [InlineKeyboardButton("❌ انصراف", callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(rows)


def post_reading_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔁 فال دیگر", callback_data="menu:new_reading")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(rows)


def gallery_page(cards_slice: list[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for card in cards_slice:
        label = engine.name_fa(card)
        row.append(InlineKeyboardButton(label, callback_data=f"gal:card:{card['id']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"gal:page:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"gal:page:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def card_detail_menu(back_to_page: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔙 بازگشت به گالری", callback_data=f"gal:page:{back_to_page}")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(rows)
