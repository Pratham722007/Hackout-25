from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from heatmap.models import Report


class Command(BaseCommand):
    help = 'Create sample environmental reports for heatmap testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of sample reports to create (default: 50)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Sample data for different locations in India
        locations = [
            {'name': 'Mumbai', 'lat': 19.0760, 'lng': 72.8777},
            {'name': 'Delhi', 'lat': 28.7041, 'lng': 77.1025},
            {'name': 'Bangalore', 'lat': 12.9716, 'lng': 77.5946},
            {'name': 'Chennai', 'lat': 13.0827, 'lng': 80.2707},
            {'name': 'Kolkata', 'lat': 22.5726, 'lng': 88.3639},
            {'name': 'Hyderabad', 'lat': 17.3850, 'lng': 78.4867},
            {'name': 'Pune', 'lat': 18.5204, 'lng': 73.8567},
            {'name': 'Ahmedabad', 'lat': 23.0225, 'lng': 72.5714},
            {'name': 'Surat', 'lat': 21.1702, 'lng': 72.8311},
            {'name': 'Jaipur', 'lat': 26.9124, 'lng': 75.7873},
        ]
        
        # Sample titles and descriptions for different report types
        sample_data = {
            'air_pollution': {
                'titles': [
                    'Heavy Air Pollution Detected',
                    'Smog Alert in Industrial Area',
                    'Unusual Air Quality Issues',
                    'Toxic Fumes from Factory'
                ],
                'descriptions': [
                    'Noticed thick smog and poor air quality in the area. Visibility is severely reduced.',
                    'Industrial emissions causing breathing difficulties for local residents.',
                    'Air quality has deteriorated significantly over the past week.',
                    'Strong chemical smell and visible pollution from nearby factory.'
                ]
            },
            'water_pollution': {
                'titles': [
                    'Water Contamination Report',
                    'River Pollution Observed',
                    'Industrial Waste in Water Body',
                    'Drinking Water Quality Issues'
                ],
                'descriptions': [
                    'Water body showing signs of contamination with unusual color and odor.',
                    'Industrial waste being discharged directly into the river.',
                    'Local water supply has become unsafe for consumption.',
                    'Fish mortality observed due to water pollution.'
                ]
            },
            'noise_pollution': {
                'titles': [
                    'Excessive Noise Levels',
                    'Construction Noise Complaint',
                    'Traffic Noise Disturbance',
                    'Industrial Noise Issue'
                ],
                'descriptions': [
                    'Continuous loud noise from construction activities affecting residents.',
                    'Traffic noise exceeding normal levels throughout the day.',
                    'Industrial machinery causing noise pollution in residential area.',
                    'Late night noise disturbances affecting sleep quality.'
                ]
            },
            'waste_management': {
                'titles': [
                    'Improper Waste Disposal',
                    'Garbage Accumulation',
                    'Hazardous Waste Issue',
                    'Illegal Dumping Site'
                ],
                'descriptions': [
                    'Large accumulation of garbage in public area with no proper disposal.',
                    'Hazardous waste materials improperly stored affecting local environment.',
                    'Illegal dumping of construction waste in natural habitat.',
                    'Overflowing waste bins attracting pests and causing health issues.'
                ]
            },
            'deforestation': {
                'titles': [
                    'Illegal Tree Cutting',
                    'Forest Area Cleared',
                    'Unauthorized Deforestation',
                    'Habitat Destruction'
                ],
                'descriptions': [
                    'Large number of trees cut down without proper authorization.',
                    'Forest area being cleared for commercial development.',
                    'Illegal logging activities observed in protected area.',
                    'Natural habitat being destroyed affecting local wildlife.'
                ]
            }
        }
        
        created_reports = []
        
        for i in range(count):
            # Random location with some variance
            base_location = random.choice(locations)
            lat_variance = random.uniform(-0.05, 0.05)  # ~5km variance
            lng_variance = random.uniform(-0.05, 0.05)
            
            latitude = Decimal(str(base_location['lat'] + lat_variance))
            longitude = Decimal(str(base_location['lng'] + lng_variance))
            
            # Random report type
            report_type = random.choice([key for key in sample_data.keys()])
            
            # Random title and description
            titles = sample_data[report_type]['titles']
            descriptions = sample_data[report_type]['descriptions']
            
            title = random.choice(titles)
            description = random.choice(descriptions)
            
            # Random severity and status
            severity = random.choice(['low', 'medium', 'high', 'critical'])
            status = random.choice(['pending', 'validated', 'rejected', 'under_review'])
            
            # Random date within last 60 days
            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            # Create report
            report = Report.objects.create(
                title=title,
                description=description,
                report_type=report_type,
                severity=severity,
                status=status,
                latitude=latitude,
                longitude=longitude,
                location_name=base_location['name'],
                address=f"Near {base_location['name']}, India",
                reporter_name=f"Reporter {i+1}",
                reporter_email=f"reporter{i+1}@example.com",
                created_at=created_at,
                confidence_score=random.uniform(0.6, 1.0),
                verified=random.choice([True, False])
            )
            
            created_reports.append(report)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_reports)} sample reports'
            )
        )
        
        # Print some statistics
        self.stdout.write(f'Reports by type:')
        for report_type, _ in Report.REPORT_TYPES:
            count = Report.objects.filter(report_type=report_type).count()
            self.stdout.write(f'  {report_type}: {count}')
        
        self.stdout.write(f'Reports by severity:')
        for severity, _ in Report.SEVERITY_CHOICES:
            count = Report.objects.filter(severity=severity).count()
            self.stdout.write(f'  {severity}: {count}')
        
        self.stdout.write(f'Reports by status:')
        for status, _ in Report.STATUS_CHOICES:
            count = Report.objects.filter(status=status).count()
            self.stdout.write(f'  {status}: {count}')
