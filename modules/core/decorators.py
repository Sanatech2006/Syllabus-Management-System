from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def login_required_custom(view_func):
    """
    Simple decorator that redirects to login if user is not authenticated.
    Dashboard and Course Management are NOT protected by this decorator.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If user is not authenticated, redirect to login
        if not request.user.is_authenticated:
            # Store the current path to redirect back after login
            request.session['next_url'] = request.path
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            request.session['next_url'] = request.path
            return redirect('/login/')

        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access that section.')
            return redirect('/dashboard/')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
