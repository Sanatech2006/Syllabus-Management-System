from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from modules.dashboard.views import dashboard as dashboard_view


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
        return not user.is_superuser
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

        # HOD usernames are stored in uppercase
        if post_role == 'hod':
            username = username.upper()

        # Always ensure a safe redirect path
        if not post_next or not post_next.startswith('/'):
            post_next = '/dashboard/'

        try:
            User = get_user_model()
            user_exists = User.objects.filter(username=username).exists()

            if not user_exists:
                messages.error(request, 'Username not found.')
            else:
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
                    messages.error(request, 'Incorrect password.')
        except Exception:
            messages.error(request, 'Server error. Please try again later.')

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


from django.http import JsonResponse
from modules.core.utils import get_upload_progress

def upload_progress_view(request):
    upload_id = request.GET.get('upload_id')
    if not upload_id:
        return JsonResponse({'error': 'Missing upload_id'}, status=400)
    progress = get_upload_progress(upload_id)
    if progress is None:
        return JsonResponse({'status': 'not_found', 'current': 0, 'total': 0})
    return JsonResponse(progress)
