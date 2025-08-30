"""
Django Management Command: test_achievements
Test the achievements system with Clerk user integration

Usage:
    python manage.py test_achievements --setup-user 1
    python manage.py test_achievements --create-test-report 1
    python manage.py test_achievements --check-progress 1
    python manage.py test_achievements --create-achievements
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from achievements.services import AchievementService
from achievements.models import Achievement, UserStats, UserAchievement
from heatmap.models import Report
from authentication.models import UserProfile
import random


class Command(BaseCommand):
    help = 'Test achievements system with Clerk user integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup-user',
            type=int,
            help='Setup achievements for user ID'
        )
        parser.add_argument(
            '--create-test-report',
            type=int,
            help='Create test report for user ID to trigger achievements'
        )
        parser.add_argument(
            '--check-progress',
            type=int,
            help='Check achievement progress for user ID'
        )
        parser.add_argument(
            '--create-achievements',
            action='store_true',
            help='Create default achievements'
        )
        parser.add_argument(
            '--test-all',
            type=int,
            help='Run complete test for user ID'
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List available users'
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "🏆" * 30)
        self.stdout.write("🎯 ACHIEVEMENTS SYSTEM TESTER 🎯")
        self.stdout.write("🏆" * 30 + "\n")

        try:
            # List users option
            if options['list_users']:
                self.list_users()
                return

            # Create achievements option
            if options['create_achievements']:
                self.create_achievements()
                return

            # Setup user option
            if options.get('setup_user'):
                self.setup_user(options['setup_user'])
                return

            # Create test report option
            if options.get('create_test_report'):
                self.create_test_report(options['create_test_report'])
                return

            # Check progress option
            if options.get('check_progress'):
                self.check_progress(options['check_progress'])
                return

            # Test all option
            if options.get('test_all'):
                self.test_all(options['test_all'])
                return

            # Show help if no options provided
            self.stdout.write("🎯 Available commands:")
            self.stdout.write("   --list-users")
            self.stdout.write("   --create-achievements")
            self.stdout.write("   --setup-user <user_id>")
            self.stdout.write("   --create-test-report <user_id>")
            self.stdout.write("   --check-progress <user_id>")
            self.stdout.write("   --test-all <user_id>")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Command failed: {e}")
            )
            raise CommandError(f"Achievements test command failed: {e}")

    def list_users(self):
        """List available users"""
        self.stdout.write("👥 Available Users:")
        self.stdout.write("-" * 40)
        
        users = User.objects.all()[:20]
        
        for user in users:
            try:
                profile = UserProfile.objects.filter(user=user).first()
                self.stdout.write(f"\n🧑 {user.username}")
                self.stdout.write(f"   ID: {user.id}")
                self.stdout.write(f"   Email: {user.email}")
                self.stdout.write(f"   Full name: {user.get_full_name()}")
                self.stdout.write(f"   Clerk ID: {profile.clerk_user_id if profile else 'N/A'}")
                self.stdout.write(f"   Verified: {profile.is_verified if profile else 'N/A'}")
            except Exception as e:
                self.stdout.write(f"   Error: {e}")

    def create_achievements(self):
        """Create default achievements"""
        self.stdout.write("🏆 Creating default achievements...")
        
        try:
            count = AchievementService.create_default_achievements()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created {count} new achievements!")
            )
            
            total = Achievement.objects.filter(is_active=True).count()
            self.stdout.write(f"📊 Total active achievements: {total}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to create achievements: {e}")
            )

    def setup_user(self, user_id):
        """Setup achievements for a user"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"🧑 Setting up achievements for: {user.username}")
            
            # Ensure achievements setup
            success = ClerkAchievementService.ensure_achievements_setup_for_user(user)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ User achievements setup completed!")
                )
                
                # Show user stats
                stats, profile = ClerkAchievementService.get_or_create_user_stats_with_clerk(user)
                if stats:
                    self.stdout.write(f"\n📊 User Stats:")
                    self.stdout.write(f"   Level: {stats.level}")
                    self.stdout.write(f"   Points: {stats.total_points}")
                    self.stdout.write(f"   Reports: {stats.reports_created}")
                    self.stdout.write(f"   Achievements: {stats.achievements_unlocked}")
                    
                if profile:
                    self.stdout.write(f"\n🔐 Clerk Integration:")
                    self.stdout.write(f"   Clerk ID: {profile.clerk_user_id or 'N/A'}")
                    self.stdout.write(f"   Verified: {profile.is_verified}")
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Failed to setup user achievements")
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with ID {user_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error setting up user: {e}")
            )

    def create_test_report(self, user_id):
        """Create a test report and track achievement"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"📝 Creating test report for: {user.username}")
            
            # Create test report
            report = Report.objects.create(
                title=f"Test Report for {user.username}",
                description="This is a test environmental report to trigger achievement tracking.",
                report_type=random.choice(['air_pollution', 'water_pollution', 'waste_management']),
                severity=random.choice(['low', 'medium', 'high', 'critical']),
                latitude=random.uniform(40.0, 41.0),
                longitude=random.uniform(-74.0, -73.0),
                location_name="Test Location",
                created_by=user,
            )
            
            self.stdout.write(f"✅ Report created: {report.title}")
            self.stdout.write(f"   Type: {report.get_report_type_display()}")
            self.stdout.write(f"   Severity: {report.get_severity_display()}")
            self.stdout.write(f"   Location: {report.latitude}, {report.longitude}")
            
            # Track achievement
            self.stdout.write(f"\n🏆 Tracking achievements...")
            success = AchievementTracker.track_report_creation(user, report)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Achievement tracking completed!")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ Achievement tracking had issues")
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with ID {user_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error creating test report: {e}")
            )

    def check_progress(self, user_id):
        """Check achievement progress for user"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"📊 Checking progress for: {user.username}")
            
            # Get progress summary
            progress = ClerkAchievementService.get_user_progress_summary_with_clerk(user)
            
            if progress:
                self.stdout.write("\n🎯 ACHIEVEMENT PROGRESS:")
                self.stdout.write("=" * 40)
                
                # User info
                self.stdout.write(f"👤 User: {progress['user_info']['full_name'] or user.username}")
                self.stdout.write(f"📧 Email: {progress['user_info']['email']}")
                self.stdout.write(f"🔐 Clerk ID: {progress['clerk_data']['clerk_user_id'] or 'N/A'}")
                self.stdout.write(f"✅ Verified: {progress['clerk_data']['is_verified']}")
                
                # Stats
                stats = progress['stats']
                self.stdout.write(f"\n📊 Statistics:")
                self.stdout.write(f"   🎯 Level: {stats.level}")
                self.stdout.write(f"   ⭐ Points: {stats.total_points}")
                self.stdout.write(f"   🏆 Achievements: {progress['unlocked_count']}/{progress['total_achievements']}")
                self.stdout.write(f"   📋 Reports: {stats.reports_created}")
                self.stdout.write(f"   ✅ Validations: {stats.reports_validated}")
                self.stdout.write(f"   🔥 Current Streak: {stats.streak_current}")
                self.stdout.write(f"   🎖️ Best Streak: {stats.streak_best}")
                self.stdout.write(f"   📍 Locations: {len(stats.locations_reported)}")
                self.stdout.write(f"   📝 Report Types: {len(stats.report_types_used)}")
                self.stdout.write(f"   🥇 Rank: #{progress['user_rank']}")
                
                # Recent achievements
                if progress['recent_achievements']:
                    self.stdout.write(f"\n🎉 Recent Achievements:")
                    for achievement in progress['recent_achievements']:
                        self.stdout.write(f"   {achievement.achievement.icon} {achievement.achievement.name}")
                        self.stdout.write(f"      {achievement.achievement.description}")
                        self.stdout.write(f"      Points: {achievement.achievement.points}")
                
                # In progress
                if progress['in_progress']:
                    self.stdout.write(f"\n⏳ In Progress:")
                    for achievement in progress['in_progress']:
                        progress_pct = achievement.progress_percentage
                        self.stdout.write(f"   {achievement.achievement.icon} {achievement.achievement.name}")
                        self.stdout.write(f"      Progress: {achievement.current_progress}/{achievement.achievement.target_value} ({progress_pct:.1f}%)")
                
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Could not retrieve user progress")
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with ID {user_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error checking progress: {e}")
            )

    def test_all(self, user_id):
        """Run complete test suite for user"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"🧪 Running complete test for: {user.username}")
            self.stdout.write("=" * 50)
            
            # Step 1: Setup
            self.stdout.write("📋 Step 1: Setting up achievements...")
            self.setup_user(user_id)
            
            # Step 2: Create achievements if needed
            self.stdout.write("\n🏆 Step 2: Ensuring achievements exist...")
            count = AchievementService.create_default_achievements()
            if count > 0:
                self.stdout.write(f"   Created {count} new achievements")
            else:
                self.stdout.write("   All achievements already exist")
            
            # Step 3: Create test reports
            self.stdout.write("\n📝 Step 3: Creating test reports...")
            for i in range(3):
                self.create_test_report(user_id)
                self.stdout.write(f"   Report {i+1}/3 created")
            
            # Step 4: Check final progress
            self.stdout.write("\n📊 Step 4: Final progress check...")
            self.check_progress(user_id)
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.SUCCESS("🎉 Complete test finished!")
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with ID {user_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Complete test failed: {e}")
            )
