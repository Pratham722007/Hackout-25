# sms_app/utils.py
import requests
from django.conf import settings

CLERK_API_KEY = settings.CLERK_API_KEY

def get_logged_in_user_email(clerk_user_id):
    """Fetch user email from Clerk API using user ID"""
    headers = {"Authorization": f"Bearer {CLERK_API_KEY}"}
    url = f"https://api.clerk.com/v1/users/{clerk_user_id}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        return data["email_addresses"][0]["email_address"]
    return None

# sms_app/utils.py
from django.core.mail import send_mail

def send_test_alert(email, message="This is a test SMS alert!"):
    # Print to terminal for dev
    print(f"[ALERT MOCK] To: {email}, Message: {message}")

    # Optional: send as email in dev
    send_mail(
        subject="Test Alert",
        message=message,
        from_email="noreply@mysite.com",
        recipient_list=[email],
        fail_silently=False,
    )
