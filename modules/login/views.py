from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials!')
    
    # ✅ USE YOUR EXISTING PROJECT-LEVEL TEMPLATE
    return render(request, 'login.html')  # Found in templates/login.html

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('core:login')
