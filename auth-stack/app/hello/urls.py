# auth-stack/app/hello/urls.py
from django.urls import path
from .views import public_view, private_view

urlpatterns = [
    path("public", public_view, name="public"),
    path("private", private_view, name="private"),
]
