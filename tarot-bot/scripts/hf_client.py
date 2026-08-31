#!/usr/bin/env python3
"""Chat completion via Hugging Face Inference Providers router."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROUTER = "https://router.huggingface.co/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct:fastest")


def complete(
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = 1600,
    temperature: float = 0.55,
    timeout: int = 90,
) -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError("HF_TOKEN is empty")
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        ROUTER,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HF HTTP {exc.code}: {detail}") from exc
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected HF payload: {body!r}"[:400]) from exc
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("empty model content")
    return text.strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ping", action="store_true")
    args = p.parse_args()
    if args.ping:
        msg = complete(
            [{"role": "user", "content": "پاسخ بده فقط: باشه"}],
            max_tokens=16,
        )
        print(msg)
        return 0
    print("usage: HF_TOKEN=... python3 scripts/hf_client.py --ping", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
