from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from modules.upload_center.models import CourseStr, CourseContent
from django.http import HttpResponse, FileResponse, Http404
import os
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
import pandas as pd
from decimal import Decimal, InvalidOperation


# Required columns that must exist in the Excel file
REQUIRED_COLUMNS = [
    'prog_code', 'year', 'prog_type', 'sem',
    'course_code', 'part', 'course_category', 'course_title',
    'hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks'
]

# Decimal fields that need type conversion
DECIMAL_FIELDS = ['hrs_per_week', 'credit', 'marks_cia', 'marks_ese', 'total_marks']

# Text fields
TEXT_FIELDS = [
    'prog_code', 'year', 'prog_type', 'sem',
    'course_code', 'part', 'course_category', 'course_title'
]


def to_decimal(value):
    """Safely convert a value to Decimal, return None if invalid."""
    try:
        if value is None or str(value).strip() in ('', 'nan', 'NaN', 'None'):
            return None
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def home(request):
    return redirect('course_manage:course_management')


def bulk_upload(request):
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

            # Validation 3: Empty file (no rows)
            if df.empty:
                messages.error(request, "The uploaded Excel file is empty. Please add data and try again.")
                return redirect('course_manage:bulk_upload')

            # Normalize column names: strip spaces, lowercase
            df.columns = [col.strip().lower() for col in df.columns]

            # Validation 4: Check all required columns exist
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                messages.error(
                    request,
                    f"Missing columns in Excel file: {', '.join(missing_cols)}. "
                    f"Required columns are: {', '.join(REQUIRED_COLUMNS)}"
                )
                return redirect('course_manage:bulk_upload')

            # Validation 5: Drop completely empty rows, check if anything remains
            df = df.dropna(how='all')
            if df.empty:
                messages.error(request, "The Excel file contains no data rows. Please fill in the data and try again.")
                return redirect('course_manage:bulk_upload')

            # Process rows
            success_count = 0
            skip_count = 0
            error_rows = []

            for index, row in df.iterrows():
                row_num = index + 2  # Excel row number (1-based + header)

                # Extract and clean text fields
                course_code = str(row.get('course_code', '') or '').strip().upper()

                # Validation 6: course_code is mandatory per row
                if not course_code:
                    error_rows.append(f"Row {row_num}: Missing course_code — skipped.")
                    skip_count += 1
                    continue

                # Extract all text values
                prog_code       = str(row.get('prog_code', '') or '').strip()
                year            = str(row.get('year', '') or '').strip()
                prog_type       = str(row.get('prog_type', '') or '').strip()
                sem             = str(row.get('sem', '') or '').strip()
                part            = str(row.get('part', '') or '').strip()
                course_category = str(row.get('course_category', '') or '').strip()
                course_title    = str(row.get('course_title', '') or '').strip()

                # Extract and convert decimal values
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

                # Save to database
                CourseStr.objects.create(
                    prog_code=prog_code,
                    year=year,
                    prog_type=prog_type,
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

            # Show results
            if success_count:
                messages.success(request, f"Successfully uploaded {success_count} course(s).")
            if error_rows:
                for err in error_rows:
                    messages.warning(request, err)
            if success_count == 0 and not error_rows:
                messages.error(request, "No courses were uploaded. Please check your file.")

            return redirect('course_manage:course_management')

        except Exception as e:
            messages.error(request, f"Failed to process file: {str(e)}")
            return redirect('course_manage:bulk_upload')

    return render(request, 'bulk_upload.html')


def course_management(request):
    year = request.GET.get('year')
    prog_type = request.GET.get('prog_type')
    course_category = request.GET.get('course_category')
    prog_code = request.GET.get('prog_code')
    branch = request.GET.get('branch')
    part = request.GET.get('part')
    sem = request.GET.get('sem')
    course_code = request.GET.get('course_code')
    course_title = request.GET.get('course_title')

    courses = CourseStr.objects.filter(is_finalized=True)

    if year: courses = courses.filter(year=year)
    if prog_type: courses = courses.filter(prog_type=prog_type)
    if course_category: courses = courses.filter(course_category=course_category)
    if prog_code: courses = courses.filter(prog_code=prog_code)
    if branch: courses = courses.filter(branch=branch)
    if part: courses = courses.filter(part=part)
    if sem: courses = courses.filter(sem=sem)
    if course_code: courses = courses.filter(course_code=course_code)
    if course_title: courses = courses.filter(course_title=course_title)

    context = {
        'courses': courses,
        'years': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(year__isnull=True).exclude(year='')
            .values_list('year', flat=True).distinct().order_by('year')),
        'prog_types': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(prog_type__isnull=True).exclude(prog_type='')
            .values_list('prog_type', flat=True).distinct().order_by('prog_type')),
        'course_categories': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(course_category__isnull=True).exclude(course_category='')
            .values_list('course_category', flat=True).distinct().order_by('course_category')),
        'prog_codes': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(prog_code__isnull=True).exclude(prog_code='')
            .values_list('prog_code', flat=True).distinct().order_by('prog_code')),
        'branches': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(branch__isnull=True).exclude(branch='')
            .values_list('branch', flat=True).distinct().order_by('branch')),
        'parts': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(part__isnull=True).exclude(part='')
            .values_list('part', flat=True).distinct().order_by('part')),
        'semesters': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(sem__isnull=True).exclude(sem='')
            .values_list('sem', flat=True).distinct().order_by('sem')),
        'course_codes': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(course_code__isnull=True).exclude(course_code='')
            .values_list('course_code', flat=True).distinct().order_by('course_code')),
        'course_titles': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(course_title__isnull=True).exclude(course_title='')
            .values_list('course_title', flat=True).distinct().order_by('course_title')),
        'course_code_titles': list(CourseStr.objects.filter(is_finalized=True)
            .exclude(course_code__isnull=True).exclude(course_code='')
            .values('course_code', 'course_title')
            .distinct().order_by('course_code')),
        'arts_count': CourseStr.objects.filter(is_finalized=True, prog_category='Arts').count(),
        'science_count': CourseStr.objects.filter(is_finalized=True, prog_category='Science').count(),
        'ug_count': CourseStr.objects.filter(is_finalized=True, prog_type='UG').count(),
        'pg_count': CourseStr.objects.filter(is_finalized=True, prog_type='PG').count(),
    }

    return render(request, 'cou_manage.html', context)


def view_course_pdf(request, course_code):
    course_code = course_code.strip()
    try:
        course = CourseContent.objects.get(course_code=course_code)
    except CourseContent.DoesNotExist:
        raise Http404("Course not found")

    if not course.pdf:
        raise Http404("PDF not uploaded for this course")

    full_path = course.pdf.path
    if not os.path.isfile(full_path):
        raise Http404("PDF file not found on server")

    return FileResponse(open(full_path, "rb"), content_type="application/pdf")


def debug_pdf_path(request, course_code):
    code = course_code.strip()
    course_content = get_object_or_404(CourseContent, course_code__iexact=code)
    path_in_db = course_content.course_content
    full_path = os.path.join(settings.MEDIA_ROOT, path_in_db)
    return HttpResponse(f"""
    <h2>DEBUG INFO for {course_code}</h2>
    <p>DB Path: <strong>{path_in_db}</strong></p>
    <p>MEDIA_ROOT: <strong>{settings.MEDIA_ROOT}</strong></p>
    <p>Full Path: <strong>{full_path}</strong></p>
    <p>File Exists: <strong>{os.path.exists(full_path)}</strong></p>
    """)


def get_filter_options(request):
    year = request.GET.get('year')
    prog_type = request.GET.get('prog_type')
    course_category = request.GET.get('course_category')
    prog_code = request.GET.get('prog_code')
    branch = request.GET.get('branch')
    part = request.GET.get('part')
    sem = request.GET.get('sem')
    course_code = request.GET.get('course_code')
    course_title = request.GET.get('course_title')

    queryset = CourseStr.objects.filter(is_finalized=True)

    if year: queryset = queryset.filter(year=year)
    if prog_type: queryset = queryset.filter(prog_type=prog_type)
    if course_category: queryset = queryset.filter(course_category=course_category)
    if prog_code: queryset = queryset.filter(prog_code=prog_code)
    if branch: queryset = queryset.filter(branch=branch)
    if part: queryset = queryset.filter(part=part)
    if sem: queryset = queryset.filter(sem=sem)
    if course_code: queryset = queryset.filter(course_code=course_code)
    if course_title: queryset = queryset.filter(course_title=course_title)

    options = {
        'years': list(queryset.exclude(year__isnull=True).exclude(year='').values_list('year', flat=True).distinct().order_by('year')),
        'prog_types': list(queryset.exclude(prog_type__isnull=True).exclude(prog_type='').values_list('prog_type', flat=True).distinct().order_by('prog_type')),
        'course_categories': list(queryset.exclude(course_category__isnull=True).exclude(course_category='').values_list('course_category', flat=True).distinct().order_by('course_category')),
        'prog_codes': list(queryset.exclude(prog_code__isnull=True).exclude(prog_code='').values_list('prog_code', flat=True).distinct().order_by('prog_code')),
        'branches': list(queryset.exclude(branch__isnull=True).exclude(branch='').values_list('branch', flat=True).distinct().order_by('branch')),
        'parts': list(queryset.exclude(part__isnull=True).exclude(part='').values_list('part', flat=True).distinct().order_by('part')),
        'semesters': list(queryset.exclude(sem__isnull=True).exclude(sem='').values_list('sem', flat=True).distinct().order_by('sem')),
        'course_codes': list(queryset.exclude(course_code__isnull=True).exclude(course_code='').values_list('course_code', flat=True).distinct().order_by('course_code')),
        'course_titles': list(queryset.exclude(course_title__isnull=True).exclude(course_title='').values_list('course_title', flat=True).distinct().order_by('course_title')),
    }
    return JsonResponse(options)