#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from achievements.views import achievements_dashboard
from achievements.services import AchievementService
from django.contrib.auth.models import User
from django.test import RequestFactory

# Create a request
factory = RequestFactory()
request = factory.get('/achievements/')

# Get the user
user = User.objects.get(username='surajshah')
request.user = user

print(f"Testing achievements dashboard for {user.username}")
print()

try:
    # Call the view directly
    response = achievements_dashboard(request)
    print(f"Response status: {response.status_code}")
    
    # Check if the view has context data
    if hasattr(response, 'context_data'):
        context = response.context_data
        print("Context keys:", list(context.keys()))
        
        if 'progress_summary' in context:
            progress = context['progress_summary']
            print(f"Progress summary found:")
            print(f"  - Level: {progress['stats'].level}")
            print(f"  - Points: {progress['stats'].total_points}")
            print(f"  - Achievements: {progress['unlocked_count']}/{progress['total_achievements']}")
            
        if 'achievements_by_category' in context:
            categories = context['achievements_by_category']
            print(f"Categories found: {len(categories)}")
            for cat_key, cat_data in categories.items():
                print(f"  - {cat_data['name']}: {len(cat_data['achievements'])} achievements")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("Testing AchievementService directly...")

try:
    progress_summary = AchievementService.get_user_progress_summary(user)
    if progress_summary:
        print("✅ AchievementService working correctly")
        print(f"  - Unlocked: {progress_summary['unlocked_count']}")
        print(f"  - Recent: {len(progress_summary['recent_achievements'])}")
    else:
        print("❌ AchievementService returned None")
except Exception as e:
    print(f"❌ AchievementService error: {e}")
    import traceback
    traceback.print_exc()
