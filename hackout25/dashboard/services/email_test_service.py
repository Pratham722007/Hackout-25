"""
Email Test Service for Alert Notification Verification
Integrates with Clerk authentication to fetch current user data
and send test alert notifications via Django email backend
"""

import logging
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from authentication.models import UserProfile
from ..models import Alert, AlertRecipient
from .email_service import AlertEmailService

logger = logging.getLogger(__name__)

class EmailTestService:
    """Service for testing email alert notifications with Clerk user integration"""
    
    @staticmethod
    def get_current_user_from_clerk(clerk_user_id=None, user_id=None, email=None):
        """
        Fetch current logged-in user data from Clerk integration
        Supports fetching by Clerk user ID, Django user ID, or email
        """
        try:
            user = None
            user_profile = None
            
            if clerk_user_id:
                # Find user by Clerk ID
                user_profile = UserProfile.objects.select_related('user').filter(
                    clerk_user_id=clerk_user_id
                ).first()
                if user_profile:
                    user = user_profile.user
                    
            elif user_id:
                # Find user by Django user ID
                user = User.objects.filter(id=user_id).first()
                if user:
                    user_profile = UserProfile.objects.filter(user=user).first()
                    
            elif email:
                # Find user by email
                user = User.objects.filter(email=email).first()
                if user:
                    user_profile = UserProfile.objects.filter(user=user).first()
            
            if not user:
                logger.warning(f"User not found with provided criteria")
                return None
                
            # Return user data with Clerk integration info
            user_data = {
                'user': user,
                'user_profile': user_profile,
                'clerk_user_id': user_profile.clerk_user_id if user_profile else None,
                'is_verified': user_profile.is_verified if user_profile else False,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'username': user.username,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_active': user.is_active,
            }
            
            logger.info(f"Successfully fetched user data for: {user.email}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error fetching user from Clerk: {e}")
            return None
    
    @staticmethod
    def create_test_alert(user_data, alert_text=None, priority='medium', location=None):
        """
        Create a test alert notification with given text and user data
        """
        try:
            if not user_data or not user_data.get('user'):
                raise ValueError("Valid user data is required to create test alert")
            
            user = user_data['user']
            
            # Default alert text if not provided
            if not alert_text:
                alert_text = f"""
🧪 **EMAIL TEST VERIFICATION** 🧪

This is a test alert notification to verify the email system functionality.

User Information:
- Name: {user_data.get('full_name') or user_data.get('username')}
- Email: {user_data.get('email')}
- Clerk User ID: {user_data.get('clerk_user_id') or 'N/A'}
- Account Status: {'Verified' if user_data.get('is_verified') else 'Unverified'}
- Date Joined: {user_data.get('date_joined').strftime('%B %d, %Y at %I:%M %p') if user_data.get('date_joined') else 'N/A'}

System Information:
- Email Backend: {settings.EMAIL_BACKEND}
- From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}
- Site URL: {getattr(settings, 'SITE_URL', 'Not configured')}

If you can see this message, the email alert system is working correctly! ✅

This test was generated at: {timezone.now().strftime('%B %d, %Y at %I:%M:%S %p %Z')}
                """.strip()
            
            # Create test alert
            alert = Alert.objects.create(
                title="🧪 Email System Test Verification",
                description=alert_text,
                location=location or "Test Environment - Email System",
                priority=priority,
                created_by=user,
            )
            
            logger.info(f"Created test alert: {alert.id} for user: {user.email}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating test alert: {e}")
            return None
    
    @staticmethod
    def send_test_alert_email(user_data, alert=None, alert_text=None, priority='medium', location=None):
        """
        Send a test alert email to the specified user
        """
        try:
            if not user_data:
                raise ValueError("User data is required")
            
            # Create test alert if not provided
            if not alert:
                alert = EmailTestService.create_test_alert(
                    user_data, alert_text, priority, location
                )
                
            if not alert:
                raise ValueError("Failed to create test alert")
            
            # Create AlertRecipient entry for tracking
            recipient, created = AlertRecipient.objects.get_or_create(
                alert=alert,
                user=user_data['user'],
                defaults={'email_sent': False}
            )
            
            # Send the email using existing email service
            success = AlertEmailService._send_single_alert_email(recipient)
            
            if success:
                recipient.email_sent = True
                recipient.email_sent_at = timezone.now()
                recipient.error_message = ""
                logger.info(f"✅ Test email sent successfully to: {user_data['email']}")
            else:
                recipient.email_sent = False
                recipient.error_message = "Failed to send test email"
                logger.error(f"❌ Failed to send test email to: {user_data['email']}")
            
            recipient.save()
            
            # Update alert stats
            alert.recipients_count = 1
            alert.sent_at = timezone.now()
            alert.save()
            
            return {
                'success': success,
                'alert_id': alert.id,
                'recipient_id': recipient.id,
                'user_email': user_data['email'],
                'sent_at': recipient.email_sent_at,
                'error_message': recipient.error_message
            }
            
        except Exception as e:
            logger.error(f"Error sending test alert email: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_email': user_data.get('email') if user_data else 'Unknown'
            }
    
    @staticmethod
    def test_email_verification_complete(clerk_user_id=None, user_id=None, email=None, 
                                       alert_text=None, priority='medium', location=None):
        """
        Complete end-to-end email verification test
        1. Fetch user from Clerk
        2. Create test alert
        3. Send email
        4. Return comprehensive results
        """
        try:
            # Reset email display counter for clean testing
            from django.conf import settings
            if 'simple_console_email' in settings.EMAIL_BACKEND:
                from dashboard.backends.simple_console_email import SimpleConsoleEmailBackend
                SimpleConsoleEmailBackend._displayed_subjects.clear()
                SimpleConsoleEmailBackend._first_email_shown = False
            
            print("🧪 Starting Email Verification Test...")
            print("=" * 50)
            
            # Step 1: Fetch user data
            print("📋 Step 1: Fetching user data from Clerk integration...")
            user_data = EmailTestService.get_current_user_from_clerk(
                clerk_user_id=clerk_user_id, 
                user_id=user_id, 
                email=email
            )
            
            if not user_data:
                error_msg = "❌ Failed to fetch user data. Please ensure user exists and parameters are correct."
                print(error_msg)
                return {'success': False, 'error': error_msg}
            
            print(f"✅ User found: {user_data['full_name']} ({user_data['email']})")
            print(f"   Clerk ID: {user_data.get('clerk_user_id') or 'N/A'}")
            print(f"   Verified: {user_data.get('is_verified')}")
            
            # Step 2: Send test email
            print("\n📧 Step 2: Creating and sending test alert email...")
            result = EmailTestService.send_test_alert_email(
                user_data=user_data,
                alert_text=alert_text,
                priority=priority,
                location=location
            )
            
            if result['success']:
                print(f"✅ Email sent successfully!")
                print(f"   Alert ID: {result['alert_id']}")
                print(f"   Sent to: {result['user_email']}")
                print(f"   Sent at: {result['sent_at']}")
            else:
                print(f"❌ Email sending failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Step 3: Display email backend info
            print(f"\n🔧 Step 3: Email Configuration Check...")
            print(f"   Email Backend: {settings.EMAIL_BACKEND}")
            print(f"   From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}")
            
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                print("   📺 EMAIL OUTPUT: Check your terminal/console for email content!")
                print("   💡 The email should appear above this message in your terminal.")
            
            print("\n" + "=" * 50)
            print("🧪 Email Verification Test Complete!")
            
            return {
                'success': result['success'],
                'user_data': user_data,
                'email_result': result,
                'email_backend': settings.EMAIL_BACKEND,
                'instructions': 'Check terminal output for email content' if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend' else 'Check email provider'
            }
            
        except Exception as e:
            error_msg = f"❌ Email verification test failed: {e}"
            print(error_msg)
            logger.error(error_msg)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_available_users(limit=10):
        """
        List available users for testing purposes
        """
        try:
            users = User.objects.filter(email__isnull=False).exclude(email='')[:limit]
            user_list = []
            
            for user in users:
                try:
                    profile = UserProfile.objects.filter(user=user).first()
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.get_full_name(),
                        'clerk_user_id': profile.clerk_user_id if profile else None,
                        'is_verified': profile.is_verified if profile else False,
                        'date_joined': user.date_joined,
                        'is_active': user.is_active
                    }
                    user_list.append(user_info)
                except Exception as e:
                    logger.warning(f"Error processing user {user.id}: {e}")
            
            return user_list
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    @staticmethod  
    def print_terminal_email_instructions():
        """
        Print instructions for viewing email output in terminal
        """
        print("\n" + "🔔" * 20)
        print("📧 EMAIL OUTPUT INSTRUCTIONS:")
        print("🔔" * 20)
        print("Since EMAIL_BACKEND is set to 'console', emails will be printed to this terminal.")
        print("Look for email content above this message.")
        print("The email includes both HTML and text versions.")
        print("🔔" * 20 + "\n")
