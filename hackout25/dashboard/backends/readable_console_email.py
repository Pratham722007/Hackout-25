"""
Custom Email Backend for Readable Console Output
Displays emails in a clean, readable format instead of raw MIME content
"""

import sys
from django.core.mail.backends.console import EmailBackend as DjangoConsoleEmailBackend
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html


class ReadableConsoleEmailBackend(DjangoConsoleEmailBackend):
    """
    Email backend that displays emails in a clean, readable format in the console
    instead of showing raw MIME content with base64 encoding
    """
    
    def send_messages(self, email_messages):
        """Send email messages to console in readable format"""
        if not email_messages:
            return 0
        
        msg_count = 0
        for message in email_messages:
            try:
                self._display_readable_email(message)
                msg_count += 1
            except Exception as e:
                sys.stderr.write(f"Error displaying email: {e}\n")
        
        return msg_count
    
    def _display_readable_email(self, message):
        """Display email in a clean, readable format"""
        
        # Email header separator
        print("\n" + "="*80)
        print("📧 EMAIL ALERT NOTIFICATION")
        print("="*80)
        
        # Basic email info
        print(f"📤 FROM: {message.from_email}")
        print(f"📥 TO: {', '.join(message.to) if hasattr(message, 'to') and message.to else 'No recipients'}")
        if hasattr(message, 'cc') and message.cc:
            print(f"📋 CC: {', '.join(message.cc)}")
        if hasattr(message, 'bcc') and message.bcc:
            print(f"🔒 BCC: {', '.join(message.bcc)}")
        
        print(f"📝 SUBJECT: {message.subject}")
        print(f"⏰ DATE: {message.extra_headers.get('Date', 'Not specified')}")
        
        print("\n" + "-"*80)
        
        # Handle different message types
        if isinstance(message, EmailMultiAlternatives):
            self._display_multipart_email(message)
        else:
            self._display_simple_email(message)
        
        print("-"*80)
        print("✅ Email successfully sent to console!")
        print("="*80 + "\n")
    
    def _display_simple_email(self, message):
        """Display simple text email"""
        print("📄 EMAIL CONTENT (Text):")
        print("-"*40)
        print(message.body)
        print()
    
    def _display_multipart_email(self, message):
        """Display multipart email with text and HTML alternatives"""
        
        # Display plain text version
        if message.body:
            print("📄 EMAIL CONTENT (Plain Text Version):")
            print("-"*40)
            print(message.body)
            print()
        
        # Display HTML alternatives
        if hasattr(message, 'alternatives') and message.alternatives:
            for content, content_type in message.alternatives:
                if content_type == 'text/html':
                    print("🌐 EMAIL CONTENT (HTML Version - Rendered):")
                    print("-"*40)
                    # Convert HTML to more readable format
                    readable_html = self._html_to_readable(content)
                    print(readable_html)
                    print()
                    
                    # Also show raw HTML for debugging if needed
                    print("🔧 EMAIL CONTENT (Raw HTML - For Debugging):")
                    print("-"*40)
                    # Truncate very long HTML content
                    if len(content) > 2000:
                        print(content[:2000] + "\n... [HTML content truncated] ...")
                    else:
                        print(content)
                    print()
        
        # Display attachments info
        if hasattr(message, 'attachments') and message.attachments:
            print("📎 ATTACHMENTS:")
            print("-"*40)
            for attachment in message.attachments:
                if hasattr(attachment, 'name'):
                    print(f"   📁 {attachment.name}")
                else:
                    print(f"   📁 Attachment: {type(attachment)}")
            print()
    
    def _html_to_readable(self, html_content):
        """Convert HTML content to a more readable format"""
        try:
            # Remove HTML tags and decode entities for a readable version
            import re
            
            # Remove script and style tags completely
            html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Replace common HTML elements with readable equivalents
            html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p[^>]*>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</p>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h[1-6][^>]*>', '\n--- ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</h[1-6]>', ' ---\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<div[^>]*>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</div>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<strong[^>]*>', '**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</strong>', '**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<b[^>]*>', '**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</b>', '**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<em[^>]*>', '*', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</em>', '*', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<i[^>]*>', '*', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</i>', '*', html_content, flags=re.IGNORECASE)
            
            # Remove all other HTML tags
            html_content = re.sub(r'<[^>]+>', '', html_content)
            
            # Decode HTML entities
            html_content = html.unescape(html_content)
            
            # Clean up whitespace
            html_content = re.sub(r'\n\s*\n', '\n\n', html_content)  # Multiple newlines to double newline
            html_content = re.sub(r'^\s+', '', html_content, flags=re.MULTILINE)  # Leading whitespace
            html_content = html_content.strip()
            
            return html_content
            
        except Exception as e:
            return f"[Error converting HTML to readable format: {e}]\n{html_content[:500]}..."


class VerboseConsoleEmailBackend(ReadableConsoleEmailBackend):
    """
    Even more verbose version that shows all email details including headers
    """
    
    def _display_readable_email(self, message):
        """Display email with extra verbose information"""
        
        # Call parent method first
        super()._display_readable_email(message)
        
        # Add extra debug information
        print("🔍 DEBUG INFORMATION:")
        print("-"*40)
        print(f"Message Type: {type(message).__name__}")
        print(f"Message ID: {getattr(message, 'extra_headers', {}).get('Message-ID', 'Not set')}")
        
        if hasattr(message, 'extra_headers') and message.extra_headers:
            print("Extra Headers:")
            for key, value in message.extra_headers.items():
                print(f"  {key}: {value}")
        
        print(f"Body Length: {len(message.body) if message.body else 0} characters")
        
        if hasattr(message, 'alternatives'):
            print(f"Number of Alternatives: {len(message.alternatives)}")
            for i, (content, content_type) in enumerate(message.alternatives):
                print(f"  Alternative {i+1}: {content_type} ({len(content)} characters)")
        
        print("-"*40)
