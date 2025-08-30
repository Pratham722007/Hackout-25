#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from achievements.services import AchievementService
from achievements.services import AchievementTracker
from django.contrib.auth.models import User
from heatmap.models import Report
from decimal import Decimal

def test_report_achievement():
    print('=== Testing Report Creation and Achievement Tracking ===')
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_achiever',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print(f'Created new test user: {user.username}')
        else:
            print(f'Using existing test user: {user.username}')
        
        # Get initial progress
        print('\n1. Initial progress check...')
        initial_progress = AchievementService.get_user_progress_summary(user)
        if initial_progress:
            print(f'   Initial: {initial_progress["unlocked_count"]} achievements unlocked')
            print(f'   Points: {initial_progress["stats"].total_points}')
            print(f'   Reports created: {initial_progress["stats"].reports_created}')
        
        # Create a test report
        print('\n2. Creating test report...')
        report = Report.objects.create(
            title='Test Environmental Report',
            description='This is a test report for achievement tracking',
            report_type='pollution',
            severity='high',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            location_name='New York, NY',
            address='Test Address',
            created_by=user,
            status='pending'
        )
        print(f'   Created report: {report.id} - {report.title}')
        
        # Track the achievement
        print('\n3. Tracking achievement...')
        AchievementTracker.track_report_creation(user, report)
        print('   Achievement tracking completed')
        
        # Get updated progress
        print('\n4. Updated progress check...')
        updated_progress = AchievementService.get_user_progress_summary(user)
        if updated_progress:
            print(f'   Updated: {updated_progress["unlocked_count"]} achievements unlocked')
            print(f'   Points: {updated_progress["stats"].total_points}')
            print(f'   Reports created: {updated_progress["stats"].reports_created}')
            
            # Show new achievements
            if updated_progress["unlocked_count"] > initial_progress["unlocked_count"]:
                print('\n   🎉 NEW ACHIEVEMENTS UNLOCKED! 🎉')
                recent = updated_progress["recent_achievements"]
                for achievement in recent:
                    print(f'   {achievement.achievement.icon} {achievement.achievement.name}: {achievement.achievement.description}')
            else:
                print('   No new achievements unlocked (may need more reports)')
        
        # Get notifications
        print('\n5. Checking notifications...')
        notifications = AchievementService.get_unread_notifications(user)
        if notifications:
            print(f'   {len(notifications)} unread notifications:')
            for notification in notifications:
                print(f'   - {notification.message}')
        else:
            print('   No unread notifications')
        
        print('\n✅ Test completed successfully!')
        
    except Exception as e:
        print(f'❌ Error during testing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_report_achievement()
