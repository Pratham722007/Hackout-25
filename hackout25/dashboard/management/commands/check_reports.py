from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import EnvironmentalAnalysis


class Command(BaseCommand):
    help = 'Check the status of reports and user assignments'

    def handle(self, *args, **options):
        # Get report statistics
        total_reports = EnvironmentalAnalysis.objects.count()
        reports_with_users = EnvironmentalAnalysis.objects.filter(created_by__isnull=False).count()
        reports_without_users = EnvironmentalAnalysis.objects.filter(created_by__isnull=True).count()
        
        self.stdout.write(f'Total reports: {total_reports}')
        self.stdout.write(f'Reports with users: {reports_with_users}')
        self.stdout.write(f'Reports without users: {reports_without_users}')
        
        # Show recent reports
        self.stdout.write('\nRecent reports:')
        recent_reports = EnvironmentalAnalysis.objects.select_related('created_by').order_by('-created_at')[:5]
        
        for report in recent_reports:
            user_info = report.created_by.username if report.created_by else 'None'
            self.stdout.write(f'  - ID: {report.id}, Title: {report.title[:30]}..., User: {user_info}, Created: {report.created_at}')
        
        # Show user statistics
        self.stdout.write(f'\nTotal users: {User.objects.count()}')
        for user in User.objects.all():
            user_report_count = EnvironmentalAnalysis.objects.filter(created_by=user).count()
            self.stdout.write(f'  - {user.username}: {user_report_count} reports')
