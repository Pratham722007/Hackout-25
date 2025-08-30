#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from achievements.services import AchievementService
from django.contrib.auth.models import User

def test_achievements():
    print('=== Testing Achievements System ===')
    
    try:
        print('1. Creating default achievements...')
        count = AchievementService.create_default_achievements()
        print(f'   Created {count} achievements')

        print('2. Finding test user...')
        user = User.objects.first()
        if user:
            print(f'   Using user: {user.username}')
            
            print('3. Setting up user stats...')
            stats = AchievementService.get_or_create_user_stats(user)
            print(f'   User stats: Level {stats.level}, Points: {stats.total_points}')
            
            print('4. Getting user progress...')
            progress = AchievementService.get_user_progress_summary(user)
            if progress:
                print(f'   Progress: {progress["completion_percentage"]}% complete, {progress["unlocked_count"]}/{progress["total_achievements"]} achievements')
            
            print('5. Testing achievement check...')
            AchievementService.check_achievements_for_user(user)
            print('   Achievement check completed')
            
            print('Test completed successfully!')
        else:
            print('   No users found - need to create a test user first')
            
    except Exception as e:
        print(f'Error during testing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_achievements()
