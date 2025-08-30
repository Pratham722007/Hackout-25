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

def test_multiple_achievements():
    print('=== Testing Multiple Achievement Unlocks ===')
    
    try:
        # Get the test user
        user = User.objects.get(username='test_achiever')
        print(f'Using test user: {user.username}')
        
        # Get current progress
        progress = AchievementService.get_user_progress_summary(user)
        print(f'Current progress: {progress["stats"].reports_created} reports, {progress["unlocked_count"]} achievements')
        
        # Create 2 more reports to try to unlock "Getting Started" (3 reports)
        print('\\nCreating 2 more reports...')
        for i in range(2):
            report = Report.objects.create(
                title=f'Test Report {i+2}',
                description=f'Test report number {i+2}',
                report_type='pollution' if i % 2 == 0 else 'wildlife',
                severity='medium',
                latitude=Decimal('40.7128') + Decimal(str(i * 0.01)),
                longitude=Decimal('-74.0060') + Decimal(str(i * 0.01)),
                location_name=f'Test Location {i+2}',
                created_by=user,
                status='pending'
            )
            print(f'   Created report {i+2}: {report.title}')
            AchievementTracker.track_report_creation(user, report)
        
        # Check final progress
        print('\\nFinal progress check...')
        final_progress = AchievementService.get_user_progress_summary(user)
        print(f'Final: {final_progress["stats"].reports_created} reports created')
        print(f'Points: {final_progress["stats"].total_points}')
        print(f'Achievements unlocked: {final_progress["unlocked_count"]}/{final_progress["total_achievements"]}')
        print(f'Completion: {final_progress["completion_percentage"]}%')
        
        # Show all unlocked achievements
        print('\\n🏆 All unlocked achievements:')
        for achievement in final_progress["recent_achievements"]:
            print(f'   {achievement.achievement.icon} {achievement.achievement.name} - {achievement.achievement.points} points')
        
        # Test notifications
        notifications = AchievementService.get_unread_notifications(user)
        print(f'\\n📬 Unread notifications: {len(notifications)}')
        
        print('\\n✅ Multiple achievement test completed!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_multiple_achievements()
