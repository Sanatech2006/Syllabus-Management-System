from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

def user_management(request):

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Split full name into first & last
        first_name = full_name.split()[0]
        last_name = " ".join(full_name.split()[1:])

        # IMPORTANT: use create_user (hashes password)
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        return redirect("user_manage:user_management")

    users = User.objects.all()

    return render(request, "user_mgt.html", {
        "users": users,
        "total_users": users.count(),
    })

def add_user(request):
    if request.method == "POST":
        User = get_user_model()

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 🔐 Role mapping using Django fields
        if role == "ADMIN":
            user.is_superuser = True
            user.is_staff = True
        elif role == "HOD":
            user.is_staff = True
        else:
            user.is_staff = False
            user.is_superuser = False

        user.save()

        return redirect("user_manage:user_management")

def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")

        new_password = request.POST.get("password")

        # Only change password if filled
        if new_password:
            user.set_password(new_password)

        user.save()
        return redirect("user_manage:user_management")

    return render(request, "edit_user.html", {"user": user})