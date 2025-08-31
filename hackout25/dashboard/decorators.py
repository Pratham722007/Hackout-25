"""
Custom authentication decorators for Clerk integration
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.conf import settings


def clerk_authentication_optional(view_func):
    """
    Decorator that allows both authenticated and unauthenticated access
    but handles Clerk authentication gracefully
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # For now, allow access but log authentication status
        if request.user.is_authenticated:
            print(f"DEBUG: Authenticated user {request.user.username} accessing {view_func.__name__}")
        else:
            print(f"DEBUG: Unauthenticated user accessing {view_func.__name__}")
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def clerk_authentication_preferred(view_func):
    """
    Decorator that prefers authentication but allows unauthenticated access
    with limited functionality
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # For dashboard and analysis views, we might want to redirect to login
            # But for now, we'll allow access with limited data
            print(f"DEBUG: Unauthenticated access to {view_func.__name__} - showing limited data")
        else:
            print(f"DEBUG: Authenticated user {request.user.username} accessing {view_func.__name__}")
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def require_authentication(view_func):
    """
    Decorator that requires some form of authentication but is more lenient than @login_required
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for Django authentication first
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # If no Django authentication, check if there's a way to determine user from headers
        # This is where you might integrate with Clerk's backend validation
        
        # For now, redirect to sign-in for required views
        print(f"DEBUG: Authentication required for {view_func.__name__} - redirecting to sign-in")
        return redirect('/sign-in/')
    
    return _wrapped_view
