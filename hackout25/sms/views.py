# sms_app/views.py
from django.shortcuts import render
from .forms import SMSMessageForm
from .utils import get_logged_in_user_email, send_test_alert

def create_sms(request):
    """
    View to create SMSMessage, fetch logged-in user's email from Clerk,
    and send a test alert in development.
    """
    if request.method == "POST":
        form = SMSMessageForm(request.POST)
        if form.is_valid():
            sms = form.save(commit=False)  # Don't save yet if you want
            
            # --- Fetch logged-in user email from Clerk ---
            # In dev, get Clerk user ID from headers or JWT
            clerk_user_id = request.headers.get("Clerk-User-Id")  # adjust based on your setup
            if clerk_user_id:
                user_email = get_logged_in_user_email(clerk_user_id)
                if user_email:
                    send_test_alert(user_email, sms.message)
            
            sms.save()  # Save the SMS message to DB
            return render(request, "sms_app/success.html", {"form": form, "msg": "SMS test alert sent!"})
        else:
            # form invalid
            return render(request, "sms_app/create_sms.html", {"form": form})
    else:
        form = SMSMessageForm()
    
    return render(request, "sms_app/create_sms.html", {"form": form})
