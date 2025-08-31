from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Extended user profile for Clerk integration
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clerk_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Additional Clerk data
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    
    # Account status from Clerk
    is_banned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    # Timestamps from Clerk
    clerk_created_at = models.DateTimeField(null=True, blank=True)
    clerk_updated_at = models.DateTimeField(null=True, blank=True)
    last_sign_in_at = models.DateTimeField(null=True, blank=True)
    
    # Local timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = 'user_profiles'
