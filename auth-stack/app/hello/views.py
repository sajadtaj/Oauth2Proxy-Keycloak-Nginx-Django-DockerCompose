from django.shortcuts import render
from django.http import HttpResponse

def public_view(request):
    return HttpResponse("Hello Public", content_type="text/plain; charset=utf-8")

def private_view(request):
    return HttpResponse("Hello Private", content_type="text/plain; charset=utf-8")
