# Proxy Aggregator v2 — Auto Discovery

این نسخه علاوه بر ۱۰ source دستی، روزانه sourceهای عمومی جدید را از GitHub کشف می‌کند.

## چرخه خودکار
- Discovery: روزانه
- Collection: هر ساعت
- خروجی‌ها: بعد از هر collection بازسازی می‌شوند
- Dependabot: هفتگی dependencyها و GitHub Actions را بررسی می‌کند

Discovery فقط public GitHub metadata/README و لینک‌های subscription منتشرشده را می‌خواند؛ active probing یا port scanning انجام نمی‌دهد.

## راه‌اندازی
1. محتویات این ZIP را جایگزین نسخه قبلی در root همان repository کن.
2. Commit و Push کن.
3. Actions → **Discover public sources** → Run workflow را یک‌بار اجرا کن.
4. سپس **Collect subscriptions** را Run کن.
5. از این به بعد هر دو زمان‌بندی خودکار هستند.

## خروجی مهم
`output/subscription.b64`

همچنین:
`all.txt`, `top100.txt`, `vless.txt`, `vmess.txt`, `trojan.txt`, `ss.txt`

`fast.txt` فعلاً score-based است و latency واقعی نیست.

## Self-update
کد اصلی پروژه عمداً از اینترنت overwrite نمی‌شود. registry source و خروجی‌ها خودکار به‌روزرسانی می‌شوند و Dependabot برای update وابستگی‌ها Pull Request می‌سازد.
