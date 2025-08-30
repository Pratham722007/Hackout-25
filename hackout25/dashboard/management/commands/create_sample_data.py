from django.core.management.base import BaseCommand
from dashboard.models import EnvironmentalAnalysis
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create sample environmental analysis data'

    def handle(self, *args, **options):
        # Clear existing data
        EnvironmentalAnalysis.objects.all().delete()
        
        sample_data = [
            {
                'title': 'Vanishing Mangroves: Human Actions and Environmental Impact',
                'location': 'Amazon Rainforest',
                'risk_level': 'critical',
                'status': 'mixed',
                'confidence': 85
            },
            {
                'title': 'FEGTHREFGG',
                'location': 'GDSFSF',
                'risk_level': 'low',
                'status': 'unknown',
                'confidence': 0
            },
            {
                'title': 'Coral Reef Bleaching Assessment',
                'location': 'Great Barrier Reef, Australia',
                'risk_level': 'high',
                'status': 'completed',
                'confidence': 92
            },
            {
                'title': 'Illegal Deforestation Detection',
                'location': 'Congo Basin',
                'risk_level': 'critical',
                'status': 'flagged',
                'confidence': 78
            },
            {
                'title': 'Wildlife Conservation Survey',
                'location': 'Yellowstone National Park',
                'risk_level': 'low',
                'status': 'completed',
                'confidence': 95
            }
        ]
        
        for i, data in enumerate(sample_data):
            EnvironmentalAnalysis.objects.create(
                **data,
                created_at=timezone.now() - timedelta(days=i)
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(sample_data)} sample analyses')
        )
