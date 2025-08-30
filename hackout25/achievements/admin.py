from django.contrib import admin
from django.utils.html import format_html
from .models import Achievement, UserAchievement, UserStats, AchievementNotification, Leaderboard


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_display', 'tier', 'points', 'target_value', 'is_active']
    list_filter = ['category', 'tier', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category', 'tier', 'target_value']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'tier')
        }),
        ('Logic', {
            'fields': ('action_type', 'target_value')
        }),
        ('Visual & Rewards', {
            'fields': ('icon', 'color', 'points', 'badge_unlocked')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_hidden', 'created_at')
        }),
    )
    
    def category_display(self, obj):
        return obj.get_category_display_with_emoji()
    category_display.short_description = 'Category'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement_name', 'progress_display', 'status_display', 'unlocked_at']
    list_filter = ['is_unlocked', 'achievement__category', 'achievement__tier', 'unlocked_at']
    search_fields = ['user__username', 'achievement__name']
    ordering = ['-unlocked_at', 'user__username']
    readonly_fields = ['unlocked_at']
    
    def achievement_name(self, obj):
        return f"{obj.achievement.icon} {obj.achievement.name}"
    achievement_name.short_description = 'Achievement'
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        color = '#28a745' if obj.is_unlocked else '#ffc107' if percentage > 50 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 4px; padding: 2px;">'
            '<div style="width: {width}%; background: {color}; height: 16px; border-radius: 2px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">'
            '{percentage}%</div></div>',
            width=percentage, color=color, percentage=int(percentage)
        )
    progress_display.short_description = 'Progress'
    
    def status_display(self, obj):
        if obj.is_unlocked:
            return format_html('<span style="color: #28a745;">✅ Unlocked</span>')
        return format_html('<span style="color: #6c757d;">🔒 Locked</span>')
    status_display.short_description = 'Status'


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'total_points', 'achievements_unlocked', 'reports_created', 'streak_current']
    list_filter = ['level', 'last_activity']
    search_fields = ['user__username']
    ordering = ['-total_points']
    readonly_fields = ['last_activity']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Reporting Stats', {
            'fields': ('reports_created', 'reports_validated', 'high_severity_found')
        }),
        ('Engagement', {
            'fields': ('map_views', 'streak_current', 'streak_best', 'last_activity')
        }),
        ('Quality', {
            'fields': ('validation_accuracy', 'locations_reported', 'report_types_used')
        }),
        ('Achievements', {
            'fields': ('total_points', 'achievements_unlocked', 'level')
        }),
        ('Social', {
            'fields': ('helpful_validations', 'community_contributions')
        }),
    )


@admin.register(AchievementNotification)
class AchievementNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement_name', 'is_read', 'is_displayed', 'created_at']
    list_filter = ['is_read', 'is_displayed', 'created_at', 'achievement__category']
    search_fields = ['user__username', 'achievement__name', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def achievement_name(self, obj):
        return f"{obj.achievement.icon} {obj.achievement.name}"
    achievement_name.short_description = 'Achievement'


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['leaderboard_type', 'rank', 'user', 'score', 'period_display']
    list_filter = ['leaderboard_type', 'period_start', 'period_end']
    search_fields = ['user__username']
    ordering = ['leaderboard_type', 'rank']
    
    def period_display(self, obj):
        return f"{obj.period_start} to {obj.period_end}"
    period_display.short_description = 'Period'


# Customize admin site
admin.site.site_header = "EcoValidate Achievement System"
admin.site.site_title = "Achievement Admin"
admin.site.index_title = "Achievement Management"
