"""
Clerk-Integrated Achievements Service
Handles achievement tracking with proper Clerk user data integration
"""

import logging
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from authentication.models import UserProfile
from ..models import Achievement, UserAchievement, UserStats, AchievementNotification
from ..services import AchievementService

logger = logging.getLogger(__name__)


class ClerkAchievementService(AchievementService):
    """
    Extended Achievement Service with Clerk user integration
    Properly handles user data from Clerk authentication system
    """
    
    @staticmethod
    def get_user_from_clerk_context(user=None, clerk_user_id=None, user_id=None, email=None):
        """
        Get Django user from various Clerk-related identifiers
        Returns (user, user_profile) tuple
        """
        try:
            user_profile = None
            
            # If user object is provided directly
            if user and isinstance(user, User):
                try:
                    user_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    # Create user profile if it doesn't exist
                    user_profile = UserProfile.objects.create(
                        user=user,
                        clerk_user_id=clerk_user_id,
                        is_verified=True
                    )
                return user, user_profile
            
            # Find by Clerk user ID
            if clerk_user_id:
                try:
                    user_profile = UserProfile.objects.select_related('user').get(
                        clerk_user_id=clerk_user_id
                    )
                    return user_profile.user, user_profile
                except UserProfile.DoesNotExist:
                    logger.warning(f"User profile not found for Clerk ID: {clerk_user_id}")
            
            # Find by Django user ID
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user_profile = UserProfile.objects.filter(user=user).first()
                    return user, user_profile
                except User.DoesNotExist:
                    logger.warning(f"User not found for ID: {user_id}")
            
            # Find by email
            if email:
                try:
                    user = User.objects.get(email=email)
                    user_profile = UserProfile.objects.filter(user=user).first()
                    return user, user_profile
                except User.DoesNotExist:
                    logger.warning(f"User not found for email: {email}")
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting user from Clerk context: {e}")
            return None, None
    
    @staticmethod
    def get_or_create_user_stats_with_clerk(user, user_profile=None):
        """
        Get or create user stats with Clerk integration
        Ensures user profile exists and is properly linked
        """
        try:
            # Ensure user profile exists
            if not user_profile:
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'is_verified': True,
                        'clerk_user_id': None
                    }
                )
            
            # Get or create user stats
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
                    'high_severity_found': 0,
                    'locations_reported': [],
                    'report_types_used': [],
                    'helpful_validations': 0,
                    'community_contributions': 0,
                }
            )
            
            if created:
                logger.info(f"Created new user stats for: {user.username}")
            
            return stats, user_profile
            
        except Exception as e:
            logger.error(f"Error creating user stats with Clerk: {e}")
            return None, None
    
    @staticmethod
    def track_report_created_with_clerk(user, report, clerk_user_id=None):
        """
        Track report creation with Clerk user integration
        """
        try:
            with transaction.atomic():
                # Get user and profile
                user, user_profile = ClerkAchievementService.get_user_from_clerk_context(
                    user=user, clerk_user_id=clerk_user_id
                )
                
                if not user:
                    logger.error("Cannot track report creation - user not found")
                    return False
                
                # Get or create user stats
                stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(
                    user, user_profile
                )
                
                if not stats:
                    logger.error("Cannot track report creation - stats creation failed")
                    return False
                
                # Update stats
                stats.reports_created += 1
                stats.update_streak()
                
                # Add location and report type variety
                if hasattr(report, 'latitude') and hasattr(report, 'longitude'):
                    stats.add_location(report.latitude, report.longitude)
                
                if hasattr(report, 'report_type'):
                    stats.add_report_type(report.report_type)
                
                # Check for high severity
                if hasattr(report, 'severity') and report.severity in ['high', 'critical']:
                    stats.high_severity_found += 1
                
                stats.save()
                
                # Check achievements
                ClerkAchievementService.check_achievements_for_user_with_clerk(user, 'report_created')
                
                logger.info(f"Successfully tracked report creation for {user.username}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking report creation with Clerk for user {user.username if user else 'Unknown'}: {e}")
            return False
    
    @staticmethod
    def track_analysis_created_with_clerk(user, analysis, clerk_user_id=None):
        """
        Track analysis creation with Clerk user integration
        """
        try:
            with transaction.atomic():
                # Get user and profile
                user, user_profile = ClerkAchievementService.get_user_from_clerk_context(
                    user=user, clerk_user_id=clerk_user_id
                )
                
                if not user:
                    logger.error("Cannot track analysis creation - user not found")
                    return False
                
                # Get or create user stats
                stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(
                    user, user_profile
                )
                
                if not stats:
                    logger.error("Cannot track analysis creation - stats creation failed")
                    return False
                
                # Update stats (count analyses as reports for achievements)
                stats.reports_created += 1
                stats.update_streak()
                
                # Add location variety if coordinates are available
                if hasattr(analysis, 'latitude') and hasattr(analysis, 'longitude'):
                    if analysis.latitude and analysis.longitude:
                        stats.add_location(analysis.latitude, analysis.longitude)
                
                # Map analysis risk levels to severity for achievement tracking
                if hasattr(analysis, 'risk_level'):
                    risk_to_severity = {
                        'critical': 'critical',
                        'high': 'high',
                        'low': 'low'
                    }
                    severity = risk_to_severity.get(analysis.risk_level, 'medium')
                    
                    # Check for high severity analyses
                    if severity in ['high', 'critical']:
                        stats.high_severity_found += 1
                    
                    # Add analysis type variety
                    analysis_type = f"analysis_{analysis.risk_level}"
                    stats.add_report_type(analysis_type)
                
                stats.save()
                
                # Check achievements
                ClerkAchievementService.check_achievements_for_user_with_clerk(user, 'analysis_created')
                
                logger.info(f"Successfully tracked analysis creation for {user.username}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking analysis creation with Clerk for user {user.username if user else 'Unknown'}: {e}")
            return False
    
    @staticmethod
    def check_achievements_for_user_with_clerk(user, trigger_type=None):
        """
        Check and unlock achievements for a user with Clerk integration
        """
        try:
            # Get user stats
            stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(user)
            
            if not stats:
                logger.error(f"Cannot check achievements - stats not available for {user.username}")
                return
            
            # Get all active achievements
            achievements = Achievement.objects.filter(is_active=True)
            
            unlocked_this_session = []
            
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
                current_value = ClerkAchievementService.get_current_value_for_achievement(stats, achievement)
                user_achievement.current_progress = current_value
                
                # Check if achievement should be unlocked
                if current_value >= achievement.target_value:
                    if user_achievement.unlock():
                        # Award points
                        stats.total_points += achievement.points
                        stats.achievements_unlocked += 1
                        stats.update_level()
                        stats.save()
                        
                        unlocked_this_session.append(achievement)
                        logger.info(f"🏆 Achievement unlocked: {achievement.name} for user {user.username}")
                else:
                    user_achievement.save()
            
            # Display unlocked achievements
            if unlocked_this_session:
                ClerkAchievementService.display_achievement_unlocks(user, unlocked_this_session)
            
            return len(unlocked_this_session)
                    
        except Exception as e:
            logger.error(f"Error checking achievements with Clerk for user {user.username}: {e}")
            return 0
    
    @staticmethod
    def display_achievement_unlocks(user, achievements):
        """
        Display achievement unlock notifications in terminal
        """
        try:
            print("\n" + "🏆" * 60)
            print("🎉 ACHIEVEMENT UNLOCKED! 🎉")
            print("🏆" * 60)
            
            for achievement in achievements:
                print(f"\n{achievement.icon} {achievement.name}")
                print(f"📝 {achievement.description}")
                print(f"🏅 Tier: {achievement.get_tier_display()}")
                print(f"⭐ Points Earned: {achievement.points}")
                print(f"👤 User: {user.get_full_name() or user.username}")
                
                # Get user's updated stats
                try:
                    stats = UserStats.objects.get(user=user)
                    print(f"📊 Total Points: {stats.total_points}")
                    print(f"🎯 Level: {stats.level}")
                    print(f"🏆 Achievements: {stats.achievements_unlocked}")
                except UserStats.DoesNotExist:
                    pass
                
                print("-" * 50)
            
            print("🏆" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"Error displaying achievement unlocks: {e}")
    
    @staticmethod
    def initialize_user_achievements(user, clerk_user_id=None):
        """
        Initialize achievement tracking for a new user
        """
        try:
            with transaction.atomic():
                # Get or create user profile
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'clerk_user_id': clerk_user_id,
                        'is_verified': True
                    }
                )
                
                # Get or create user stats
                stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(
                    user, user_profile
                )
                
                # Create UserAchievement records for all active achievements
                achievements = Achievement.objects.filter(is_active=True)
                created_count = 0
                
                for achievement in achievements:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement,
                        defaults={'current_progress': 0}
                    )
                    if created:
                        created_count += 1
                
                logger.info(f"Initialized {created_count} achievements for user: {user.username}")
                return stats, user_profile, created_count
                
        except Exception as e:
            logger.error(f"Error initializing user achievements: {e}")
            return None, None, 0
    
    @staticmethod
    def get_user_progress_summary_with_clerk(user):
        """
        Get comprehensive progress summary with Clerk integration
        """
        try:
            # Ensure user has proper setup
            stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(user)
            
            if not stats:
                logger.error(f"Could not get stats for user: {user.username}")
                return None
            
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
            
            # Leaderboard position
            user_rank = UserStats.objects.filter(
                total_points__gt=stats.total_points
            ).count() + 1
            
            return {
                'stats': stats,
                'user_profile': user_profile,
                'unlocked_count': unlocked_count,
                'total_achievements': total_achievements,
                'completion_percentage': round((unlocked_count / total_achievements) * 100, 1) if total_achievements > 0 else 0,
                'recent_achievements': recent_achievements,
                'in_progress': in_progress,
                'user_rank': user_rank,
                'next_level_points': ClerkAchievementService.get_points_for_next_level(stats.level),
                'clerk_data': {
                    'clerk_user_id': user_profile.clerk_user_id if user_profile else None,
                    'is_verified': user_profile.is_verified if user_profile else False,
                    'created_at': user_profile.created_at if user_profile else None,
                },
                'user_info': {
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                    'is_active': user.is_active,
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress with Clerk for {user.username}: {e}")
            return None
    
    @staticmethod
    def ensure_achievements_setup_for_user(user):
        """
        Ensure user has proper achievement setup
        Call this when a user logs in or creates their first report
        """
        try:
            with transaction.atomic():
                # Initialize user achievements if needed
                stats, user_profile, created_count = ClerkAchievementService.initialize_user_achievements(user)
                
                if stats:
                    # Check if any achievements should be immediately unlocked based on existing data
                    ClerkAchievementService.check_achievements_for_user_with_clerk(user, 'setup')
                    
                    logger.info(f"Achievement setup completed for {user.username}")
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring achievement setup for {user.username}: {e}")
            return False


class AchievementTracker:
    """
    Helper class to track achievements from various parts of the application
    """
    
    @staticmethod
    def track_report_creation(user, report):
        """
        Track report creation - call this after a report is successfully created
        """
        try:
            # Ensure achievements are set up for user
            ClerkAchievementService.ensure_achievements_setup_for_user(user)
            
            # Track the report creation
            success = ClerkAchievementService.track_report_created_with_clerk(user, report)
            
            if success:
                logger.info(f"✅ Report creation tracked for {user.username}")
            else:
                logger.warning(f"⚠️ Failed to track report creation for {user.username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in report creation tracking: {e}")
            return False
    
    @staticmethod
    def track_analysis_creation(user, analysis):
        """
        Track analysis creation - call this after an analysis is successfully created
        """
        try:
            # Ensure achievements are set up for user
            ClerkAchievementService.ensure_achievements_setup_for_user(user)
            
            # Track the analysis creation
            success = ClerkAchievementService.track_analysis_created_with_clerk(user, analysis)
            
            if success:
                logger.info(f"✅ Analysis creation tracked for {user.username}")
            else:
                logger.warning(f"⚠️ Failed to track analysis creation for {user.username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in analysis creation tracking: {e}")
            return False
    
    @staticmethod
    def track_user_login(user):
        """
        Track user login - ensures achievement system is properly set up
        """
        try:
            # Ensure achievements are set up for user
            setup_success = ClerkAchievementService.ensure_achievements_setup_for_user(user)
            
            if setup_success:
                # Update streak and activity
                stats, user_profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(user)
                if stats:
                    stats.update_streak()
                    stats.save()
            
            logger.info(f"✅ User login tracked for {user.username}")
            return setup_success
            
        except Exception as e:
            logger.error(f"Error tracking user login: {e}")
            return False
    
    @staticmethod
    def get_user_achievement_summary(user):
        """
        Get user achievement summary with proper error handling
        """
        try:
            return ClerkAchievementService.get_user_progress_summary_with_clerk(user)
        except Exception as e:
            logger.error(f"Error getting achievement summary for {user.username}: {e}")
            return None
    
    @staticmethod
    def get_current_value_for_achievement(stats, achievement):
        """
        Get current value for achievement based on action type - Clerk-aware version
        """
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
    def get_points_for_next_level(current_level):
        """
        Calculate points needed for next level - inherited from base service
        """
        return AchievementService.get_points_for_next_level(current_level)
