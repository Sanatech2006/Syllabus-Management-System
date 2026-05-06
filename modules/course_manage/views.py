from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from modules.upload_center.models import CourseStr, CourseContent, normalize_course_code
from django.http import HttpResponse, FileResponse, Http404
import os
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
import pandas as pd
from decimal import Decimal, InvalidOperation


# Required columns that must exist in the Excel file
REQUIRED_COLUMNS = [
    'prog_code', 'year', 'prog_type', 'prog_category', 'sem',
    'course_code', 'part', 'course_category', 'course_title',
    'hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks'
]

# Decimal fields that need type conversion
DECIMAL_FIELDS = ['hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks']

# Text fields
TEXT_FIELDS = [
    'prog_code', 'year', 'prog_type', 'prog_category', 'sem',
    'course_code', 'part', 'course_category', 'course_title'
]


COURSE_FILTER_FIELDS = (
    'year',
    'prog_type',
    'prog_category',
    'course_category',
    'prog_code',
    'branch',
    'part',
    'sem',
    'course_code',
    'course_title',
)


def to_decimal(value):
    """Safely convert a value to Decimal, return None if invalid."""
    try:
        if value is None or str(value).strip() in ('', 'nan', 'NaN', 'None'):
            return None
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _distinct_non_empty(queryset, field_name):
    return list(
        queryset.exclude(**{f'{field_name}__isnull': True})
        .exclude(**{field_name: ''})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _apply_course_filters(queryset, filters, exclude_field=None):
    for field in COURSE_FILTER_FIELDS:
        if field == exclude_field:
            continue

        value = filters.get(field)
        if value:
            queryset = queryset.filter(**{field: value})

    return queryset


def _build_course_filter_options(base_queryset, filters):
    option_querysets = {
        field: _apply_course_filters(base_queryset, filters, exclude_field=field)
        for field in COURSE_FILTER_FIELDS
    }

    return {
        'years': _distinct_non_empty(option_querysets['year'], 'year'),
        'prog_types': _distinct_non_empty(option_querysets['prog_type'], 'prog_type'),
        'prog_categories': _distinct_non_empty(option_querysets['prog_category'], 'prog_category'),
        'course_categories': _distinct_non_empty(option_querysets['course_category'], 'course_category'),
        'prog_codes': _distinct_non_empty(option_querysets['prog_code'], 'prog_code'),
        'branches': _distinct_non_empty(option_querysets['branch'], 'branch'),
        'parts': _distinct_non_empty(option_querysets['part'], 'part'),
        'semesters': _distinct_non_empty(option_querysets['sem'], 'sem'),
        'course_codes': _distinct_non_empty(option_querysets['course_code'], 'course_code'),
        'course_titles': _distinct_non_empty(option_querysets['course_title'], 'course_title'),
        'course_code_titles': list(
            option_querysets['course_code']
            .exclude(course_code__isnull=True)
            .exclude(course_code='')
            .values('course_code', 'course_title')
            .distinct()
            .order_by('course_code')
        ),
    }


def home(request):
    return redirect('course_manage:course_management')


def bulk_upload(request):
    # Require login for bulk upload
    if not request.user.is_authenticated:
        return redirect('/login/')

    # Allow only admins and HODs (staff)
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to access bulk upload.')
        return redirect('course_manage:course_management')

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        # Validation 1: No file selected
        if not excel_file:
            messages.error(request, "Please select an Excel file before uploading.")
            return redirect('course_manage:bulk_upload')

        # Validation 2: Must be an Excel file
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Invalid file type. Please upload an Excel file (.xlsx or .xls).")
            return redirect('course_manage:bulk_upload')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Could not read file: {str(e)}")
            return redirect('course_manage:bulk_upload')

        # Validation 3: Empty file
        if df.empty:
            messages.error(request, "The uploaded Excel file is empty. Please add data and try again.")
            return redirect('course_manage:bulk_upload')

        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]

        # Validation 4: Check required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            messages.error(
                request,
                f"Missing columns: {', '.join(missing_cols)}. "
                f"Required: {', '.join(REQUIRED_COLUMNS)}"
            )
            return redirect('course_manage:bulk_upload')

        # Drop completely empty rows
        df = df.dropna(how='all')
        if df.empty:
            messages.error(request, "No data rows found in the file.")
            return redirect('course_manage:bulk_upload')

        success_count = 0
        skip_count = 0
        error_rows = []

        for index, row in df.iterrows():
            row_num = index + 2

            # course_code is mandatory
            course_code = normalize_course_code(row.get('course_code', ''))
            if not course_code:
                error_rows.append(f"Row {row_num}: Missing course_code — skipped.")
                skip_count += 1
                continue

            # Year: accept 2023 or 2023-2024, always store just 2023
            year_raw = str(row.get('year', '') or '').strip()
            year = year_raw.split('-')[0].strip() if year_raw else ''
            if year and (not year.isdigit() or len(year) != 4):
                error_rows.append(f"Row {row_num}: Invalid year '{year_raw}' — must be a 4-digit year. Skipped.")
                skip_count += 1
                continue

            # Extract text fields
            prog_code       = str(row.get('prog_code', '') or '').strip()
            prog_type       = str(row.get('prog_type', '') or '').strip()
            prog_category   = str(row.get('prog_category', '') or '').strip()
            sem             = str(row.get('sem', '') or '').strip()
            part            = str(row.get('part', '') or '').strip()
            course_category = str(row.get('course_category', '') or '').strip()
            course_title    = str(row.get('course_title', '') or '').strip()

            # Extract decimal fields
            hrs_per_week = to_decimal(row.get('hrs_per_week'))
            credit       = to_decimal(row.get('credit'))
            marks_cia    = to_decimal(row.get('marks_cia'))
            marks_ese    = to_decimal(row.get('marks_ese'))
            total_marks  = to_decimal(row.get('total_marks'))

            # Skip duplicate course_code
            if CourseStr.objects.filter(course_code=course_code).exists():
                error_rows.append(f"Row {row_num}: course_code '{course_code}' already exists — skipped.")
                skip_count += 1
                continue

            CourseStr.objects.create(
                prog_code=prog_code,
                year=year,
                prog_type=prog_type,
                prog_category=prog_category,
                sem=sem,
                course_code=course_code,
                part=part,
                course_category=course_category,
                course_title=course_title,
                hrs_per_week=hrs_per_week,
                credit=credit,
                marks_cia=marks_cia,
                marks_ese=marks_ese,
                total_marks=total_marks,
                is_finalized=True,
            )
            success_count += 1

        if success_count:
            messages.success(request, f"Successfully uploaded {success_count} course(s).")
        if error_rows:
            for err in error_rows:
                messages.warning(request, err)
        if success_count == 0 and not error_rows:
            messages.error(request, "No courses were uploaded. Please check your file.")

        return redirect('course_manage:course_management')

    return render(request, 'bulk_upload.html')


def course_management(request):
    filters = {field: request.GET.get(field) for field in COURSE_FILTER_FIELDS}
    base_queryset = CourseStr.objects.filter(is_finalized=True)
    courses = _apply_course_filters(base_queryset, filters)
    filter_options = _build_course_filter_options(base_queryset, filters)

    context = {
        'courses': courses,
        **filter_options,
        'total_count': base_queryset.count(),
        'arts_count': base_queryset.filter(prog_category='Arts').count(),
        'science_count': base_queryset.filter(prog_category='Science').count(),
        'ug_count': base_queryset.filter(prog_type='UG').count(),
        'pg_count': base_queryset.filter(prog_type='PG').count(),
    }

    return render(request, 'cou_manage.html', context)


def view_course_pdf(request, course_code):
    course_code = normalize_course_code(course_code)
    try:
        course = CourseContent.objects.get(course_code=course_code)
    except CourseContent.DoesNotExist:
        raise Http404("Course not found")

    if not course.pdf:
        raise Http404("PDF not uploaded for this course")

    if not course.pdf.storage.exists(course.pdf.name):
        raise Http404("PDF file not found on server")

    filename = os.path.basename(course.pdf.name)
    response = FileResponse(
        course.pdf.open("rb"),
        content_type="application/pdf",
        filename=filename,
        as_attachment=False,
    )
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def debug_pdf_path(request, course_code):
    code = normalize_course_code(course_code)
    course_content = get_object_or_404(CourseContent, course_code__iexact=code)
    path_in_db = course_content.pdf.name
    full_path = os.path.join(settings.MEDIA_ROOT, path_in_db)
    return HttpResponse(f"""
    <h2>DEBUG INFO for {course_code}</h2>
    <p>DB Path: <strong>{path_in_db}</strong></p>
    <p>MEDIA_ROOT: <strong>{settings.MEDIA_ROOT}</strong></p>
    <p>Full Path: <strong>{full_path}</strong></p>
    <p>File Exists: <strong>{os.path.exists(full_path)}</strong></p>
    """)


def get_filter_options(request):
    filters = {field: request.GET.get(field) for field in COURSE_FILTER_FIELDS}
    queryset = CourseStr.objects.filter(is_finalized=True)
    return JsonResponse(_build_course_filter_options(queryset, filters))
