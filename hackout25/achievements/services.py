from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import Achievement, UserAchievement, UserStats, AchievementNotification
from heatmap.models import Report
import logging

logger = logging.getLogger(__name__)


class AchievementService:
    """
    Service class to handle achievement tracking and unlocking
    """
    
    @staticmethod
    def get_or_create_user_stats(user):
        """Get or create user stats"""
        stats, created = UserStats.objects.get_or_create(
            user=user,
            defaults={
                'reports_created': 0,
                'reports_validated': 0,
                'map_views': 0,
                'streak_current': 0,
                'streak_best': 0,
                'validation_accuracy': 0.0,
                'total_points': 0,
                'achievements_unlocked': 0,
                'level': 1,
            }
        )
        return stats
    
    @staticmethod
    def track_report_created(user, report):
        """Track when user creates a report"""
        try:
            with transaction.atomic():
                stats = AchievementService.get_or_create_user_stats(user)
                stats.reports_created += 1
                stats.update_streak()
                
                # Add location and report type variety
                stats.add_location(report.latitude, report.longitude)
                stats.add_report_type(report.report_type)
                
                # Check for high severity
                if report.severity in ['high', 'critical']:
                    stats.high_severity_found += 1
                
                stats.save()
                
                # Check achievements
                AchievementService.check_achievements_for_user(user, 'report_created')
                
        except Exception as e:
            logger.error(f"Error tracking report creation for user {user.username}: {e}")
    
    @staticmethod
    def track_analysis_created(user, analysis):
        """Track when user creates an environmental analysis"""
        try:
            with transaction.atomic():
                stats = AchievementService.get_or_create_user_stats(user)
                stats.reports_created += 1  # Count analyses as reports for achievements
                stats.update_streak()
                
                # Add location variety if coordinates are available
                if analysis.latitude and analysis.longitude:
                    stats.add_location(analysis.latitude, analysis.longitude)
                
                # Map analysis risk levels to severity for achievement tracking
                risk_to_severity = {
                    'critical': 'critical',
                    'high': 'high',
                    'low': 'low'
                }
                severity = risk_to_severity.get(analysis.risk_level, 'medium')
                
                # Check for high severity analyses
                if severity in ['high', 'critical']:
                    stats.high_severity_found += 1
                
                # Add analysis type variety (treat risk level as type for variety)
                analysis_type = f"analysis_{analysis.risk_level}"
                stats.add_report_type(analysis_type)
                
                stats.save()
                
                # Check achievements
                AchievementService.check_achievements_for_user(user, 'analysis_created')
                
        except Exception as e:
            logger.error(f"Error tracking analysis creation for user {user.username}: {e}")
    
    @staticmethod
    def track_analysis_validated(user, analysis):
        """Track when user validates an environmental analysis"""
        try:
            with transaction.atomic():
                stats = AchievementService.get_or_create_user_stats(user)
                stats.reports_validated += 1
                stats.update_streak()
                
                # Check if validation was quick (within 24 hours)
                if analysis.created_at and timezone.now() - analysis.created_at <= timezone.timedelta(hours=24):
                    stats.helpful_validations += 1
                
                stats.save()
                
                # Check achievements
                AchievementService.check_achievements_for_user(user, 'analysis_validation')
                
        except Exception as e:
            logger.error(f"Error tracking analysis validation for user {user.username}: {e}")
    
    @staticmethod
    def track_report_validated(user, report):
        """Track when user validates a report"""
        try:
            with transaction.atomic():
                stats = AchievementService.get_or_create_user_stats(user)
                stats.reports_validated += 1
                stats.update_streak()
                
                # Check if validation was quick (within 24 hours)
                if report.created_at and timezone.now() - report.created_at <= timezone.timedelta(hours=24):
                    stats.helpful_validations += 1
                
                stats.save()
                
                # Check achievements
                AchievementService.check_achievements_for_user(user, 'validation')
                
        except Exception as e:
            logger.error(f"Error tracking validation for user {user.username}: {e}")
    
    @staticmethod
    def track_map_usage(user):
        """Track when user views the heatmap"""
        try:
            stats = AchievementService.get_or_create_user_stats(user)
            stats.map_views += 1
            stats.update_streak()
            stats.save()
            
            # Check achievements
            AchievementService.check_achievements_for_user(user, 'map_usage')
            
        except Exception as e:
            logger.error(f"Error tracking map usage for user {user.username}: {e}")
    
    @staticmethod
    def check_achievements_for_user(user, trigger_type=None):
        """Check and unlock achievements for a user"""
        try:
            stats = AchievementService.get_or_create_user_stats(user)
            
            # Get all active achievements
            achievements = Achievement.objects.filter(is_active=True)
            
            for achievement in achievements:
                # Get or create user achievement record
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'current_progress': 0}
                )
                
                # Skip if already unlocked
                if user_achievement.is_unlocked:
                    continue
                
                # Calculate current progress based on achievement type
                current_value = AchievementService.get_current_value_for_achievement(stats, achievement)
                user_achievement.current_progress = current_value
                
                # Check if achievement should be unlocked
                if current_value >= achievement.target_value:
                    if user_achievement.unlock():
                        # Award points
                        stats.total_points += achievement.points
                        stats.achievements_unlocked += 1
                        stats.update_level()
                        stats.save()
                        
                        logger.info(f"Achievement unlocked: {achievement.name} for user {user.username}")
                else:
                    user_achievement.save()
                    
        except Exception as e:
            logger.error(f"Error checking achievements for user {user.username}: {e}")
    
    @staticmethod
    def get_current_value_for_achievement(stats, achievement):
        """Get current value for achievement based on action type"""
        mapping = {
            'report_count': stats.reports_created,
            'validation_count': stats.reports_validated,
            'streak_days': stats.streak_best,
            'map_usage': stats.map_views,
            'high_severity': stats.high_severity_found,
            'accuracy_score': int(stats.validation_accuracy),
            'location_variety': len(stats.locations_reported),
            'report_types': len(stats.report_types_used),
            'quick_response': stats.helpful_validations,
            'community_help': stats.community_contributions,
        }
        return mapping.get(achievement.action_type, 0)
    
    @staticmethod
    def get_user_progress_summary(user):
        """Get comprehensive progress summary for user"""
        try:
            stats = AchievementService.get_or_create_user_stats(user)
            
            # Get achievement progress
            user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
            
            unlocked_count = user_achievements.filter(is_unlocked=True).count()
            total_achievements = Achievement.objects.filter(is_active=True).count()
            
            # Recent achievements
            recent_achievements = user_achievements.filter(
                is_unlocked=True,
                unlocked_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-unlocked_at')[:3]
            
            # In-progress achievements (closest to completion)
            in_progress = user_achievements.filter(
                is_unlocked=False,
                current_progress__gt=0
            ).order_by('-current_progress')[:5]
            
            # Leaderboard position (simplified)
            user_rank = UserStats.objects.filter(
                total_points__gt=stats.total_points
            ).count() + 1
            
            return {
                'stats': stats,
                'unlocked_count': unlocked_count,
                'total_achievements': total_achievements,
                'completion_percentage': round((unlocked_count / total_achievements) * 100, 1) if total_achievements > 0 else 0,
                'recent_achievements': recent_achievements,
                'in_progress': in_progress,
                'user_rank': user_rank,
                'next_level_points': AchievementService.get_points_for_next_level(stats.level),
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress for {user.username}: {e}")
            return None
    
    @staticmethod
    def get_points_for_next_level(current_level):
        """Calculate points needed for next level"""
        # Level progression: 100 points for level 1, then +50 for each subsequent level
        points_for_next = 100 + (current_level * 50)
        return points_for_next
    
    @staticmethod
    def get_unread_notifications(user):
        """Get unread achievement notifications"""
        return AchievementNotification.objects.filter(
            user=user,
            is_read=False
        ).select_related('achievement').order_by('-created_at')
    
    @staticmethod
    def mark_notifications_as_read(user, notification_ids=None):
        """Mark notifications as read"""
        notifications = AchievementNotification.objects.filter(user=user, is_read=False)
        
        if notification_ids:
            notifications = notifications.filter(id__in=notification_ids)
            
        notifications.update(is_read=True)
    
    @staticmethod
    def create_default_achievements():
        """Create default set of achievements"""
        default_achievements = [
            # Reporter Achievements
            {
                'name': 'First Report',
                'description': 'Submit your first environmental report',
                'category': 'reporter',
                'tier': 'bronze',
                'action_type': 'report_count',
                'target_value': 1,
                'icon': '🌱',
                'points': 10,
            },
            {
                'name': 'Environmental Activist',
                'description': 'Submit 5 environmental reports',
                'category': 'reporter',
                'tier': 'silver',
                'action_type': 'report_count',
                'target_value': 5,
                'icon': '🌿',
                'points': 25,
            },
            {
                'name': 'Dedicated Reporter',
                'description': 'Submit 10 environmental reports',
                'category': 'reporter',
                'tier': 'silver',
                'action_type': 'report_count',
                'target_value': 10,
                'icon': '📋',
                'points': 50,
            },
            {
                'name': 'Eco Warrior',
                'description': 'Submit 25 environmental reports',
                'category': 'reporter',
                'tier': 'gold',
                'action_type': 'report_count',
                'target_value': 25,
                'icon': '🌳',
                'points': 100,
            },
            {
                'name': 'Environmental Champion',
                'description': 'Submit 50 environmental reports',
                'category': 'reporter',
                'tier': 'gold',
                'action_type': 'report_count',
                'target_value': 50,
                'icon': '🏆',
                'points': 250,
            },
            {
                'name': 'Environmental Guardian',
                'description': 'Submit 100 environmental reports',
                'category': 'reporter',
                'tier': 'platinum',
                'action_type': 'report_count',
                'target_value': 100,
                'icon': '🌲',
                'points': 500,
            },
            
            # Validator Achievements
            {
                'name': 'Fact Checker',
                'description': 'Validate your first report',
                'category': 'validator',
                'tier': 'bronze',
                'action_type': 'validation_count',
                'target_value': 1,
                'icon': '✅',
                'points': 15,
            },
            {
                'name': 'Quality Controller',
                'description': 'Validate 10 reports',
                'category': 'validator',
                'tier': 'silver',
                'action_type': 'validation_count',
                'target_value': 10,
                'icon': '🔍',
                'points': 50,
            },
            {
                'name': 'Expert Validator',
                'description': 'Validate 50 reports',
                'category': 'validator',
                'tier': 'gold',
                'action_type': 'validation_count',
                'target_value': 50,
                'icon': '🎯',
                'points': 200,
            },
            
            # Streak Achievements
            {
                'name': 'Consistent Reporter',
                'description': 'Stay active for 3 consecutive days',
                'category': 'streak',
                'tier': 'bronze',
                'action_type': 'streak_days',
                'target_value': 3,
                'icon': '🔥',
                'points': 20,
            },
            {
                'name': 'Weekly Champion',
                'description': 'Stay active for 7 consecutive days',
                'category': 'streak',
                'tier': 'silver',
                'action_type': 'streak_days',
                'target_value': 7,
                'icon': '🔥',
                'points': 75,
            },
            {
                'name': 'Unstoppable Force',
                'description': 'Stay active for 30 consecutive days',
                'category': 'streak',
                'tier': 'gold',
                'action_type': 'streak_days',
                'target_value': 30,
                'icon': '🔥',
                'points': 300,
            },
            
            # Explorer Achievements
            {
                'name': 'Map Explorer',
                'description': 'View the environmental heatmap 5 times',
                'category': 'explorer',
                'tier': 'bronze',
                'action_type': 'map_usage',
                'target_value': 5,
                'icon': '🗺️',
                'points': 15,
            },
            {
                'name': 'Area Scout',
                'description': 'Report from 10 different locations',
                'category': 'explorer',
                'tier': 'silver',
                'action_type': 'location_variety',
                'target_value': 10,
                'icon': '📍',
                'points': 50,
            },
            {
                'name': 'Regional Expert',
                'description': 'Report from 25 different locations',
                'category': 'explorer',
                'tier': 'gold',
                'action_type': 'location_variety',
                'target_value': 25,
                'icon': '🌍',
                'points': 150,
            },
            
            # Impact Achievements
            {
                'name': 'Alert Citizen',
                'description': 'Report 3 high severity incidents',
                'category': 'impact',
                'tier': 'bronze',
                'action_type': 'high_severity',
                'target_value': 3,
                'icon': '⚠️',
                'points': 30,
            },
            {
                'name': 'Crisis Spotter',
                'description': 'Report 10 high severity incidents',
                'category': 'impact',
                'tier': 'silver',
                'action_type': 'high_severity',
                'target_value': 10,
                'icon': '🚨',
                'points': 100,
            },
            
            # Expert Achievements
            {
                'name': 'Versatile Reporter',
                'description': 'Use 5 different report types',
                'category': 'expert',
                'tier': 'bronze',
                'action_type': 'report_types',
                'target_value': 5,
                'icon': '🎓',
                'points': 40,
            },
            {
                'name': 'Environmental Specialist',
                'description': 'Use all available report types',
                'category': 'expert',
                'tier': 'gold',
                'action_type': 'report_types',
                'target_value': 8,  # Assuming 8 report types exist
                'icon': '👨‍🔬',
                'points': 200,
            },
            
            # Community Achievements
            {
                'name': 'Quick Responder',
                'description': 'Validate 5 reports within 24 hours of submission',
                'category': 'community',
                'tier': 'silver',
                'action_type': 'quick_response',
                'target_value': 5,
                'icon': '⚡',
                'points': 75,
            },
            
            # Milestone Achievements
            {
                'name': 'Getting Started',
                'description': 'Submit 3 environmental reports',
                'category': 'reporter',
                'tier': 'bronze',
                'action_type': 'report_count',
                'target_value': 3,
                'icon': '🌟',
                'points': 15,
            },
            {
                'name': 'Super Reporter',
                'description': 'Submit 75 environmental reports',
                'category': 'reporter',
                'tier': 'platinum',
                'action_type': 'report_count',
                'target_value': 75,
                'icon': '⭐',
                'points': 400,
            },
            {
                'name': 'Environmental Legend',
                'description': 'Submit 200 environmental reports',
                'category': 'reporter',
                'tier': 'legendary',
                'action_type': 'report_count',
                'target_value': 200,
                'icon': '🌟',
                'points': 1000,
            },
            
            # Special milestone achievements
            {
                'name': 'Marathon Reporter',
                'description': 'Submit 500 environmental reports',
                'category': 'reporter',
                'tier': 'legendary',
                'action_type': 'report_count',
                'target_value': 500,
                'icon': '🏃‍♂️',
                'points': 2500,
            },
        ]
        
        created_count = 0
        for achievement_data in default_achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                tier=achievement_data['tier'],
                defaults=achievement_data
            )
            if created:
                created_count += 1
                
        logger.info(f"Created {created_count} default achievements")
        return created_count