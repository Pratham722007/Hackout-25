import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Alert, AlertRecipient
import logging

logger = logging.getLogger(__name__)


class AlertEmailService:
    """Service for sending environmental alert emails"""
    
    @staticmethod
    def send_alert_to_all_users(alert):
        """
        Send an alert email to all registered users
        Returns tuple (success_count, total_count)
        """
        try:
            # Get all users with email addresses
            users = User.objects.filter(email__isnull=False).exclude(email='')
            total_count = users.count()
            success_count = 0
            
            if total_count == 0:
                logger.warning("No users found with email addresses")
                return 0, 0
            
            # Create AlertRecipient entries for tracking
            recipients = []
            for user in users:
                recipient, created = AlertRecipient.objects.get_or_create(
                    alert=alert,
                    user=user,
                    defaults={'email_sent': False}
                )
                recipients.append(recipient)
            
            # Send emails
            for recipient in recipients:
                try:
                    success = AlertEmailService._send_single_alert_email(recipient)
                    if success:
                        success_count += 1
                        recipient.email_sent = True
                        recipient.email_sent_at = timezone.now()
                        recipient.error_message = ""
                    else:
                        recipient.email_sent = False
                        recipient.error_message = "Failed to send email"
                    
                    recipient.save()
                    
                except Exception as e:
                    logger.error(f"Failed to send alert to {recipient.user.email}: {e}")
                    recipient.email_sent = False
                    recipient.error_message = str(e)
                    recipient.save()
            
            # Update alert with results
            alert.recipients_count = success_count
            alert.sent_at = timezone.now()
            alert.save()
            
            logger.info(f"Alert sent to {success_count}/{total_count} users")
            return success_count, total_count
            
        except Exception as e:
            logger.error(f"Error sending alert emails: {e}")
            return 0, 0
    
    @staticmethod
    def _send_single_alert_email(recipient):
        """Send alert email to a single recipient"""
        try:
            alert = recipient.alert
            user = recipient.user
            
            # Priority-based subject prefixes
            priority_prefixes = {
                'low': '📢 Info',
                'medium': '⚠️ Alert',
                'high': '🚨 Urgent Alert',
                'critical': '🔴 CRITICAL ALERT'
            }
            
            subject_prefix = priority_prefixes.get(alert.priority, '📢')
            subject = f"{subject_prefix}: {alert.title}"
            
            # Email context
            context = {
                'user': user,
                'alert': alert,
                'priority_color': alert.priority_color,
                'priority_icon': alert.priority_icon,
                'site_name': 'EcoValidate',
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            # Render email templates
            html_content = render_to_string('emails/alert_notification.html', context)
            text_content = render_to_string('emails/alert_notification.txt', context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@ecovalidate.com',
                to=[user.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Attach image if present
            if alert.image:
                try:
                    email.attach_file(alert.image.path)
                except Exception as e:
                    logger.warning(f"Could not attach image to alert email: {e}")
            
            # Send email
            email.send()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email to {recipient.user.email}: {e}")
            return False
    
    @staticmethod
    def get_alert_statistics():
        """Get statistics about alert emails"""
        try:
            total_alerts = Alert.objects.count()
            total_recipients = AlertRecipient.objects.count()
            successful_sends = AlertRecipient.objects.filter(email_sent=True).count()
            failed_sends = AlertRecipient.objects.filter(email_sent=False).count()
            
            return {
                'total_alerts': total_alerts,
                'total_recipients': total_recipients,
                'successful_sends': successful_sends,
                'failed_sends': failed_sends,
                'success_rate': (successful_sends / total_recipients * 100) if total_recipients > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {
                'total_alerts': 0,
                'total_recipients': 0,
                'successful_sends': 0,
                'failed_sends': 0,
                'success_rate': 0
            }
