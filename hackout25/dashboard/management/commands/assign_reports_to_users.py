from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import EnvironmentalAnalysis
import random


class Command(BaseCommand):
    help = 'Assign existing reports without users to random users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create test users if none exist',
        )

    def handle(self, *args, **options):
        # Check if we need to create test users
        users = User.objects.all()
        if not users.exists():
            if options['create_test_users']:
                self.stdout.write('Creating test users...')
                test_users = [
                    ('admin', 'admin@ecovalidate.com', 'Admin User'),
                    ('testuser1', 'user1@ecovalidate.com', 'Test User 1'),
                    ('testuser2', 'user2@ecovalidate.com', 'Test User 2'),
                    ('testuser3', 'user3@ecovalidate.com', 'Test User 3'),
                ]
                
                for username, email, full_name in test_users:
                    if not User.objects.filter(username=username).exists():
                        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password='testpass123',
                            first_name=first_name,
                            last_name=last_name
                        )
                        self.stdout.write(f'Created user: {username}')
                
                users = User.objects.all()
            else:
                self.stdout.write(self.style.ERROR(
                    'No users found! Run with --create-test-users to create some test users.'
                ))
                return

        # Get reports without users
        reports_without_users = EnvironmentalAnalysis.objects.filter(created_by__isnull=True)
        count = reports_without_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All reports already have users assigned!'))
            return

        self.stdout.write(f'Found {count} reports without users assigned.')
        
        # Convert users to list for random selection
        user_list = list(users)
        
        updated_count = 0
        for report in reports_without_users:
            # Assign a random user to this report
            random_user = random.choice(user_list)
            report.created_by = random_user
            report.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully assigned {updated_count} reports to users!'
            )
        )

        # Show summary
        self.stdout.write('\n--- Summary ---')
        for user in users:
            user_report_count = EnvironmentalAnalysis.objects.filter(created_by=user).count()
            self.stdout.write(f'{user.username}: {user_report_count} reports')
