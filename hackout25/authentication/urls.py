from django.urls import path
from .views import index, clerk_webhook

urlpatterns = [
    # React app handles all routing - login/signup automatically shown
    path('', index, name='index'),
    path('login/', index, name='login'),
    path('signup/', index, name='signup'),
    path('map/', index, name='map'),
    
    # Clerk webhook endpoint
    path('webhooks/clerk/', clerk_webhook, name='clerk_webhook'),
]
