#!/usr/bin/env python
"""
Script to set up JWT blacklist functionality
Run this script after adding the blacklist app to INSTALLED_APPS
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'election_portal.settings')
django.setup()

from django.core.management import execute_from_command_line

def setup_jwt_blacklist():
    """Set up JWT blacklist tables and functionality"""
    print("Setting up JWT blacklist functionality...")
    
    try:
        # Run migrations for the blacklist app
        print("Running migrations for JWT blacklist...")
        execute_from_command_line(['manage.py', 'makemigrations', 'rest_framework_simplejwt'])
        execute_from_command_line(['manage.py', 'migrate', 'rest_framework_simplejwt'])
        
        # Run all migrations to ensure everything is up to date
        print("Running all migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("JWT blacklist setup completed successfully!")
        print("\nYou can now:")
        print("1. Use refresh tokens to get new access tokens")
        print("2. Blacklist refresh tokens on logout")
        print("3. Access the API endpoints with proper authentication")
        
    except Exception as e:
        print(f"Error setting up JWT blacklist: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_jwt_blacklist() 