# taroot-bot

ربات تلگرام فارسی فال تاروت — کاملاً با دکمه‌های شیشه‌ای، همراه با عکس هر
کارت + تفسیر متنی، و پروتکل مهارت `tarot` که معنی کارت‌ها را تعیین می‌کند.

توکن، رمز سرور و فایل `.env` داخل این ریپو نیستند.

## امکانات ربات

- ۱۲ اسپرد مستند (یک‌کارتی تا سالانه) با انتخاب مرحله‌ای از طریق دکمه
- ۳ سنت: رایدر-وایت، مارسی، فقط آرکانای بزرگ — با/بدون کارت معکوس
- ثبت نیت اختیاری قبل از کشیدن کارت
- ارسال عکس هر کارت + کپشن (جایگاه، نام فارسی/انگلیسی، جهت) به‌صورت آلبوم
- تفسیر روایی فارسی از طریق Hugging Face؛ اگر مدل در دسترس نبود، به‌صورت
  خودکار به یک تفسیر متنی مبتنی بر دیتاست (بدون مدل زبانی) سوییچ می‌کند
- `/rooz` — کارت روزانه (برای هر کاربر در هر روز ثابت)
- گالری کامل ۷۸ کارت با ورق‌زدن و نمایش جزئیات هر کارت
- اجرا به‌صورت Webhook (پشت Nginx) یا Polling (برای تست سریع محلی)

## ساختار

```
tarot/                 داده کارت و اسپرد (مهارت tarot)
  scripts/
    fetch_cards.py      دانلود دیتاست ۷۸ کارتی (cards.json)
    draw.py              ابزار CLI تست، مستقل از ربات
tarot-bot/              ربات تلگرام (مهارت tarot-bot)
  scripts/
    bot.py               نقطه‌ی ورود ربات — اجرا می‌شود
    engine.py             کشیدن اسپرد + ساخت پرامپت مدل + fallback متنی
    hf_client.py           کلاینت Hugging Face Inference Providers
    cards_repo.py           کش دیتاست کارت + مسیر عکس هر کارت
    catalog.py               برچسب فارسی اسپردها/سنت‌ها/خانواده‌ها
    keyboards.py              همه‌ی صفحه‌کلیدهای شیشه‌ای
    texts.py                   متن‌های فارسی رابط کاربری
    config.py                   خواندن و اعتبارسنجی متغیرهای محیطی
    utils.py                     تقسیم پیام طولانی، seed روزانه، ...
    download_cards.py             دانلود عکس اسکن ۱۹۰۹ کارت‌ها
deploy/
  tarot-bot.service      واحد systemd
  nginx-tarot-bot.conf    نمونه‌ی تنظیمات Nginx برای webhook
```

## نصب و اجرا

### ۱) نصب وابستگی‌ها

```bash
git clone https://github.com/amirxoo13/taroot-bot.git
cd taroot-bot
python3 -m venv .venv
.venv/bin/pip install -r tarot-bot/assets/requirements.txt
```

### ۲) تنظیم `.env`

```bash
cp tarot-bot/assets/env.example tarot-bot/.env
chmod 600 tarot-bot/.env
```

مقادیر زیر را در `tarot-bot/.env` پر کنید — **توکن‌ها را هرگز در چت،
گیت یا هیچ فایل عمومی دیگری قرار ندهید**، فقط مستقیم روی سرور در همین
فایل:

- `TELEGRAM_BOT_TOKEN` — از BotFather
- `HF_TOKEN` — از Hugging Face (اختیاری؛ بدون آن ربات کار می‌کند ولی
  تفسیرها فقط از دیتاست ساخته می‌شن، نه مدل زبانی)
- `WEBHOOK_DOMAIN=amirxo.com`
- `WEBHOOK_PATH=/webhook/...` — یک مسیر تصادفی و منحصربه‌فرد بسازید و
  همین مقدار را عیناً در `deploy/nginx-tarot-bot.conf` هم بگذارید

### ۳) دانلود داده و عکس کارت‌ها (هر دو لازم‌اند)

```bash
export TAROT_SKILL_DIR=$PWD/tarot
python3 tarot/scripts/fetch_cards.py        # دیتاست ۷۸ کارتی (ضروری)
python3 tarot-bot/scripts/download_cards.py # عکس‌های اسکن ۱۹۰۹ (بدونش ربات فقط متنی جواب می‌ده)
```

### ۴) اجرای Webhook پشت Nginx (روش توصیه‌شده برای production)

روی سرور `155.103.71.163` با دامنه‌ی `amirxo.com`. وب‌هوک عمداً روی
پورت **۸۴۴۳** (یکی از پورت‌های مجاز خود تلگرام) اجرا می‌شه، نه ۴۴۳ —
یعنی هیچ تداخلی با هر برنامه‌ی دیگه‌ای (مثل Xray/3X-UI) که روی ۴۴۳ هست
نداره و کاری هم بهش نداریم.

1. گواهی SSL بگیرید: `certbot certonly --nginx -d amirxo.com`
   (این فقط از پورت ۸۰ برای تأیید دامنه استفاده می‌کنه، ربطی به ۴۴۳ یا
   ۸۴۴۳ نداره)
2. مطمئن بشید پورت ۸۴۴۳ در فایروال سرور باز باشه (`ufw allow 8443/tcp`
   یا معادلش)
3. `deploy/nginx-tarot-bot.conf` را کپی کنید، `WEBHOOK_PATH` را با مقدار
   `.env` یکسان کنید، فعالش کنید و Nginx را reload کنید
4. `deploy/tarot-bot.service` را در `/etc/systemd/system/` کپی کنید
   (مسیرها را با محل واقعی ریپو روی سرور تطبیق دهید)، سپس:

```bash
systemctl daemon-reload
systemctl enable --now tarot-bot
journalctl -u tarot-bot -f   # لاگ زنده
```

با اجرا شدن، `bot.py` خودش `setWebhook` را به آدرس
`https://amirxo.com:8443${WEBHOOK_PATH}` صدا می‌زند — نیازی به کار دستی
دیگه‌ای نیست.

### دیپلوی خودکار (GitHub Actions)

با هر push به شاخه‌ی اصلی، `.github/workflows/deploy.yml` از طریق یک
کاربر محدود (`deploy`، نه root) با کلید SSH به سرور وصل می‌شه، کد را
sync می‌کنه، `.env` را از GitHub Secret می‌نویسه و سرویس را ری‌استارت
می‌کنه. جزئیات و پیش‌نیازها در همان فایل workflow کامنت شده.

### تست سریع محلی (Polling)

برای تست بدون دامنه/Nginx، در `.env`: `RUN_MODE=polling` و
`.venv/bin/python tarot-bot/scripts/bot.py` را مستقیم اجرا کنید.

---

Card images are public-domain 1909 Smith scans and are downloaded by
script, not stored in git.
