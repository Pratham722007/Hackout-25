from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('new-analysis/', views.new_analysis_view, name='new_analysis'),
    path('api/coordinates/', views.get_coordinates, name='get_coordinates'),
]
