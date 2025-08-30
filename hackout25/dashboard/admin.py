from django.contrib import admin
from django.utils.html import format_html
from .models import EnvironmentalAnalysis, Alert, AlertRecipient

@admin.register(EnvironmentalAnalysis)
class EnvironmentalAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'location', 'risk_level', 'status', 'confidence', 
        'has_image', 'has_coordinates', 'created_at'
    ]
    list_filter = ['risk_level', 'status', 'created_at']
    search_fields = ['title', 'location', 'description']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('title', 'description', 'location'),
        }),
        ('Analysis Results', {
            'fields': ('risk_level', 'status', 'confidence'),
        }),
        ('Media & Location', {
            'fields': ('image', 'latitude', 'longitude'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    ]
    
    def has_image(self, obj):
        return obj.image is not None and bool(obj.image)
    has_image.short_description = 'Has Image'
    has_image.boolean = True
    
    def has_coordinates(self, obj):
        return obj.latitude is not None and obj.longitude is not None
    has_coordinates.short_description = 'Has GPS'
    has_coordinates.boolean = True
    
    actions = ['mark_as_flagged', 'mark_as_completed']
    
    def mark_as_flagged(self, request, queryset):
        updated = queryset.update(status='flagged')
        self.message_user(request, f'{updated} reports marked as flagged.')
    mark_as_flagged.short_description = 'Mark selected reports as flagged'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} reports marked as completed.')
    mark_as_completed.short_description = 'Mark selected reports as completed'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'priority', 'location', 'created_by', 'recipients_count', 
        'created_at'
    ]
    list_filter = ['priority', 'created_at', 'created_by']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'sent_at', 'recipients_count']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = [
        ('Alert Information', {
            'fields': ('title', 'description', 'location', 'priority'),
        }),
        ('Media', {
            'fields': ('image',),
        }),
        ('Sending Information', {
            'fields': ('created_by', 'recipients_count', 'sent_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    ]

@admin.register(AlertRecipient)
class AlertRecipientAdmin(admin.ModelAdmin):
    list_display = ['alert', 'user', 'email_sent', 'email_sent_at']
    list_filter = ['email_sent', 'email_sent_at']
    search_fields = ['user__email', 'user__username', 'alert__title']
    readonly_fields = ['alert', 'user', 'email_sent_at']
    list_per_page = 30
    ordering = ['-email_sent_at']
