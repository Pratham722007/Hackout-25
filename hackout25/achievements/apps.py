from django.apps import AppConfig


class AchievementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'achievements'
    verbose_name = 'Achievement System'
    
    def ready(self):
        """Initialize default achievements when app is ready"""
        import achievements.signals  # Import signals
