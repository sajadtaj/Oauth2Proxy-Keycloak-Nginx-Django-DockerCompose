
## پرامپت فاز 1 — اسکلت پایه (Django + Nginx بدون Auth)

**Prompt (کپی کن و در پیام بعدی بده):**

```
[PHASE-1 REQUEST]

هدف فاز:
- راه‌اندازی اسکلت پروژه با Docker Compose شامل Nginx (Reverse Proxy) و Django (Hello World) بدون احراز هویت.
- تعریف دو مسیر /public و /private (فعلاً هر دو آزاد).
- آماده‌سازی برای الحاق OAuth2-Proxy و Keycloak در فاز بعد.

ساخت مسیر با دستور در ترمینال:
- لطفاً دستورات bash برای ایجاد ساختار زیر را تولید کن (بدون اجرای کد، فقط دستورها را بده):
  - ریشه پروژه: ./auth-stack
  - زیرشاخه‌ها و فایل‌ها:
    auth-stack/
    ├── docker-compose.yml
    ├── nginx/
    │   └── nginx.conf
    └── app/

فایل‌ها و مسیرهایی که باید در این فاز تکمیل شوند:
- auth-stack/docker-compose.yml : تعریف سرویس‌های nginx و django (مینیمال، بدون auth).
- auth-stack/nginx/nginx.conf : پیکربندی reverse proxy به django و دو location برای /public و /private (فعلاً باز).
- auth-stack/app/ : اسکلت Django با یک view یا دو route ساده که "Hello Public" و "Hello Private" را برگردانند.

نقش هر فایل در توسعه:
- docker-compose.yml : هماهنگ‌کننده سرویس‌ها و شبکه/ولوم‌های پایه.
- nginx.conf : درگاه ورودی و مسیریابی به Django؛ پایه‌گذاری الگوی /public و /private.
- app/ : منطق بسیار ساده اپلیکیشن (Hello World) و آماده برای دریافت هدرها در فازهای بعد.

روش تست (High-Level):
- پس از بالا آمدن سرویس‌ها، فراخوانی GET /public و /private هر دو 200 OK برگردانند و متن مناسب نمایش دهند.
- بررسی لاگ nginx و django برای صحت روتینگ.

الزامات اجرایی:
- خروجی باید Markdown UTF-8 باشد.
- در ابتدای پاسخ یک دیاگرام Mermaid از معماری همین فاز بده (Nginx → Django بدون Auth).
- سپس دستورات bash ایجاد مسیرها/فایل‌ها را بده.
- سپس فایل‌ها را با توضیح نقش‌شان لیست کن.
- در انتها «چک‌لیست پذیرش فاز» کوتاه بده.

استانداردها و اصول (Clean Architecture + DDD + SOLID + Pythonic):
- جداسازی concerns: gateway (nginx) از app (django).
- حداقل وابستگی و کانفیگ شفاف (.env در صورت نیاز).
- نام‌گذاری واضح سرویس‌ها و شبکه‌ها.
- خوانایی، ایزومافیک بودن ساختار فایل‌ها، و امکان توسعه در فاز بعد.
```

---

## پرامپت فاز 2 — افزودن Keycloak و OAuth2‑Proxy و محافظت از /private

**Prompt (کپی کن و در پیام بعدی بده):**

```
[PHASE-2 REQUEST]

هدف فاز:
- افزودن Keycloak (start-dev) و OAuth2-Proxy.
- محافظت از مسیر /private با الگوی Nginx auth_request → OAuth2-Proxy → Keycloak (OIDC).
- حفظ /public به‌صورت بدون لاگین.

ساخت مسیر با دستور در ترمینال:
- لطفاً دستورات bash برای ایجاد/تکمیل ساختار زیر را تولید کن:
  auth-stack/
  ├── docker-compose.yml          (به‌روزرسانی برای افزودن سرویس‌های keycloak و oauth2-proxy)
  ├── nginx/
  │   └── nginx.conf              (افزودن بلوک‌های /oauth2/ و location = /oauth2/auth + auth_request)
  ├── oauth2-proxy/
  │   └── oauth2-proxy.cfg        (provider=keycloak-oidc, issuer, client-id/secret, redirect-url, set-xauthrequest)
  ├── keycloak/
  │   └── realms/
  │       └── demo-realm.json     (Realm نمونه برای import با client: oauth2-proxy)
  └── app/                        (بدون تغییر ساختاری، فقط اشاره)

فایل‌ها و مسیرهایی که باید در این فاز تکمیل شوند:
- docker-compose.yml : اضافه شدن دو سرویس جدید و شبکه‌/alias لازم برای سازگاری نام دامنه (مثلاً nip.io).
- nginx/nginx.conf : auth_request به /oauth2/auth، بلوک‌های proxy_pass به oauth2-proxy، و مسیرهای /public و /private.
- oauth2-proxy/oauth2-proxy.cfg : کانفیگ OIDC (issuer، client-id، client-secret، redirect-uri، cookie گزینه‌ها).
- keycloak/realms/demo-realm.json : realm از پیش‌تعریف‌شده با client مناسب (redirect به /oauth2/callback).

نقش هر فایل در توسعه:
- docker-compose.yml : ارکستراسیون چهار سرویس (nginx, django, oauth2-proxy, keycloak).
- nginx.conf : نقطه اعمال سیاست دسترسی؛ /private فقط در صورت 202 از /oauth2/auth عبور می‌کند.
- oauth2-proxy.cfg : منطق OIDC و نگهداری نشست (cookies/sessions) و ارسال هدرها به nginx.
- demo-realm.json : خودکارسازی راه‌اندازی Keycloak در dev.

روش تست (High-Level):
- GET /public → 200 OK بدون لاگین.
- GET /private → هدایت به صفحه لاگین Keycloak؛ پس از ورود، 200 OK.
- بررسی پاسخ /oauth2/auth (202 هنگام احراز هویت معتبر، 401 در غیر این‌صورت).

الزامات اجرایی:
- خروجی باید Markdown UTF-8 باشد.
- ابتدا دیاگرام Mermaid برای فاز 2 بده (Nginx + auth_request → OAuth2-Proxy ↔ Keycloak → Django).
- سپس دستورات bash ایجاد/به‌روزرسانی مسیرها/فایل‌ها را بده.
- سپس پیکربندی‌های نمونه مینیمال برای oauth2-proxy.cfg و توضیح فیلدهای مهم.
- در پایان چک‌لیست پذیرش فاز (public آزاد، private محافظت‌شده، جریان لاگین کار می‌کند).

استانداردها و اصول (Clean Architecture + DDD + SOLID + Pythonic):
- Separation of concerns: IdP و Proxy و Gateway از App جدا.
- حداقل تنظیمات لازم و استفاده از defaultهای امن (مثلاً cookie secure در محیط‌های TLS).
- تنظیم نام‌ها/labels شفاف و قابل‌توسعه.
- مستندسازی مفاهیم OIDC در حد مینیمال اما دقیق.
```

---

## پرامپت فاز 3 — عبور هدرهای هویتی و نمایش نام کاربر در Django

**Prompt (کپی کن و در پیام بعدی بده):**

```
[PHASE-3 REQUEST]

هدف فاز:
- عبور هدرهای هویتی از Nginx به Django برای مسیر /private.
- نمایش نام کاربر (و در صورت امکان ایمیل) در پاسخ Django: "Hello Private, <user>".

ساخت مسیر با دستور در ترمینال:
- مسیر جدید لازم نیست؛ فقط به‌روزرسانی فایل‌های موجود:
  - nginx/nginx.conf : اطمینان از auth_request_set و proxy_set_header برای X-User, X-Email.
  - app/ : به‌روزرسانی view مربوط به /private برای خواندن هدرها.

فایل‌ها و مسیرهایی که باید در این فاز تکمیل شوند:
- nginx/nginx.conf : افزودن یا تصحیح directiveهای عبور هدرها (X-Auth-Request-User → X-User و مشابه آن برای ایمیل).
- app/ (views.py/urls.py/templates) : نمایش اطلاعات هویتیِ ارسال‌شده از Nginx.

نقش هر فایل در توسعه:
- nginx.conf : پل ارتباطی نهایی برای انتقال claims به اپ.
- Django app : ارائه پاسخ شخصی‌سازی‌شده به کاربر لاگین کرده.

روش تست (High-Level):
- ورود با Keycloak و فراخوانی /private → متن شامل نام کاربر (و ایمیل اگر موجود) چاپ شود.
- فراخوانی /public بدون کوکی → همچنان آزاد.

الزامات اجرایی:
- خروجی باید Markdown UTF-8 باشد.
- ابتدا sequence diagram Mermaid از جریان هدرها بده (Nginx ↔ OAuth2-Proxy ↔ Keycloak → Django).
- سپس بخش‌های تغییر لازم در nginx.conf و نمونه کد view Django را (مینیمال) ارائه کن.
- در پایان چک‌لیست پذیرش فاز: وجود هدرها، لاگ‌ها، و نمایش کاربر.

استانداردها و اصول (Clean Architecture + DDD + SOLID + Pythonic):
- حداقل کد در اپ؛ منطق احراز در لبه.
- naming شفاف برای هدرها، عدم نشت اطلاعات غیرضروری.
- تست‌پذیری (ساده‌سازی view و قابلیت mock هدرها).
```

---

## پرامپت فاز 4 — سخت‌سازی و بهبودهای اختیاری (TLS, Redis Session, RBAC)

**Prompt (کپی کن و در پیام بعدی بده):**

```
[PHASE-4 REQUEST]

هدف فاز:
- سخت‌سازی و بهبودهای اختیاری: فعال‌سازی TLS، استفاده از Redis برای session store در OAuth2-Proxy (در صورت بزرگی توکن‌ها)، و RBAC (role/group-based access) از طریق Keycloak Mappers.
- حفظ سادگی اجرا در Docker Compose (dev-friendly)، اما با الگوی نزدیک به production.

ساخت مسیر با دستور در ترمینال:
- در صورت نیاز، ایجاد مسیرهای جدید:
  - auth-stack/redis/ (در صورت افزودن Redis)
  - auth-stack/nginx/certs/ (Self-signed برای لوکال) یا کانفیگ Let’s Encrypt در محیط واقعی.
  - به‌روزرسانی docker-compose.yml برای سرویس redis (اختیاری) و کانفیگ TLS در nginx.

فایل‌ها و مسیرهایی که باید در این فاز تکمیل شوند:
- docker-compose.yml : افزودن سرویس redis (اختیاری) و ولوم‌های certs برای nginx.
- nginx/nginx.conf : پیکربندی TLS (server { listen 443 ssl; ... }) و ریدایرکت 80→443.
- oauth2-proxy/oauth2-proxy.cfg : گزینه‌های session store (redis)، cookie_secure در TLS، pass-access-token (در صورت نیاز).
- keycloak/realms/demo-realm.json : افزودن/اصلاح Mappers (roles/groups) و محدودسازی دسترسی در oauth2-proxy (allowed_groups/allowed_roles).

نقش هر فایل در توسعه:
- docker-compose.yml : فراهم‌سازی زیرساخت اجرایی برای امنیت (TLS/Redis).
- nginx.conf : اجرای TLS termination و سیاست‌های امنیتی پایه (HSTS در صورت نیاز).
- oauth2-proxy.cfg : پایداری نشست‌ها و کنترل دقیق دسترسی.
- realm.json : اطمینان از claims مناسب برای RBAC.

روش تست (High-Level):
- دسترسی HTTPS به /public و /private (Self-signed در dev).
- ورود و عبور از /private با نقش مجاز → 200؛ کاربر بدون نقش → 403/401.
- بررسی اندازه کوکی‌ها و صحت ذخیره سشن در Redis (در صورت فعال‌سازی).

الزامات اجرایی:
- خروجی باید Markdown UTF-8 باشد.
- ابتدا دیاگرام Mermaid از معماری نهایی با TLS/Redis/RBAC بده.
- سپس دستورات bash ایجاد مسیرها/فایل‌های جدید و نمونه پیکربندی‌ها را ارائه کن.
- در پایان چک‌لیست پذیرش فاز: HTTPS کار می‌کند، RBAC اعمال شده، سشن پایدار، لاگ‌ها تمیز.

استانداردها و اصول (Clean Architecture + DDD + SOLID + Pythonic):
- اصل least privilege و کاهش سطح حمله (TLS, HSTS, secure cookies).
- حداقل پیچیدگی لازم؛ گزینه‌ها اختیاری و ماژولار بمانند.
- مستندسازی شفاف برای انتقال به محیط‌های بالاتر (staging/production).
```

---

