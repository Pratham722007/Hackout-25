# Email Alert Testing System - User Guide

## Overview
This guide explains how to test the email alert notification system with Clerk user integration in the EcoValidate Django application.

## Features
✅ **Clerk Integration**: Fetches user data from Clerk authentication system  
✅ **Terminal Email Output**: Prints emails directly to terminal for easy testing  
✅ **Multiple User Selection**: Test with user ID, email, or Clerk user ID  
✅ **Custom Alert Content**: Send personalized alert messages  
✅ **Priority Levels**: Support for low, medium, high, and critical alerts  
✅ **Beautiful Templates**: Uses existing HTML and text email templates  
✅ **User Management**: Create test users and list available users  

## Quick Start

### 1. Create a Test User
```bash
python manage.py test_email_alerts --create-test-user
```

### 2. Send Test Email
```bash
python manage.py test_email_alerts --user-id 2
```

### 3. List Available Users
```bash
python manage.py test_email_alerts --list-users
```

## Command Usage

### Basic Commands
```bash
# Test with user ID
python manage.py test_email_alerts --user-id 1

# Test with email address
python manage.py test_email_alerts --email user@example.com

# Test with Clerk user ID  
python manage.py test_email_alerts --clerk-user-id clerk_12345

# List all available users
python manage.py test_email_alerts --list-users

# Create a new test user
python manage.py test_email_alerts --create-test-user
```

### Advanced Options
```bash
# Custom alert message
python manage.py test_email_alerts --user-id 2 --alert-text "Custom alert message"

# Set priority level
python manage.py test_email_alerts --user-id 2 --priority critical

# Custom location
python manage.py test_email_alerts --user-id 2 --location "San Francisco, CA"

# Combine all options
python manage.py test_email_alerts \
  --email user@example.com \
  --alert-text "Critical environmental issue detected!" \
  --priority critical \
  --location "Industrial District"
```

## Priority Levels
- **low**: 📢 Info - Information Only
- **medium**: ⚠️ Alert - Attention Required (default)
- **high**: 🚨 Urgent Alert - Urgent Action Needed
- **critical**: 🔴 CRITICAL ALERT - Immediate Response Required

## Email Output Location
Since the Django settings use `django.core.mail.backends.console.EmailBackend`, all emails are printed directly to your terminal/console. Look for email content above the success message.

## System Components

### 1. EmailTestService (`dashboard/services/email_test_service.py`)
Core service handling:
- Clerk user data fetching
- Test alert creation
- Email sending
- User management

### 2. Management Command (`dashboard/management/commands/test_email_alerts.py`)
Command-line interface for email testing with comprehensive options and help.

### 3. Web API Views (`dashboard/views/email_test_views.py`)
RESTful API endpoints for web-based testing:
- `POST /api/test-email-alert/` - Send test email
- `GET /api/list-users/` - List available users  
- `POST /api/create-test-user/` - Create test user
- `GET /test-current-user/` - Test current logged-in user

### 4. Models Integration
Uses existing models:
- `Alert` - Stores alert information
- `AlertRecipient` - Tracks email delivery status
- `UserProfile` - Links Django users with Clerk data

## Clerk Integration Features

### User Data Fetched from Clerk:
- Clerk User ID
- Verification status
- Account creation date
- User profile information

### Supports Multiple User Lookup Methods:
```python
# By Clerk user ID
EmailTestService.get_current_user_from_clerk(clerk_user_id="clerk_12345")

# By Django user ID
EmailTestService.get_current_user_from_clerk(user_id=1)

# By email address
EmailTestService.get_current_user_from_clerk(email="user@example.com")
```

## Email Templates
Uses the existing professional email templates:
- `dashboard/templates/emails/alert_notification.html` (HTML version)
- `dashboard/templates/emails/alert_notification.txt` (Text version)

## Example Output
```
🧪 Starting Email Verification Test...
==================================================
📋 Step 1: Fetching user data from Clerk integration...
✅ User found: Test User (test@example.com)
   Clerk ID: clerk_test_abc123
   Verified: True

📧 Step 2: Creating and sending test alert email...
[EMAIL CONTENT DISPLAYED IN TERMINAL]

✅ Email sent successfully!
   Alert ID: 1
   Sent to: test@example.com
   Sent at: 2025-08-30 17:50:49.429580+00:00

🔧 Step 3: Email Configuration Check...
   Email Backend: django.core.mail.backends.console.EmailBackend
   From Email: EcoValidate <noreply@ecovalidate.com>
   📺 EMAIL OUTPUT: Check your terminal/console for email content!
   
==================================================
🧪 Email Verification Test Complete!
```

## Troubleshooting

### No Users Found
```bash
# Create a test user
python manage.py test_email_alerts --create-test-user

# Then test with the new user
python manage.py test_email_alerts --user-id 2
```

### User Not Found
```bash
# List available users first
python manage.py test_email_alerts --list-users

# Use correct user ID/email from the list
python manage.py test_email_alerts --user-id <correct_id>
```

### Email Not Displaying
- Ensure you're looking at terminal output above the success message
- Check that `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in settings
- Both HTML and plain text versions are displayed

## Integration with Existing Code
The email testing system integrates seamlessly with the existing alert system:
- Uses existing `AlertEmailService` for email sending
- Leverages existing email templates
- Maintains compatibility with existing `Alert` and `AlertRecipient` models
- Works with current Clerk authentication setup

## API Endpoints (for web integration)
```javascript
// Send test email
POST /api/test-email-alert/
{
  "user_id": 2,
  "alert_text": "Custom message",
  "priority": "high",
  "location": "Test Location"
}

// List users
GET /api/list-users/

// Create test user
POST /api/create-test-user/

// Test current user
GET /test-current-user/
```

## Best Practices
1. Always create test users for testing to avoid affecting real users
2. Use appropriate priority levels for different test scenarios
3. Test with both Clerk-integrated users and regular Django users
4. Check terminal output carefully for email content
5. Use custom alert text to verify specific functionality

This email testing system provides a comprehensive way to verify that your alert notification system is working correctly with proper Clerk integration and beautiful email templates! 🧪📧✅
