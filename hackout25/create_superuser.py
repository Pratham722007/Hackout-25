#!/usr/bin/env python3
"""
Script to create superuser jethala
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackout25.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    username = 'jethala'
    email = 'jethala@example.com'
    password = 'dayal1234'
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"✅ Superuser '{username}' already exists!")
        return
    
    # Create superuser
    user = User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email: {email}")
    print(f"Access admin at: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    create_superuser()
