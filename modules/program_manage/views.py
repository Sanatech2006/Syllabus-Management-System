from .models import Program
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from modules.upload_center.models import CourseStr
from modules.core.decorators import admin_required


PROGRAM_FILTER_FIELDS = (
    "year",
    "prog_type",
    "prog_category",
    "prog_code",
    "branch",
)


def _distinct_non_empty(queryset, field_name):
    return list(
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _apply_program_filters(queryset, filters, exclude_field=None):
    for field in PROGRAM_FILTER_FIELDS:
        if field == exclude_field:
            continue

        value = filters.get(field)
        if value:
            queryset = queryset.filter(**{field: value})

    return queryset


def _build_program_filter_options(base_queryset, filters):
    option_querysets = {
        field: _apply_program_filters(base_queryset, filters, exclude_field=field)
        for field in PROGRAM_FILTER_FIELDS
    }

    return {
        "years": _distinct_non_empty(option_querysets["year"], "year"),
        "prog_types": _distinct_non_empty(option_querysets["prog_type"], "prog_type"),
        "prog_categories": _distinct_non_empty(option_querysets["prog_category"], "prog_category"),
        "prog_codes": _distinct_non_empty(option_querysets["prog_code"], "prog_code"),
        "branches": _distinct_non_empty(option_querysets["branch"], "branch"),
    }


@admin_required
def program_management(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    base_queryset = Program.objects.filter(is_active=True)
    programs = _apply_program_filters(base_queryset, filters)
    filter_options = _build_program_filter_options(base_queryset, filters)

    paginator = Paginator(programs.order_by("id"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "program_management.html", {
    "programs": page_obj,
    "page_obj": page_obj,
    **filter_options,
    'arts_count': base_queryset.filter(prog_category='Arts').count(),
    'science_count': base_queryset.filter(prog_category='Science').count(),
    'ug_count': base_queryset.filter(prog_type='UG').count(),
    'pg_count': base_queryset.filter(prog_type='PG').count(),
    })


@admin_required
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
            Program.objects.create(
            year=request.POST.get("year"),
            prog_type=request.POST.get("prog_type"),
            prog_category=request.POST.get("prog_category"),
            prog_code=request.POST.get("prog_code"),
            branch=request.POST.get("branch"),
    )

        messages.success(request, "Program added successfully!")

        return redirect("program_manage:program_management")  # 🔥 redirect here

    return render(request, "add_program.html")
    
@admin_required
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

    # ✅ ADD THIS
    science_count = CourseStr.objects.filter(
        is_finalized=True,
        branch="Science"
    ).count()

    return render(request, "program_management.html", {
        "edit_program": program,
        "preview_programs": [],
        "science_count": science_count,   # ✅ ADD THIS
    })

@admin_required
def delete_program(request, id):
    program = get_object_or_404(Program, id=id)
    program.delete()
    messages.success(request, "Program deleted successfully!")
    return redirect("program_manage:program_management")


@admin_required
def get_filter_options(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    queryset = Program.objects.filter(is_active=True)
    return JsonResponse(_build_program_filter_options(queryset, filters))
