#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from achievements.models import UserAchievement, Achievement
from django.contrib.auth.models import User

# Get the user
user = User.objects.get(username='surajshah')

print(f"=== Achievement Status for {user.username} ===")
print()

# Get all achievements for the user
achievements = user.achievements.all().select_related('achievement')
print(f"Total UserAchievements: {achievements.count()}")

unlocked = achievements.filter(is_unlocked=True)
print(f"Unlocked: {unlocked.count()}")
print()

if unlocked.exists():
    print("🏆 Unlocked Achievements:")
    for ua in unlocked:
        print(f"  - {ua.achievement.icon} {ua.achievement.name} ({ua.achievement.tier})")
        print(f"    Progress: {ua.current_progress}/{ua.achievement.target_value}")
        print(f"    Points: {ua.achievement.points}")
        print(f"    Unlocked: {ua.unlocked_at}")
        print()

locked = achievements.filter(is_unlocked=False)
if locked.exists():
    print("🔒 Locked Achievements (showing progress):")
    for ua in locked[:5]:  # Show first 5
        print(f"  - {ua.achievement.icon} {ua.achievement.name} ({ua.achievement.tier})")
        print(f"    Progress: {ua.current_progress}/{ua.achievement.target_value} ({ua.progress_percentage:.1f}%)")
        print()

# Check categories
print("=== Achievements by Category ===")
categories = Achievement.CATEGORY_CHOICES
for category_key, category_name in categories:
    user_achievements = achievements.filter(achievement__category=category_key)
    if user_achievements.exists():
        unlocked_in_category = user_achievements.filter(is_unlocked=True).count()
        total_in_category = user_achievements.count()
        print(f"{category_name}: {unlocked_in_category}/{total_in_category} unlocked")
