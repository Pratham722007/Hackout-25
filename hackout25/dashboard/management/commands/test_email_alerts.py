"""
Django Management Command: test_email_alerts
Test email alert notification system with Clerk user integration

Usage:
    python manage.py test_email_alerts --user-id 1
    python manage.py test_email_alerts --email user@example.com
    python manage.py test_email_alerts --clerk-user-id clerk_12345
    python manage.py test_email_alerts --list-users
    python manage.py test_email_alerts --help
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from dashboard.services.email_test_service import EmailTestService
import sys


class Command(BaseCommand):
    help = 'Test email alert notification system with Clerk user integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Django User ID to test email with'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='User email address to test with'
        )
        parser.add_argument(
            '--clerk-user-id',
            type=str,
            help='Clerk User ID to test email with'
        )
        parser.add_argument(
            '--alert-text',
            type=str,
            help='Custom alert text content (optional)'
        )
        parser.add_argument(
            '--priority',
            type=str,
            choices=['low', 'medium', 'high', 'critical'],
            default='medium',
            help='Alert priority level (default: medium)'
        )
        parser.add_argument(
            '--location',
            type=str,
            help='Alert location (optional)'
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List available users for testing'
        )
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Create a test user for email testing'
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "🧪" * 30)
        self.stdout.write("📧 EMAIL ALERT NOTIFICATION TESTER 📧")
        self.stdout.write("🧪" * 30 + "\n")

        try:
            # List users option
            if options['list_users']:
                self.list_users()
                return

            # Create test user option
            if options['create_test_user']:
                self.create_test_user()
                return

            # Get user parameters
            user_id = options.get('user_id')
            email = options.get('email')
            clerk_user_id = options.get('clerk_user_id')

            # Validate that at least one user identifier is provided
            if not any([user_id, email, clerk_user_id]):
                self.stdout.write(
                    self.style.ERROR(
                        "❌ Please provide at least one user identifier:"
                    )
                )
                self.stdout.write("   --user-id <id>")
                self.stdout.write("   --email <email>")
                self.stdout.write("   --clerk-user-id <clerk_id>")
                self.stdout.write("\nOr use:")
                self.stdout.write("   --list-users (to see available users)")
                self.stdout.write("   --create-test-user (to create a test user)")
                self.stdout.write("   --help (for full help)")
                return

            # Run email verification test
            self.run_email_test(
                user_id=user_id,
                email=email,
                clerk_user_id=clerk_user_id,
                alert_text=options.get('alert_text'),
                priority=options.get('priority', 'medium'),
                location=options.get('location')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Command failed: {e}")
            )
            raise CommandError(f"Email test command failed: {e}")

    def run_email_test(self, user_id=None, email=None, clerk_user_id=None, 
                      alert_text=None, priority='medium', location=None):
        """Run the complete email verification test"""
        
        self.stdout.write("🚀 Starting email alert verification test...")
        
        # Use the email test service for complete verification
        result = EmailTestService.test_email_verification_complete(
            user_id=user_id,
            email=email,
            clerk_user_id=clerk_user_id,
            alert_text=alert_text,
            priority=priority,
            location=location
        )
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Email test completed successfully!")
            )
            
            # Display additional information
            user_data = result.get('user_data', {})
            email_result = result.get('email_result', {})
            
            self.stdout.write(f"\n📊 Test Results Summary:")
            self.stdout.write(f"   📧 Email sent to: {user_data.get('email', 'Unknown')}")
            self.stdout.write(f"   👤 User: {user_data.get('full_name', 'Unknown')}")
            self.stdout.write(f"   🆔 Alert ID: {email_result.get('alert_id', 'Unknown')}")
            self.stdout.write(f"   ⏰ Sent at: {email_result.get('sent_at', 'Unknown')}")
            self.stdout.write(f"   🔧 Email Backend: {result.get('email_backend', 'Unknown')}")
            
            # Print email viewing instructions
            self.print_email_instructions(result.get('email_backend'))
            
        else:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Email test failed!")
            )
            error_msg = result.get('error', 'Unknown error')
            self.stdout.write(f"   Error: {error_msg}")
            
            # Provide troubleshooting tips
            self.print_troubleshooting_tips()

    def list_users(self):
        """List available users for testing"""
        self.stdout.write("📋 Available Users for Email Testing:")
        self.stdout.write("-" * 50)
        
        users = EmailTestService.list_available_users(limit=20)
        
        if not users:
            self.stdout.write(self.style.WARNING("⚠️ No users found with email addresses."))
            self.stdout.write("💡 Try creating a test user with: --create-test-user")
            return
        
        for i, user in enumerate(users, 1):
            self.stdout.write(f"\n{i}. {user['full_name'] or user['username']}")
            self.stdout.write(f"   ID: {user['id']}")
            self.stdout.write(f"   Email: {user['email']}")
            self.stdout.write(f"   Clerk ID: {user['clerk_user_id'] or 'N/A'}")
            self.stdout.write(f"   Verified: {user['is_verified']}")
            self.stdout.write(f"   Active: {user['is_active']}")
        
        self.stdout.write(f"\n💡 To test with any user, use:")
        self.stdout.write(f"   python manage.py test_email_alerts --user-id <ID>")
        self.stdout.write(f"   python manage.py test_email_alerts --email <EMAIL>")

    def create_test_user(self):
        """Create a test user for email testing"""
        self.stdout.write("👤 Creating test user for email testing...")
        
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
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                clerk_user_id=f"clerk_test_{uuid.uuid4().hex[:12]}",
                is_verified=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Test user created successfully!")
            )
            self.stdout.write(f"   Username: {user.username}")
            self.stdout.write(f"   Email: {user.email}")
            self.stdout.write(f"   User ID: {user.id}")
            self.stdout.write(f"   Clerk ID: {profile.clerk_user_id}")
            
            self.stdout.write(f"\n🧪 Now you can test with:")
            self.stdout.write(f"   python manage.py test_email_alerts --user-id {user.id}")
            self.stdout.write(f"   python manage.py test_email_alerts --email {user.email}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to create test user: {e}")
            )

    def print_email_instructions(self, email_backend):
        """Print instructions on how to view the email"""
        self.stdout.write(f"\n📧 EMAIL VIEWING INSTRUCTIONS:")
        self.stdout.write("=" * 40)
        
        if email_backend == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(
                self.style.SUCCESS(
                    "📺 Console Backend: Email content should appear in your terminal above!"
                )
            )
            self.stdout.write("💡 Look for the email content printed above this message.")
            self.stdout.write("📄 Both HTML and plain text versions are included.")
        elif email_backend == 'django.core.mail.backends.filebased.EmailBackend':
            self.stdout.write("📁 File Backend: Check your email file directory.")
        elif 'smtp' in email_backend.lower():
            self.stdout.write("📮 SMTP Backend: Check the recipient's email inbox.")
        else:
            self.stdout.write(f"🔧 Backend: {email_backend}")
            self.stdout.write("💡 Check your email configuration for viewing instructions.")

    def print_troubleshooting_tips(self):
        """Print troubleshooting tips for email issues"""
        self.stdout.write(f"\n🔍 TROUBLESHOOTING TIPS:")
        self.stdout.write("=" * 30)
        self.stdout.write("1. ✅ Verify user exists: --list-users")
        self.stdout.write("2. 👤 Create test user: --create-test-user")
        self.stdout.write("3. 📧 Check email settings in settings.py")
        self.stdout.write("4. 🔗 Verify Clerk integration is working")
        self.stdout.write("5. 📝 Check Django logs for detailed errors")
        self.stdout.write("6. 🧪 Try with different user: --user-id <different_id>")
        
        self.stdout.write(f"\n💡 For detailed help: python manage.py test_email_alerts --help")
