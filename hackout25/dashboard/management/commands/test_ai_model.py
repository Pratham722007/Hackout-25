from django.core.management.base import BaseCommand
from dashboard.ai_model import environmental_analyzer
import os

class Command(BaseCommand):
    help = 'Test the AI model with sample analysis'

    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str, help='Path to the image file to analyze')

    def handle(self, *args, **options):
        image_path = options['image_path']
        
        if not os.path.exists(image_path):
            self.stdout.write(
                self.style.ERROR(f'Image file not found: {image_path}')
            )
            return
        
        self.stdout.write('Analyzing image with AI model...')
        self.stdout.write(f'Image path: {image_path}')
        
        # Analyze the image
        result = environmental_analyzer.detect_environmental_content(image_path)
        
        # Display results
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('AI ANALYSIS RESULTS'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'Is Environmental: {result["is_environmental"]}')
        self.stdout.write(f'Risk Level: {result["risk_level"].upper()}')
        self.stdout.write(f'Confidence: {result["confidence"]}%')
        self.stdout.write(f'Analysis: {result["analysis"]}')
        
        if result.get("detected_objects"):
            self.stdout.write(f'Detected Objects: {", ".join(result["detected_objects"])}')
        
        if result.get("environmental_score"):
            self.stdout.write(f'Environmental Score: {result["environmental_score"]}')
        
        if result.get("color_analysis"):
            color = result["color_analysis"]
            self.stdout.write('\nColor Analysis:')
            self.stdout.write(f'  Green Dominance: {color["green_dominance"]:.3f}')
            self.stdout.write(f'  Blue Dominance: {color["blue_dominance"]:.3f}')
            self.stdout.write(f'  Brown Score: {color["brown_score"]:.3f}')
        
        self.stdout.write('\n' + '='*50)
        
        # Provide interpretation
        if not result["is_environmental"]:
            self.stdout.write(
                self.style.WARNING('This appears to be non-environmental content (e.g., screenshots, documents, etc.)')
            )
        elif result["risk_level"] == "critical":
            self.stdout.write(
                self.style.ERROR('CRITICAL: Environmental threat detected!')
            )
        elif result["risk_level"] == "high":
            self.stdout.write(
                self.style.WARNING('HIGH RISK: Environmental concern identified')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('LOW RISK: Environmental content with minimal concern')
            )
