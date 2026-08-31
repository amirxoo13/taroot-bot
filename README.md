# taroot-bot

ربات تلگرام فال تاروت فارسی + داده و پروتکل مهارت `tarot`.

توکن، رمز سرور و فایل `.env` داخل این ریپو نیست.

## ساختار

```
tarot/           داده کارت و اسپرد
tarot-bot/       ربات تلگرام
```

## اجرا روی سرور

```bash
python3 -m venv .venv
.venv/bin/pip install -r tarot-bot/assets/requirements.txt
cp tarot-bot/assets/env.example tarot-bot/.env
# put tokens in .env
export TAROT_SKILL_DIR=$PWD/tarot
python3 tarot-bot/scripts/download_cards.py
.venv/bin/python tarot-bot/scripts/bot.py
```

Card images are public-domain 1909 Smith scans and are downloaded by script, not stored in git.
