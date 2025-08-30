from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_home, name='news_home'),  # Home view for news app
    path('like/<int:aid>/', views.like_article, name='like_article'),  # Like endpoint
    path('latest-json/', views.latest_articles_json, name='latest_articles_json'),  # API for latest news
]

