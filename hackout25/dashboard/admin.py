from django.contrib import admin
from .models import EnvironmentalAnalysis

@admin.register(EnvironmentalAnalysis)
class EnvironmentalAnalysisAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'risk_level', 'status', 'confidence', 'created_at']
    list_filter = ['risk_level', 'status', 'created_at']
    search_fields = ['title', 'location', 'description']
    readonly_fields = ['created_at']
    list_per_page = 20
    fields = ['title', 'location', 'description', 'image', 'risk_level', 'status', 'confidence', 'created_at']
