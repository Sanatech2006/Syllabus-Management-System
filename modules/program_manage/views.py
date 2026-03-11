from .models import Program
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator


@login_required(login_url='/login/')
def program_management(request):
    programs = Program.objects.filter(is_active=True)

    year = request.GET.get("year")
    prog_type = request.GET.get("prog_type")
    prog_category = request.GET.get("prog_category")
    prog_code = request.GET.get("prog_code")
    branch = request.GET.get("branch")

    if year:
        programs = programs.filter(year=year)
    if prog_type:
        programs = programs.filter(prog_type=prog_type)
    if prog_category:
        programs = programs.filter(prog_category=prog_category)
    if prog_code:
        programs = programs.filter(prog_code__icontains=prog_code)
    if branch:
        programs = programs.filter(branch=branch)

    paginator = Paginator(programs.order_by("id"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    branches = Program.objects.values_list("branch", flat=True).distinct()

    return render(request, "program_management.html", {
    "programs": page_obj,
    "page_obj": page_obj,
    "branches": branches,
    'arts_count': Program.objects.filter(is_active=True, prog_category='Arts').count(),
    'science_count': Program.objects.filter(is_active=True, prog_category='Science').count(),
    'ug_count': Program.objects.filter(is_active=True, prog_type='UG').count(),
    'pg_count': Program.objects.filter(is_active=True, prog_type='PG').count(),
    })


@login_required(login_url='/login/')
def add_program(request):
    preview_programs = request.session.get("preview_programs", [])

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete":
            index = int(request.POST.get("index"))
            if 0 <= index < len(preview_programs):
                preview_programs.pop(index)
                request.session["preview_programs"] = preview_programs
            return redirect("program_manage:add_program")

        if action == "edit":
            index = int(request.POST.get("index"))
            return render(request, "add_program.html", {
                "preview_programs": preview_programs,
                "edit_index": index,
            })

        if action == "update":
            index = int(request.POST.get("index"))
            if 0 <= index < len(preview_programs):
                preview_programs[index] = {
                    "year": request.POST.get("year"),
                    "prog_type": request.POST.get("prog_type"),
                    "prog_category": request.POST.get("prog_category"),
                    "prog_code": request.POST.get("prog_code"),
                    "branch": request.POST.get("branch"),
                }
                request.session["preview_programs"] = preview_programs
            return redirect("program_manage:add_program")

        if action == "cancel":
            return redirect("program_manage:add_program")

        if action == "add":
            new_program = {
                "year": request.POST.get("year"),
                "prog_type": request.POST.get("prog_type"),
                "prog_category": request.POST.get("prog_category"),
                "prog_code": request.POST.get("prog_code"),
                "branch": request.POST.get("branch"),
            }
            preview_programs.append(new_program)
            request.session["preview_programs"] = preview_programs

        elif action == "save":
            saved_count = 0
            skipped_count = 0
            for p in preview_programs:
                obj, created = Program.objects.get_or_create(**p)
                if created:
                    saved_count += 1
                else:
                    skipped_count += 1
            request.session["preview_programs"] = []
            if saved_count:
                messages.success(request, f"{saved_count} program(s) saved successfully!")
            if skipped_count:
                messages.warning(request, f"{skipped_count} duplicate program(s) skipped.")
            return redirect("program_manage:add_program")

    return render(request, "add_program.html", {"preview_programs": preview_programs})


@login_required(login_url='/login/')
def edit_program(request, id):
    program = get_object_or_404(Program, id=id)

    if request.method == "POST":
        program.year = request.POST.get("year")
        program.prog_type = request.POST.get("prog_type")
        program.prog_category = request.POST.get("prog_category")
        program.prog_code = request.POST.get("prog_code")
        program.branch = request.POST.get("branch")
        program.save()
        messages.success(request, "Program updated successfully!")
        return redirect("program_manage:program_management")

    return render(request, "program_management.html", {
        "edit_program": program,
        "preview_programs": [],
    })


@login_required(login_url='/login/')
def delete_program(request, id):
    program = get_object_or_404(Program, id=id)
    program.delete()
    messages.success(request, "Program deleted successfully!")
    return redirect("program_manage:program_management")