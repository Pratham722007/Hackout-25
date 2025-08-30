from django.contrib import admin
from .models import Report, ReportStatistics


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'severity', 'status', 
        'location_name', 'reporter_name', 'created_at', 'verified'
    ]
    list_filter = [
        'report_type', 'severity', 'status', 'verified', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'title', 'description', 'location_name', 'address',
        'reporter_name', 'reporter_email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'verified']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'report_type', 'severity', 'status')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'location_name', 'address')
        }),
        ('Reporter Information', {
            'fields': ('reporter_name', 'reporter_email', 'reporter_phone'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('verified', 'confidence_score', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_validated', 'mark_as_verified', 'mark_as_rejected']
    
    def mark_as_validated(self, request, queryset):
        updated = queryset.update(status='validated')
        self.message_user(request, f'{updated} reports marked as validated.')
    mark_as_validated.short_description = "Mark selected reports as validated"
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} reports marked as verified.')
    mark_as_verified.short_description = "Mark selected reports as verified"
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} reports marked as rejected.')
    mark_as_rejected.short_description = "Mark selected reports as rejected"


@admin.register(ReportStatistics)
class ReportStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_reports', 'pending_reports', 
        'validated_reports', 'rejected_reports'
    ]
    list_filter = ['date']
    readonly_fields = ['date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('General Statistics', {
            'fields': ('date', 'total_reports', 'pending_reports', 
                      'validated_reports', 'rejected_reports')
        }),
        ('Type Distribution', {
            'fields': ('air_pollution_count', 'water_pollution_count', 
                      'noise_pollution_count', 'waste_management_count',
                      'deforestation_count', 'wildlife_conservation_count',
                      'climate_change_count', 'other_count'),
            'classes': ('collapse',)
        }),
        ('Severity Distribution', {
            'fields': ('low_severity_count', 'medium_severity_count',
                      'high_severity_count', 'critical_severity_count'),
            'classes': ('collapse',)
        })
    )
