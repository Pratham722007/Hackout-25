"""
Simple Console Email Backend
Displays only the plain text email content once, without any HTML code or repetition
"""

import sys
import time
from django.core.mail.backends.console import EmailBackend as DjangoConsoleEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives


class SimpleConsoleEmailBackend(DjangoConsoleEmailBackend):
    """
    Simple email backend that displays only the text content from alert_notification.txt
    No HTML, no repetition, no encoded content - just clean text output
    Shows only the first email, then just counts additional emails
    """
    
    _last_display_time = 0
    _displayed_subjects = set()
    
    def send_messages(self, email_messages):
        """Send email messages to console in simple text format"""
        if not email_messages:
            return 0
        
        current_time = time.time()
        
        # Reset displayed subjects if more than 5 seconds have passed (new alert session)
        if current_time - SimpleConsoleEmailBackend._last_display_time > 5:
            SimpleConsoleEmailBackend._displayed_subjects.clear()
        
        msg_count = 0
        for message in email_messages:
            try:
                # Only display if we haven't shown this subject recently
                if message.subject not in SimpleConsoleEmailBackend._displayed_subjects:
                    self._display_simple_email(message)
                    SimpleConsoleEmailBackend._displayed_subjects.add(message.subject)
                    SimpleConsoleEmailBackend._last_display_time = current_time
                
                msg_count += 1
            except Exception as e:
                sys.stderr.write(f"Error processing email: {e}\n")
        
        return msg_count
    
    def _display_simple_email(self, message, total_recipients=1):
        """Display email in simple text format - only the .txt content"""
        
        # Simple header
        print("\n" + "="*60)
        print("📧 EMAIL ALERT SENT")
        print("="*60)
        
        # Basic info
        print(f"FROM: {message.from_email}")
        print(f"TO: {', '.join(message.to) if hasattr(message, 'to') and message.to else 'No recipients'}")
        print(f"SUBJECT: {message.subject}")
        
        print("\n" + "-"*60)
        print("MESSAGE:")
        print("-"*60)
        
        # Display only the plain text content (from .txt template)
        if message.body:
            print(message.body)
        else:
            print("(No text content)")
        
        print("-"*60)
        print("✅ Email sent successfully!")
        print("="*60 + "\n")
