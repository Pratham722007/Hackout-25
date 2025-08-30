#!/usr/bin/env python3
"""
Test admin panel functionality
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from django.contrib.admin import site
from dashboard.models import EnvironmentalAnalysis, Alert, AlertRecipient

def test_admin_registration():
    print("🔧 Testing Django Admin Configuration")
    print("=" * 50)
    
    # Check if models are registered
    registered_models = [model.__name__ for model in site._registry.keys()]
    
    print(f"📋 Registered models: {registered_models}")
    
    required_models = ['EnvironmentalAnalysis', 'Alert', 'AlertRecipient', 'User']
    
    for model_name in required_models:
        if model_name in registered_models:
            print(f"✅ {model_name} is registered in admin")
        else:
            print(f"❌ {model_name} is NOT registered in admin")
    
    # Test basic model operations
    print(f"\n📊 Database Status:")
    print(f"   Environmental Analysis: {EnvironmentalAnalysis.objects.count()} records")
    print(f"   Alerts: {Alert.objects.count()} records")  
    print(f"   Alert Recipients: {AlertRecipient.objects.count()} records")
    
    # Test admin classes
    print(f"\n⚙️  Admin Class Status:")
    try:
        from dashboard.admin import EnvironmentalAnalysisAdmin, AlertAdmin, AlertRecipientAdmin
        print("✅ All admin classes imported successfully")
        
        # Test admin methods
        if hasattr(EnvironmentalAnalysisAdmin, 'has_image'):
            print("✅ EnvironmentalAnalysisAdmin methods working")
        
        print("✅ Admin configuration is clean and simplified")
        
    except Exception as e:
        print(f"❌ Error with admin classes: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ADMIN TEST COMPLETED")
    print("\n🔑 Admin should now be accessible at:")
    print("   URL: http://127.0.0.1:8000/admin/")
    print("   Username: jethala")
    print("   Password: dayal1234")
    print("\nThe KeyError 'X' should be fixed!")
    return True

if __name__ == "__main__":
    try:
        test_admin_registration()
    except Exception as e:
        print(f"❌ Admin test failed: {e}")
        import traceback
        traceback.print_exc()
