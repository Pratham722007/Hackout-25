# Achievements services package
from ..services import AchievementService
from .clerk_achievements import ClerkAchievementService

# For backward compatibility
def get_achievement_service():
    return AchievementService

def get_clerk_achievement_service():
    return ClerkAchievementService

__all__ = ['AchievementService', 'ClerkAchievementService', 'get_achievement_service', 'get_clerk_achievement_service']
