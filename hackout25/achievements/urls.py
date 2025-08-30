from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.achievements_dashboard, name='achievements_dashboard'),
    path('achievement/<int:achievement_id>/', views.achievement_detail, name='achievement_detail'),
    path('leaderboard/', views.leaderboard, name='achievements_leaderboard'),
    
    # API endpoints
    path('api/progress/', views.user_progress_api, name='user_progress_api'),
    path('api/notifications/', views.notifications_api, name='achievement_notifications_api'),
    path('api/notifications/read/', views.mark_notifications_read_api, name='mark_notifications_read_api'),
    path('api/track/', views.track_action_api, name='track_action_api'),
    path('api/leaderboard/', views.public_leaderboard_api, name='public_leaderboard_api'),
]
