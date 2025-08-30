#!/usr/bin/env python3
"""
Test script to verify URL patterns are working correctly
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from django.urls import reverse
from django.test import Client
from django.http import HttpRequest

def test_logout_url():
    """Test that the logout URL is properly configured"""
    print("=" * 50)
    print("TESTING LOGOUT URL CONFIGURATION")
    print("=" * 50)
    
    try:
        # Test URL reverse lookup
        logout_url = reverse('logout')
        print(f"✅ Logout URL reverse lookup successful: {logout_url}")
        
        # Test with a mock request
        client = Client()
        response = client.get('/logout/')
        print(f"✅ GET request to /logout/ status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect expected
            print(f"✅ Redirect location: {response.url}")
            print("✅ Logout URL is working correctly!")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing logout URL: {e}")

def test_all_main_urls():
    """Test all main URL patterns"""
    print("\n" + "=" * 50)
    print("TESTING ALL MAIN URL PATTERNS")
    print("=" * 50)
    
    test_urls = [
        ('/', 'Home page'),
        ('/logout/', 'Logout'),
        ('/dashboard/', 'Dashboard'),
        ('/news/', 'News'),
    ]
    
    client = Client()
    
    for url, description in test_urls:
        try:
            response = client.get(url)
            status_icon = "✅" if response.status_code in [200, 302] else "❌"
            print(f"{status_icon} {description:20} {url:15} -> Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"   └─ Redirects to: {response.url}")
                
        except Exception as e:
            print(f"❌ {description:20} {url:15} -> Error: {e}")

if __name__ == "__main__":
    test_logout_url()
    test_all_main_urls()
    
    print("\n" + "=" * 50)
    print("🎉 URL TESTING COMPLETE!")
    print("If you see ✅ for logout URL, the fix is working!")
    print("=" * 50)
