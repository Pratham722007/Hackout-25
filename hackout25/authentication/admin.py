from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import UserProfile
from .services.clerk_service import ClerkService
import logging

logger = logging.getLogger(__name__)

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = (
        'clerk_user_id', 'last_synced_at', 'clerk_created_at', 
        'clerk_updated_at', 'created_at', 'updated_at'
    )
    fieldsets = (
        ('Clerk Integration', {
            'fields': ('clerk_user_id', 'last_synced_at')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'email_verified', 'phone_verified')
        }),
        ('Additional Information', {
            'fields': ('phone_number', 'profile_image_url')
        }),
        ('Account Status', {
            'fields': ('is_banned', 'is_locked')
        }),
        ('Timestamps', {
            'fields': ('clerk_created_at', 'clerk_updated_at', 'last_sign_in_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Extended User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified_display', 'clerk_id_display', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__is_verified', 'userprofile__email_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'userprofile__clerk_user_id')
    actions = ['sync_selected_users_from_clerk', 'sync_all_users_from_clerk']
    
    def is_verified_display(self, obj):
        """Display verification status with icon"""
        try:
            profile = obj.userprofile
            if profile.is_verified:
                return format_html('<span style="color: green;">✓ Verified</span>')
            else:
                return format_html('<span style="color: red;">✗ Unverified</span>')
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: gray;">No Profile</span>')
    is_verified_display.short_description = 'Verified'
    
    def clerk_id_display(self, obj):
        """Display Clerk ID with link to sync"""
        try:
            profile = obj.userprofile
            if profile.clerk_user_id:
                return format_html(
                    '<code>{}</code>',
                    profile.clerk_user_id[:20] + '...' if len(profile.clerk_user_id) > 20 else profile.clerk_user_id
                )
            else:
                return format_html('<span style="color: gray;">Not linked</span>')
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: gray;">No Profile</span>')
    clerk_id_display.short_description = 'Clerk ID'
    
    def sync_selected_users_from_clerk(self, request, queryset):
        """Admin action to sync selected users from Clerk"""
        clerk_service = ClerkService()
        success_count = 0
        error_count = 0
        
        for user in queryset:
            try:
                # Try to get user profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Fetch from Clerk by email or Clerk ID
                clerk_user = None
                if profile.clerk_user_id:
                    clerk_user = clerk_service.get_user_by_id(profile.clerk_user_id)
                else:
                    clerk_user = clerk_service.get_user_by_email(user.email)
                
                if clerk_user:
                    user_data = clerk_service.extract_user_data(clerk_user)
                    
                    # Update user
                    user.first_name = user_data.get('first_name', '')
                    user.last_name = user_data.get('last_name', '')
                    user.is_active = not (user_data.get('banned', False) or user_data.get('locked', False))
                    user.save()
                    
                    # Update profile
                    profile.clerk_user_id = user_data.get('clerk_id')
                    profile.email_verified = user_data.get('email_verified', False)
                    profile.phone_verified = user_data.get('phone_verified', False)
                    profile.is_verified = user_data.get('email_verified', False)
                    profile.phone_number = user_data.get('phone_number')
                    profile.profile_image_url = user_data.get('profile_image_url')
                    profile.is_banned = user_data.get('banned', False)
                    profile.is_locked = user_data.get('locked', False)
                    profile.last_synced_at = timezone.now()
                    profile.save()
                    
                    success_count += 1
                else:
                    error_count += 1
                    logger.warning(f"User {user.email} not found in Clerk")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error syncing user {user.username}: {e}")
        
        if success_count > 0:
            messages.success(request, f'Successfully synced {success_count} user(s) from Clerk')
        if error_count > 0:
            messages.error(request, f'Failed to sync {error_count} user(s)')
    
    sync_selected_users_from_clerk.short_description = "Sync selected users from Clerk"
    
    def sync_all_users_from_clerk(self, request, queryset):
        """Admin action to sync all users from Clerk"""
        clerk_service = ClerkService()
        
        try:
            clerk_users = clerk_service.fetch_all_users_paginated()
            
            created_count = 0
            updated_count = 0
            
            for clerk_user in clerk_users:
                try:
                    user_data = clerk_service.extract_user_data(clerk_user)
                    
                    if not user_data['email']:
                        continue
                    
                    # Try to find existing user
                    user_profile = None
                    if user_data['clerk_id']:
                        try:
                            user_profile = UserProfile.objects.get(clerk_user_id=user_data['clerk_id'])
                        except UserProfile.DoesNotExist:
                            pass
                    
                    if not user_profile:
                        try:
                            user = User.objects.get(email=user_data['email'])
                            user_profile, _ = UserProfile.objects.get_or_create(user=user)
                        except User.DoesNotExist:
                            pass
                    
                    if not user_profile:
                        # Create new user
                        username = user_data.get('username') or user_data['email'].split('@')[0]
                        base_username = username
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}_{counter}"
                            counter += 1
                        
                        user = User.objects.create(
                            username=username,
                            email=user_data['email'],
                            first_name=user_data.get('first_name', ''),
                            last_name=user_data.get('last_name', ''),
                            is_active=not user_data.get('banned', False)
                        )
                        
                        user_profile = UserProfile.objects.create(user=user)
                        created_count += 1
                    else:
                        updated_count += 1
                    
                    # Update profile with Clerk data
                    user_profile.clerk_user_id = user_data.get('clerk_id')
                    user_profile.email_verified = user_data.get('email_verified', False)
                    user_profile.phone_verified = user_data.get('phone_verified', False)
                    user_profile.is_verified = user_data.get('email_verified', False)
                    user_profile.phone_number = user_data.get('phone_number')
                    user_profile.profile_image_url = user_data.get('profile_image_url')
                    user_profile.is_banned = user_data.get('banned', False)
                    user_profile.is_locked = user_data.get('locked', False)
                    user_profile.last_synced_at = timezone.now()
                    user_profile.save()
                    
                except Exception as e:
                    logger.error(f"Error syncing user {clerk_user.get('id')}: {e}")
            
            messages.success(
                request, 
                f'Sync completed: {created_count} users created, {updated_count} users updated'
            )
            
        except Exception as e:
            logger.error(f"Error during bulk sync: {e}")
            messages.error(request, f'Sync failed: {e}')
    
    sync_all_users_from_clerk.short_description = "Sync all users from Clerk"

# UserProfile admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'clerk_user_id_short', 'email_verified', 'phone_verified', 
        'is_banned', 'is_locked', 'last_sign_in_at', 'last_synced_at'
    )
    list_filter = (
        'is_verified', 'email_verified', 'phone_verified', 
        'is_banned', 'is_locked', 'created_at'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name', 
        'clerk_user_id', 'phone_number'
    )
    readonly_fields = (
        'created_at', 'updated_at', 'last_synced_at', 'clerk_created_at', 'clerk_updated_at'
    )
    actions = ['sync_selected_profiles_from_clerk']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Clerk Integration', {
            'fields': ('clerk_user_id', 'last_synced_at')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'email_verified', 'phone_verified')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'profile_image_url')
        }),
        ('Account Status', {
            'fields': ('is_banned', 'is_locked')
        }),
        ('Timestamps', {
            'fields': (
                'clerk_created_at', 'clerk_updated_at', 'last_sign_in_at',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        """Display user with link to user admin"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{} ({})</a>',
            user_url,
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_display.short_description = 'User'
    
    def clerk_user_id_short(self, obj):
        """Display shortened Clerk user ID"""
        if obj.clerk_user_id:
            return format_html(
                '<code title="{}">{}</code>',
                obj.clerk_user_id,
                obj.clerk_user_id[:15] + '...' if len(obj.clerk_user_id) > 15 else obj.clerk_user_id
            )
        return format_html('<span style="color: gray;">Not linked</span>')
    clerk_user_id_short.short_description = 'Clerk ID'
    
    def sync_selected_profiles_from_clerk(self, request, queryset):
        """Admin action to sync selected user profiles from Clerk"""
        clerk_service = ClerkService()
        success_count = 0
        error_count = 0
        
        for profile in queryset:
            try:
                # Fetch from Clerk by Clerk ID or email
                clerk_user = None
                if profile.clerk_user_id:
                    clerk_user = clerk_service.get_user_by_id(profile.clerk_user_id)
                else:
                    clerk_user = clerk_service.get_user_by_email(profile.user.email)
                
                if clerk_user:
                    user_data = clerk_service.extract_user_data(clerk_user)
                    
                    # Update Django user
                    user = profile.user
                    user.first_name = user_data.get('first_name', '')
                    user.last_name = user_data.get('last_name', '')
                    user.is_active = not (user_data.get('banned', False) or user_data.get('locked', False))
                    user.save()
                    
                    # Update profile
                    profile.clerk_user_id = user_data.get('clerk_id')
                    profile.email_verified = user_data.get('email_verified', False)
                    profile.phone_verified = user_data.get('phone_verified', False)
                    profile.is_verified = user_data.get('email_verified', False)
                    profile.phone_number = user_data.get('phone_number')
                    profile.profile_image_url = user_data.get('profile_image_url')
                    profile.is_banned = user_data.get('banned', False)
                    profile.is_locked = user_data.get('locked', False)
                    profile.last_synced_at = timezone.now()
                    profile.save()
                    
                    success_count += 1
                else:
                    error_count += 1
                    logger.warning(f"User {profile.user.email} not found in Clerk")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error syncing profile {profile.id}: {e}")
        
        if success_count > 0:
            messages.success(request, f'Successfully synced {success_count} profile(s) from Clerk')
        if error_count > 0:
            messages.error(request, f'Failed to sync {error_count} profile(s)')
    
    sync_selected_profiles_from_clerk.short_description = "Sync selected profiles from Clerk"

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
