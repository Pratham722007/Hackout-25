from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from achievements.services import AchievementService


class Command(BaseCommand):
    help = 'Set up the achievements system with default achievements and user stats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-achievements',
            action='store_true',
            help='Create default achievements',
        )
        parser.add_argument(
            '--setup-users',
            action='store_true',
            help='Set up user stats for existing users',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all setup tasks',
        )

    def handle(self, *args, **options):
        if options['all']:
            options['create_achievements'] = True
            options['setup_users'] = True

        if options['create_achievements']:
            self.stdout.write('Creating default achievements...')
            created_count = AchievementService.create_default_achievements()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} achievements')
            )

        if options['setup_users']:
            self.stdout.write('Setting up user stats...')
            users = User.objects.all()
            created_stats = 0
            
            for user in users:
                stats = AchievementService.get_or_create_user_stats(user)
                if stats:
                    created_stats += 1
                    # Check achievements for existing users
                    AchievementService.check_achievements_for_user(user)

            self.stdout.write(
                self.style.SUCCESS(f'Successfully set up stats for {created_stats} users')
            )

        if not options['create_achievements'] and not options['setup_users']:
            self.stdout.write(
                self.style.WARNING(
                    'No action specified. Use --create-achievements, --setup-users, or --all'
                )
            )
