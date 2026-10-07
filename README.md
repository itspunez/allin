# Proxy Aggregator — Final MVP

این پروژه منابع subscription عمومی/شخصی را جمع‌آوری می‌کند، محتوا را decode/parse می‌کند، کانفیگ‌ها را normalize و dedupe می‌کند، برای source و config امتیاز freshness/reliability می‌سازد و خروجی‌های آماده مصرف تولید می‌کند.

## Pipeline

sources.yml
→ fetch
→ decode
→ parse
→ normalize
→ SQLite
→ score
→ export

این نسخه روی availability/freshness و کیفیت داده تمرکز دارد و endpointهای شخص ثالث را active-probe یا port-scan نمی‌کند.

## Sources included

۱۰ ورودی‌ای که داده شد در `sources.yml` قرار گرفته‌اند. مورد تکراری Mahdi0024 فقط یک بار ثبت شده است.

## اجرا روی سیستم شخصی

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m src.main
```

خروجی‌ها در `output/` ساخته می‌شوند.

## خروجی‌ها

- `all.txt`
- `top100.txt`
- `fast.txt` — در این MVP «fast» به معنی score-based است، نه latency واقعی.
- `vless.txt`
- `vmess.txt`
- `trojan.txt`
- `ss.txt`
- `configs.json`
- `sources.json`
- `subscription.b64`

`subscription.b64` یک feed Base64 از کانفیگ‌های deduplicated است.

## GitHub Actions

Workflow هر ساعت اجرا می‌شود و با `workflow_dispatch` هم دستی قابل اجراست.

Workflow فقط `contents: write` می‌گیرد تا output/state را commit کند. GitHub مستند کرده که permissionها را می‌توان در خود workflow محدود کرد و `contents: write` برای نوشتن محتویات repository استفاده می‌شود.

اگر repository شما private نیست، هیچ URL خصوصی را داخل `sources.yml` commit نکنید. برای URL خصوصی از GitHub Secret استفاده کنید.

## Secret source

برای source خصوصی می‌توانید به جای URL مستقیم از این ساختار استفاده کنید:

```yaml
- id: private-source
  name: Private source
  url_env: PRIVATE_SOURCE_URL
  enabled: true
  weight: 100
  format: auto
  tags: [private]
```

سپس در GitHub:
Settings → Secrets and variables → Actions → New repository secret

نام:
`PRIVATE_SOURCE_URL`

مقدار:
URL subscription

## Cloudflare Worker

پوشه `worker/` یک cache/API ساده برای فایل‌های خروجی است.

متغیر محیطی:
`ORIGIN=https://YOUR-GITHUB-PAGES-ORIGIN`

این Worker خودش collector نیست؛ فقط output را cache/proxy می‌کند.

## نکته

این پروژه فقط داده‌ای را که source منتشر کرده دریافت و پردازش می‌کند. تست latency یا اتصال واقعی به هزاران endpoint در این MVP وجود ندارد.
