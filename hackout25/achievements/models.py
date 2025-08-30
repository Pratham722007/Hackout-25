from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Achievement(models.Model):
    """
    Achievement definition model
    """
    
    CATEGORY_CHOICES = [
        ('reporter', '🌍 Environmental Reporter'),
        ('validator', '✅ Data Validator'),
        ('explorer', '🗺️ Map Explorer'),
        ('streak', '🔥 Consistency Master'),
        ('impact', '💚 Environmental Impact'),
        ('community', '👥 Community Builder'),
        ('expert', '🎓 Expert Analyst'),
        ('pioneer', '🚀 Platform Pioneer'),
    ]
    
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
        ('legendary', 'Legendary'),
    ]
    
    ACTION_TYPE_CHOICES = [
        ('report_count', 'Number of reports created'),
        ('validation_count', 'Number of reports validated'),
        ('streak_days', 'Consecutive days active'),
        ('map_usage', 'Times used heatmap'),
        ('high_severity', 'High severity reports found'),
        ('accuracy_score', 'Validation accuracy percentage'),
        ('location_variety', 'Different locations reported'),
        ('report_types', 'Different report types used'),
        ('quick_response', 'Reports validated within 24 hours'),
        ('community_help', 'Times helped other users'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    
    # Achievement Logic
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    target_value = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Visual Elements
    icon = models.CharField(max_length=10, default='🏆', help_text="Emoji icon for achievement")
    color = models.CharField(max_length=7, default='#16a085', help_text="Hex color code")
    
    # Rewards
    points = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    badge_unlocked = models.BooleanField(default=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Hidden until unlocked")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'tier', 'target_value']
        unique_together = ['name', 'tier']
        
    def __str__(self):
        return f"{self.get_tier_display()} {self.name}"
    
    def get_tier_color(self):
        colors = {
            'bronze': '#CD7F32',
            'silver': '#C0C0C0', 
            'gold': '#FFD700',
            'platinum': '#E5E4E2',
            'diamond': '#B9F2FF',
            'legendary': '#FF69B4'
        }
        return colors.get(self.tier, self.color)
    
    def get_category_display_with_emoji(self):
        return dict(self.CATEGORY_CHOICES)[self.category]


class UserAchievement(models.Model):
    """
    User's unlocked achievements
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    # Progress tracking
    current_progress = models.IntegerField(default=0)
    is_unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    notification_sent = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text="Show in user profile highlights")
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at', '-current_progress']
    
    def __str__(self):
        status = "🔓" if self.is_unlocked else "🔒"
        return f"{status} {self.user.username} - {self.achievement.name}"
    
    @property
    def progress_percentage(self):
        if self.achievement.target_value == 0:
            return 100
        return min(100, (self.current_progress / self.achievement.target_value) * 100)
    
    def unlock(self):
        """Unlock the achievement"""
        if not self.is_unlocked:
            self.is_unlocked = True
            self.unlocked_at = timezone.now()
            self.current_progress = self.achievement.target_value
            self.save()
            
            # Create notification
            AchievementNotification.objects.create(
                user=self.user,
                achievement=self.achievement,
                message=f"🎉 Achievement Unlocked: {self.achievement.name}!"
            )
            
            return True
        return False


class UserStats(models.Model):
    """
    User statistics for achievement tracking
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    
    # Reporting Stats
    reports_created = models.IntegerField(default=0)
    reports_validated = models.IntegerField(default=0)
    high_severity_found = models.IntegerField(default=0)
    
    # Engagement Stats
    map_views = models.IntegerField(default=0)
    streak_current = models.IntegerField(default=0)
    streak_best = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Quality Stats
    validation_accuracy = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    locations_reported = models.JSONField(default=list, help_text="List of unique location coordinates")
    report_types_used = models.JSONField(default=list, help_text="List of report types used")
    
    # Achievement Stats
    total_points = models.IntegerField(default=0)
    achievements_unlocked = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Social Stats
    helpful_validations = models.IntegerField(default=0)
    community_contributions = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} Stats - Level {self.level}"
    
    def update_level(self):
        """Update user level based on points"""
        # Level progression: 100 points per level, increasing by 50 each level
        points = self.total_points
        level = 1
        required_points = 100
        
        while points >= required_points:
            points -= required_points
            level += 1
            required_points += 50
            
        if self.level != level:
            self.level = level
            self.save()
            
    def add_location(self, latitude, longitude):
        """Add unique location to user's explored locations"""
        location = [float(latitude), float(longitude)]
        locations = self.locations_reported
        
        # Check if location is already recorded (within 0.01 degree tolerance)
        for existing in locations:
            if (abs(existing[0] - location[0]) < 0.01 and 
                abs(existing[1] - location[1]) < 0.01):
                return False
                
        locations.append(location)
        self.locations_reported = locations
        return True
    
    def add_report_type(self, report_type):
        """Add report type to user's variety"""
        types = self.report_types_used
        if report_type not in types:
            types.append(report_type)
            self.report_types_used = types
            return True
        return False
    
    def update_streak(self):
        """Update activity streak"""
        today = timezone.now().date()
        last_activity_date = self.last_activity.date() if self.last_activity else None
        
        if last_activity_date:
            if last_activity_date == today:
                # Same day, no change
                pass
            elif last_activity_date == today - timezone.timedelta(days=1):
                # Yesterday, increment streak
                self.streak_current += 1
                if self.streak_current > self.streak_best:
                    self.streak_best = self.streak_current
            else:
                # Gap in activity, reset streak
                self.streak_current = 1
        else:
            # First activity
            self.streak_current = 1
            
        self.last_activity = timezone.now()
        self.save()


class AchievementNotification(models.Model):
    """
    Achievement unlock notifications
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievement_notifications')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    is_displayed = models.BooleanField(default=False, help_text="Has popup been shown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Notification for {self.user.username}: {self.achievement.name}"


class Leaderboard(models.Model):
    """
    Leaderboard entries for different categories
    """
    LEADERBOARD_TYPES = [
        ('points', 'Total Points'),
        ('reports', 'Reports Created'),
        ('validations', 'Reports Validated'),
        ('streak', 'Best Streak'),
        ('achievements', 'Achievements Unlocked'),
    ]
    
    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    rank = models.IntegerField()
    
    # Metadata
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['leaderboard_type', 'user', 'period_start', 'period_end']
        ordering = ['leaderboard_type', 'rank']
        
    def __str__(self):
        return f"#{self.rank} {self.user.username} - {self.get_leaderboard_type_display()}: {self.score}"
