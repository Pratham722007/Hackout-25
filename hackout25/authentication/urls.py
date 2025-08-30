from django.urls import path, re_path
from .views import index, clerk_webhook, redirect_to_dashboard, logout_view

urlpatterns = [
    path('', index, name='index'),
    re_path(r'^sign-in.*$', index, name='sign-in'),   # catch /sign-in and any subroutes
    re_path(r'^sign-up.*$', index, name='sign-up'),   # catch /sign-up and any subroutes
    path('dashboard/', redirect_to_dashboard, name='dashboard_redirect'),
    path('logout/', logout_view, name='logout'),
    path('webhooks/clerk/', clerk_webhook, name='clerk_webhook'),
]
