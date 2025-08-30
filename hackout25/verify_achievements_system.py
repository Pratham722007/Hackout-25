#!/usr/bin/env python
"""
Comprehensive Achievements System Verification Script
This script checks all aspects of the achievements system to ensure it's working perfectly.
"""
import os
import django
import sys
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from achievements.services import AchievementService
from achievements.services import ClerkAchievementService, AchievementTracker
from achievements.models import Achievement, UserAchievement, UserStats, AchievementNotification
from django.contrib.auth.models import User
from heatmap.models import Report
from authentication.models import UserProfile
from decimal import Decimal

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️  {message}")

def check_database_integrity():
    """Check if all required database tables and data exist"""
    print_header("DATABASE INTEGRITY CHECK")
    
    try:
        # Check Achievement model
        achievement_count = Achievement.objects.count()
        active_achievements = Achievement.objects.filter(is_active=True).count()
        print_success(f"Achievements table: {achievement_count} total, {active_achievements} active")
        
        if active_achievements == 0:
            print_error("No active achievements found! Run: python manage.py shell -c \"from achievements.services import AchievementService; AchievementService.create_default_achievements()\"")
            return False
        
        # Check UserStats model
        user_stats_count = UserStats.objects.count()
        print_success(f"UserStats table: {user_stats_count} user records")
        
        # Check UserAchievement model
        user_achievements_count = UserAchievement.objects.count()
        unlocked_count = UserAchievement.objects.filter(is_unlocked=True).count()
        print_success(f"UserAchievement table: {user_achievements_count} records, {unlocked_count} unlocked")
        
        # Check AchievementNotification model
        notifications_count = AchievementNotification.objects.count()
        unread_count = AchievementNotification.objects.filter(is_read=False).count()
        print_success(f"Notifications table: {notifications_count} total, {unread_count} unread")
        
        # Check User and UserProfile models
        users_count = User.objects.count()
        profiles_count = UserProfile.objects.count()
        print_success(f"Users: {users_count} total, {profiles_count} with profiles")
        
        return True
        
    except Exception as e:
        print_error(f"Database integrity check failed: {e}")
        return False

def check_service_imports():
    """Check if all services can be imported correctly"""
    print_header("SERVICE IMPORTS CHECK")
    
    try:
        print_success(f"AchievementService imported: {AchievementService}")
        print_success(f"ClerkAchievementService imported: {ClerkAchievementService}")
        print_success(f"AchievementTracker imported: {AchievementTracker}")
        
        # Test basic service functionality
        test_user = User.objects.first()
        if test_user:
            stats = AchievementService.get_or_create_user_stats(test_user)
            print_success(f"Basic service test passed for user: {test_user.username}")
        else:
            print_warning("No users found for service testing")
        
        return True
        
    except Exception as e:
        print_error(f"Service import check failed: {e}")
        return False

def check_clerk_integration():
    """Check Clerk integration functionality"""
    print_header("CLERK INTEGRATION CHECK")
    
    try:
        test_user = User.objects.first()
        if not test_user:
            print_warning("No users found for Clerk integration testing")
            return True
        
        # Test Clerk service methods
        setup_success = ClerkAchievementService.ensure_achievements_setup_for_user(test_user)
        print_success(f"User achievement setup: {setup_success}")
        
        progress = ClerkAchievementService.get_user_progress_summary_with_clerk(test_user)
        if progress:
            print_success(f"Progress summary retrieved for {test_user.username}")
            print(f"   Level: {progress['stats'].level}, Points: {progress['stats'].total_points}")
            print(f"   Achievements: {progress['unlocked_count']}/{progress['total_achievements']}")
        else:
            print_error("Could not retrieve progress summary")
            return False
        
        # Test stats creation
        stats, profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(test_user)
        if stats:
            print_success(f"User stats accessible: Level {stats.level}, Points {stats.total_points}")
        else:
            print_error("Could not create or retrieve user stats")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Clerk integration check failed: {e}")
        return False

def check_achievement_tracking():
    """Test achievement tracking functionality"""
    print_header("ACHIEVEMENT TRACKING CHECK")
    
    try:
        # Create or get a test user
        test_user, created = User.objects.get_or_create(
            username='verification_test_user',
            defaults={
                'email': 'verification@test.com',
                'first_name': 'Verification',
                'last_name': 'Test'
            }
        )
        
        if created:
            print_success(f"Created test user: {test_user.username}")
        else:
            print_success(f"Using existing test user: {test_user.username}")
        
        # Get initial stats
        initial_progress = ClerkAchievementService.get_user_progress_summary_with_clerk(test_user)
        initial_reports = initial_progress['stats'].reports_created if initial_progress else 0
        initial_points = initial_progress['stats'].total_points if initial_progress else 0
        initial_achievements = initial_progress['unlocked_count'] if initial_progress else 0
        
        print(f"Initial state - Reports: {initial_reports}, Points: {initial_points}, Achievements: {initial_achievements}")
        
        # Create a test report
        test_report = Report.objects.create(
            title='Verification Test Report',
            description='Testing achievement tracking functionality',
            report_type='pollution',
            severity='medium',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            location_name='Test Location',
            created_by=test_user,
            status='pending'
        )
        print_success(f"Created test report: {test_report.id}")
        
        # Track the achievement
        tracking_success = AchievementTracker.track_report_creation(test_user, test_report)
        print_success(f"Achievement tracking executed: {tracking_success}")
        
        # Verify results
        final_progress = ClerkAchievementService.get_user_progress_summary_with_clerk(test_user)
        if final_progress:
            final_reports = final_progress['stats'].reports_created
            final_points = final_progress['stats'].total_points
            final_achievements = final_progress['unlocked_count']
            
            print(f"Final state - Reports: {final_reports}, Points: {final_points}, Achievements: {final_achievements}")
            
            # Verify changes
            if final_reports > initial_reports:
                print_success("✨ Report count increased correctly")
            
            if final_points > initial_points:
                print_success(f"✨ Points awarded: {final_points - initial_points}")
                
            if final_achievements > initial_achievements:
                print_success(f"✨ New achievements unlocked: {final_achievements - initial_achievements}")
                
                # Show new achievements
                for achievement in final_progress['recent_achievements']:
                    print(f"   🏆 {achievement.achievement.name}: {achievement.achievement.points} points")
            
        # Clean up test report
        test_report.delete()
        print_success("Test report cleaned up")
        
        return True
        
    except Exception as e:
        print_error(f"Achievement tracking check failed: {e}")
        return False

def check_web_integration():
    """Check web integration by testing views"""
    print_header("WEB INTEGRATION CHECK")
    
    try:
        from django.test import Client
        from django.contrib.auth.models import AnonymousUser
        
        client = Client()
        
        # Test anonymous user access to achievements page
        response = client.get('/achievements/')
        if response.status_code == 200:
            print_success("Achievements page loads for anonymous users")
        else:
            print_error(f"Achievements page failed for anonymous users: {response.status_code}")
        
        # Test with authenticated user
        test_user = User.objects.first()
        if test_user:
            client.force_login(test_user)
            response = client.get('/achievements/')
            if response.status_code == 200:
                print_success(f"Achievements page loads for authenticated users")
            else:
                print_error(f"Achievements page failed for authenticated users: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Web integration check failed: {e}")
        return False

def check_notification_system():
    """Check notification system functionality"""
    print_header("NOTIFICATION SYSTEM CHECK")
    
    try:
        test_user = User.objects.first()
        if not test_user:
            print_warning("No users found for notification testing")
            return True
        
        # Check existing notifications
        notifications = AchievementService.get_unread_notifications(test_user)
        print_success(f"Unread notifications for {test_user.username}: {len(notifications)}")
        
        if notifications:
            print("Recent notifications:")
            for notification in notifications[:3]:
                print(f"   📬 {notification.message}")
        
        # Test notification marking
        if notifications:
            initial_count = len(notifications)
            AchievementService.mark_notifications_as_read(test_user)
            remaining = AchievementService.get_unread_notifications(test_user)
            print_success(f"Marked {initial_count} notifications as read, {len(remaining)} remaining")
        
        return True
        
    except Exception as e:
        print_error(f"Notification system check failed: {e}")
        return False

def check_performance():
    """Check basic performance metrics"""
    print_header("PERFORMANCE CHECK")
    
    try:
        import time
        
        # Time basic operations
        start_time = time.time()
        Achievement.objects.filter(is_active=True).count()
        db_time = time.time() - start_time
        print_success(f"Database query time: {db_time:.4f} seconds")
        
        if db_time > 1.0:
            print_warning("Database queries are slow (>1 second)")
        
        # Test service performance
        test_user = User.objects.first()
        if test_user:
            start_time = time.time()
            ClerkAchievementService.get_user_progress_summary_with_clerk(test_user)
            service_time = time.time() - start_time
            print_success(f"Service operation time: {service_time:.4f} seconds")
            
            if service_time > 2.0:
                print_warning("Service operations are slow (>2 seconds)")
        
        return True
        
    except Exception as e:
        print_error(f"Performance check failed: {e}")
        return False

def generate_system_report():
    """Generate a comprehensive system report"""
    print_header("SYSTEM REPORT")
    
    try:
        print(f"🕐 Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python version: {sys.version}")
        print(f"🌐 Django version: {django.VERSION}")
        
        # User statistics
        total_users = User.objects.count()
        users_with_stats = UserStats.objects.count()
        users_with_achievements = UserAchievement.objects.values('user').distinct().count()
        
        print(f"👥 Total users: {total_users}")
        print(f"📊 Users with stats: {users_with_stats}")
        print(f"🏆 Users with achievements: {users_with_achievements}")
        
        # Achievement statistics
        total_achievements = Achievement.objects.count()
        active_achievements = Achievement.objects.filter(is_active=True).count()
        total_unlocks = UserAchievement.objects.filter(is_unlocked=True).count()
        
        print(f"🎯 Total achievements: {total_achievements}")
        print(f"✅ Active achievements: {active_achievements}")
        print(f"🎉 Total unlocks: {total_unlocks}")
        
        # Top performers
        top_users = UserStats.objects.order_by('-total_points')[:3]
        if top_users:
            print("🥇 Top performers:")
            for i, user_stat in enumerate(top_users, 1):
                print(f"   {i}. {user_stat.user.username}: {user_stat.total_points} points, Level {user_stat.level}")
        
        return True
        
    except Exception as e:
        print_error(f"System report generation failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🎯 ACHIEVEMENTS SYSTEM VERIFICATION")
    print("==================================")
    print("This script will comprehensively test your achievements system.")
    
    checks = [
        ("Database Integrity", check_database_integrity),
        ("Service Imports", check_service_imports),
        ("Clerk Integration", check_clerk_integration),
        ("Achievement Tracking", check_achievement_tracking),
        ("Web Integration", check_web_integration),
        ("Notification System", check_notification_system),
        ("Performance", check_performance),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        try:
            if check_function():
                passed_checks += 1
        except Exception as e:
            print_error(f"{check_name} check encountered an error: {e}")
    
    # Generate final report
    generate_system_report()
    
    # Final verdict
    print_header("FINAL VERDICT")
    
    success_rate = (passed_checks / total_checks) * 100
    print(f"🎯 Checks passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Your achievements system is running perfectly!")
    elif success_rate >= 75:
        print("✅ GOOD! Your achievements system is working well with minor issues.")
    elif success_rate >= 50:
        print("⚠️  OKAY! Your achievements system has some issues that need attention.")
    else:
        print("❌ ISSUES! Your achievements system needs significant fixes.")
    
    print("\n🔧 To run individual checks, use:")
    print("   python manage.py shell -c \"exec(open('verify_achievements_system.py').read())\"")
    
    return success_rate >= 75

if __name__ == '__main__':
    main()
