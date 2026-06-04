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
            messages.error(
                request,
                "Please select an Excel file before uploading."
            )
            return redirect("program_manage:bulk_upload")

        if not excel_file.name.endswith((".xlsx", ".xls")):
            messages.error(
                request,
                "Invalid file type. Please upload an Excel file (.xlsx or .xls)."
            )
            return redirect("program_manage:bulk_upload")

        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
        except Exception as exc:
            messages.error(
                request,
                f"Could not read file: {exc}"
            )
            return redirect("program_manage:bulk_upload")

        rows = list(sheet.iter_rows(values_only=True))

        if not rows:
            messages.error(
                request,
                "The uploaded Excel file is empty."
            )
            return redirect("program_manage:bulk_upload")

        headers = [
            str(value).strip().lower() if value is not None else ""
            for value in rows[0]
        ]

        missing_cols = [
            col
            for col in PROGRAM_BULK_REQUIRED_COLUMNS
            if col not in headers
        ]

        if missing_cols:
            messages.error(
                request,
                f"Missing columns: {', '.join(missing_cols)}"
            )
            return redirect("program_manage:bulk_upload")

        data_rows = [
            row
            for row in rows[1:]
            if any(value not in (None, "") for value in row)
        ]

        if not data_rows:
            messages.error(
                request,
                "No data rows found in the file."
            )
            return redirect("program_manage:bulk_upload")

        success_count = 0
        error_rows = []
        uploaded_codes = set()

        for index, row in enumerate(data_rows, start=2):

            row_data = dict(zip(headers, row))

            prog_type = str(
                row_data.get("prog_type") or ""
            ).strip().upper()

            prog_category = str(
                row_data.get("prog_category") or ""
            ).strip().title()

            degree = str(
                row_data.get("degree") or ""
            ).strip()

            branch = str(
                row_data.get("branch") or ""
            ).strip()

            prog_code = str(
                row_data.get("prog_code") or ""
            ).strip().upper().replace(" ", "")

            # Required field validation
            if not all([
                prog_type,
                prog_category,
                degree,
                branch,
                prog_code
            ]):
                error_rows.append(
                    f"Row {index}: All fields are required."
                )
                continue

            # Program Type validation
            if prog_type not in {"UG", "PG"}:
                error_rows.append(
                    f"Row {index}: Invalid Program Type '{prog_type}'."
                )
                continue

            # Program Category validation
            if prog_category not in {"Arts", "Science"}:
                error_rows.append(
                    f"Row {index}: Invalid Program Category '{prog_category}'."
                )
                continue

            # Duplicate inside uploaded file
            if prog_code in uploaded_codes:
                error_rows.append(
                    f"Row {index}: Duplicate Program Code '{prog_code}' in file."
                )
                continue

            uploaded_codes.add(prog_code)

            # Duplicate in database
            if Program.objects.filter(
                prog_code=prog_code
            ).exists():
                error_rows.append(
                    f"Row {index}: Program Code '{prog_code}' already exists."
                )
                continue

            try:
                Program.objects.create(
                    prog_code=prog_code,
                    degree=degree,
                    branch=branch,
                    prog_type=prog_type,
                    prog_category=prog_category,
                )

                success_count += 1

            except Exception as exc:
                error_rows.append(
                    f"Row {index}: {str(exc)}"
                )

        if success_count:
            messages.success(
                request,
                f"{success_count} program(s) uploaded successfully."
            )

        for error in error_rows:
            messages.warning(request, error)

        if success_count == 0:
            messages.error(
                request,
                "No programs were uploaded."
            )

        return redirect(
            "program_manage:program_management"
        )

    return render(
        request,
        "program_bulk_upload.html"
    )
    

@admin_required
def download_template(request):
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter
    from openpyxl.styles import Alignment, Border, Side

    wb = openpyxl.Workbook()

    # ── Sheet 1: Programs ────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Programs"

    HEADER_BG  = "1E40AF"
    HEADER_FG  = "FFFFFF"
    EXAMPLE_BG = "EFF6FF"
    BORDER_CLR = "CBD5E1"

    thin   = Side(style="thin", color=BORDER_CLR)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers    = ["prog_type", "prog_category", "degree", "branch", "prog_code"]
    col_widths = [16, 20, 24, 36, 20]
    col_notes  = [
        "UG or PG only",
        "Arts or Science only",
        "e.g. B.Sc, B.A, M.Sc, M.A",
        "e.g. Computer Science, Mathematics",
        "e.g. BSC-CS, BA-ENG (auto-uppercased)",
    ]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font      = Font(bold=True, color=HEADER_FG, name="Arial", size=11)
        cell.fill      = PatternFill("solid", start_color=HEADER_BG)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[1].height = 30

    for col, note in enumerate(col_notes, 1):
        cell = ws.cell(row=2, column=col, value=note)
        cell.font      = Font(italic=True, color="92400E", name="Arial", size=9)
        cell.fill      = PatternFill("solid", start_color="FEF3C7")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
    ws.row_dimensions[2].height = 28

    examples = [
        ("UG", "Science", "B.Sc", "Computer Science", "BSC-CS"),
        ("UG", "Arts",    "B.A",  "English",           "BA-ENG"),
        ("PG", "Science", "M.Sc", "Mathematics",       "MSC-MATHS"),
    ]
    for r, row_data in enumerate(examples, 3):
        for c, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font      = Font(name="Arial", size=10, color="1E3A5F")
            cell.fill      = PatternFill("solid", start_color=EXAMPLE_BG)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border    = border

    for r in range(6, 201):
        for c in range(1, 6):
            cell = ws.cell(row=r, column=c)
            cell.font      = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border    = border

    ws.freeze_panes = "A3"

    dv_type = DataValidation(
        type="list", formula1='"UG,PG"', allow_blank=False,
        showDropDown=False,
        error="Only UG or PG allowed.", errorTitle="Invalid prog_type",
        prompt="Select UG or PG", promptTitle="prog_type"
    )
    dv_cat = DataValidation(
        type="list", formula1='"Arts,Science"', allow_blank=False,
        showDropDown=False,
        error="Only Arts or Science allowed.", errorTitle="Invalid prog_category",
        prompt="Select Arts or Science", promptTitle="prog_category"
    )
    ws.add_data_validation(dv_type)
    ws.add_data_validation(dv_cat)
    dv_type.sqref = "A3:A200"
    dv_cat.sqref  = "B3:B200"

    # ── Sheet 2: Instructions ────────────────────────────────────────────────
    wi = wb.create_sheet("Instructions")
    wi.column_dimensions["A"].width = 22
    wi.column_dimensions["B"].width = 60

    def ins_row(r, label, value):
        lc = wi.cell(row=r, column=1, value=label)
        lc.font      = Font(bold=True, name="Arial", size=10, color="1E40AF")
        lc.alignment = Alignment(vertical="top")
        vc = wi.cell(row=r, column=2, value=value)
        vc.font      = Font(name="Arial", size=10)
        vc.alignment = Alignment(vertical="top", wrap_text=True)
        wi.row_dimensions[r].height = 20

    wi.cell(row=1, column=1, value="Program Bulk Upload – Instructions").font = Font(
        bold=True, size=13, color="1E40AF", name="Arial"
    )
    wi.merge_cells("A1:B1")
    wi.row_dimensions[1].height = 28

    ins_row(3,  "Sheet to edit:",   "Fill data in the 'Programs' sheet only. Do NOT rename columns.")
    ins_row(4,  "Row 1:",           "Column headers – do not modify.")
    ins_row(5,  "Row 2:",           "Notes/hints – you may delete this row before uploading.")
    ins_row(6,  "Rows 3-5:",        "Example data – delete before uploading.")
    ins_row(7,  "Rows 6+:",         "Enter your program data here.")
    ins_row(9,  "prog_type",        "Must be exactly: UG  or  PG  (dropdown enforced).")
    ins_row(10, "prog_category",    "Must be exactly: Arts  or  Science  (dropdown enforced).")
    ins_row(11, "degree",           "Free text. Examples: B.Sc, B.A, M.Sc, M.A, B.Com, M.Com.")
    ins_row(12, "branch",           "Full branch/department name. E.g. 'Computer Science', 'Tamil'.")
    ins_row(13, "prog_code",        "Short unique code. Spaces and lowercase are auto-corrected.")
    ins_row(15, "Duplicates:",      "Rows where all five fields already exist will be skipped with a warning.")
    ins_row(16, "Empty rows:",      "Rows where any field is blank will be skipped with a warning.")
    ins_row(17, "File format:",     "Save as .xlsx or .xls before uploading.")
    wi.sheet_view.showGridLines = False

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="program_upload_template.xlsx"'
    wb.save(response)
    return response


@admin_required
def get_filter_options(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    queryset = Program.objects.filter(is_active=True)
    return JsonResponse(_build_program_filter_options(queryset, filters))
