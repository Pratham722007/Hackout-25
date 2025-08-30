from django.urls import path
from . import views

urlpatterns = [
    # Main heatmap page
    path('', views.heatmap_view, name='heatmap'),
    
    # API endpoints
    path('api/reports/', views.get_reports_api, name='heatmap_reports_api'),
    path('api/heatmap-data/', views.get_heatmap_data_api, name='heatmap_data_api'),
    path('api/statistics/', views.get_statistics_api, name='heatmap_statistics_api'),
    path('api/create-report/', views.create_report_api, name='create_report_api'),
]
