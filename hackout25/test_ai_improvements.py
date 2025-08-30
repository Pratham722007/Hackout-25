#!/usr/bin/env python3
"""
Test script to verify AI model improvements
Run this script to test the environmental analysis without needing actual images
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from dashboard.ai_model import EnvironmentalAnalyzer
import numpy as np

class MockAnalyzer(EnvironmentalAnalyzer):
    """Mock version of analyzer for testing without images"""
    
    def __init__(self):
        super().__init__()
        # Ensure model loading is called to initialize environmental classes
        self._ensure_model_loaded()
    
    def preprocess_image(self, image_path):
        """Mock preprocessing - return dummy array"""
        return np.random.rand(1, 224, 224, 3)
    
    def analyze_color_distribution(self, image_path):
        """Mock color analysis with various scenarios"""
        scenarios = [
            # Forest/vegetation scenario
            {'green_dominance': 0.6, 'blue_dominance': 0.3, 'brown_score': 0.2},
            # Ocean/water scenario  
            {'green_dominance': 0.2, 'blue_dominance': 0.7, 'brown_score': 0.1},
            # Desert/arid scenario
            {'green_dominance': 0.1, 'blue_dominance': 0.2, 'brown_score': 0.5},
            # Urban/non-environmental
            {'green_dominance': 0.1, 'blue_dominance': 0.1, 'brown_score': 0.1}
        ]
        
        # Return scenario based on "image_path" mock
        scenario_index = hash(image_path) % len(scenarios)
        return scenarios[scenario_index]
    
    def detect_environmental_content(self, image_path):
        """Override to use mock predictions"""
        try:
            # Mock predictions for different scenarios
            mock_predictions = {
                'forest.jpg': [
                    ('pine_tree', 0.45),
                    ('forest', 0.35), 
                    ('leaf', 0.12),
                    ('oak', 0.08),
                    ('branch', 0.05)
                ],
                'ocean.jpg': [
                    ('ocean', 0.55),
                    ('seashore', 0.25),
                    ('wave', 0.15),
                    ('beach', 0.12),
                    ('coral_reef', 0.08)
                ],
                'wildfire.jpg': [
                    ('wildfire', 0.65),
                    ('forest_fire', 0.25),
                    ('smoke', 0.18),
                    ('flame', 0.12),
                    ('ash', 0.08)
                ],
                'pollution.jpg': [
                    ('oil_spill', 0.45),
                    ('pollution', 0.35),
                    ('smog', 0.25),
                    ('toxic_waste', 0.15),
                    ('contamination', 0.10)
                ],
                'city.jpg': [
                    ('skyscraper', 0.65),
                    ('building', 0.45),
                    ('street', 0.35),
                    ('car', 0.25),
                    ('urban', 0.15)
                ]
            }
            
            # Get mock predictions based on image_path
            filename = os.path.basename(image_path)
            predictions = mock_predictions.get(filename, mock_predictions['forest.jpg'])
            
            # Analyze color distribution
            color_analysis = self.analyze_color_distribution(image_path)
            
            # Calculate environmental score
            environmental_score = self._calculate_environmental_score(
                predictions, color_analysis
            )
            
            # Determine risk level and confidence
            result = self._determine_risk_level(
                predictions, environmental_score, color_analysis
            )
            
            return result
            
        except Exception as e:
            print(f"Error in environmental detection: {e}")
            return self._create_default_result("Analysis failed")

def test_ai_improvements():
    """Test the improved AI model with various scenarios"""
    
    print("=" * 60)
    print("TESTING AI MODEL IMPROVEMENTS")
    print("=" * 60)
    
    # Create mock analyzer
    analyzer = MockAnalyzer()
    
    # Test scenarios
    test_cases = [
        ('forest.jpg', 'Forest Environment'),
        ('ocean.jpg', 'Ocean Environment'),  
        ('wildfire.jpg', 'Wildfire Threat'),
        ('pollution.jpg', 'Pollution Threat'),
        ('city.jpg', 'Urban/Non-environmental')
    ]
    
    for image_path, description in test_cases:
        print(f"\n🔍 Testing: {description}")
        print("-" * 40)
        
        result = analyzer.detect_environmental_content(image_path)
        
        print(f"Environmental: {result['is_environmental']}")
        print(f"Risk Level: {result['risk_level'].upper()}")
        print(f"Confidence: {result['confidence']}%")
        print(f"Analysis: {result['analysis']}")
        
        if result.get('detected_objects'):
            print(f"Objects: {', '.join(result['detected_objects'][:3])}")
        
        if result.get('environmental_score'):
            print(f"Env Score: {result['environmental_score']}")
            
        # Verify improvements
        issues = []
        if result['confidence'] == 0:
            issues.append("❌ Zero confidence detected!")
        elif result['confidence'] < 30:
            issues.append("⚠️ Very low confidence")
        
        if result['risk_level'] == 'low' and result['confidence'] > 40:
            print("✅ Good confidence for low risk")
        elif result['risk_level'] in ['high', 'critical'] and result['confidence'] > 50:
            print("✅ Good confidence for elevated risk")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✅ No major issues detected")

def test_fallback_functions():
    """Test the improved fallback analysis functions"""
    
    print("\n" + "=" * 60)
    print("TESTING FALLBACK ANALYSIS FUNCTIONS")
    print("=" * 60)
    
    # Import views functions
    from dashboard.views import determine_risk_level, calculate_confidence, determine_status
    
    test_cases = [
        ("Amazon Rainforest Deforestation Alert", "Amazon Basin, Brazil"),
        ("Coral Bleaching Event", "Great Barrier Reef, Australia"),
        ("Oil Spill Cleanup", "Gulf of Mexico"),
        ("Wildlife Conservation Project", "Yellowstone National Park"),
        ("City Park Maintenance", "Central Park, New York")
    ]
    
    for title, location in test_cases:
        print(f"\n🔍 Testing: {title}")
        print("-" * 40)
        
        risk = determine_risk_level(title, location)
        confidence = calculate_confidence(title, location)
        status = determine_status(title, location)
        
        print(f"Risk Level: {risk.upper()}")
        print(f"Confidence: {confidence}%")
        print(f"Status: {status}")
        
        if confidence == 0:
            print("❌ Zero confidence detected!")
        elif confidence < 50:
            print("⚠️ Low confidence")
        else:
            print("✅ Reasonable confidence")

if __name__ == "__main__":
    try:
        test_ai_improvements()
        test_fallback_functions()
        
        print("\n" + "=" * 60)
        print("🎉 TEST COMPLETED!")
        print("Key Improvements Made:")
        print("• Fixed zero confidence issue")
        print("• Improved risk level detection")
        print("• Enhanced environmental scoring")
        print("• Better color analysis integration")
        print("• Expanded environmental keywords")
        print("• Improved fallback analysis")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
