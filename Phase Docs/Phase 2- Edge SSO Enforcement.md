<div dir="rtl">

# فاز ۲ — «Edge SSO Enforcement»

## 0) نام فاز

**Edge SSO Enforcement**
(اجرای احراز هویت تک‌ورودی در لبه‌ی معماری با Nginx + OAuth2-Proxy + Keycloak برای محافظت از `/private`.)

---

## 1) هدف

### 1.1 تعریف عمومی (برای درک سریع)

در این فاز «درِ ورودیِ ساختمان» (Nginx) فقط به کسانی اجازه عبور از راهروی خاص (`/private`) را می‌دهد که کارت عبور معتبر داشته باشند. اعتبار کارت را «مسئول احراز هویت» (OAuth2-Proxy) از «دفتر هویت» (Keycloak) می‌پرسد. اگر کارت معتبر بود، اجازه‌ی ورود داده می‌شود؛ اگر نبود، به اتاق ثبت‌نام/ورود هدایت می‌شوید. راهروی عمومی (`/public`) همچنان آزاد است.

### 1.2 تعریف تخصصی (Developer-centric)

الگوی **Nginx `auth_request`** پیاده‌سازی می‌شود:

* برای هر درخواست به `/private`، Nginx یک sub-request به `oauth2-proxy` در مسیر `/oauth2/auth` می‌فرستد.
* اگر پاسخ **202** باشد، درخواست اصلی به Django عبور می‌کند (و هدرهای هویتی مثل `X-User` تنظیم می‌شود).
* اگر **401** باشد، Nginx به `/oauth2/start` ری‌دایرکت می‌کند تا جریان OIDC **Authorization Code** با Keycloak آغاز شود.
* `/public` مستقیم به Django می‌رود (بدون احراز هویت).

### 1.3 تحلیل سیستم‌دیزاین (چرایی/چیستی)

**چرایی**

* جدا کردن Concern احراز هویت از اپلیکیشن: Django ساده می‌ماند؛ امنیت در لایه‌ی Edge اجرا می‌شود.
* مقیاس‌پذیری: افزودن سرویس‌های جدید پشت Nginx بدون افزودن کد Auth در تک‌تک سرویس‌ها.
* استاندارد باز: OIDC با IdP قدرتمندی مثل Keycloak.

**چیستی**

* یک **Gateway** (Nginx) با upstreamهای `web:8000` و `oauth2-proxy:4180`
* یک **Auth Proxy** (OAuth2-Proxy) با Provider `keycloak-oidc`
* یک **IdP** (Keycloak) در حالت dev با Realm ایمپورت‌شده
* قرارداد: `/oauth2/*` برای تبادلات Auth، `/private` محافظت‌شده، `/public` آزاد.

### 1.4 تحلیل کسب‌وکار (چرایی/چیستی)

**چرایی**

* رعایت الزامات سازمانی (SSO، Audit، مدیریت متمرکز کاربران و نقش‌ها).
* کاهش زمان پیاده‌سازی: توسعه‌دهندگان اپ نیازی به درگیر شدن با پیچیدگی OIDC ندارند.

**چیستی**

* تحویل یک مسیر «واقعاً امن» و قابل‌نمایش به ذی‌نفعان (login → redirect back → access).
* مبنایی برای RBAC و سیاست‌های پیشرفته در فازهای بعدی، بدون تغییر در هسته‌ی اپ.

### 1.5 شکستن هدف به زیرهدف‌ها

1. افزودن سرویس‌های **Keycloak** و **OAuth2-Proxy** به Compose.
2. تنظیم **Realm/Client** (Redirect URI و Secret) در Keycloak.
3. پیکربندی **OAuth2-Proxy** (issuer, client, redirect, cookies, reverse-proxy).
4. پیکربندی **Nginx** با `auth_request` و error\_page 401 → `/oauth2/start`.
5. تست جریان کامل: `/public` آزاد، `/private` نیازمند لاگین و بازگشت موفق.

### 1.6 جایگاه و اهمیت در پروژه

فاز ۲ «لایه امنیت لبه» را برقرار می‌کند؛ سنگ‌بنای کل الگوی **Zero-Trust Edge** در پروژه. هر توسعه‌ی بعدی (RBAC، TLS، پاس‌دادن توکن‌ها) بر همین پایه سوار می‌شود.

### 1.7 دیاگرام معماری فاز ۲

```mermaid
flowchart LR
  U[Browser] --> N[Nginx (auth_request)]
  N -->|/public| D[Django]
  N -->|/private → /oauth2/auth| O[OAuth2-Proxy]
  O <-->|OIDC| K[Keycloak (Realm: demo)]
  O -->|202/401| N
  N -->|proxy + X-User/X-Email| D
```

---

## 2) عناصر فاز

### 2.1 لیست فایل‌ها/کلاس‌ها/توابع (ساختار درختی)

```text
auth-stack/
├── docker-compose.yml
├── nginx/
│   └── nginx.conf                # server{}, /oauth2/*, auth_request, proxy_pass
├── oauth2-proxy/
│   └── oauth2-proxy.cfg          # ENV-style configs (issuer, client, cookie, reverse-proxy)
└── keycloak/
    └── realms/
        └── demo-realm.json       # Realm import (client oauth2-proxy, demo user)
```

> در این فاز «کلاس» یا «دیتاکلاس» اپلیکیشن اضافه نمی‌کنیم؛ همه‌چیز در لایه‌ی Edge/Auth و کانفیگ است.

### 2.2 شرح عملکرد هر بخش

#### `docker-compose.yml`

* **هدف فایل**: ارکستراسیون چهار سرویس (nginx, web, oauth2-proxy, keycloak) و شبکه مشترک.
* **نقش در این فاز**: ایجاد dependency chain، اکسپوز پورت Keycloak برای لاگین، اتصال Nginx به upstreamها.
* **توابع/بخش‌های مؤثر**:

  * service `oauth2-proxy` با `env_file` → خواندن تنظیمات از `oauth2-proxy.cfg`
  * service `keycloak` با `start-dev --import-realm`
  * service `nginx` با mount `nginx.conf`
  * volumes و exposeها

#### `nginx/nginx.conf`

* **هدف فایل**: درگاه ورودی + سیاست دسترسی مسیرها.
* **نقش در این فاز**:

  * `/public` → آزاد
  * `/private` → `auth_request /oauth2/auth` → اگر 401 شد، `error_page 401 = /oauth2/start?rd=$request_uri`
  * عبور هدرهای هویتی (`X-User`, `X-Email`) پس از تأیید.
* **بخش‌های مهم**:

  * `upstream` برای `django_upstream` و `oauth2_upstream`
  * بلوک `location = /oauth2/auth` (internal)
  * بلوک `location /oauth2/` (proxy به oauth2-proxy)
  * `auth_request_set` و `proxy_set_header` برای هدرهای هویتی

#### `oauth2-proxy/oauth2-proxy.cfg`

* **هدف فایل**: پیکربندی Provider `keycloak-oidc` و رفتار نشست/کوکی.
* **نقش در این فاز**: نگهداری سشن کاربر، هندل کردن callback، set کردن هدرهای `X-Auth-Request-*`.
* **کلیدهای مهم**:

  * `OAUTH2_PROXY_OIDC_ISSUER_URL` (مثلاً `http://keycloak:8080/realms/demo`)
  * `OAUTH2_PROXY_CLIENT_ID/SECRET` (هم‌خوان با Realm)
  * `OAUTH2_PROXY_REDIRECT_URL` (مثلاً `http://app.127.0.0.1.nip.io:8080/oauth2/callback`)
  * `OAUTH2_PROXY_SET_XAUTHREQUEST=true`, `OAUTH2_PROXY_REVERSE_PROXY=true`
  * `OAUTH2_PROXY_COOKIE_SECRET` (۳۲ بایت base64url)

#### `keycloak/realms/demo-realm.json`

* **هدف فایل**: خودکارسازی Keycloak در dev.
* **نقش در این فاز**: Realm `demo` با Client `oauth2-proxy` (redirectURI صحیح) و یک کاربر تست (`demo/demo`).
* **بخش‌های مهم**:

  * `"clients"[].redirectUris` دقیقاً مطابق `REDIRECT_URL`
  * `"secret"` برای Client (همان در Proxy)
  * کاربر تست برای لاگین سریع

---

## 3) ارتباط و تعامل

### 3.1 تعامل در همین فاز/لایه (Edge/Auth)

* **Nginx ↔ OAuth2-Proxy**

  * `location = /oauth2/auth` برای sub-request (202/401)
  * `location /oauth2/` برای شروع جریان لاگین (`/oauth2/start`) و callback
* **OAuth2-Proxy ↔ Keycloak**

  * جریان **OIDC Authorization Code**: تبادل کد/توکن، اعتبارسنجی سشن
* **Nginx ↔ Django**

  * پس از **202**، هدرهای `X-User/X-Email` ست و به Django پاس می‌شوند
  * `/public` مستقیم به Django

### 3.2 تعامل با سایر فازها/لایه‌ها

* **با فاز ۱ (App/Gateway Bootstrap)**

  * از همان سرویس `web` و روت‌های `/public`, `/private` استفاده می‌شود؛ بدون تغییر کد اپ.
* **با فاز ۳ (Header Propagation در اپ)**

  * Django در `/private` هدرهای `X-User/X-Email` را می‌خواند و به کاربر نمایش می‌دهد (UI/Response شخصی‌سازی شده).
* **با فاز ۴ (TLS/Redis/RBAC)**

  * اضافه‌کردن TLS روی Nginx (کوکی Secure)،
  * اضافه‌کردن Redis به OAuth2-Proxy برای session store،
  * RBAC با Role/Group Claims در Keycloak و سیاست‌های `allowed_groups/roles` در Proxy.

---

### جمع‌بندی

**Edge SSO Enforcement** امنیت مسیر خصوصی را بدون دست‌کاری کد اپلیکیشن برقرار می‌کند. این فاز هم از نظر **سیستم‌دیزاین** (جداکردن concerns، مقیاس‌پذیری، سادگی دیباگ) و هم از نظر **کسب‌وکار** (یکپارچگی با SSO سازمانی، آماده برای RBAC) نقطه‌ی عطف پروژه است. با تکمیل آن، بلافاصله می‌توانیم وارد فاز ۳ شویم و هویت کاربر را در پاسخ Django نمایش دهیم.

# اجرای فاز ۲

```mermaid
flowchart LR
  U[Browser] --> N[Nginx]
  N -->|/public (no auth)| D[Django]
  N -->|/private → auth_request| O[OAuth2-Proxy]
  O <-->|OIDC| K[Keycloak (start-dev)]
  O -->|202/401| N
  N -->|X-User/X-Email| D
```

> الگوی `auth_request` باید با گزینه‌ی `reverse-proxy` در OAuth2-Proxy فعال باشد؛ `/oauth2/auth` فقط 202/401 برمی‌گرداند و Nginx بر اساس آن اجازه عبور می‌دهد. ([OAuth2 Proxy][1])
> Provider مناسب: **keycloak-oidc** با Issuer در Realm هدف. ([OAuth2 Proxy][2])
> ایمپورت Realm با `start-dev --import-realm`. ([Keycloak][3])

---

## 1) دستورات Bash (ساخت/تکمیل مسیرها و فایل‌ها)

از ریشه‌ی پروژه (`auth-stack/`):

```bash
# پوشه‌ها
mkdir -p oauth2-proxy keycloak/realms

# فایل‌های جدید
touch oauth2-proxy/oauth2-proxy.cfg
touch keycloak/realms/demo-realm.json

# نکته امنیتی: ساخت Cookie Secret 32-بایتی (base64-urlsafe)
python3 - <<'PY'
import secrets, base64
print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
PY
```

---

## 2) docker-compose.yml (به‌روزرسانی کامل)

> نسخه OAuth2-Proxy حداقل **v7.11+** (رفع باگ امنیتی اخیر). اینجا از **v7.12.0** استفاده می‌کنیم. ([NVD][4], [SOCRadar® Cyber Intelligence Inc.][5], [GitHub][6])
> Keycloak مطابق گاید رسمی: **26.3.3** و `start-dev`. ([Keycloak][7])

```yaml
version: "3.9"

services:
  web:
    build:
      context: ./app
    container_name: demo-django
    restart: unless-stopped
    env_file:
      - ./.env
    expose:
      - "8000"
    volumes:
      - ./app:/app:cached
      - static_data:/app/staticfiles

  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:v7.12.0
    container_name: demo-oauth2-proxy
    restart: unless-stopped
    env_file:
      - ./oauth2-proxy/oauth2-proxy.cfg
    depends_on:
      - keycloak
    expose:
      - "4180"

  keycloak:
    image: quay.io/keycloak/keycloak:26.3.3
    container_name: demo-keycloak
    command: ["start-dev", "--import-realm"]
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: "admin"
      KC_BOOTSTRAP_ADMIN_PASSWORD: "admin"
      KC_HOSTNAME: "auth.127.0.0.1.nip.io"
    volumes:
      - ./keycloak/realms:/opt/keycloak/data/import
    ports:
      - "8081:8080"   # http://auth.127.0.0.1.nip.io:8081
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    container_name: demo-nginx
    depends_on:
      - web
      - oauth2-proxy
    ports:
      - "8080:80"     # http://app.127.0.0.1.nip.io:8080
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_data:/var/www/static:ro

volumes:
  static_data:
```

---

## 3) nginx/nginx.conf (auth\_request + مسیرهای /oauth2/\*)

> پیکربندی مطابق راهنمای رسمی `auth_request` و ست‌کردن هدرها. ([OAuth2 Proxy][1], [Stack Overflow][8])

```nginx
user  nginx;
worker_processes  auto;

events { worker_connections 1024; }

http {
  sendfile on;
  include       mime.types;
  default_type  application/octet-stream;

  upstream django_upstream { server web:8000; keepalive 32; }
  upstream oauth2_upstream { server oauth2-proxy:4180; keepalive 32; }

  server {
    listen 80;
    server_name _;

    # مسیرهای OAuth2-Proxy
    location /oauth2/ {
      proxy_pass       http://oauth2_upstream;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $scheme;
    }

    # نقطه بررسی Auth برای Nginx (فقط 202/401)
    location = /oauth2/auth {
      internal;
      proxy_pass       http://oauth2_upstream/oauth2/auth;
      proxy_set_header X-Original-URL     $scheme://$http_host$request_uri;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Scheme           $scheme;
      proxy_pass_request_body off;
      proxy_set_header Content-Length "";
      # هدرهای خروجی از oauth2-proxy که می‌خواهیم استفاده کنیم
      add_header X-Auth-Request-User   $upstream_http_x_auth_request_user;
      add_header X-Auth-Request-Email  $upstream_http_x_auth_request_email;
    }

    # مسیر عمومی: آزاد
    location /public {
      proxy_pass       http://django_upstream;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $scheme;
    }

    # مسیر خصوصی: نیازمند احراز هویت
    location /private {
      auth_request /oauth2/auth;

      # اگر 401 شد، کاربر را به صفحه شروع لاگین بفرست
      error_page 401 = /oauth2/start?rd=$request_uri;

      # ست هدرهای هویتی به اپ
      auth_request_set $user  $upstream_http_x_auth_request_user;
      auth_request_set $email $upstream_http_x_auth_request_email;

      proxy_set_header X-User  $user;
      proxy_set_header X-Email $email;

      proxy_pass       http://django_upstream;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $scheme;
    }

    # سایر مسیرها → اپ
    location / {
      proxy_pass       http://django_upstream;
      proxy_set_header Host               $host;
      proxy_set_header X-Real-IP          $remote_addr;
      proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto  $scheme;
    }
  }
}
```

---

## 4) oauth2-proxy/oauth2-proxy.cfg (env-style)

> استفاده از ENVهای رسمی با پیشوند `OAUTH2_PROXY_...` (خوانده‌شده توسط خود کانتینر). ([OAuth2 Proxy][9])

```bash
python3 - <<'PY'
import secrets, base64
raw = secrets.token_bytes(32)           # 32 بایت واقعی
b64 = base64.urlsafe_b64encode(raw).decode().rstrip('\n')
print("PUT_THIS_IN_CONFIG=", b64)
print("DECODED_LEN=", len(base64.urlsafe_b64decode(b64)))
PY

```
> عدد بدست امده را در زیر وارد کنید :
> OAUTH2_PROXY_COOKIE_SECRET=CHANGE_ME_32BYTE_BASE64URL

```dotenv
# Provider & OIDC
OAUTH2_PROXY_PROVIDER=keycloak-oidc
OAUTH2_PROXY_OIDC_ISSUER_URL=http://keycloak:8080/realms/demo
OAUTH2_PROXY_CLIENT_ID=oauth2-proxy
OAUTH2_PROXY_CLIENT_SECRET=CHANGE_ME_CLIENT_SECRET

# App external URL for callback (Nginx public host)
OAUTH2_PROXY_REDIRECT_URL=http://app.127.0.0.1.nip.io:8080/oauth2/callback

# Server
OAUTH2_PROXY_HTTP_ADDRESS=0.0.0.0:4180
OAUTH2_PROXY_REVERSE_PROXY=true
OAUTH2_PROXY_SET_XAUTHREQUEST=true

# Sessions / Cookies
OAUTH2_PROXY_COOKIE_SECRET=CHANGE_ME_32BYTE_BASE64URL
OAUTH2_PROXY_COOKIE_NAME=_oauth2_proxy
OAUTH2_PROXY_COOKIE_SECURE=false   # در محیط TLS → true

# Policy (دموی ساده)
OAUTH2_PROXY_EMAIL_DOMAINS=*
OAUTH2_PROXY_SKIP_PROVIDER_BUTTON=true
```

> یادآوری: مقدار `CHANGE_ME_CLIENT_SECRET` همان Secret کلاینت در Realm است؛ `CHANGE_ME_32BYTE_BASE64URL` را با خروجی اسکریپت تولید کوکی جایگزین کن.

---

## 5) keycloak/realms/demo-realm.json (Realm مینیمال برای import)

> Client با `redirectUris` همانی که در تنظیمات OAuth2-Proxy گذاشته‌ایم. ([Keycloak][3])

```json
{
  "realm": "demo",
  "enabled": true,
  "clients": [
    {
      "clientId": "oauth2-proxy",
      "name": "OAuth2 Proxy",
      "protocol": "openid-connect",
      "publicClient": false,
      "secret": "CHANGE_ME_CLIENT_SECRET",
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "redirectUris": [
        "http://app.127.0.0.1.nip.io:8080/oauth2/callback"
      ],
      "webOrigins": ["*"],
      "attributes": {
        "post.logout.redirect.uris": "+"
      }
    }
  ],
  "users": [
    {
      "username": "demo",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Demo",
      "lastName": "User",
      "email": "demo@example.com",
      "credentials": [
        { "type": "password", "value": "demo", "temporary": false }
      ]
    }
  ]
}
```

> نکته این دو باید برابر باشند:
> `secret`=`OAUTH2_PROXY_CLIENT_SECRET`
+ OAUTH2_PROXY_CLIENT_SECRET --> /oauth2-proxy/oauth2-proxy.cfg 
+ secret  --> o keycloak/realms/demo-realm.json
---

## 6) اجرای تست (High-Level)

```bash
docker compose up -d --build

# 1) مسیر عمومی: بدون لاگین
curl -i http://app.127.0.0.1.nip.io:8080/public

# 2) مسیر خصوصی: باید ری‌دایرکت به لاگین Keycloak شود
# (در مرورگر بهتر تست می‌شود؛ با curl هم هدر Location را می‌بینی)
curl -i http://app.127.0.0.1.nip.io:8080/private

# لاگ‌ها برای عیب‌یابی:
docker compose logs -f oauth2-proxy
docker compose logs -f keycloak
docker compose logs -f nginx
```

**انتظار:**

* `/public` → 200 OK (بدون لاگین).
* `/private` → هدایت به Keycloak روی `http://auth.127.0.0.1.nip.io:8081`، ورود با `demo/demo`، سپس برگشت به `/private` و 200 با هدرهای `X-User`, `X-Email`.

---

## نکات و خطاهای رایج

* **invalid redirect URI**: مقدار `redirectUris` در Realm دقیقاً با `OAUTH2_PROXY_REDIRECT_URL` یکی باشد (پروتکل/هاست/پورت/مسیر). ([OAuth2 Proxy][2])
* **502 از Nginx**: سرویس/نام Upstream را بررسی کن (`oauth2-proxy:4180`, `web:8000`). ([GitHub][10])
* **عدم ست‌شدن هدرها**: `OAUTH2_PROXY_SET_XAUTHREQUEST=true` و بلوک `location = /oauth2/auth` با `add_header`ها درست باشد. ([OAuth2 Proxy][1], [Stack Overflow][8])
* **نسخه‌های وصله‌شده**: از **v7.11+** برای OAuth2-Proxy استفاده کن (CVE-2025-54576). ([NVD][4], [zeropath.com][11])

---

## چک‌لیست پذیرش فاز ۲

* [ ] `/public` آزاد (200 بدون لاگین).
* [ ] `/private` محافظت‌شده: ری‌دایرکت به Keycloak و بازگشت موفق بعد از لاگین.
* [ ] `X-User/X-Email` به Django پاس می‌شوند.
* [ ] لاگ‌های Nginx/OAuth2-Proxy/Keycloak بدون خطای حیاتی.

اگر موافقی، دستور بده تا وارد **فاز ۳** شویم (عبور هدرها در Django و نمایش نام/ایمیل کاربر در پاسخ).

[1]: https://oauth2-proxy.github.io/oauth2-proxy/configuration/integration/?utm_source=chatgpt.com "Integration | OAuth2 Proxy - GitHub Pages"
[2]: https://oauth2-proxy.github.io/oauth2-proxy/configuration/providers/keycloak_oidc/?utm_source=chatgpt.com "Keycloak OIDC | OAuth2 Proxy - GitHub Pages"
[3]: https://www.keycloak.org/server/importExport?utm_source=chatgpt.com "Importing and exporting realms"
[4]: https://nvd.nist.gov/vuln/detail/CVE-2025-54576?utm_source=chatgpt.com "CVE-2025-54576 Detail - NVD"
[5]: https://socradar.io/oauth2-proxy-cve-2025-54576-bypass-authentication/?utm_source=chatgpt.com "Critical OAuth2-Proxy Vulnerability (CVE-2025-54576) Lets ..."
[6]: https://github.com/oauth2-proxy/oauth2-proxy/releases?utm_source=chatgpt.com "Releases · oauth2-proxy/oauth2-proxy"
[7]: https://www.keycloak.org/getting-started/getting-started-docker?utm_source=chatgpt.com "Docker"
[8]: https://stackoverflow.com/questions/19366215/setting-headers-with-nginx-auth-request-and-oauth2-proxy?utm_source=chatgpt.com "Setting headers with NGINX auth_request and oauth2_proxy"
[9]: https://oauth2-proxy.github.io/oauth2-proxy/?utm_source=chatgpt.com "Welcome | OAuth2 Proxy - GitHub Pages"
[10]: https://github.com/oauth2-proxy/oauth2-proxy/issues/2653?utm_source=chatgpt.com "Trying to implement simple Oauth2-proxy/nginx configuration"
[11]: https://zeropath.com/blog/cve-2025-54576-oauth2-proxy-auth-bypass?utm_source=chatgpt.com "OAuth2-Proxy CVE-2025-54576: Brief Summary of a ..."


# Patch


## 🧩 نحوه دسترسی (Access)

* **اپ (Nginx → Django)**

  * صفحه عمومی: `http://app.127.0.0.1.nip.io:8080/public`
  * صفحه خصوصی (نیازمند لاگین): `http://app.127.0.0.1.nip.io:8080/private`
* **Keycloak (IdP)**

  * کنسول ادمین: `http://auth.127.0.0.1.nip.io:8081/admin/`

    * **ادمین (master realm):** `admin / admin`
  * صفحه لاگین رِلم demo به‌صورت خودکار از `/private` فراخوانی می‌شود.

    * **کاربر تست (demo realm):** `demo / demo`

> اگر دامنه‌های nip.io در مرورگرت دردسر داشتند، از ورودی‌های معادل نیز می‌توانی استفاده کنی:
> `http://127.0.0.1:8080/public` و `http://127.0.0.1:8080/private` (redirect همچنان به nip.io می‌رود؛ مطمئن شو `/etc/hosts` مطابق بخش «دیباگ» ست شده است).

---

## 🌐 آدرس‌ها (Endpoints)

* **Nginx (Gateway):**

  * `/public` → آزاد
  * `/private` → `auth_request /oauth2/auth` → (202/401)
  * `/oauth2/*` → proxy به OAuth2-Proxy
* **OAuth2-Proxy:**

  * Discovery: `OAUTH2_PROXY_OIDC_ISSUER_URL = http://auth.127.0.0.1.nip.io:8081/realms/demo`
  * Callback: `http://app.127.0.0.1.nip.io:8080/oauth2/callback`
* **Keycloak (demo realm):**

  * Discovery: `http://auth.127.0.0.1.nip.io:8081/realms/demo/.well-known/openid-configuration`
  * Auth endpoint: `/realms/demo/protocol/openid-connect/auth`
  * Token endpoint: `/realms/demo/protocol/openid-connect/token`

---

## 🛠️ دیباگ (Troubleshooting)

### 1) اطمینان از سلامت سرویس‌ها

```bash
docker compose ps
docker compose logs -f keycloak
docker compose logs -f oauth2-proxy
docker compose logs -f nginx
```

### 2) تست لایه به لایه با curl

```bash
# Keycloak Discovery باید 200 دهد
curl -I http://auth.127.0.0.1.nip.io:8081/realms/demo/.well-known/openid-configuration

# Gateway → App
curl -i http://app.127.0.0.1.nip.io:8080/public      # 200 Hello Public
curl -i http://app.127.0.0.1.nip.io:8080/private     # 302 → Keycloak

# شبیه‌سازی Host Header (اگر DNS مرورگر مشکوک بود)
curl -i -H 'Host: app.127.0.0.1.nip.io' http://127.0.0.1:8080/public
```

### 3) مشکلات مرورگر (ERR\_EMPTY\_RESPONSE / redirect کار نمی‌کند)

* **DNS محلی را قطعی کن** (Override در /etc/hosts):

  ```bash
  # هر دو دامنه باید به 127.0.0.1 نگاشت شوند
  sudo sh -c 'printf "\n# dev overrides for auth-stack\n127.0.0.1 app.127.0.0.1.nip.io auth.127.0.0.1.nip.io\n" >> /etc/hosts'
  getent hosts app.127.0.0.1.nip.io
  getent hosts auth.127.0.0.1.nip.io
  ```
* **پاکسازی Chrome** (برای DEV HTTP):

  1. Settings → Privacy:

     * **Use secure DNS** = OFF
     * **Always use secure connections (HTTPS-First)** = OFF
  2. `chrome://net-internals/#dns` → **Clear host cache**
  3. `chrome://net-internals/#hsts` → **Delete domain security policies** برای:
     `app.127.0.0.1.nip.io` و `auth.127.0.0.1.nip.io`
  4. یک پنجره **Incognito** بدون افزونه باز کن.
* **بررسی Nginx واقعاً فایل کانفیگ جدید را دارد**:

  ```bash
  docker exec -it demo-nginx ash -lc 'sed -n "1,140p" /etc/nginx/nginx.conf'
  # باید resolver 127.0.0.11 و proxy_pass مستقیم ببینی (بدون upstream)
  docker compose restart nginx
  ```

### 4) OAuth2-Proxy Cookie Secret اشتباه

* خطا: `cookie_secret must be 16, 24, or 32 bytes ...`
* تولید درست 32 بایتی:

  ```bash
  python3 - <<'PY'
  import secrets, base64
  raw = secrets.token_bytes(32)
  b64 = base64.urlsafe_b64encode(raw).decode().rstrip('\n')
  print("PUT_THIS_IN_CONFIG=", b64)
  print("DECODED_LEN=", len(base64.urlsafe_b64decode(b64)))
  PY
  ```

  مقدار `PUT_THIS_IN_CONFIG_=` را در `oauth2-proxy.cfg` جایگزین کن و سرویس را ریستارت کن.

### 5) خطای issuer mismatch

* مقدار Issuer Keycloak (در Discovery) باید **مو به مو** با `OAUTH2_PROXY_OIDC_ISSUER_URL` یکی باشد.
* چک:

  ```bash
  curl -s http://auth.127.0.0.1.nip.io:8081/realms/demo/.well-known/openid-configuration | jq .issuer
  # باید: "http://auth.127.0.0.1.nip.io:8081/realms/demo"
  ```

---

## 🧭 نحوه دسترسی (Quick Start برای تیم)

1. **بالا آوردن استک**

   ```bash
   cd auth-stack
   docker compose up -d --build
   ```
2. **باز کردن صفحات**

   * اپ:
     `http://app.127.0.0.1.nip.io:8080/public`
     `http://app.127.0.0.1.nip.io:8080/private`
   * Keycloak Admin:
     `http://auth.127.0.0.1.nip.io:8081/admin/` → `admin / admin`
3. **لاگین تست**

   * رِلم demo: `demo / demo` → بعد از ورود، `/private` باید 200 شود.

---

## 🌐 نکته شبکه و VPN

* **VPN** یا **Proxy سازمانی** می‌تواند ترافیک دامنه‌های `*.nip.io` را از مسیر غیرلوکال عبور دهد و باعث عدم دسترسی یا خطا شود.
* برای توسعهٔ محلی، توصیه می‌شود:

  * **VPN را موقتاً خاموش** کنید، یا
  * برای `*.nip.io` استثنا (Split Tunnel) تعریف کنید، یا
  * از **/etc/hosts** همان‌طور که بالاتر گفتیم استفاده کنید تا همیشه به `127.0.0.1` resolve شود.

> اگر مجبورید VPN روشن باشد و امکان Split Tunnel ندارید، برای DEV می‌توانید **ورودی‌های معادل** را استفاده کنید:
> `http://127.0.0.1:8080/public` و `http://127.0.0.1:8080/private`
> (Redirect به nip.io با `/etc/hosts` درست کار خواهد کرد.)

---

### ✅ چک‌لیست نهایی فاز ۲ (به‌روزشده با دسترسی/دیباگ)

* [x] `/public` → 200 OK
* [x] `/private` → 302 به Keycloak → پس از لاگین 200
* [x] Issuer واحد (nip.io:8081) و هماهنگ با OAuth2-Proxy
* [x] Redirect URI دقیق (`/oauth2/callback`) در Realm و Proxy
* [x] Nginx: `resolver 127.0.0.11` + `proxy_pass` مستقیم (بدون upstream)
* [x] Cookie Secret صحیح (۳۲ بایت)
* [x] `/etc/hosts` (dev override) برای `app.` و `auth.` → `127.0.0.1`
* [x] راهنمای دیباگ و روش کار با مرورگر (DNS/HSTS/DoH/Proxy/VPN)

---
