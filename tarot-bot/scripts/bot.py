#!/usr/bin/env python3
"""Persian Telegram tarot bot — entrypoint.

Reads cards + spreads from the sibling ``tarot`` skill dataset via
``engine.py`` and ``cards_repo.py``, narrates readings through Hugging Face
Inference Providers via ``hf_client.py`` (falling back to
``engine.format_fallback`` if the model call fails or HF_TOKEN is unset),
and drives a fully button-based conversation over python-telegram-bot.

Run mode (webhook by default, polling for local testing) and all secrets
come from environment variables — see ../assets/env.example.
"""

from __future__ import annotations

import asyncio
import html
import logging
import math
import sys

from telegram import (
    BotCommand,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import cards_repo
import catalog
import engine
import hf_client
import keyboards
import texts
import utils
from config import Config, load_config

logger = logging.getLogger("tarot_bot")

# --- conversation states -----------------------------------------------
(
    ST_CATEGORY,
    ST_SPREAD,
    ST_TRADITION,
    ST_REVERSALS,
    ST_NIYAT,
    ST_CONFIRM,
) = range(6)


def _cfg(context: ContextTypes.DEFAULT_TYPE) -> Config:
    return context.bot_data["cfg"]


def _reading(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("reading", {})


# --- small helpers -------------------------------------------------------

def _card_caption(index: int, card: dict) -> str:
    orient = "🔄 معکوس" if card["orientation"] == "reversed" else "⬆️ قائم"
    position = html.escape(str(card["position"]))
    name_fa = html.escape(str(card["name_fa"]))
    name_en = html.escape(str(card["name"]))
    return f"<b>{index}. {position}</b>\n{name_fa} ({name_en}) — {orient}"


def _card_detail_caption(card: dict) -> str:
    name_fa = html.escape(engine.name_fa(card))
    name_en = html.escape(str(card["name"]))
    arcana_fa = "آرکانای بزرگ" if card.get("arcana") == "major" else "آرکانای کوچک"
    suit = card.get("suit")
    suit_line = f" — {catalog.SUIT_FA.get(suit, suit)}" if suit else ""
    keywords = "، ".join(card.get("keywords_upright") or [])
    meaning = card.get("meaning_upright") or ""
    lines = [
        f"<b>{name_fa}</b> ({name_en})",
        f"{arcana_fa}{suit_line}",
    ]
    if keywords:
        lines.append(f"کلیدواژه: {html.escape(keywords)}")
    if meaning:
        lines.append("")
        lines.append(html.escape(meaning))
    yes_no = card.get("yes_no")
    if yes_no:
        yn_fa = {"yes": "بله", "no": "خیر", "maybe": "شاید"}.get(yes_no, yes_no)
        lines.append("")
        lines.append(f"برچسب آره/نه: {yn_fa}")
    return "\n".join(lines)


async def _send_cards(context: ContextTypes.DEFAULT_TYPE, chat_id: int, cards: list[dict]) -> None:
    cfg = _cfg(context)
    media_batch: list[tuple[bytes, str]] = []
    text_only: list[str] = []
    for i, card in enumerate(cards, start=1):
        caption = _card_caption(i, card)
        path = cards_repo.image_path(card["id"], cfg.assets_dir)
        if path:
            try:
                media_batch.append((path.read_bytes(), caption))
                continue
            except OSError:
                logger.warning("could not read card image %s", path, exc_info=True)
        text_only.append(caption)

    for batch in utils.chunked(media_batch, 10):
        media = [
            InputMediaPhoto(media=data, caption=cap, parse_mode=ParseMode.HTML)
            for data, cap in batch
        ]
        await context.bot.send_media_group(chat_id, media)

    if text_only:
        await context.bot.send_message(chat_id, "\n\n".join(text_only), parse_mode=ParseMode.HTML)


async def _build_reading(pack: dict, hf_token_present: bool) -> tuple[str, bool]:
    """Returns (reading_text, used_fallback)."""
    if not hf_token_present:
        return engine.format_fallback(pack), True
    messages = engine.build_messages(pack)
    try:
        text = await asyncio.to_thread(hf_client.complete, messages)
        return text, False
    except Exception:
        logger.warning("HF completion failed, using dataset fallback", exc_info=True)
        return engine.format_fallback(pack), True


async def _render_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int) -> None:
    q = update.callback_query
    cfg = _cfg(context)
    page_size = cfg.gallery_page_size
    cards = cards_repo.all_cards()
    total_pages = max(1, math.ceil(len(cards) / page_size))
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    cards_slice = cards[start : start + page_size]

    text_ = texts.gallery_header(len(cards), page, total_pages)
    markup = keyboards.gallery_page(cards_slice, page, total_pages)

    if q is not None:
        await q.answer()
        if q.message and q.message.photo:
            await q.message.delete()
            await context.bot.send_message(q.message.chat_id, text_, reply_markup=markup)
        else:
            await q.edit_message_text(text_, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text_, reply_markup=markup)


# --- top-level commands ---------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This bot only ever uses inline keyboards. If an older version of the
    # bot (on this same token) left a persistent custom reply-keyboard
    # behind, clear it once, silently, so it stops confusing people.
    chat_id = update.effective_chat.id
    try:
        cleanup = await context.bot.send_message(chat_id, "🧹", reply_markup=ReplyKeyboardRemove())
        await context.bot.delete_message(chat_id, cleanup.message_id)
    except Exception:
        logger.debug("reply-keyboard cleanup skipped", exc_info=True)
    await update.effective_message.reply_html(texts.WELCOME, reply_markup=keyboards.main_menu())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            texts.HELP, parse_mode=ParseMode.HTML, reply_markup=keyboards.main_menu()
        )
    else:
        await update.effective_message.reply_html(texts.HELP, reply_markup=keyboards.main_menu())


async def cb_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("reading", None)
    q = update.callback_query
    if q is not None:
        await q.answer()
        await q.edit_message_text(texts.MAIN_MENU_PROMPT, reply_markup=keyboards.main_menu())
    else:
        await update.effective_message.reply_text(texts.MAIN_MENU_PROMPT, reply_markup=keyboards.main_menu())
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    had = bool(context.user_data.pop("reading", None))
    await update.effective_message.reply_text(
        texts.CANCELLED if had else texts.NOTHING_TO_CANCEL,
        reply_markup=keyboards.main_menu(),
    )
    return ConversationHandler.END


async def cmd_rooz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    cfg = _cfg(context)

    await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
    seed = utils.daily_seed(user_id)
    pack = await asyncio.to_thread(
        engine.draw_spread, "one-card", seed=seed, reversals=True, tradition="rws"
    )
    card = pack["cards"][0]
    header = texts.rooz_header(
        card["name_fa"], card["name"], "معکوس" if card["orientation"] == "reversed" else "قائم"
    )
    path = cards_repo.image_path(card["id"], cfg.assets_dir)
    if path:
        await context.bot.send_photo(
            chat_id, photo=path.read_bytes(), caption=header, parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.send_message(chat_id, header, parse_mode=ParseMode.HTML)

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    reading_text, used_fallback = await _build_reading(pack, bool(cfg.hf_token))
    if used_fallback:
        reading_text += texts.HF_UNAVAILABLE_NOTE
    for chunk in utils.chunk_text(reading_text):
        await context.bot.send_message(chat_id, chunk)

    await context.bot.send_message(chat_id, texts.ROOZ_ASK_MORE, reply_markup=keyboards.post_reading_menu())


async def cmd_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _render_gallery(update, context, 0)


async def cb_gallery_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    page = int(update.callback_query.data.split(":")[2])
    await _render_gallery(update, context, page)


async def cb_gallery_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    card_id = int(q.data.split(":")[2])
    card = cards_repo.by_id(card_id)
    if not card:
        await q.answer("پیدا نشد.", show_alert=True)
        return
    cfg = _cfg(context)
    caption = _card_detail_caption(card)
    back_page = card_id // cfg.gallery_page_size
    markup = keyboards.card_detail_menu(back_page)
    chat_id = q.message.chat_id
    path = cards_repo.image_path(card_id, cfg.assets_dir)
    if path:
        await context.bot.send_photo(
            chat_id, photo=path.read_bytes(), caption=caption, parse_mode=ParseMode.HTML, reply_markup=markup
        )
    else:
        await context.bot.send_message(chat_id, caption, parse_mode=ParseMode.HTML, reply_markup=markup)


async def cb_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()


# --- reading conversation ---------------------------------------------------

async def cb_new_reading(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["reading"] = {}
    text_, markup = texts.CHOOSE_CATEGORY, keyboards.categories_menu()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text_, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text_, reply_markup=markup)
    return ST_CATEGORY


async def cb_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    _reading(context)["category"] = key
    await q.edit_message_text(texts.CHOOSE_SPREAD, reply_markup=keyboards.spreads_menu(key))
    return ST_SPREAD


async def cb_spread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    _reading(context)["spread"] = key
    await q.edit_message_text(texts.CHOOSE_TRADITION, reply_markup=keyboards.tradition_menu())
    return ST_TRADITION


async def cb_back_to_spread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    cat = _reading(context).get("category")
    if not cat:
        return await cb_new_reading(update, context)
    await q.edit_message_text(texts.CHOOSE_SPREAD, reply_markup=keyboards.spreads_menu(cat))
    return ST_SPREAD


async def cb_tradition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    _reading(context)["tradition"] = key
    await q.edit_message_text(texts.CHOOSE_REVERSALS, reply_markup=keyboards.reversals_menu())
    return ST_REVERSALS


async def cb_back_to_tradition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(texts.CHOOSE_TRADITION, reply_markup=keyboards.tradition_menu())
    return ST_TRADITION


async def cb_reversals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    value = q.data.split(":", 1)[1] == "yes"
    _reading(context)["reversals"] = value
    await q.edit_message_text(texts.ASK_NIYAT, reply_markup=keyboards.niyat_menu())
    return ST_NIYAT


async def cb_back_to_reversals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(texts.CHOOSE_REVERSALS, reply_markup=keyboards.reversals_menu())
    return ST_REVERSALS


def _confirm_text(reading: dict) -> str:
    spread_meta = catalog.SPREAD_META[reading["spread"]]
    spread_label = f"{spread_meta['emoji']} {spread_meta['label']}"
    tradition_label = catalog.TRADITION_META[reading["tradition"]]["label"]
    return texts.confirm_summary(spread_label, tradition_label, reading["reversals"], reading.get("niyat", ""))


async def cb_niyat_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    _reading(context)["niyat"] = ""
    await q.edit_message_text(
        _confirm_text(_reading(context)), parse_mode=ParseMode.HTML, reply_markup=keyboards.confirm_menu()
    )
    return ST_CONFIRM


async def msg_niyat_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text_ = (update.effective_message.text or "").strip()[:300]
    _reading(context)["niyat"] = text_
    await update.effective_message.reply_html(
        _confirm_text(_reading(context)), reply_markup=keyboards.confirm_menu()
    )
    return ST_CONFIRM


async def cb_confirm_draw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    reading = context.user_data.get("reading")
    if not reading or "spread" not in reading or "tradition" not in reading:
        await q.edit_message_text(texts.NOTHING_TO_CANCEL, reply_markup=keyboards.main_menu())
        return ConversationHandler.END

    cfg = _cfg(context)
    chat_id = update.effective_chat.id

    await q.edit_message_text(texts.DRAWING)
    await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
    try:
        pack = await asyncio.to_thread(
            engine.draw_spread,
            reading["spread"],
            reversals=reading["reversals"],
            tradition=reading["tradition"],
            question=reading.get("niyat", ""),
        )
    except Exception:
        logger.exception("draw_spread failed")
        await context.bot.send_message(chat_id, texts.GENERIC_ERROR)
        context.user_data.pop("reading", None)
        return ConversationHandler.END

    await _send_cards(context, chat_id, pack["cards"])

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    status_msg = await context.bot.send_message(chat_id, texts.INTERPRETING)
    reading_text, used_fallback = await _build_reading(pack, bool(cfg.hf_token))
    if used_fallback:
        reading_text += texts.HF_UNAVAILABLE_NOTE

    try:
        await context.bot.delete_message(chat_id, status_msg.message_id)
    except Exception:
        pass

    for chunk in utils.chunk_text(reading_text):
        await context.bot.send_message(chat_id, chunk)

    await context.bot.send_message(chat_id, texts.READING_DONE, reply_markup=keyboards.post_reading_menu())
    context.user_data.pop("reading", None)
    return ConversationHandler.END


async def cb_unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "متوجه نشدم 🤔 لطفاً از دکمه‌های زیر پیام‌ها استفاده کنید:",
        reply_markup=keyboards.main_menu(),
    )


# --- error handling ---------------------------------------------------

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception while processing update: %s", update, exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(update.effective_chat.id, texts.GENERIC_ERROR)
        except Exception:
            pass


# --- application wiring ---------------------------------------------------

async def _post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "شروع / منوی اصلی"),
            BotCommand("fal", "شروع یک فال جدید"),
            BotCommand("rooz", "فال روز"),
            BotCommand("gallery", "گالری کارت‌ها"),
            BotCommand("cards", "گالری کارت‌ها"),
            BotCommand("help", "راهنما"),
            BotCommand("cancel", "لغو فالِ در حال انجام"),
        ]
    )
    logger.info("Bot commands registered with Telegram.")


def build_application(cfg: Config) -> Application:
    application = (
        ApplicationBuilder()
        .token(cfg.telegram_token)
        .rate_limiter(AIORateLimiter())
        .post_init(_post_init)
        .build()
    )
    application.bot_data["cfg"] = cfg

    reading_conv = ConversationHandler(
        entry_points=[
            CommandHandler("fal", cb_new_reading),
            CallbackQueryHandler(cb_new_reading, pattern="^menu:new_reading$"),
        ],
        states={
            ST_CATEGORY: [
                CallbackQueryHandler(cb_category, pattern="^cat:"),
            ],
            ST_SPREAD: [
                CallbackQueryHandler(cb_spread, pattern="^spread:"),
                CallbackQueryHandler(cb_new_reading, pattern="^menu:new_reading$"),
            ],
            ST_TRADITION: [
                CallbackQueryHandler(cb_tradition, pattern="^trad:"),
                CallbackQueryHandler(cb_back_to_spread, pattern="^nav:back_to_spread$"),
            ],
            ST_REVERSALS: [
                CallbackQueryHandler(cb_reversals, pattern="^rev:"),
                CallbackQueryHandler(cb_back_to_tradition, pattern="^nav:back_to_tradition$"),
            ],
            ST_NIYAT: [
                CallbackQueryHandler(cb_niyat_skip, pattern="^niyat:skip$"),
                CallbackQueryHandler(cb_back_to_reversals, pattern="^nav:back_to_reversals$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_niyat_text),
            ],
            ST_CONFIRM: [
                CallbackQueryHandler(cb_confirm_draw, pattern="^confirm:draw$"),
                CallbackQueryHandler(cb_back_to_reversals, pattern="^nav:back_to_reversals$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(cb_home, pattern="^menu:home$"),
        ],
        name="reading_conversation",
        allow_reentry=True,
        persistent=False,
    )
    application.add_handler(reading_conv)

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("rooz", cmd_rooz))
    application.add_handler(CommandHandler("gallery", cmd_gallery))
    application.add_handler(CommandHandler("cards", cmd_gallery))
    application.add_handler(CommandHandler("cancel", cmd_cancel))

    application.add_handler(CallbackQueryHandler(cmd_help, pattern="^menu:help$"))
    application.add_handler(CallbackQueryHandler(cmd_rooz, pattern="^menu:rooz$"))
    application.add_handler(CallbackQueryHandler(cb_home, pattern="^menu:home$"))
    application.add_handler(CallbackQueryHandler(cb_gallery_page, pattern="^gal:page:"))
    application.add_handler(CallbackQueryHandler(cb_gallery_card, pattern="^gal:card:"))
    application.add_handler(CallbackQueryHandler(cb_noop, pattern="^noop$"))

    # Lower-priority catch-all: anything not consumed above (stray text,
    # legacy reply-keyboard button presses from earlier bot versions, etc.)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, cb_unknown_text), group=1
    )

    application.add_error_handler(on_error)
    return application


def main() -> int:
    try:
        cfg = load_config()
    except RuntimeError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 1

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=getattr(logging, cfg.log_level, logging.INFO),
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext.Application").setLevel(logging.INFO)

    try:
        cards = cards_repo.all_cards()
    except Exception as exc:
        logger.error(
            "خطا در بارگذاری دیتاست کارت‌ها (cards.json). "
            "اول tarot/scripts/fetch_cards.py را اجرا کنید. جزئیات: %s",
            exc,
        )
        return 1
    logger.info("Loaded %d cards.", len(cards))

    if not cfg.hf_token:
        logger.warning("HF_TOKEN تنظیم نشده — همه‌ی خوانش‌ها به‌جای مدل زبانی از fallback دیتاست استفاده می‌کنند.")

    application = build_application(cfg)

    if cfg.run_mode == "polling":
        logger.info("Starting in POLLING mode.")
        application.run_polling(drop_pending_updates=cfg.drop_pending_updates)
    else:
        logger.info(
            "Starting in WEBHOOK mode: public_url=%s internal=%s:%s path=%s",
            cfg.webhook_url,
            cfg.webhook_listen,
            cfg.webhook_port,
            cfg.webhook_path,
        )
        application.run_webhook(
            listen=cfg.webhook_listen,
            port=cfg.webhook_port,
            url_path=cfg.webhook_path,
            webhook_url=cfg.webhook_url,
            secret_token=cfg.webhook_secret,
            drop_pending_updates=cfg.drop_pending_updates,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
