import os
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class ClerkService:
    """Service class to interact with Clerk API"""
    
    def __init__(self):
        self.secret_key = getattr(settings, 'CLERK_SECRET_KEY', None)
        if not self.secret_key or self.secret_key == 'your-clerk-secret-key-here':
            logger.warning("Clerk secret key not properly configured")
        
        self.base_url = "https://api.clerk.dev/v1"
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> Dict:
        """
        Fetch all users from Clerk
        
        Args:
            limit: Number of users to fetch per request (max 100)
            offset: Number of users to skip
            
        Returns:
            Dictionary containing users data and pagination info
        """
        try:
            url = f"{self.base_url}/users"
            params = {
                'limit': min(limit, 100),  # Clerk API has a max limit of 100
                'offset': offset
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching users from Clerk: {e}")
            return {'data': [], 'total_count': 0}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Fetch a specific user by their Clerk ID
        
        Args:
            user_id: Clerk user ID
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/users/{user_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user {user_id} from Clerk: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Fetch a user by their email address
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/users"
            params = {'email_address': email}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return data[0]  # Return first match
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user by email {email} from Clerk: {e}")
            return None
    
    def fetch_all_users_paginated(self) -> List[Dict]:
        """
        Fetch all users from Clerk using pagination
        
        Returns:
            List of all user dictionaries
        """
        all_users = []
        offset = 0
        limit = 100
        
        while True:
            response_data = self.get_all_users(limit=limit, offset=offset)
            users = response_data.get('data', [])
            
            if not users:
                break
                
            all_users.extend(users)
            
            # Check if we've fetched all users
            total_count = response_data.get('total_count', 0)
            if len(all_users) >= total_count:
                break
                
            offset += limit
            
        logger.info(f"Fetched {len(all_users)} users from Clerk")
        return all_users
    
    def extract_user_data(self, clerk_user: Dict) -> Dict:
        """
        Extract relevant user data from Clerk user object
        
        Args:
            clerk_user: Raw user data from Clerk API
            
        Returns:
            Dictionary with extracted user data
        """
        # Get primary email address
        email_addresses = clerk_user.get('email_addresses', [])
        primary_email = None
        for email_obj in email_addresses:
            if email_obj.get('id') == clerk_user.get('primary_email_address_id'):
                primary_email = email_obj.get('email_address')
                break
        
        # Get phone numbers
        phone_numbers = clerk_user.get('phone_numbers', [])
        primary_phone = None
        for phone_obj in phone_numbers:
            if phone_obj.get('id') == clerk_user.get('primary_phone_number_id'):
                primary_phone = phone_obj.get('phone_number')
                break
        
        return {
            'clerk_id': clerk_user.get('id'),
            'email': primary_email,
            'first_name': clerk_user.get('first_name', ''),
            'last_name': clerk_user.get('last_name', ''),
            'username': clerk_user.get('username'),
            'phone_number': primary_phone,
            'profile_image_url': clerk_user.get('profile_image_url'),
            'created_at': clerk_user.get('created_at'),
            'updated_at': clerk_user.get('updated_at'),
            'last_sign_in_at': clerk_user.get('last_sign_in_at'),
            'email_verified': any(email.get('verification', {}).get('status') == 'verified' 
                                for email in email_addresses),
            'phone_verified': any(phone.get('verification', {}).get('status') == 'verified' 
                                for phone in phone_numbers),
            'banned': clerk_user.get('banned', False),
            'locked': clerk_user.get('locked', False),
        }
