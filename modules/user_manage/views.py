from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

User = get_user_model()

@login_required(login_url='/login/')
def user_management(request):
    """Display user management table with stats."""
    users = User.objects.all()

    context = {
        "users": users,
        "total_users": users.count(),
        "admin_count": users.filter(is_superuser=True).count(),
        "hod_count": users.filter(is_staff=True, is_superuser=False).count(),
        "staff_student_count": users.filter(is_staff=False, is_superuser=False).count(),
    }
    return render(request, "user_mgt.html", context)

@login_required(login_url='/login/')
def add_user(request):
    """Handle creation of a new user from the modal."""
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role", "HOD")

        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        is_superuser = role == "ADMIN"
        is_staff = role in ["ADMIN", "HOD"]

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_superuser=is_superuser,
            is_staff=is_staff
        )

    return redirect("user_manage:user_management")

@login_required(login_url='/login/')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")

        full_name = request.POST.get("full_name", "").strip()
        parts = full_name.split()
        user.first_name = parts[0] if parts else ""
        user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        new_password = request.POST.get("password")
        if new_password:
            user.set_password(new_password)
            if request.user == user:
                update_session_auth_hash(request, user)

        role = request.POST.get("role", "HOD")
        user.is_superuser = role == "ADMIN"
        user.is_staff = role in ["ADMIN", "HOD"]

        user.save()

    return redirect("user_manage:user_management")