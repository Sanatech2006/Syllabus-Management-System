from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from modules.dashboard.views import dashboard as dashboard_view
from modules.course_management.access import is_hod_user


def _get_role_home(user):
    if user.is_superuser:
        return '/dashboard/'
    if user.is_staff:
        return '/dashboard/'
    return '/dashboard/'


def _role_matches_user(role, user):
    if not role:
        return True
    if role == 'admin':
        return user.is_superuser
    if role == 'hod':
        return is_hod_user(user) or (user.is_staff and not user.is_superuser)
    return False


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_get_role_home(request.user))

    next_url = request.GET.get('next', '/dashboard/')
    role = request.GET.get('role', '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        post_next = request.POST.get('next', '/dashboard/').strip()
        post_role = request.POST.get('role', '').strip()

        # Always ensure a safe redirect path
        if not post_next or not post_next.startswith('/'):
            post_next = '/dashboard/'

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not _role_matches_user(post_role, user):
                messages.error(request, 'Those credentials do not match the selected role.')
                return render(request, 'login.html', {'next': post_next, 'role': post_role})

            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or username}!')

            if post_role in {'admin', 'hod'}:
                return redirect(_get_role_home(user))

            return redirect(post_next or _get_role_home(user))
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'login.html', {'next': next_url, 'role': role})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')


def dashboard(request):
    return dashboard_view(request)


def home(request):
    if request.user.is_authenticated:
        logout(request)

    return dashboard_view(request)
