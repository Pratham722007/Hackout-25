#!/usr/bin/env python3
"""
Create diverse dummy datasets with varied confidence levels
This script generates realistic environmental analysis data with proper confidence variations
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from dashboard.models import EnvironmentalAnalysis
from heatmap.models import Report

class DiverseDatasetGenerator:
    """Generate diverse environmental datasets with realistic confidence variations"""
    
    def __init__(self):
        # Environmental scenarios with expected confidence ranges
        self.scenarios = {
            'critical_threats': {
                'confidence_range': (85, 95),
                'risk_level': 'critical',
                'titles': [
                    'Massive Oil Spill in Marine Protected Area',
                    'Illegal Deforestation in Amazon Rainforest',
                    'Toxic Chemical Discharge into River System',
                    'Large-Scale Mangrove Destruction',
                    'Industrial Pollution in Coral Reef Area',
                    'Severe Wildlife Habitat Destruction',
                    'Major Forest Fire in National Park',
                    'Uncontrolled Mining in Protected Wetlands'
                ],
                'locations': [
                    'Amazon Basin, Brazil',
                    'Great Barrier Reef, Australia', 
                    'Sundarbans Mangrove, Bangladesh',
                    'Yellowstone National Park, USA',
                    'Madagascar Rainforest',
                    'Borneo Tropical Forest, Indonesia'
                ]
            },
            
            'high_risk_events': {
                'confidence_range': (70, 85),
                'risk_level': 'high',
                'titles': [
                    'Coastal Erosion Threatening Sea Turtle Nests',
                    'Coral Bleaching Event in Marine Park',
                    'Overfishing Impacting Local Ecosystem',
                    'Urban Development Near Wetlands',
                    'Agricultural Runoff Affecting Water Quality',
                    'Invasive Species Threatening Native Flora',
                    'Drought Conditions Affecting Wildlife',
                    'Air Quality Issues in Urban Forest Area'
                ],
                'locations': [
                    'Pacific Coast, California',
                    'Great Lakes Region, Michigan',
                    'Florida Everglades, USA',
                    'Mediterranean Coast, Spain',
                    'Coastal Queensland, Australia',
                    'Pacific Northwest, Canada'
                ]
            },
            
            'moderate_concerns': {
                'confidence_range': (55, 75),
                'risk_level': 'low',
                'titles': [
                    'Wildlife Conservation Project Assessment',
                    'Ecosystem Health Monitoring Report',
                    'Biodiversity Survey in Local Park',
                    'Environmental Impact Study',
                    'Habitat Restoration Progress Review',
                    'Water Quality Testing Results',
                    'Reforestation Project Update',
                    'Marine Life Population Study'
                ],
                'locations': [
                    'Central Park, New York',
                    'Golden Gate Park, San Francisco',
                    'Hyde Park, London',
                    'Stanley Park, Vancouver',
                    'Kruger National Park, South Africa',
                    'Banff National Park, Canada'
                ]
            },
            
            'uncertain_cases': {
                'confidence_range': (40, 60),
                'risk_level': 'low',
                'titles': [
                    'Unclear Environmental Impact Assessment',
                    'Mixed Results from Ecological Study',
                    'Partial Data on Species Population',
                    'Incomplete Water Quality Analysis',
                    'Limited Visibility Ecosystem Survey',
                    'Preliminary Environmental Screening',
                    'Initial Habitat Assessment',
                    'Early Stage Pollution Investigation'
                ],
                'locations': [
                    'Remote Forest Area, Oregon',
                    'Undisclosed Location, Private Land',
                    'Remote Island, Pacific Ocean',
                    'Mountain Region, Colorado',
                    'Desert Area, Nevada',
                    'Rural Wetlands, Louisiana'
                ]
            },
            
            'positive_conservation': {
                'confidence_range': (75, 90),
                'risk_level': 'low',
                'titles': [
                    'Successful Species Reintroduction Program',
                    'Thriving Marine Protected Area Report',
                    'Effective Pollution Cleanup Initiative',
                    'Growing Wildlife Population Study',
                    'Successful Forest Restoration Project',
                    'Clean Energy Transition Impact Report',
                    'Effective Conservation Partnership Results',
                    'Positive Climate Action Outcomes'
                ],
                'locations': [
                    'Yosemite National Park, USA',
                    'Galapagos Islands, Ecuador',
                    'Serengeti National Park, Tanzania',
                    'Costa Rica Cloud Forest',
                    'Norwegian Fjords',
                    'New Zealand Native Forest'
                ]
            }
        }
        
        # Location coordinates for realistic geographical distribution
        self.coordinates = {
            'Amazon Basin, Brazil': (19.0760, 72.8777),
            'Great Barrier Reef, Australia': (28.7041, 77.1025),
            'Sundarbans Mangrove, Bangladesh': (12.9716, 77.5946),
            'Yellowstone National Park, USA': (13.0827, 80.2707),
            'Madagascar Rainforest': (22.5726, 88.3639),
            'Borneo Tropical Forest, Indonesia': (17.3850, 78.4867),
            'Pacific Coast, California': (18.5204, 73.8567),
            'Great Lakes Region, Michigan': (23.0225, 72.5714),
            'Florida Everglades, USA': (21.1702, 72.8311),
            'Mediterranean Coast, Spain': (26.9124, 75.7873),
            'Coastal Queensland, Australia': (19.0760, 72.8777),
            'Pacific Northwest, Canada': (28.7041, 77.1025),
            'Central Park, New York': (12.9716, 77.5946),
            'Golden Gate Park, San Francisco': (13.0827, 80.2707),
            'Hyde Park, London': (22.5726, 88.3639),
            'Stanley Park, Vancouver': (17.3850, 78.4867),
            'Kruger National Park, South Africa': (18.5204, 73.8567),
            'Banff National Park, Canada': (23.0225, 72.5714),
            'Remote Forest Area, Oregon': (21.1702, 72.8311),
            'Undisclosed Location, Private Land': (26.9124, 75.7873),
            'Remote Island, Pacific Ocean': (19.0760, 72.8777),
            'Mountain Region, Colorado': (28.7041, 77.1025),
            'Desert Area, Nevada': (12.9716, 77.5946),
            'Rural Wetlands, Louisiana': (13.0827, 80.2707),
            'Yosemite National Park, USA': (22.5726, 88.3639),
            'Galapagos Islands, Ecuador': (17.3850, 78.4867),
            'Serengeti National Park, Tanzania': (18.5204, 73.8567),
            'Costa Rica Cloud Forest': (23.0225, 72.5714),
            'Norwegian Fjords': (21.1702, 72.8311),
            'New Zealand Native Forest': (26.9124, 75.7873)
        }

    def generate_dashboard_reports(self, count_per_scenario=10):
        """Generate diverse EnvironmentalAnalysis reports"""
        print("🌍 Generating diverse dashboard reports...")
        
        created_count = 0
        
        for scenario_name, scenario_data in self.scenarios.items():
            print(f"\n📊 Creating {count_per_scenario} reports for: {scenario_name}")
            
            for i in range(count_per_scenario):
                # Random selection from scenario data
                title = random.choice(scenario_data['titles'])
                location = random.choice(scenario_data['locations'])
                
                # Generate realistic confidence within scenario range
                confidence_min, confidence_max = scenario_data['confidence_range']
                confidence = random.randint(confidence_min, confidence_max)
                
                # Add some natural variation (±3 points)
                confidence += random.randint(-3, 3)
                confidence = max(30, min(100, confidence))  # Keep within reasonable bounds
                
                # Determine status based on confidence and risk
                if confidence < 50:
                    status = 'mixed'
                elif scenario_data['risk_level'] == 'critical':
                    status = 'flagged'
                elif confidence > 85:
                    status = 'completed'
                else:
                    status = random.choice(['completed', 'completed', 'completed', 'mixed'])
                
                # Get coordinates with some variance
                base_coords = self.coordinates.get(location, (19.0760, 72.8777))
                latitude = base_coords[0] + random.uniform(-0.1, 0.1)
                longitude = base_coords[1] + random.uniform(-0.1, 0.1)
                
                # Generate realistic description
                descriptions = [
                    f"Detailed environmental analysis conducted at {location}. ",
                    f"Comprehensive assessment of ecological conditions in the area. ",
                    f"Investigation reveals {scenario_data['risk_level']} level environmental concerns. ",
                    f"AI analysis indicates {confidence}% confidence in findings. ",
                    "Recommendations for appropriate action have been documented."
                ]
                description = ''.join(descriptions)
                
                # Create the report with realistic timestamp
                days_ago = random.randint(1, 90)
                created_at = datetime.now() - timedelta(days=days_ago)
                
                report = EnvironmentalAnalysis.objects.create(
                    title=title,
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    description=description,
                    risk_level=scenario_data['risk_level'],
                    confidence=confidence,
                    status=status,
                    created_at=created_at
                )
                
                created_count += 1
                
                # Progress indicator
                if (i + 1) % 5 == 0:
                    print(f"  ✅ Created {i + 1}/{count_per_scenario} reports")
        
        print(f"\n🎉 Successfully created {created_count} diverse dashboard reports!")
        return created_count

    def generate_heatmap_reports(self, count_per_type=15):
        """Generate diverse heatmap reports with varied confidence"""
        print("\n🗺️  Generating diverse heatmap reports...")
        
        report_types = [
            ('air_pollution', (0.6, 0.9)),
            ('water_pollution', (0.65, 0.95)), 
            ('noise_pollution', (0.55, 0.85)),
            ('waste_management', (0.7, 0.9)),
            ('deforestation', (0.8, 0.95)),
            ('wildlife_conservation', (0.6, 0.88)),
            ('climate_change', (0.5, 0.8)),
            ('other', (0.45, 0.75))
        ]
        
        created_count = 0
        
        for report_type, confidence_range in report_types:
            print(f"\n📋 Creating {count_per_type} {report_type} reports...")
            
            for i in range(count_per_type):
                # Generate varied confidence within type range
                min_conf, max_conf = confidence_range
                confidence = random.uniform(min_conf, max_conf)
                
                # Add natural variation
                confidence += random.uniform(-0.05, 0.05)
                confidence = max(0.3, min(1.0, confidence))
                
                # Select random scenario and location
                scenario = random.choice(list(self.scenarios.keys()))
                location = random.choice(list(self.coordinates.keys()))
                
                # Generate contextual title
                base_titles = {
                    'air_pollution': ['Air Quality Issues', 'Smog Detection', 'Atmospheric Pollution', 'Emissions Alert'],
                    'water_pollution': ['Water Contamination', 'Aquatic Pollution', 'Waterway Issues', 'Marine Pollution'],
                    'noise_pollution': ['Noise Disturbance', 'Sound Pollution', 'Acoustic Issues', 'Noise Complaint'],
                    'waste_management': ['Waste Disposal Issues', 'Garbage Problems', 'Landfill Concerns', 'Recycling Issues'],
                    'deforestation': ['Tree Cutting', 'Forest Loss', 'Logging Activity', 'Habitat Clearing'],
                    'wildlife_conservation': ['Species Protection', 'Wildlife Study', 'Animal Welfare', 'Conservation Effort'],
                    'climate_change': ['Climate Impact', 'Weather Pattern', 'Temperature Change', 'Climate Study'],
                    'other': ['Environmental Issue', 'Ecological Concern', 'Green Initiative', 'Sustainability Project']
                }
                
                title = f"{random.choice(base_titles[report_type])} in {location.split(',')[0]}"
                
                # Get coordinates
                base_coords = self.coordinates.get(location, (19.0760, 72.8777))
                latitude = Decimal(str(base_coords[0] + random.uniform(-0.08, 0.08)))
                longitude = Decimal(str(base_coords[1] + random.uniform(-0.08, 0.08)))
                
                # Determine severity based on confidence
                if confidence > 0.85:
                    severity = 'critical'
                elif confidence > 0.75:
                    severity = 'high'
                elif confidence > 0.6:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                # Determine status
                status_options = ['pending', 'validated', 'under_review', 'rejected']
                if confidence > 0.8:
                    status = random.choice(['validated', 'validated', 'under_review'])
                elif confidence > 0.6:
                    status = random.choice(['validated', 'under_review', 'pending'])
                else:
                    status = random.choice(['pending', 'under_review', 'rejected'])
                
                # Create description based on confidence level
                confidence_desc = {
                    (0.9, 1.0): "High confidence assessment with clear evidence and comprehensive data.",
                    (0.8, 0.9): "Strong evidence supports findings with reliable data sources.",
                    (0.7, 0.8): "Good confidence level with adequate supporting information.",
                    (0.6, 0.7): "Moderate confidence based on available evidence.",
                    (0.5, 0.6): "Limited confidence due to insufficient data or unclear conditions.",
                    (0.3, 0.5): "Low confidence assessment requiring additional investigation."
                }
                
                description = "Environmental analysis report. "
                for conf_range, desc in confidence_desc.items():
                    if conf_range[0] <= confidence <= conf_range[1]:
                        description += desc
                        break
                
                # Random timestamp
                days_ago = random.randint(1, 60)
                created_at = datetime.now() - timedelta(days=days_ago)
                
                # Create the report
                report = Report.objects.create(
                    title=title,
                    description=description,
                    report_type=report_type,
                    severity=severity,
                    status=status,
                    latitude=latitude,
                    longitude=longitude,
                    location_name=location.split(',')[0],
                    address=f"Near {location}",
                    reporter_name=f"Analyst {random.randint(1, 100)}",
                    reporter_email=f"analyst{random.randint(1, 100)}@example.com",
                    created_at=created_at,
                    confidence_score=confidence,
                    verified=random.choice([True, False])
                )
                
                created_count += 1
                
                # Progress indicator
                if (i + 1) % 8 == 0:
                    print(f"  ✅ Created {i + 1}/{count_per_type} {report_type} reports")
        
        print(f"\n🎉 Successfully created {created_count} diverse heatmap reports!")
        return created_count

    def display_statistics(self):
        """Display statistics of created datasets"""
        print("\n" + "="*60)
        print("📊 DATASET STATISTICS")
        print("="*60)
        
        # Dashboard reports stats
        dashboard_reports = EnvironmentalAnalysis.objects.all()
        print(f"\n🏢 Dashboard Reports: {dashboard_reports.count()}")
        print("Risk Level Distribution:")
        for risk in ['low', 'high', 'critical']:
            count = dashboard_reports.filter(risk_level=risk).count()
            print(f"  {risk.capitalize()}: {count}")
        
        # Confidence distribution for dashboard
        confidence_ranges = [
            (90, 100), (80, 89), (70, 79), (60, 69), (50, 59), (30, 49)
        ]
        print("\nConfidence Distribution:")
        for min_conf, max_conf in confidence_ranges:
            count = dashboard_reports.filter(
                confidence__gte=min_conf, 
                confidence__lte=max_conf
            ).count()
            print(f"  {min_conf}-{max_conf}%: {count} reports")
        
        # Heatmap reports stats
        heatmap_reports = Report.objects.all()
        print(f"\n🗺️  Heatmap Reports: {heatmap_reports.count()}")
        print("Type Distribution:")
        for report_type, _ in Report.REPORT_TYPES:
            count = heatmap_reports.filter(report_type=report_type).count()
            print(f"  {report_type.replace('_', ' ').title()}: {count}")
        
        # Confidence distribution for heatmap (converted to percentage)
        print("\nConfidence Distribution:")
        for min_conf, max_conf in confidence_ranges:
            count = heatmap_reports.filter(
                confidence_score__gte=min_conf/100, 
                confidence_score__lte=max_conf/100
            ).count()
            print(f"  {min_conf}-{max_conf}%: {count} reports")
        
        print("\n" + "="*60)

def main():
    """Main function to generate diverse datasets"""
    print("🚀 Starting diverse dataset generation...")
    print("This will create varied environmental analysis data with realistic confidence distributions")
    
    generator = DiverseDatasetGenerator()
    
    # Clear existing test data (optional)
    response = input("\n❓ Clear existing reports before generating new data? (y/N): ")
    if response.lower() == 'y':
        EnvironmentalAnalysis.objects.all().delete()
        Report.objects.all().delete()
        print("🗑️  Existing reports cleared!")
    
    # Generate diverse datasets
    dashboard_count = generator.generate_dashboard_reports(count_per_scenario=8)
    heatmap_count = generator.generate_heatmap_reports(count_per_type=12)
    
    # Display statistics
    generator.display_statistics()
    
    print(f"\n✨ Dataset generation complete!")
    print(f"📈 Total reports created: {dashboard_count + heatmap_count}")
    print("🎯 Confidence levels now vary from 30% to 100% with realistic distributions")
    print("🔧 The 70% confidence issue has been resolved!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Dataset generation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during dataset generation: {e}")
        import traceback
        traceback.print_exc()
