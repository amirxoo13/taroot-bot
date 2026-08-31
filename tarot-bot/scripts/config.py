#!/usr/bin/env python3
"""Central configuration for tarot-bot, loaded entirely from environment
variables (see ../assets/env.example). Nothing secret is hard-coded here.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name).lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    telegram_token: str
    hf_token: str
    hf_model: str
    assets_dir: Path

    run_mode: str  # "webhook" | "polling"
    webhook_domain: str
    webhook_public_port: int
    webhook_path: str
    webhook_listen: str
    webhook_port: int
    webhook_secret: str
    drop_pending_updates: bool

    gallery_page_size: int
    log_level: str

    @property
    def webhook_url(self) -> str:
        domain = self.webhook_domain.rstrip("/")
        path = self.webhook_path if self.webhook_path.startswith("/") else f"/{self.webhook_path}"
        # Telegram only accepts webhook URLs on ports 443, 80, 88 or 8443.
        # Default is 8443 specifically so we never have to touch whatever
        # else (e.g. Xray/3X-UI) already owns port 443 on this host.
        if self.webhook_public_port == 443:
            return f"https://{domain}{path}"
        return f"https://{domain}:{self.webhook_public_port}{path}"


def load_config() -> Config:
    token = _env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN تنظیم نشده. آن را در فایل .env قرار دهید."
        )

    hf_token = _env("HF_TOKEN")
    hf_model = _env("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct:fastest")

    # tarot-bot/scripts/config.py -> parents[1] == tarot-bot/ -> assets/
    assets_dir = Path(__file__).resolve().parents[1] / "assets"

    run_mode = _env("RUN_MODE", "webhook").lower()
    if run_mode not in ("webhook", "polling"):
        run_mode = "webhook"

    webhook_domain = _env("WEBHOOK_DOMAIN")
    webhook_public_port = _env_int("WEBHOOK_PUBLIC_PORT", 8443)
    if webhook_public_port not in (443, 80, 88, 8443):
        raise RuntimeError(
            "WEBHOOK_PUBLIC_PORT باید یکی از مقادیر مجاز تلگرام باشد: 443, 80, 88, 8443 "
            f"(مقدار فعلی: {webhook_public_port})"
        )
    # Prefer an explicit, human-chosen path so it can be matched exactly in
    # the reverse-proxy (Nginx) config. Fall back to a token-derived path
    # only for quick local testing.
    webhook_path = _env("WEBHOOK_PATH") or (
        "/webhook/" + hashlib.sha256(token.encode()).hexdigest()[:24]
    )
    webhook_listen = _env("WEBHOOK_LISTEN", "127.0.0.1")
    webhook_port = _env_int("WEBHOOK_PORT", 8081)
    webhook_secret = _env("WEBHOOK_SECRET") or hashlib.sha256(
        (token + ":secret").encode()
    ).hexdigest()[:32]
    drop_pending = _env_bool("DROP_PENDING_UPDATES", False)

    if run_mode == "webhook" and not webhook_domain:
        raise RuntimeError(
            "RUN_MODE=webhook است ولی WEBHOOK_DOMAIN خالی است. "
            "یا دامنه را ست کنید یا RUN_MODE=polling بگذارید."
        )

    gallery_page_size = _env_int("GALLERY_PAGE_SIZE", 10)
    log_level = _env("LOG_LEVEL", "INFO").upper()

    return Config(
        telegram_token=token,
        hf_token=hf_token,
        hf_model=hf_model,
        assets_dir=assets_dir,
        run_mode=run_mode,
        webhook_domain=webhook_domain,
        webhook_public_port=webhook_public_port,
        webhook_path=webhook_path,
        webhook_listen=webhook_listen,
        webhook_port=webhook_port,
        webhook_secret=webhook_secret,
        drop_pending_updates=drop_pending,
        gallery_page_size=gallery_page_size,
        log_level=log_level,
    )
