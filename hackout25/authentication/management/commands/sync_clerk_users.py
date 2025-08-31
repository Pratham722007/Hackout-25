from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from authentication.models import UserProfile
from authentication.services.clerk_service import ClerkService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync users from Clerk to Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Sync a specific user by Clerk user ID',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Sync a specific user by email address',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing users even if they were recently synced',
        )

    def handle(self, *args, **options):
        self.clerk_service = ClerkService()
        self.dry_run = options['dry_run']
        self.force = options['force']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            if options['user_id']:
                self.sync_user_by_id(options['user_id'])
            elif options['email']:
                self.sync_user_by_email(options['email'])
            else:
                self.sync_all_users()
                
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise CommandError(f"Sync failed: {e}")

    def sync_user_by_id(self, clerk_user_id):
        """Sync a specific user by Clerk user ID"""
        self.stdout.write(f'Syncing user with Clerk ID: {clerk_user_id}')
        
        clerk_user = self.clerk_service.get_user_by_id(clerk_user_id)
        if not clerk_user:
            raise CommandError(f"User with ID {clerk_user_id} not found in Clerk")
        
        user_data = self.clerk_service.extract_user_data(clerk_user)
        created, updated = self.create_or_update_user(user_data)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created user: {user_data["email"]}'))
        elif updated:
            self.stdout.write(self.style.SUCCESS(f'Updated user: {user_data["email"]}'))
        else:
            self.stdout.write(f'No changes for user: {user_data["email"]}')

    def sync_user_by_email(self, email):
        """Sync a specific user by email"""
        self.stdout.write(f'Syncing user with email: {email}')
        
        clerk_user = self.clerk_service.get_user_by_email(email)
        if not clerk_user:
            raise CommandError(f"User with email {email} not found in Clerk")
        
        user_data = self.clerk_service.extract_user_data(clerk_user)
        created, updated = self.create_or_update_user(user_data)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created user: {email}'))
        elif updated:
            self.stdout.write(self.style.SUCCESS(f'Updated user: {email}'))
        else:
            self.stdout.write(f'No changes for user: {email}')

    def sync_all_users(self):
        """Sync all users from Clerk"""
        self.stdout.write('Fetching all users from Clerk...')
        
        clerk_users = self.clerk_service.fetch_all_users_paginated()
        if not clerk_users:
            self.stdout.write(self.style.WARNING('No users found in Clerk'))
            return
        
        self.stdout.write(f'Found {len(clerk_users)} users in Clerk')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for clerk_user in clerk_users:
            try:
                user_data = self.clerk_service.extract_user_data(clerk_user)
                created, updated = self.create_or_update_user(user_data)
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Created: {user_data["email"]}')
                elif updated:
                    updated_count += 1
                    self.stdout.write(f'Updated: {user_data["email"]}')
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error syncing user {clerk_user.get('id')}: {e}")
                self.stdout.write(
                    self.style.ERROR(f'Error syncing user {clerk_user.get("id")}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'Sync complete: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))

    def create_or_update_user(self, user_data):
        """Create or update a Django user and profile from Clerk data"""
        if self.dry_run:
            self.stdout.write(f'[DRY RUN] Would sync user: {user_data["email"]}')
            return False, False
        
        if not user_data['email']:
            logger.warning(f"Skipping user {user_data['clerk_id']} - no email address")
            return False, False
        
        created = False
        updated = False
        
        with transaction.atomic():
            # Try to find existing user profile by Clerk ID first
            user_profile = None
            if user_data['clerk_id']:
                try:
                    user_profile = UserProfile.objects.get(clerk_user_id=user_data['clerk_id'])
                except UserProfile.DoesNotExist:
                    pass
            
            # If not found by Clerk ID, try by email
            if not user_profile:
                try:
                    user = User.objects.get(email=user_data['email'])
                    user_profile, _ = UserProfile.objects.get_or_create(user=user)
                except User.DoesNotExist:
                    pass
            
            # Create new user if not found
            if not user_profile:
                # Generate username from email or use Clerk username
                username = user_data.get('username') or user_data['email'].split('@')[0]
                
                # Ensure username is unique
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
                created = True
            else:
                # Check if we should update (force or not recently synced)
                if not self.force and user_profile.last_synced_at:
                    # Skip if synced within last hour (you can adjust this)
                    time_diff = timezone.now() - user_profile.last_synced_at
                    if time_diff.total_seconds() < 3600:  # 1 hour
                        return False, False
            
            # Update user profile with Clerk data
            profile_updated = self.update_user_profile(user_profile, user_data)
            user_updated = self.update_django_user(user_profile.user, user_data)
            
            if profile_updated or user_updated:
                updated = True
                user_profile.last_synced_at = timezone.now()
                user_profile.save(update_fields=['last_synced_at'])
        
        return created, updated

    def update_django_user(self, user, user_data):
        """Update Django User model fields"""
        updated = False
        
        # Update basic fields
        if user.email != user_data.get('email', ''):
            user.email = user_data.get('email', '')
            updated = True
            
        if user.first_name != user_data.get('first_name', ''):
            user.first_name = user_data.get('first_name', '')
            updated = True
            
        if user.last_name != user_data.get('last_name', ''):
            user.last_name = user_data.get('last_name', '')
            updated = True
        
        # Update active status based on banned/locked status
        should_be_active = not (user_data.get('banned', False) or user_data.get('locked', False))
        if user.is_active != should_be_active:
            user.is_active = should_be_active
            updated = True
        
        if updated:
            user.save()
        
        return updated

    def update_user_profile(self, profile, user_data):
        """Update UserProfile model fields"""
        updated = False
        
        # Update Clerk ID
        if profile.clerk_user_id != user_data.get('clerk_id'):
            profile.clerk_user_id = user_data.get('clerk_id')
            updated = True
        
        # Update verification status
        if profile.email_verified != user_data.get('email_verified', False):
            profile.email_verified = user_data.get('email_verified', False)
            updated = True
            
        if profile.phone_verified != user_data.get('phone_verified', False):
            profile.phone_verified = user_data.get('phone_verified', False)
            updated = True
        
        # Update general verification (email verified)
        is_verified = user_data.get('email_verified', False)
        if profile.is_verified != is_verified:
            profile.is_verified = is_verified
            updated = True
        
        # Update additional fields
        if profile.phone_number != user_data.get('phone_number'):
            profile.phone_number = user_data.get('phone_number')
            updated = True
            
        if profile.profile_image_url != user_data.get('profile_image_url'):
            profile.profile_image_url = user_data.get('profile_image_url')
            updated = True
        
        # Update account status
        if profile.is_banned != user_data.get('banned', False):
            profile.is_banned = user_data.get('banned', False)
            updated = True
            
        if profile.is_locked != user_data.get('locked', False):
            profile.is_locked = user_data.get('locked', False)
            updated = True
        
        # Update timestamps
        if user_data.get('created_at'):
            clerk_created_at = self.parse_clerk_timestamp(user_data['created_at'])
            if profile.clerk_created_at != clerk_created_at:
                profile.clerk_created_at = clerk_created_at
                updated = True
        
        if user_data.get('updated_at'):
            clerk_updated_at = self.parse_clerk_timestamp(user_data['updated_at'])
            if profile.clerk_updated_at != clerk_updated_at:
                profile.clerk_updated_at = clerk_updated_at
                updated = True
                
        if user_data.get('last_sign_in_at'):
            last_sign_in_at = self.parse_clerk_timestamp(user_data['last_sign_in_at'])
            if profile.last_sign_in_at != last_sign_in_at:
                profile.last_sign_in_at = last_sign_in_at
                updated = True
        
        if updated:
            profile.save()
        
        return updated

    def parse_clerk_timestamp(self, timestamp):
        """Parse Clerk timestamp to Django datetime"""
        if not timestamp:
            return None
        
        try:
            # Clerk timestamps are in Unix milliseconds
            if isinstance(timestamp, int):
                return timezone.datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            elif isinstance(timestamp, str):
                # Try parsing as ISO format
                return timezone.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse timestamp {timestamp}: {e}")
            return None
