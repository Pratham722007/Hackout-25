from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from heatmap.models import Report
from dashboard.models import EnvironmentalAnalysis
from achievements.services import AchievementService
import random


class Command(BaseCommand):
    help = 'Backfill user assignments for existing reports and trigger achievements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to assign all reports to (optional)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" does not exist')
                )
                return
        else:
            # Get or create a default user
            user, created = User.objects.get_or_create(
                username='default_user',
                defaults={
                    'email': 'default@example.com',
                    'first_name': 'Default',
                    'last_name': 'User'
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created default user: {user.username}')
                )

        # Get all reports without created_by
        reports_without_user = Report.objects.filter(created_by__isnull=True)
        analyses_without_user = EnvironmentalAnalysis.objects.filter(created_by__isnull=True)
        
        report_count = reports_without_user.count()
        analysis_count = analyses_without_user.count()
        total_count = report_count + analysis_count
        
        self.stdout.write(f'Found {report_count} reports and {analysis_count} analyses without assigned users')
        
        if total_count == 0:
            self.stdout.write('No reports or analyses to update')
            return
            
        # Assign all reports and analyses to the user
        if report_count > 0:
            reports_without_user.update(created_by=user)
            self.stdout.write(
                self.style.SUCCESS(f'Assigned {report_count} reports to user: {user.username}')
            )
            
        if analysis_count > 0:
            analyses_without_user.update(created_by=user)
            self.stdout.write(
                self.style.SUCCESS(f'Assigned {analysis_count} analyses to user: {user.username}')
            )
        
        # Trigger achievement checking for the user
        self.stdout.write('Triggering achievement calculations...')
        AchievementService.check_achievements_for_user(user)
        
        # Get user stats to see the results
        stats = AchievementService.get_or_create_user_stats(user)
        progress_summary = AchievementService.get_user_progress_summary(user)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Achievement processing complete!\n'
                f'User Stats:\n'
                f'  - Reports Created: {stats.reports_created}\n'
                f'  - Total Points: {stats.total_points}\n'
                f'  - Level: {stats.level}\n'
                f'  - Achievements Unlocked: {stats.achievements_unlocked}\n'
                f'  - Completion: {progress_summary["completion_percentage"]}%'
            )
        )
