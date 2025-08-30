from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile
import json

def index(request):
    """Serve the React app with Clerk authentication - this will show login/signup automatically"""
    return render(request, 'index.html')

def redirect_to_dashboard(request):
    """Redirect users to dashboard after successful authentication"""
    return redirect('/dashboard/')

def logout_view(request):
    """Handle user logout - works for both Clerk and Django auth"""
    # Clear any Django session data
    if request.user.is_authenticated:
        logout(request)
    
    # Redirect to home page (where Clerk will handle the logout UI)
    return redirect('/')

@csrf_exempt
def clerk_webhook(request):
    """Handle Clerk webhooks for user management"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_type = data.get('type')
            user_data = data.get('data', {})
            
            if event_type == 'user.created':
                # Handle new user creation from Clerk
                clerk_user_id = user_data.get('id')
                email = user_data.get('email_addresses', [{}])[0].get('email_address')
                first_name = user_data.get('first_name', '')
                last_name = user_data.get('last_name', '')
                username = user_data.get('username') or email.split('@')[0] if email else clerk_user_id
                
                # Create Django user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                
                # Create user profile
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'clerk_user_id': clerk_user_id,
                        'is_verified': True,
                    }
                )
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'method not allowed'}, status=405)
