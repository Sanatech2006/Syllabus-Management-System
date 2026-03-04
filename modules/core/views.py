from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    next_url = request.GET.get('next', '/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        post_next = request.POST.get('next', '/dashboard/').strip()

        # Always ensure a safe redirect path
        if not post_next or not post_next.startswith('/'):
            post_next = '/dashboard/'

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or username}!')
            return redirect(post_next)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/login/')


def dashboard(request):
    return render(request, 'dashboard.html')