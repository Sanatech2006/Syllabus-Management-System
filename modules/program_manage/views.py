from .models import Program
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator



# 🔐 LOGIN PAGE (PROJECT LEVEL)
def login_page(request):
    error = ""

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirect to dashboard after login
        else:
            error = "Invalid username or password"

    return render(request, "login_front.html", {"error": error})


# 🚪 LOGOUT
def logout_view(request):
    logout(request)
    return redirect("login")


# 📚 PROGRAM MANAGEMENT (PROTECTED)
@login_required(login_url="login")
def program_management(request):

    programs = Program.objects.filter(is_active=True)

    # Get filter values
    year = request.GET.get("year")
    prog_type = request.GET.get("prog_type")
    prog_category = request.GET.get("prog_category")
    branch = request.GET.get("branch")

    semester = request.GET.get("semester")
   
    # Apply filters
    if year:
        programs = programs.filter(year=year)

    if prog_type:
        programs = programs.filter(prog_type=prog_type)

    if prog_category:
        programs = programs.filter(prog_category=prog_category)

    if branch:
        programs = programs.filter(branch=branch)    

    if semester:
        programs = programs.filter(semester=semester)

     # PAGINATION (10 per page)
    paginator = Paginator(programs.order_by("id"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    # Get distinct branches for dropdown
    branches = Program.objects.values_list("branch", flat=True).distinct()

    return render(
    request,
    "program_management.html",
    {
        "programs": page_obj,   # table loop
        "page_obj": page_obj,   # pagination controls
        "branches": branches,
    }
)

# ➕ ADD PROGRAM (PROTECTED)
@login_required(login_url="login")
def add_program(request):
    preview_programs = request.session.get("preview_programs", [])
     
    if request.method == "POST":
        action = request.POST.get("action")

         # ---------------- DELETE ----------------
        if action == "delete":
            index = int(request.POST.get("index"))
            if 0 <= index < len(preview_programs):
                preview_programs.pop(index)
                request.session["preview_programs"] = preview_programs
            return redirect("add_program")

        # ---------------- EDIT CLICK ----------------
        if action == "edit":
            index = int(request.POST.get("index"))
            return render(
                request,
                "add_program.html",
                {
                    "preview_programs": preview_programs,
                    "edit_index": index
                }
            )

        # ---------------- UPDATE ROW (STEP 2 GOES HERE) ----------------
        if action == "update":
            index = int(request.POST.get("index"))

            if 0 <= index < len(preview_programs):
                preview_programs[index] = {
                    "year": request.POST.get("year"),
                    "prog_type": request.POST.get("prog_type"),
                    "prog_category": request.POST.get("prog_category"),
                    "branch": request.POST.get("branch"),
                    "semester": request.POST.get("semester"),
                }

                request.session["preview_programs"] = preview_programs

            return redirect("add_program")

        # ---------------- CANCEL EDIT ----------------
        if action == "cancel":
            return redirect("add_program")


        # STEP 1: Add to preview grid (NOT DB)
        if action == "add":
            new_program = {
                "year": request.POST.get("year"),
                "prog_type": request.POST.get("prog_type"),
                "prog_category": request.POST.get("prog_category"),
                "branch": request.POST.get("branch"),
                "semester": request.POST.get("semester"),
            }

            preview_programs.append(new_program)
            request.session["preview_programs"] = preview_programs

        # STEP 2: Save preview grid to DATABASE (SAFE SAVE)
        elif action == "save":
            saved_count = 0
            skipped_count = 0

            for p in preview_programs:
                obj, created = Program.objects.get_or_create(**p)

                if created:
                    saved_count += 1
                else:
                    skipped_count += 1

            # clear preview session
            request.session["preview_programs"] = []

            # success + warning messages
            if saved_count:
                messages.success(request, f"{saved_count} program(s) saved successfully!")

            if skipped_count:
                messages.warning(request, f"{skipped_count} duplicate program(s) skipped.")

            return redirect("add_program")

    return render(
        request,
        "add_program.html",
        {"preview_programs": preview_programs},
    )

