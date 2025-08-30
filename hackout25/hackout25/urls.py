"""
URL configuration for hackout25 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import FileResponse
from django.views.decorators.cache import cache_control
import os

@cache_control(max_age=86400)  # Cache for 24 hours
def favicon_view(request):
    """Serve favicon.ico"""
    favicon_path = os.path.join(settings.BASE_DIR, 'authentication', 'templates', 'favicon.ico')
    try:
        return FileResponse(open(favicon_path, 'rb'), content_type='image/x-icon')
    except FileNotFoundError:
        # Return a simple HTTP 404 if favicon not found
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound("Favicon not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("dashboard/", include("dashboard.urls")),
    path('', include('authentication.urls')),
    path('news/', include('news.urls')),
    path('heatmap/', include('heatmap.urls')),
    path('achievements_dashboard/', include('achievements.urls')),
    path('favicon.ico', favicon_view, name='favicon'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
