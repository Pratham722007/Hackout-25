from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from heatmap.models import Report
from .services import AchievementService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    """Create user stats when a new user is created"""
    if created:
        try:
            AchievementService.get_or_create_user_stats(instance)
            logger.info(f"Created user stats for {instance.username}")
        except Exception as e:
            logger.error(f"Error creating user stats for {instance.username}: {e}")


@receiver(post_save, sender=Report)
def track_report_creation(sender, instance, created, **kwargs):
    """Track achievement progress when a report is created"""
    if created and hasattr(instance, 'created_by') and instance.created_by:
        try:
            AchievementService.track_report_created(instance.created_by, instance)
            logger.info(f"Tracked report creation for {instance.created_by.username}")
        except Exception as e:
            logger.error(f"Error tracking report creation: {e}")


@receiver(post_save, sender=Report)
def track_report_validation(sender, instance, created, **kwargs):
    """Track achievement progress when a report is validated"""
    if not created and instance.status == 'validated':
        # Check if status was just changed to validated
        try:
            old_instance = Report.objects.get(pk=instance.pk)
            if old_instance and old_instance.status != 'validated':
                # Status just changed to validated
                if hasattr(instance, 'validated_by') and instance.validated_by:
                    AchievementService.track_report_validated(instance.validated_by, instance)
                    logger.info(f"Tracked report validation for {instance.validated_by.username}")
        except Report.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error tracking report validation: {e}")
