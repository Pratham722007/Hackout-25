#!/usr/bin/env python3
"""
Diagnostic script to check AI model confidence issues
Run this to understand why confidence might be stuck at 50%
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from dashboard.ai_model import environmental_analyzer

def diagnose_ai_model():
    """Diagnose the current AI model state"""
    
    print("=" * 60)
    print("AI MODEL DIAGNOSTIC")
    print("=" * 60)
    
    # Check if model is loaded
    print(f"Model loaded: {environmental_analyzer._model_loaded}")
    print(f"Model object: {environmental_analyzer.model}")
    
    # Try to force model loading
    try:
        environmental_analyzer._ensure_model_loaded()
        print(f"After ensure_model_loaded:")
        print(f"  Model loaded: {environmental_analyzer._model_loaded}")
        print(f"  Has environmental_classes: {hasattr(environmental_analyzer, 'environmental_classes')}")
        if hasattr(environmental_analyzer, 'environmental_classes'):
            print(f"  Environmental classes count: {len(environmental_analyzer.environmental_classes)}")
    except Exception as e:
        print(f"Error loading model: {e}")
    
    # Test color analysis without image
    print("\nTesting color analysis with dummy data:")
    dummy_color_analysis = {
        'green_dominance': 0.6,
        'blue_dominance': 0.3, 
        'brown_score': 0.1
    }
    
    try:
        fallback_result = environmental_analyzer._fallback_analysis(dummy_color_analysis)
        print(f"Fallback analysis result:")
        print(f"  Environmental: {fallback_result['is_environmental']}")
        print(f"  Risk: {fallback_result['risk_level']}")
        print(f"  Confidence: {fallback_result['confidence']}%")
        print(f"  Analysis: {fallback_result['analysis']}")
    except Exception as e:
        print(f"Error in fallback analysis: {e}")
    
    # Test default result creation
    print("\nTesting default result creation:")
    try:
        default_result = environmental_analyzer._create_default_result("Test message")
        print(f"Default result:")
        print(f"  Environmental: {default_result['is_environmental']}")
        print(f"  Risk: {default_result['risk_level']}")
        print(f"  Confidence: {default_result['confidence']}%")
        print(f"  Analysis: {default_result['analysis']}")
    except Exception as e:
        print(f"Error creating default result: {e}")

def test_with_nonexistent_image():
    """Test what happens with a non-existent image"""
    print("\n" + "=" * 60)
    print("TESTING WITH NON-EXISTENT IMAGE")
    print("=" * 60)
    
    fake_image_path = "non_existent_image.jpg"
    
    try:
        result = environmental_analyzer.detect_environmental_content(fake_image_path)
        print(f"Result for non-existent image:")
        print(f"  Environmental: {result['is_environmental']}")
        print(f"  Risk: {result['risk_level']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Analysis: {result['analysis']}")
        
        if result['confidence'] == 50:
            print("❌ ISSUE FOUND: Confidence is exactly 50% - this suggests default fallback")
        else:
            print("✅ Confidence is not 50% - improvement working")
            
    except Exception as e:
        print(f"Error testing with non-existent image: {e}")

def test_views_fallback():
    """Test the views.py fallback functions"""
    print("\n" + "=" * 60)
    print("TESTING VIEWS.PY FALLBACK FUNCTIONS")
    print("=" * 60)
    
    from dashboard.views import determine_risk_level, calculate_confidence, determine_status
    
    test_title = "Test Environmental Analysis"
    test_location = "Test Location"
    
    risk = determine_risk_level(test_title, test_location)
    confidence = calculate_confidence(test_title, test_location)
    status = determine_status(test_title, test_location)
    
    print(f"Views fallback results:")
    print(f"  Risk: {risk}")
    print(f"  Confidence: {confidence}%")
    print(f"  Status: {status}")
    
    if confidence == 50:
        print("❌ ISSUE: Views fallback also returns 50% confidence")
    else:
        print("✅ Views fallback confidence is not 50%")

if __name__ == "__main__":
    try:
        diagnose_ai_model()
        test_with_nonexistent_image() 
        test_views_fallback()
        
        print("\n" + "=" * 60)
        print("🏁 DIAGNOSTIC COMPLETE")
        print("Check above for any ❌ issues that need fixing")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()
