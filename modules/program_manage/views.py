import openpyxl
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl.styles import Font, PatternFill

from modules.core.decorators import admin_required

from .models import Program


PROGRAM_FILTER_FIELDS = (
    "prog_type",
    "prog_category",
    "degree",
    "branch",
    "prog_code",
)

PROGRAM_BULK_REQUIRED_COLUMNS = (
    "prog_type",
    "prog_category",
    "degree",
    "branch",
    "prog_code",
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
        "prog_types": _distinct_non_empty(option_querysets["prog_type"], "prog_type"),
        "prog_categories": _distinct_non_empty(option_querysets["prog_category"], "prog_category"),
        "degrees": _distinct_non_empty(option_querysets["degree"], "degree"),
        "branches": _distinct_non_empty(option_querysets["branch"], "branch"),
        "prog_codes": _distinct_non_empty(option_querysets["prog_code"], "prog_code"),
    }


@admin_required
def program_management(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    base_queryset = Program.objects.filter(is_active=True)
    programs = _apply_program_filters(base_queryset, filters)
    filter_options = _build_program_filter_options(base_queryset, filters)

    paginator = Paginator(programs.order_by("id"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "program_management.html",
        {
            "programs": page_obj,
            "page_obj": page_obj,
            "pagination_query": query_params.urlencode(),
            **filter_options,
            "arts_count": base_queryset.filter(prog_category="Arts").count(),
            "science_count": base_queryset.filter(prog_category="Science").count(),
            "ug_count": base_queryset.filter(prog_type="UG").count(),
            "pg_count": base_queryset.filter(prog_type="PG").count(),
        },
    )


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
            return render(
                request,
                "add_program.html",
                {
                    "preview_programs": preview_programs,
                    "edit_index": index,
                },
            )

        if action == "update":
            index = int(request.POST.get("index"))
            if 0 <= index < len(preview_programs):
                preview_programs[index] = {
                    "prog_type": request.POST.get("prog_type"),
                    "prog_category": request.POST.get("prog_category"),
                    "degree": request.POST.get("degree"),
                    "branch": request.POST.get("branch"),
                    "prog_code": request.POST.get("prog_code"),
                }
                request.session["preview_programs"] = preview_programs
            return redirect("program_manage:add_program")

        if action == "cancel":
            return redirect("program_manage:add_program")

        if action == "add":
            Program.objects.create(
                prog_type=request.POST.get("prog_type"),
                prog_category=request.POST.get("prog_category"),
                degree=request.POST.get("degree"),
                branch=request.POST.get("branch"),
                prog_code=request.POST.get("prog_code"),
            )
            messages.success(request, "Program added successfully!")
            return redirect("program_manage:program_management")

    return render(request, "add_program.html")


@admin_required
def edit_program(request, id):
    program = get_object_or_404(Program, id=id)

    if request.method == "POST":
        program.prog_type = request.POST.get("prog_type")
        program.prog_category = request.POST.get("prog_category")
        program.degree = request.POST.get("degree")
        program.branch = request.POST.get("branch")
        program.prog_code = request.POST.get("prog_code")
        program.save()
        messages.success(request, "Program updated successfully!")
        return redirect("program_manage:program_management")

    return render(
        request,
        "add_program.html",
        {
            "edit_program": program,
            "preview_programs": [],
        },
    )


@admin_required
def delete_program(request, id):
    program = get_object_or_404(Program, id=id)
    program.delete()
    messages.success(request, "Program deleted successfully!")
    return redirect("program_manage:program_management")


@admin_required
def bulk_upload(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please select an Excel file before uploading.")
            return redirect("program_manage:bulk_upload")

        if not excel_file.name.endswith((".xlsx", ".xls")):
            messages.error(request, "Invalid file type. Please upload an Excel file (.xlsx or .xls).")
            return redirect("program_manage:bulk_upload")

        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
        except Exception as exc:
            messages.error(request, f"Could not read file: {exc}")
            return redirect("program_manage:bulk_upload")

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            messages.error(request, "The uploaded Excel file is empty. Please add data and try again.")
            return redirect("program_manage:bulk_upload")

        headers = [str(value).strip().lower() if value is not None else "" for value in rows[0]]
        missing_cols = [col for col in PROGRAM_BULK_REQUIRED_COLUMNS if col not in headers]
        if missing_cols:
            messages.error(
                request,
                f"Missing columns: {', '.join(missing_cols)}. Required: {', '.join(PROGRAM_BULK_REQUIRED_COLUMNS)}"
            )
            return redirect("program_manage:bulk_upload")

        data_rows = [row for row in rows[1:] if any(value not in (None, "") for value in row)]
        if not data_rows:
            messages.error(request, "No data rows found in the file.")
            return redirect("program_manage:bulk_upload")

        success_count = 0
        error_rows = []

        for index, row in enumerate(data_rows, start=2):
            row_data = dict(zip(headers, row))

            prog_type = str(row_data.get("prog_type") or "").strip().upper()
            prog_category = str(row_data.get("prog_category") or "").strip().title()
            degree = str(row_data.get("degree") or "").strip()
            branch = str(row_data.get("branch") or "").strip()
            prog_code = str(row_data.get("prog_code") or "").strip().upper().replace(" ", "")

            if not all([prog_type, prog_category, degree, branch, prog_code]):
                error_rows.append(f"Row {index}: All program fields are required — skipped.")
                continue

            if Program.objects.filter(
                prog_type=prog_type,
                prog_category=prog_category,
                degree=degree,
                branch=branch,
                prog_code=prog_code,
            ).exists():
                error_rows.append(f"Row {index}: Program {prog_code} already exists — skipped.")
                continue

            Program.objects.create(
                prog_type=prog_type,
                prog_category=prog_category,
                degree=degree,
                branch=branch,
                prog_code=prog_code,
            )
            success_count += 1

        if success_count:
            messages.success(request, f"Successfully uploaded {success_count} program(s).")
        if error_rows:
            for error in error_rows:
                messages.warning(request, error)
        if success_count == 0 and not error_rows:
            messages.error(request, "No programs were uploaded. Please check your file.")

        return redirect("program_manage:program_management")

    return render(request, "program_bulk_upload.html")


@admin_required
def download_template(request):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Program Template"

    headings = ["prog_type", "prog_category", "degree", "branch", "prog_code"]

    for col_num, heading in enumerate(headings, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.value = heading
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="program_upload_template.xlsx"'
    workbook.save(response)
    return response


@admin_required
def get_filter_options(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    queryset = Program.objects.filter(is_active=True)
    return JsonResponse(_build_program_filter_options(queryset, filters))
