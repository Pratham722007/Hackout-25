# sms_app/urls.py
from django.urls import path
from .views import create_sms

urlpatterns = [
    path("create-sms/", create_sms, name="create-sms"),
]
