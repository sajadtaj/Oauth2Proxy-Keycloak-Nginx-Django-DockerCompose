# auth-stack/app/core/views.py
from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def public_view(request):
    return HttpResponse("Hello Public", content_type="text/plain; charset=utf-8")

@require_GET
def private_view(request):
    # هدرها در WSGI با پیشوند HTTP_ در دسترس‌اند
    user  = request.META.get("HTTP_X_USER") or request.META.get("HTTP_X_AUTH_REQUEST_USER") or "Unknown"
    email = request.META.get("HTTP_X_EMAIL") or request.META.get("HTTP_X_AUTH_REQUEST_EMAIL") or ""
    # نمایش مینیمال (Plain Text)
    if email:
        msg = f"Hello Private, User:{user} , Email ({email})"
    else:
        msg = f"Hello Private, {user}"
    return HttpResponse(msg, content_type="text/plain; charset=utf-8")
