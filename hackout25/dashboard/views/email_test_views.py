"""
Django Views for Email Alert Testing
Web interface for testing email alert notifications with Clerk integration
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from dashboard.services.email_test_service import EmailTestService
import json


@login_required
def email_test_dashboard(request):
    """
    Dashboard view for email testing interface
    """
    try:
        # Get available users for testing
        users = EmailTestService.list_available_users(limit=50)
        
        context = {
            'users': users,
            'current_user': request.user,
            'page_title': 'Email Alert Test Dashboard'
        }
        
        return render(request, 'dashboard/email_test_dashboard.html', context)
        
    except Exception as e:
        context = {
            'error': f"Error loading email test dashboard: {e}",
            'page_title': 'Email Alert Test Dashboard'
        }
        return render(request, 'dashboard/email_test_dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_test_email_alert(request):
    """
    API endpoint for testing email alerts
    Supports both logged-in users and manual user selection
    """
    try:
        data = json.loads(request.body)
        
        # Get user parameters
        user_id = data.get('user_id')
        email = data.get('email')
        clerk_user_id = data.get('clerk_user_id')
        
        # Use current user if logged in and no specific user provided
        if request.user.is_authenticated and not any([user_id, email, clerk_user_id]):
            user_id = request.user.id
        
        # Get alert parameters
        alert_text = data.get('alert_text')
        priority = data.get('priority', 'medium')
        location = data.get('location')
        
        # Validate parameters
        if not any([user_id, email, clerk_user_id]):
            return JsonResponse({
                'success': False,
                'error': 'Please provide user_id, email, or clerk_user_id'
            }, status=400)
        
        # Run email verification test
        result = EmailTestService.test_email_verification_complete(
            user_id=user_id,
            email=email,
            clerk_user_id=clerk_user_id,
            alert_text=alert_text,
            priority=priority,
            location=location
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Email test completed successfully!',
                'data': {
                    'user_email': result['user_data'].get('email'),
                    'user_name': result['user_data'].get('full_name'),
                    'alert_id': result['email_result'].get('alert_id'),
                    'sent_at': result['email_result'].get('sent_at').isoformat() if result['email_result'].get('sent_at') else None,
                    'email_backend': result.get('email_backend'),
                    'instructions': result.get('instructions')
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_list_users(request):
    """
    API endpoint to list available users for email testing
    """
    try:
        users = EmailTestService.list_available_users(limit=100)
        
        return JsonResponse({
            'success': True,
            'users': users,
            'count': len(users)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error fetching users: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_test_user(request):
    """
    API endpoint to create a test user for email testing
    """
    try:
        from authentication.models import UserProfile
        import uuid
        
        # Create a test user
        test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        test_email = f"test.{uuid.uuid4().hex[:8]}@example.com"
        
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            first_name="Test",
            last_name="User",
            password="testpassword123"
        )
        
        # Create user profile with Clerk integration
        profile = UserProfile.objects.create(
            user=user,
            clerk_user_id=f"clerk_test_{uuid.uuid4().hex[:12]}",
            is_verified=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Test user created successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'clerk_user_id': profile.clerk_user_id,
                'is_verified': profile.is_verified
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error creating test user: {str(e)}'
        }, status=500)


@login_required  
def test_current_user_email(request):
    """
    Quick test endpoint for testing email with current logged-in user
    """
    try:
        # Test email with current user
        result = EmailTestService.test_email_verification_complete(
            user_id=request.user.id,
            alert_text=f"Hello {request.user.get_full_name() or request.user.username}! This is a test email to verify your alert notification settings.",
            priority='medium',
            location='Email Test Dashboard'
        )
        
        if result['success']:
            message = f"✅ Test email sent successfully to {request.user.email}! Check your terminal for email output."
        else:
            message = f"❌ Failed to send test email: {result.get('error', 'Unknown error')}"
        
        return JsonResponse({
            'success': result['success'],
            'message': message,
            'email_backend': result.get('email_backend'),
            'instructions': result.get('instructions')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error testing current user email: {str(e)}'
        }, status=500)
