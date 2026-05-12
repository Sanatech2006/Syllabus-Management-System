import os
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from modules.program_manage.models import Program, normalize_program_code, normalize_program_value
from modules.upload_center.models import CourseContent, CourseStr, normalize_course_code


REQUIRED_COLUMNS = [
    'prog_code', 'degree', 'prog_type', 'prog_category', 'branch', 'sem',
    'course_code', 'part', 'course_category', 'course_title',
    'hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks'
]

DECIMAL_FIELDS = ['hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks']

TEXT_FIELDS = [
    'prog_code', 'degree', 'prog_type', 'prog_category', 'branch', 'sem',
    'course_code', 'part', 'course_category', 'course_title'
]


COURSE_FILTER_FIELDS = (
    'degree',
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


def _program_key_from_values(prog_type, prog_category, branch, prog_code):
    return (
        normalize_program_value(prog_type).upper(),
        normalize_program_value(prog_category).title(),
        normalize_program_value(branch),
        normalize_program_code(prog_code),
    )


def _program_degree_lookup():
    lookup = {}
    for program in Program.objects.filter(is_active=True):
        lookup[_program_key_from_values(
            program.prog_type,
            program.prog_category,
            program.branch,
            program.prog_code,
        )] = program.degree or ""
    return lookup


def _course_program_key(course):
    return _program_key_from_values(
        course.prog_type,
        course.prog_category,
        course.branch,
        course.prog_code,
    )


def _matching_course_ids_for_degree(queryset, degree):
    if not degree:
        return None

    program_degree_lookup = _program_degree_lookup()
    matching_ids = []
    for course in queryset.only('id', 'prog_type', 'prog_category', 'branch', 'prog_code'):
        if program_degree_lookup.get(_course_program_key(course), "") == degree:
            matching_ids.append(course.id)
    return matching_ids


def _apply_course_filters(queryset, filters, exclude_field=None):
    for field in COURSE_FILTER_FIELDS:
        if field == exclude_field:
            continue

        if field == 'degree':
            continue

        value = filters.get(field)
        if value:
            queryset = queryset.filter(**{field: value})

    if exclude_field != 'degree' and filters.get('degree'):
        matching_ids = _matching_course_ids_for_degree(queryset, filters['degree'])
        queryset = queryset.filter(id__in=matching_ids or [])

    return queryset


def _build_course_filter_options(base_queryset, filters):
    option_querysets = {
        field: _apply_course_filters(base_queryset, filters, exclude_field=field)
        for field in COURSE_FILTER_FIELDS
    }

    program_queryset = Program.objects.filter(is_active=True)
    for program_field in ('prog_type', 'prog_category', 'branch', 'prog_code'):
        value = filters.get(program_field)
        if value:
            program_queryset = program_queryset.filter(**{program_field: value})

    return {
        'degrees': _distinct_non_empty(program_queryset, 'degree'),
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


def _program_exists_for_course(program_data):
    return Program.objects.filter(is_active=True, **program_data).exists()


def home(request):
    return redirect('course_manage:course_management')


def bulk_upload(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to access bulk upload.')
        return redirect('course_manage:course_management')

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, "Please select an Excel file before uploading.")
            return redirect('course_manage:bulk_upload')

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Invalid file type. Please upload an Excel file (.xlsx or .xls).")
            return redirect('course_manage:bulk_upload')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Could not read file: {str(e)}")
            return redirect('course_manage:bulk_upload')

        if df.empty:
            messages.error(request, "The uploaded Excel file is empty. Please add data and try again.")
            return redirect('course_manage:bulk_upload')

        df.columns = [col.strip().lower() for col in df.columns]

        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            messages.error(
                request,
                f"Missing columns: {', '.join(missing_cols)}. "
                f"Required: {', '.join(REQUIRED_COLUMNS)}"
            )
            return redirect('course_manage:bulk_upload')

        df = df.dropna(how='all')
        if df.empty:
            messages.error(request, "No data rows found in the file.")
            return redirect('course_manage:bulk_upload')

        success_count = 0
        skip_count = 0
        error_rows = []

        for index, row in df.iterrows():
            row_num = index + 2
            course_code = normalize_course_code(row.get('course_code', ''))
            if not course_code:
                error_rows.append(f"Row {row_num}: Missing course_code â€” skipped.")
                skip_count += 1
                continue

            prog_code = normalize_program_code(row.get('prog_code', ''))
            prog_type = normalize_program_value(row.get('prog_type', '')).upper()
            prog_category = normalize_program_value(row.get('prog_category', '')).title()
            degree = normalize_program_value(row.get('degree', ''))
            branch = normalize_program_value(row.get('branch', ''))
            sem = str(row.get('sem', '') or '').strip()
            part = str(row.get('part', '') or '').strip()
            course_category = str(row.get('course_category', '') or '').strip()
            course_title = str(row.get('course_title', '') or '').strip()

            if not _program_exists_for_course(
                {
                    'prog_type': prog_type,
                    'prog_category': prog_category,
                    'degree': degree,
                    'branch': branch,
                    'prog_code': prog_code,
                }
            ):
                error_rows.append(
                    f"Row {row_num}: Program {prog_type} / {prog_category} / {degree} / {branch} / {prog_code} is not in Program Management â€” skipped."
                )
                skip_count += 1
                continue

            hrs_per_week = to_decimal(row.get('hrs_per_week'))
            credit = to_decimal(row.get('credit'))
            marks_cia = to_decimal(row.get('marks_cia'))
            marks_ese = to_decimal(row.get('marks_ese'))
            total_marks = to_decimal(row.get('total_marks'))

            if CourseStr.objects.filter(course_code=course_code).exists():
                error_rows.append(f"Row {row_num}: course_code '{course_code}' already exists â€” skipped.")
                skip_count += 1
                continue

            CourseStr.objects.create(
                prog_code=prog_code,
                degree=degree,
                prog_type=prog_type,
                prog_category=prog_category,
                branch=branch,
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
    course_queryset = _apply_course_filters(base_queryset, filters).order_by('id')
    program_degree_lookup = _program_degree_lookup()
    courses = []

    for course in course_queryset:
        course.display_degree = program_degree_lookup.get(_course_program_key(course), "")
        courses.append(course)

    filter_options = _build_course_filter_options(base_queryset, filters)
    # items per page configurable via ?per_page=10|20|50|100 (defaults to 10)
    per_page_default = 10
    allowed_per_page = {10, 20, 50, 100}
    try:
        per_page = int(request.GET.get('per_page', per_page_default))
        if per_page not in allowed_per_page:
            per_page = per_page_default
    except (ValueError, TypeError):
        per_page = per_page_default

    paginator = Paginator(courses, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_courses = list(page_obj.object_list)
    course_codes = [course.course_code for course in page_courses if course.course_code]
    pdf_contents = {
        content.course_code: content
        for content in CourseContent.objects.filter(course_code__in=course_codes)
    }

    for course in page_courses:
        content = pdf_contents.get(course.course_code)
        course.has_pdf = bool(
            content
            and content.pdf
            and content.pdf.name
            and content.pdf.storage.exists(content.pdf.name)
        )

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'courses': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'pagination_query': query_params.urlencode(),
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
