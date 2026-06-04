import os
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from modules.program_manage.models import Program, normalize_program_code, normalize_program_value
from .models import CourseStructure, CourseSyllabus, normalize_course_code


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


def _apply_course_filters(queryset, filters, exclude_field=None):
    for field in COURSE_FILTER_FIELDS:
        if field == exclude_field:
            continue
        value = filters.get(field)
        if value:
            if field == 'degree':
                # Filter by program's degree
                queryset = queryset.filter(program__degree=value)
            elif field == 'prog_type':
                queryset = queryset.filter(program__prog_type=value)
            elif field == 'prog_category':
                queryset = queryset.filter(program__prog_category=value)
            elif field == 'prog_code':
                queryset = queryset.filter(program__prog_code=value)
            elif field == 'branch':
                queryset = queryset.filter(program__branch=value)
            else:
                queryset = queryset.filter(**{field: value})
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
            messages.error(request, "The uploaded Excel file is empty.")
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
                error_rows.append(f"Row {row_num}: Missing course_code — skipped.")
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

            # Find or create program
            program, created = Program.objects.get_or_create(
                prog_code=prog_code,
                degree=degree,
                branch=branch,
                prog_type=prog_type,
                prog_category=prog_category,
                defaults={'is_active': True}
            )

            hrs_per_week = to_decimal(row.get('hrs_per_week'))
            credit = to_decimal(row.get('credit'))
            marks_cia = to_decimal(row.get('marks_cia'))
            marks_ese = to_decimal(row.get('marks_ese'))
            total_marks = to_decimal(row.get('total_marks'))

            # Check if course already exists
            if CourseStructure.objects.filter(program=program, course_code=course_code).exists():
                error_rows.append(f"Row {row_num}: course_code '{course_code}' already exists for this program — skipped.")
                skip_count += 1
                continue

            CourseStructure.objects.create(
                program=program,
                course_code=course_code,
                course_title=course_title,
                sem=sem,
                part=part,
                course_category=course_category,
                hrs_per_week=hrs_per_week,
                credit=credit,
                marks_cia=marks_cia,
                marks_ese=marks_ese,
                total_marks=total_marks,
                is_finalized=True,
                is_saved=True
            )
            success_count += 1

        if success_count:
            messages.success(request, f"Successfully uploaded {success_count} course(s).")
        if error_rows:
            for err in error_rows[:10]:  # Show first 10 errors
                messages.warning(request, err)
        if success_count == 0 and not error_rows:
            messages.error(request, "No courses were uploaded. Please check your file.")

        return redirect('course_manage:course_management')

    return render(request, 'bulk_upload.html')


def course_management(request):
    filters = {field: request.GET.get(field) for field in COURSE_FILTER_FIELDS}
    base_queryset = CourseStructure.objects.filter(is_finalized=True).select_related('program')
    course_queryset = _apply_course_filters(base_queryset, filters).order_by('-created_at')
    
    courses = []
    for course in course_queryset:
        # Add program fields to course object for template
        course.prog_code = course.program.prog_code
        course.prog_type = course.program.prog_type
        course.prog_category = course.program.prog_category
        course.degree = course.program.degree
        course.branch = course.program.branch
        courses.append(course)

    filter_options = _build_course_filter_options(base_queryset, filters)
    
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
    syllabus_contents = {
        syllabus.course_code: syllabus
        for syllabus in CourseSyllabus.objects.filter(course_code__in=course_codes)
    }

    for course in page_courses:
        syllabus = syllabus_contents.get(course.course_code)
        course.has_pdf = bool(
            syllabus
            and syllabus.pdf
            and syllabus.pdf.name
            and syllabus.pdf.storage.exists(syllabus.pdf.name)
        )

    query_params = request.GET.copy()
    query_params.pop('page', None)

    # Calculate stats
    all_courses = CourseStructure.objects.filter(is_finalized=True).select_related('program')
    
    context = {
        'courses': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'pagination_query': query_params.urlencode(),
        **filter_options,
        'total_count': all_courses.count(),
        'arts_count': all_courses.filter(program__prog_category='Arts').count(),
        'science_count': all_courses.filter(program__prog_category='Science').count(),
        'ug_count': all_courses.filter(program__prog_type='UG').count(),
        'pg_count': all_courses.filter(program__prog_type='PG').count(),
    }

    return render(request, 'cou_manage.html', context)


def view_course_pdf(request, course_code):
    course_code = normalize_course_code(course_code)
    try:
        syllabus = CourseSyllabus.objects.get(course_code=course_code)
    except CourseSyllabus.DoesNotExist:
        raise Http404("Syllabus not found for this course")

    if not syllabus.pdf:
        raise Http404("PDF not uploaded for this course")

    if not syllabus.pdf.storage.exists(syllabus.pdf.name):
        raise Http404("PDF file not found on server")

    filename = os.path.basename(syllabus.pdf.name)
    response = FileResponse(
        syllabus.pdf.open("rb"),
        content_type="application/pdf",
        filename=filename,
        as_attachment=False,
    )
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def get_filter_options(request):
    filters = {field: request.GET.get(field, '').strip() for field in COURSE_FILTER_FIELDS}
    queryset = CourseStructure.objects.filter(is_finalized=True).select_related('program')
    return JsonResponse(_build_course_filter_options(queryset, filters))


def add_course(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.method == 'POST':
        try:
            prog_code = normalize_program_code(request.POST.get('prog_code', ''))
            prog_type = request.POST.get('prog_type', '').upper()
            prog_category = request.POST.get('prog_category', '').title()
            degree = request.POST.get('degree', '')
            branch = request.POST.get('branch', '')
            
            # Get or create program
            program, created = Program.objects.get_or_create(
                prog_code=prog_code,
                degree=degree,
                branch=branch,
                prog_type=prog_type,
                prog_category=prog_category,
                defaults={'is_active': True}
            )
            
            course_code = normalize_course_code(request.POST.get('course_code', ''))
            course_title = request.POST.get('course_title', '')
            sem = request.POST.get('sem', '')
            part = request.POST.get('part', '')
            course_category = request.POST.get('course_category', '')
            hrs_per_week = to_decimal(request.POST.get('hrs_per_week'))
            credit = to_decimal(request.POST.get('credit'))
            marks_cia = to_decimal(request.POST.get('marks_cia'))
            marks_ese = to_decimal(request.POST.get('marks_ese'))
            total_marks = to_decimal(request.POST.get('total_marks'))
            
            # Check if course already exists
            if CourseStructure.objects.filter(program=program, course_code=course_code).exists():
                messages.error(request, f'Course with code {course_code} already exists for this program.')
                return redirect('course_manage:add_course')
            
            course = CourseStructure.objects.create(
                program=program,
                course_code=course_code,
                course_title=course_title,
                sem=sem,
                part=part,
                course_category=course_category,
                hrs_per_week=hrs_per_week,
                credit=credit,
                marks_cia=marks_cia,
                marks_ese=marks_ese,
                total_marks=total_marks,
                is_finalized=True,
                is_saved=True
            )
            
            # Handle PDF upload
            if 'pdf_file' in request.FILES:
                pdf_file = request.FILES['pdf_file']
                syllabus, _ = CourseSyllabus.objects.get_or_create(course_code=course_code)
                syllabus.pdf = pdf_file
                syllabus.save()
            
            messages.success(request, 'Course added successfully!')
            
            if 'add_next' in request.POST:
                return redirect('course_manage:add_course')
            else:
                return redirect('course_manage:course_management')
                
        except Exception as e:
            messages.error(request, f'Error adding course: {str(e)}')
            return redirect('course_manage:add_course')
    
    # GET request - show form
    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    prog_codes = programs.values_list('prog_code', flat=True).distinct()
    
    context = {
        'form_mode': 'add',
        'prog_codes': prog_codes,
        'programs': programs,
        'form_values': {}
    }
    return render(request, 'add_course.html', context)


def edit_course(request, course_id):
    course = get_object_or_404(CourseStructure, id=course_id)
    
    if request.method == 'POST':
        try:
            prog_code = normalize_program_code(request.POST.get('prog_code', ''))
            prog_type = request.POST.get('prog_type', '').upper()
            prog_category = request.POST.get('prog_category', '').title()
            degree = request.POST.get('degree', '')
            branch = request.POST.get('branch', '')
            
            # Get or create program
            program, created = Program.objects.get_or_create(
                prog_code=prog_code,
                degree=degree,
                branch=branch,
                prog_type=prog_type,
                prog_category=prog_category,
                defaults={'is_active': True}
            )
            
            course.program = program
            course.course_code = normalize_course_code(request.POST.get('course_code', ''))
            course.course_title = request.POST.get('course_title', '')
            course.sem = request.POST.get('sem', '')
            course.part = request.POST.get('part', '')
            course.course_category = request.POST.get('course_category', '')
            course.hrs_per_week = to_decimal(request.POST.get('hrs_per_week'))
            course.credit = to_decimal(request.POST.get('credit'))
            course.marks_cia = to_decimal(request.POST.get('marks_cia'))
            course.marks_ese = to_decimal(request.POST.get('marks_ese'))
            course.total_marks = to_decimal(request.POST.get('total_marks'))
            course.save()
            
            # Handle PDF upload
            if 'pdf_file' in request.FILES:
                syllabus, _ = CourseSyllabus.objects.get_or_create(course_code=course.course_code)
                syllabus.pdf = request.FILES['pdf_file']
                syllabus.save()
            
            messages.success(request, 'Course updated successfully!')
            return redirect('course_manage:course_management')
            
        except Exception as e:
            messages.error(request, f'Error updating course: {str(e)}')
    
    # GET request - show form with data
    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    prog_codes = programs.values_list('prog_code', flat=True).distinct()
    
    form_values = {
        'prog_code': course.program.prog_code,
        'prog_type': course.program.prog_type,
        'prog_category': course.program.prog_category,
        'degree': course.program.degree,
        'branch': course.program.branch,
        'course_code': course.course_code,
        'course_title': course.course_title,
        'sem': course.sem,
        'part': course.part,
        'course_category': course.course_category,
        'hrs_per_week': course.hrs_per_week,
        'credit': course.credit,
        'marks_cia': course.marks_cia,
        'marks_ese': course.marks_ese,
        'total_marks': course.total_marks,
    }
    
    context = {
        'form_mode': 'edit',
        'prog_codes': prog_codes,
        'programs': programs,
        'form_values': form_values,
        'course_id': course_id
    }
    return render(request, 'add_course.html', context)


def delete_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(CourseStructure, id=course_id)
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_program_details(request):
    """AJAX endpoint to get program details based on prog_code and branch"""
    prog_code = request.GET.get('prog_code', '')
    branch = request.GET.get('branch', '')
    
    try:
        program = Program.objects.get(prog_code=prog_code, branch=branch, is_active=True)
        data = {
            'success': True,
            'program': {
                'degree': program.degree,
                'prog_type': program.prog_type,
                'prog_category': program.prog_category,
                'prog_code': program.prog_code,
                'branch': program.branch
            }
        }
        return JsonResponse(data)
    except Program.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Program not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_branches(request):
    """AJAX endpoint to get branches for a given prog_code"""
    prog_code = request.GET.get('prog_code', '')
    try:
        programs = Program.objects.filter(prog_code=prog_code, is_active=True)
        branches = list(programs.values_list('branch', flat=True).distinct())
        return JsonResponse({'success': True, 'branches': branches})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})