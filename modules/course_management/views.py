import io
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.db import models
from modules.core.utils import set_upload_progress, delete_upload_progress

from modules.course_management.access import (
    course_management_access_required,
    get_accessible_programs,
)

try:
    from modules.program_manage.models import Program
except ImportError:
    from program_manage.models import Program

from .models import CourseStructure, CourseSyllabus


COURSE_FILTER_FIELDS = (
    "program",
    "year",
    "sem",
    "course_category",
    "part",
)

COURSE_BULK_REQUIRED_COLUMNS = (
    "program_code",
    "course_code",
    "course_title",
    "year",
    "sem",
)


def _distinct_non_empty(queryset, field_name):
    return list(
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _apply_course_filters(queryset, filters, exclude_field=None):
    for field in COURSE_FILTER_FIELDS:
        if field == exclude_field:
            continue
        value = filters.get(field)
        if value and value != "__all__":
            if field == "program":
                queryset = queryset.filter(program_id=value)
            else:
                queryset = queryset.filter(**{field: value})
    return queryset


def _build_course_filter_options(base_queryset, filters):

    option_querysets = {
        field: _apply_course_filters(base_queryset, filters, exclude_field=field)
        for field in COURSE_FILTER_FIELDS
    }
    
    # Get programs for filter
    programs = Program.objects.filter(
        id__in=base_queryset.values_list('program_id', flat=True)
    ).distinct().order_by('prog_code')

    degrees = (
        Program.objects.filter(
            id__in=base_queryset.values_list('program_id', flat=True)
        )
        .values_list('degree', flat=True)
        .distinct()
        .order_by('degree')
    )
    
    return {
        "programs": programs,
        "degrees" : degrees,
        "years": _distinct_non_empty(option_querysets["year"], "year"),
        "sems": _distinct_non_empty(option_querysets["sem"], "sem"),
        "course_categories": _distinct_non_empty(option_querysets["course_category"], "course_category"),
        "parts": sorted({
            normalized_part
            for normalized_part in (
                _normalize_part_value(part_value)
                for part_value in _distinct_non_empty(option_querysets["part"], "part")
            )
            if normalized_part
        }, key=lambda item: int(item) if str(item).isdigit() else str(item)),
    }


def _is_blank_numeric_value(value):
    if value is None or pd.isna(value):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return not stripped or all(character in "-–—" for character in stripped)
    return False


def _parse_optional_decimal(value):
    if _is_blank_numeric_value(value):
        return None

    try:
        return float(Decimal(str(value).strip()))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'Invalid numeric value "{value}"')


def _parse_optional_integer(value):
    if _is_blank_numeric_value(value):
        return None

    try:
        return int(Decimal(str(value).strip()))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'Invalid numeric value "{value}"')


def _normalize_part_value(value):
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    roman_to_numeric = {
        "I": "1",
        "II": "2",
        "III": "3",
        "IV": "4",
        "V": "5",
    }
    if text.upper() in roman_to_numeric:
        return roman_to_numeric[text.upper()]

    try:
        return str(int(Decimal(text)))
    except (InvalidOperation, ValueError, TypeError):
        return text


def _get_accessible_course_queryset(user):
    if user.is_superuser:
        return CourseStructure.objects.select_related('program').all()
    accessible_program_ids = get_accessible_programs(user).values_list('id', flat=True)
    return CourseStructure.objects.select_related('program').filter(program_id__in=accessible_program_ids)


def _get_accessible_program_queryset(user):
    if user.is_superuser:
        return Program.objects.filter(is_active=True)
    return get_accessible_programs(user)


def _user_can_access_course(user, course):
    if user.is_superuser:
        return True
    return course.program_id in set(get_accessible_programs(user).values_list('id', flat=True))


@course_management_access_required
def course_management(request):

    # Get pagination and per page parameters
    per_page = int(request.GET.get('per_page', 10))
    page = request.GET.get('page', 1)
    
    # Apply filters
    filters = {}
    for field in COURSE_FILTER_FIELDS:
        value = request.GET.get(field)
        if value and value != "__all__":
            filters[field] = value
    
    base_queryset = _get_accessible_course_queryset(request.user)
    courses = _apply_course_filters(base_queryset, filters).annotate(
        has_syllabus_pdf=models.Exists(
            CourseSyllabus.objects.filter(
                course_code=models.OuterRef('course_code'),
                pdf__isnull=False,
            ).exclude(pdf='')
        )
    )
    
    # Get filter options for dropdowns
    filter_options = _build_course_filter_options(base_queryset, filters)
    all_courses_for_search = list(
        courses.values(
            "id",
            "course_code",
            "course_title",
            "year",
            "sem",
            "part",
            "credit",
            "has_syllabus_pdf",
            "program__prog_code",
            "program__degree",
            "program__branch",
        )
    )
    
    # Pagination
    paginator = Paginator(courses.order_by('program__prog_code', 'year', 'sem', 'course_code'), per_page)
    page_obj = paginator.get_page(page)
    
    # Preserve query parameters for pagination
    query_params = request.GET.copy()
    query_params.pop('page', None)
    
    # Calculate stats - Handle cases where there are no courses
    total_courses = courses.count()
    total_programs = _get_accessible_program_queryset(request.user).count()
    
    # Calculate average credits safely
    avg_credits = 0
    if total_courses > 0:
        avg_credits_result = courses.aggregate(avg_credits=models.Avg('credit'))
        avg_credits = avg_credits_result.get('avg_credits') or 0
    
    # Count courses with syllabus
    courses_with_syllabus = CourseSyllabus.objects.filter(
        course_code__in=courses.values_list('course_code', flat=True)
    ).count()
    
    stats = {
        'total_courses': total_courses,
        'total_programs': total_programs,
        'avg_credits': round(avg_credits, 1),
        'courses_with_syllabus': courses_with_syllabus,
    }
    
    context = {
        "courses": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "pagination_query": query_params.urlencode(),
        "all_courses_for_search": all_courses_for_search,
        **filter_options,
        **stats,
    }
    return render(request, "course_management.html", context)

@course_management_access_required
def get_filter_options(request):

    filters = {field: request.GET.get(field) for field in COURSE_FILTER_FIELDS}
    queryset = _get_accessible_course_queryset(request.user)
    options = _build_course_filter_options(queryset, filters)
    
    # Convert programs to dict for JSON
    options['programs_list'] = [
        {'id': p.id, 'code': p.prog_code, 'degree': p.degree, 'branch': p.branch}
        for p in options['programs']
    ]
    del options['programs']
    
    return JsonResponse(options)


@course_management_access_required
def get_course(request, course_id):

    try:
        course = get_object_or_404(CourseStructure.objects.select_related('program'), id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to access that course.'})
        
        # Check if syllabus exists
        has_syllabus = CourseSyllabus.objects.filter(course_code=course.course_code).exists()
        
        data = {
            'success': True,
            'course': {
                'id': course.id,
                'program_id': course.program.id,
                'program_code': course.program.prog_code,
                'course_code': course.course_code,
                'course_title': course.course_title or '',
                'year': course.year or '',
                'sem': course.sem or '',
                'course_category': course.course_category or '',
                'part': _normalize_part_value(course.part) or '',
                'hrs_per_week': str(course.hrs_per_week) if course.hrs_per_week else '',
                'credit': str(course.credit) if course.credit else '',
                'marks_cia': str(course.marks_cia) if course.marks_cia else '',
                'marks_ese': str(course.marks_ese) if course.marks_ese else '',
                'total_marks': str(course.total_marks) if course.total_marks else '',
                'has_syllabus': has_syllabus,
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def add_course(request):

    try:
        program_id = request.POST.get("program_id")
        course_code = request.POST.get("course_code", "").strip().upper().replace(" ", "")
        course_title = request.POST.get("course_title", "").strip()
        year = request.POST.get("year", "").strip()
        sem = request.POST.get("sem", "").strip()
        course_category = request.POST.get("course_category", "").strip()
        part = _normalize_part_value(request.POST.get("part", ""))
        hrs_per_week = request.POST.get("hrs_per_week", "")
        credit = request.POST.get("credit", "")
        marks_cia = request.POST.get("marks_cia", "")
        marks_ese = request.POST.get("marks_ese", "")
        total_marks = request.POST.get("total_marks", "")
        
        # Validate required fields
        if not all([program_id, course_code, course_title, year, sem]):
            return JsonResponse({'success': False, 'error': 'Program, Course Code, Course Title, Year, and Semester are required.'})
        
        # Get program
        try:
            program = Program.objects.get(id=program_id, is_active=True)
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist.'})

        if not request.user.is_superuser and not get_accessible_programs(request.user).filter(id=program.id).exists():
            return JsonResponse({'success': False, 'error': 'You do not have permission to add courses to that program.'})
        
        # Check if course exists for this program
        if CourseStructure.objects.filter(program=program, course_code=course_code).exists():
            return JsonResponse({'success': False, 'error': f'Course code "{course_code}" already exists for this program.'})
        
        # Create course
        course = CourseStructure.objects.create(
            program=program,
            course_code=course_code,
            course_title=course_title,
            year=year,
            sem=sem,
            course_category=course_category if course_category else None,
            part=part if part else None,
            hrs_per_week=_parse_optional_decimal(hrs_per_week),
            credit=_parse_optional_integer(credit),
            marks_cia=_parse_optional_decimal(marks_cia),
            marks_ese=_parse_optional_decimal(marks_ese),
            total_marks=_parse_optional_decimal(total_marks),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Course created successfully.',
            'course_id': course.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def edit_course(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to edit that course.'})
        
        program_id = request.POST.get("program_id")
        course_code = request.POST.get("course_code", "").strip().upper().replace(" ", "")
        course_title = request.POST.get("course_title", "").strip()
        year = request.POST.get("year", "").strip()
        sem = request.POST.get("sem", "").strip()
        course_category = request.POST.get("course_category", "").strip()
        part = _normalize_part_value(request.POST.get("part", ""))
        hrs_per_week = request.POST.get("hrs_per_week", "")
        credit = request.POST.get("credit", "")
        marks_cia = request.POST.get("marks_cia", "")
        marks_ese = request.POST.get("marks_ese", "")
        total_marks = request.POST.get("total_marks", "")
        
        # Validate required fields
        if not all([program_id, course_code, course_title, year, sem]):
            return JsonResponse({'success': False, 'error': 'Program, Course Code, Course Title, Year, and Semester are required.'})
        
        # Get program
        try:
            program = Program.objects.get(id=program_id, is_active=True)
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist.'})

        if not request.user.is_superuser and not get_accessible_programs(request.user).filter(id=program.id).exists():
            return JsonResponse({'success': False, 'error': 'You do not have permission to move courses into that program.'})
        
        # Check if course code exists for other courses
        if CourseStructure.objects.exclude(id=course_id).filter(program=program, course_code=course_code).exists():
            return JsonResponse({'success': False, 'error': f'Course code "{course_code}" already exists for this program.'})
        
        # Update course
        course.program = program
        course.course_code = course_code
        course.course_title = course_title
        course.year = year
        course.sem = sem
        course.course_category = course_category if course_category else None
        course.part = part if part else None
        course.hrs_per_week = _parse_optional_decimal(hrs_per_week)
        course.credit = _parse_optional_integer(credit)
        course.marks_cia = _parse_optional_decimal(marks_cia)
        course.marks_ese = _parse_optional_decimal(marks_ese)
        course.total_marks = _parse_optional_decimal(total_marks)
        course.save()
        
        return JsonResponse({'success': True, 'message': 'Course updated successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def delete_course(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to delete that course.'})
        course.delete()
        return JsonResponse({'success': True, 'message': 'Course deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
def download_sample_excel(request):

    sample_data = {
        'program_code': ['BSC-CS', 'BSC-CS', 'MA-ENG'],
        'course_code': ['CS101', 'CS102', 'ENG101'],
        'course_title': ['Programming Fundamentals', 'Data Structures', 'Literary Theory'],
        'year': ['1', '1', '1'],
        'sem': ['1', '2', '1'],
        'course_category': ['Core', 'Core', 'Elective'],
        'part': ['1', '1', '2'],
        'hrs_per_week': [4, 4, 3],
        'credit': [4, 4, 3],
        'marks_cia': [40, 40, 40],
        'marks_ese': [60, 60, 60],
        'total_marks': [100, 100, 100],
    }
    
    df = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Courses', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Course_Sample.xlsx"'
    return response


@course_management_access_required
def download_courses_excel(request):

    courses = _get_accessible_course_queryset(request.user).order_by('program__prog_code', 'year', 'sem', 'course_code')
    
    course_data = []
    for course in courses:
        course_data.append({
            'Program Code': course.program.prog_code,
            'Program Name': f"{course.program.degree} - {course.program.branch}",
            'Course Code': course.course_code,
            'Course Title': course.course_title,
            'Year': course.year,
            'Semester': course.sem,
            'Category': course.course_category or '',
            'Part': _normalize_part_value(course.part) or '',
            'Hours/Week': course.hrs_per_week or '',
            'Credit': course.credit or '',
            'CIA Marks': course.marks_cia or '',
            'ESE Marks': course.marks_ese or '',
            'Total Marks': course.total_marks or '',
        })
    
    df = pd.DataFrame(course_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Courses', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Courses_List.xlsx"'
    return response


@course_management_access_required
@require_http_methods(["POST"])
def upload_courses_excel(request):
    upload_id = request.POST.get('upload_id') or request.GET.get('upload_id')
    try:
        accessible_program_ids = set(get_accessible_programs(request.user).values_list('id', flat=True))

        if 'excel_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded.'})
        
        excel_file = request.FILES['excel_file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'})
        
        df = pd.read_excel(excel_file)
        
        required_columns = ['program_code', 'course_code', 'course_title', 'year', 'sem']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            })
        
        created_courses = []
        errors = []
        
        total_rows = len(df)
        if upload_id:
            set_upload_progress(upload_id, 0, total_rows, status="processing")
        
        for index, row in df.iterrows():
            current_row = index + 1
            if upload_id:
                set_upload_progress(upload_id, current_row, total_rows, status="processing")
            
            program_code = str(row.get('program_code', '')).strip().upper().replace(" ", "")
            course_code = str(row.get('course_code', '')).strip().upper().replace(" ", "")
            course_title = str(row.get('course_title', '')).strip()
            year = str(row.get('year', '')).strip()
            sem = str(row.get('sem', '')).strip()
            course_category = str(row.get('course_category', '')).strip() if pd.notna(row.get('course_category')) else None
            part = _normalize_part_value(row.get('part'))
            hrs_per_week = _parse_optional_decimal(row.get('hrs_per_week'))
            credit = _parse_optional_integer(row.get('credit'))
            marks_cia = _parse_optional_decimal(row.get('marks_cia'))
            marks_ese = _parse_optional_decimal(row.get('marks_ese'))
            total_marks = _parse_optional_decimal(row.get('total_marks'))
            
            # Validate required fields
            if not all([program_code, course_code, course_title, year, sem]):
                errors.append(f'Row {index + 2}: Program Code, Course Code, Course Title, Year, and Semester are required')
                continue
            
            # Get program
            try:
                program = Program.objects.get(prog_code=program_code, is_active=True)
            except Program.DoesNotExist:
                errors.append(f'Row {index + 2}: Program with code "{program_code}" not found')
                continue

            if not request.user.is_superuser and program.id not in accessible_program_ids:
                errors.append(f'Row {index + 2}: You do not have permission to import courses for program "{program_code}"')
                continue
            
            # Check if course exists
            if CourseStructure.objects.filter(program=program, course_code=course_code).exists():
                errors.append(f'Row {index + 2}: Course code "{course_code}" already exists for program "{program_code}"')
                continue
            
            try:
                CourseStructure.objects.create(
                    program=program,
                    course_code=course_code,
                    course_title=course_title,
                    year=year,
                    sem=sem,
                    course_category=course_category,
                    part=part,
                    hrs_per_week=hrs_per_week,
                    credit=credit,
                    marks_cia=marks_cia,
                    marks_ese=marks_ese,
                    total_marks=total_marks,
                )
                created_courses.append(f"{program_code}-{course_code}")
            except Exception as e:
                errors.append(f'Row {index + 2}: Error - {str(e)}')
        
        if upload_id:
            set_upload_progress(upload_id, total_rows, total_rows, status="completed")
            
        if created_courses:
            message = f'Successfully imported {len(created_courses)} courses.'
            if errors:
                message += f' {len(errors)} errors encountered.'
            return JsonResponse({'success': True, 'message': message, 'created': len(created_courses), 'errors': errors[:10]})
        if errors and all('already exists' in error for error in errors):
            return JsonResponse({
                'success': False,
                'error': 'Existing courses cannot be uploaded.',
                'message': 'Existing courses cannot be uploaded.',
                'created': 0,
                'errors': errors[:10],
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'No courses imported. Errors: {", ".join(errors[:5])}',
                'message': f'No courses imported. Errors encountered: {len(errors)}',
                'created': 0,
                'errors': errors[:10],
            })
        
    except Exception as e:
        if upload_id:
            set_upload_progress(upload_id, 0, 0, status="failed")
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def upload_syllabus(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to upload syllabus for that course.'})
        
        if 'syllabus_pdf' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No PDF file uploaded.'})
        
        pdf_file = request.FILES['syllabus_pdf']
        
        if not pdf_file.name.endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'Please upload a PDF file.'})
        
        # Rename the file using course code before saving
        pdf_file.name = f"{course.course_code}.pdf"
        
        # Ensure that the course code remains unique in the syllabus table and prevent duplicate entries
        syllabus = CourseSyllabus.objects.filter(course_code=course.course_code).first()
        if syllabus:
            # Delete old file and update existing record (preventing duplicates)
            if syllabus.pdf:
                syllabus.pdf.delete(save=False)
            syllabus.pdf = pdf_file
            syllabus.save()
        else:
            # Create a new unique record
            CourseSyllabus.objects.create(
                course_code=course.course_code,
                pdf=pdf_file
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Syllabus uploaded successfully.',
            'has_syllabus': True
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
def view_syllabus(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to view that syllabus.'})
        syllabus = get_object_or_404(CourseSyllabus, course_code=course.course_code)
        
        if not syllabus.pdf:
            return JsonResponse({'success': False, 'error': 'No syllabus file available.'})
        
        with syllabus.pdf.open('rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{course.course_code}.pdf"'
        return response
        
    except CourseSyllabus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Syllabus not found for this course.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
def download_syllabus(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to download that syllabus.'})
        syllabus = get_object_or_404(CourseSyllabus, course_code=course.course_code)
        
        if not syllabus.pdf:
            return JsonResponse({'success': False, 'error': 'No syllabus file available.'})
        
        with syllabus.pdf.open('rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{course.course_code}.pdf"'
        return response
        
    except CourseSyllabus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Syllabus not found for this course.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def delete_syllabus(request, course_id):

    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        if not _user_can_access_course(request.user, course):
            return JsonResponse({'success': False, 'error': 'You do not have permission to delete that syllabus.'})
        try:
            syllabus = CourseSyllabus.objects.get(course_code=course.course_code)
            if syllabus.pdf:
                syllabus.pdf.delete(save=False)
            syllabus.delete()
        except CourseSyllabus.DoesNotExist:
            pass
        
        return JsonResponse({'success': True, 'message': 'Syllabus deleted successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
