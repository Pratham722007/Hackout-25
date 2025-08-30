from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from heatmap.models import Report
from achievements.services import AchievementService
from achievements.models import UserStats


class Command(BaseCommand):
    help = 'Recalculate user stats from existing reports and trigger achievements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to recalculate stats for (optional, default: all users)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" does not exist')
                )
                return
        else:
            users = User.objects.all()
            
        if not users:
            self.stdout.write('No users found')
            return

        for user in users:
            self.stdout.write(f'Processing user: {user.username}')
            
            # Get or create user stats
            stats = AchievementService.get_or_create_user_stats(user)
            
            # Get user's reports
            user_reports = Report.objects.filter(created_by=user)
            reports_count = user_reports.count()
            
            self.stdout.write(f'  Found {reports_count} reports for {user.username}')
            
            if reports_count == 0:
                continue
                
            # Reset stats to recalculate from scratch
            stats.reports_created = 0
            stats.reports_validated = 0
            stats.high_severity_found = 0
            stats.map_views = 0
            stats.locations_reported = []
            stats.report_types_used = []
            stats.total_points = 0
            stats.achievements_unlocked = 0
            stats.level = 1
            
            # Process each report
            for report in user_reports:
                stats.reports_created += 1
                
                # Add location variety
                if report.latitude and report.longitude:
                    stats.add_location(report.latitude, report.longitude)
                
                # Add report type variety
                if report.report_type:
                    stats.add_report_type(report.report_type)
                
                # Count high severity reports
                if report.severity in ['high', 'critical']:
                    stats.high_severity_found += 1
                    
            # Count validated reports
            validated_reports = Report.objects.filter(validated_by=user)
            stats.reports_validated = validated_reports.count()
            
            # Update streak (simplified - just set to 1 if they have reports)
            if reports_count > 0:
                stats.streak_current = 1
                stats.streak_best = 1
                
            stats.save()
            
            self.stdout.write(f'  Updated stats:')
            self.stdout.write(f'    - Reports Created: {stats.reports_created}')
            self.stdout.write(f'    - Reports Validated: {stats.reports_validated}')
            self.stdout.write(f'    - High Severity Found: {stats.high_severity_found}')
            self.stdout.write(f'    - Unique Locations: {len(stats.locations_reported)}')
            self.stdout.write(f'    - Report Types Used: {len(stats.report_types_used)}')
            
            # Now trigger achievement checking
            AchievementService.check_achievements_for_user(user)
            
            # Refresh stats to see the achievement results
            stats.refresh_from_db()
            progress_summary = AchievementService.get_user_progress_summary(user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Final Results:\n'
                    f'    - Total Points: {stats.total_points}\n'
                    f'    - Level: {stats.level}\n'
                    f'    - Achievements Unlocked: {stats.achievements_unlocked}\n'
                    f'    - Completion: {progress_summary["completion_percentage"]}%'
                )
            )
            
            # Show unlocked achievements
            unlocked_achievements = user.achievements.filter(is_unlocked=True)
            if unlocked_achievements.exists():
                self.stdout.write(f'  Unlocked Achievements:')
                for ua in unlocked_achievements:
                    self.stdout.write(f'    - {ua.achievement.name} ({ua.achievement.tier})')
            
        self.stdout.write(
            self.style.SUCCESS('User stats recalculation complete!')
        )
