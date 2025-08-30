#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from django.contrib.auth.models import User
from heatmap.models import Report
from achievements.models import UserStats, UserAchievement
from achievements.services import AchievementService

# Get the user
user = User.objects.get(username='surajshah')

print(f"=== Testing New Report Creation for {user.username} ===")
print()

# Get current stats
stats_before = AchievementService.get_or_create_user_stats(user)
print(f"Before creating report:")
print(f"  - Reports Created: {stats_before.reports_created}")
print(f"  - Total Points: {stats_before.total_points}")
print(f"  - Achievements Unlocked: {stats_before.achievements_unlocked}")
print()

# Create a new test report
new_report = Report.objects.create(
    title="Test Achievement Report",
    description="This is a test report to verify the achievements system is working",
    report_type="air_pollution",
    severity="high",
    latitude=28.6139,  # New Delhi coordinates
    longitude=77.2090,
    location_name="New Delhi Test Location",
    reporter_name="Test Reporter",
    created_by=user
)

print(f"✅ Created new report: {new_report.title}")
print(f"   Report ID: {new_report.id}")
print(f"   Created by: {new_report.created_by.username if new_report.created_by else 'None'}")
print()

# The post_save signal should have triggered automatically
# Let's check the updated stats
stats_after = UserStats.objects.get(user=user)
print(f"After creating report:")
print(f"  - Reports Created: {stats_after.reports_created}")
print(f"  - Total Points: {stats_after.total_points}")
print(f"  - Achievements Unlocked: {stats_after.achievements_unlocked}")
print(f"  - High Severity Found: {stats_after.high_severity_found}")
print()

# Check if any new achievements were unlocked
unlocked_achievements = user.achievements.filter(is_unlocked=True).order_by('-unlocked_at')
print(f"🏆 Currently Unlocked Achievements ({unlocked_achievements.count()}):")
for ua in unlocked_achievements:
    print(f"  - {ua.achievement.icon} {ua.achievement.name} ({ua.achievement.tier})")
    if ua.unlocked_at:
        print(f"    Unlocked: {ua.unlocked_at}")
print()

# Check notifications
notifications = AchievementService.get_unread_notifications(user)
if notifications.exists():
    print(f"🔔 New Notifications ({notifications.count()}):")
    for notif in notifications:
        print(f"  - {notif.message}")
else:
    print("📭 No new notifications")

print()
print("=== Test Complete ===")
