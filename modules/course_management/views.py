import io
import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.db import models

from modules.course_management.access import (
    course_management_access_required,
    get_accessible_courses,
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
    "degree",
    "branch",
    "prog_type",
    "prog_category",
    "course_title",
)

COURSE_BULK_REQUIRED_COLUMNS = (
    "program_code",
    "course_code",
    "course_title",
    "year",
    "sem",
)


def _optional_float_from_excel(value, field_label, row_number):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-", "--"):
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: {field_label} must be a number or blank")


def _optional_integer_from_excel(value, field_label, row_number):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-", "--"):
            return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: {field_label} must be a whole number or blank")

    if not number.is_integer():
        raise ValueError(f"Row {row_number}: {field_label} must be a whole number")

    return int(number)


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
            elif field == "degree":
                queryset = queryset.filter(program__degree=value)
            elif field == "branch":
                queryset = queryset.filter(program__branch__iexact=value)
            elif field == "prog_type":
                queryset = queryset.filter(program__prog_type=value)
            elif field == "prog_category":
                queryset = queryset.filter(program__prog_category=value)
            elif field == "course_title":
                queryset = queryset.filter(
                    models.Q(course_title__icontains=value) | models.Q(course_code__icontains=value)
                )
            else:
                queryset = queryset.filter(**{field: value})
    return queryset


def _build_course_filter_options(base_queryset, filters, programs_queryset):

    option_querysets = {
        field: _apply_course_filters(base_queryset, filters, exclude_field=field)
        for field in COURSE_FILTER_FIELDS
    }
    
    programs = programs_queryset.order_by('prog_code')
    degrees = (
        programs_queryset
        .values_list('degree', flat=True)
        .distinct()
        .order_by('degree')
    )

    return {
        "programs": programs,
        "degrees": degrees,
        "years": _distinct_non_empty(option_querysets["year"], "year"),
        "sems": _distinct_non_empty(option_querysets["sem"], "sem"),
        "course_categories": _distinct_non_empty(option_querysets["course_category"], "course_category"),
        "parts": _distinct_non_empty(option_querysets["part"], "part"),
    }


def _whole_number_or_none(value, field_label):
    value = (value or "").strip()
    if not value:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} must be a whole number")

    if not number.is_integer():
        raise ValueError(f"{field_label} must be a whole number")

    return int(number)


def _get_course_scope(user):
    return get_accessible_courses(user)


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
    
    scoped_programs = get_accessible_programs(request.user)
    base_queryset = _get_course_scope(request.user)
    courses = _apply_course_filters(base_queryset, filters).annotate(
        has_syllabus_pdf=models.Exists(
            CourseSyllabus.objects.filter(
                course_code=models.OuterRef('course_code'),
                pdf__isnull=False,
            ).exclude(pdf='')
        )
    )
    
    # Get filter options for dropdowns
    filter_options = _build_course_filter_options(base_queryset, filters, scoped_programs)
    
    # Pagination
    paginator = Paginator(courses.order_by('program__prog_code', 'year', 'sem', 'course_code'), per_page)
    page_obj = paginator.get_page(page)
    
    # Preserve query parameters for pagination
    query_params = request.GET.copy()
    query_params.pop('page', None)
    
    # Calculate stats - Handle cases where there are no courses
    total_courses = base_queryset.count()
    total_programs = scoped_programs.count()
    
    # Calculate average credits safely
    avg_credits = 0
    if total_courses > 0:
        avg_credits_result = base_queryset.aggregate(avg_credits=models.Avg('credit'))
        avg_credits = avg_credits_result.get('avg_credits') or 0
    
    # Count courses with syllabus
    courses_with_syllabus = CourseSyllabus.objects.filter(
        course_code__in=base_queryset.values_list("course_code", flat=True).distinct()
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
        **filter_options,
        **stats,
    }
    return render(request, "course_management.html", context)

@course_management_access_required
def get_filter_options(request):

    filters = {field: request.GET.get(field) for field in COURSE_FILTER_FIELDS}
    queryset = _get_course_scope(request.user)
    options = _build_course_filter_options(queryset, filters, get_accessible_programs(request.user))
    
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
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
        
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
                'part': course.part or '',
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
        part = request.POST.get("part", "").strip()
        hrs_per_week = request.POST.get("hrs_per_week", "")
        credit = request.POST.get("credit", "")
        marks_cia = request.POST.get("marks_cia", "")
        marks_ese = request.POST.get("marks_ese", "")
        total_marks = request.POST.get("total_marks", "")
        
        # Validate required fields
        if not all([program_id, course_code, course_title, year, sem]):
            return JsonResponse({'success': False, 'error': 'Program, Course Code, Course Title, Year, and Semester are required.'})
        
        # Get program
        allowed_programs = get_accessible_programs(request.user)
        try:
            program = allowed_programs.get(id=program_id)
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist.'})
        
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
            hrs_per_week=float(hrs_per_week) if hrs_per_week else None,
            credit=_whole_number_or_none(credit, "Credit"),
            marks_cia=float(marks_cia) if marks_cia else None,
            marks_ese=float(marks_ese) if marks_ese else None,
            total_marks=float(total_marks) if total_marks else None,
        )
        
        CourseSyllabus.objects.get_or_create(course_code=course.course_code)

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
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
        old_course_code = course.course_code
        
        program_id = request.POST.get("program_id")
        course_code = request.POST.get("course_code", "").strip().upper().replace(" ", "")
        course_title = request.POST.get("course_title", "").strip()
        year = request.POST.get("year", "").strip()
        sem = request.POST.get("sem", "").strip()
        course_category = request.POST.get("course_category", "").strip()
        part = request.POST.get("part", "").strip()
        hrs_per_week = request.POST.get("hrs_per_week", "")
        credit = request.POST.get("credit", "")
        marks_cia = request.POST.get("marks_cia", "")
        marks_ese = request.POST.get("marks_ese", "")
        total_marks = request.POST.get("total_marks", "")
        
        # Validate required fields
        if not all([program_id, course_code, course_title, year, sem]):
            return JsonResponse({'success': False, 'error': 'Program, Course Code, Course Title, Year, and Semester are required.'})
        
        # Get program
        allowed_programs = get_accessible_programs(request.user)
        try:
            program = allowed_programs.get(id=program_id)
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist.'})
        
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
        course.hrs_per_week = float(hrs_per_week) if hrs_per_week else None
        course.credit = _whole_number_or_none(credit, "Credit")
        course.marks_cia = float(marks_cia) if marks_cia else None
        course.marks_ese = float(marks_ese) if marks_ese else None
        course.total_marks = float(total_marks) if total_marks else None
        course.save()

        CourseSyllabus.objects.get_or_create(course_code=course.course_code)
        if old_course_code != course.course_code and not CourseStructure.objects.filter(course_code=old_course_code).exists():
            CourseSyllabus.objects.filter(course_code=old_course_code).delete()

        return JsonResponse({'success': True, 'message': 'Course updated successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def delete_course(request, course_id):

    try:
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
        course_code = course.course_code
        course.delete()

        if not CourseStructure.objects.filter(course_code=course_code).exists():
            CourseSyllabus.objects.filter(course_code=course_code).delete()

        return JsonResponse({'success': True, 'message': 'Course deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
def download_sample_excel(request):

    scoped_programs = list(get_accessible_programs(request.user).values_list('prog_code', flat=True)[:3])
    if scoped_programs:
        sample_program_codes = (scoped_programs * 3)[:3]
    else:
        sample_program_codes = ['BSC-CS', 'BSC-CS', 'MA-ENG']

    sample_data = {
        'program_code': sample_program_codes,
        'course_code': ['CS101', 'CS102', 'ENG101'],
        'course_title': ['Programming Fundamentals', 'Data Structures', 'Literary Theory'],
        'year': ['1', '1', '1'],
        'sem': ['1', '2', '1'],
        'course_category': ['Core', 'Core', 'Elective'],
        'part': ['I', 'I', 'II'],
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

    courses = _get_course_scope(request.user).order_by('program__prog_code', 'year', 'sem', 'course_code')
    
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
            'Part': course.part or '',
            'Hours/Week': course.hrs_per_week or '',
            'Credit': int(course.credit) if course.credit is not None else '',
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

    try:
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
        allowed_programs = get_accessible_programs(request.user)
        
        for index, row in df.iterrows():
            program_code = str(row.get('program_code', '')).strip().upper().replace(" ", "")
            course_code = str(row.get('course_code', '')).strip().upper().replace(" ", "")
            course_title = str(row.get('course_title', '')).strip()
            year = str(row.get('year', '')).strip()
            sem = str(row.get('sem', '')).strip()
            course_category = str(row.get('course_category', '')).strip() if pd.notna(row.get('course_category')) else None
            part = str(row.get('part', '')).strip() if pd.notna(row.get('part')) else None
            try:
                hrs_per_week = _optional_float_from_excel(row.get('hrs_per_week'), 'Hours Per Week', index + 2)
                credit = _optional_integer_from_excel(row.get('credit'), 'Credit', index + 2)
                marks_cia = _optional_float_from_excel(row.get('marks_cia'), 'CIA Marks', index + 2)
                marks_ese = _optional_float_from_excel(row.get('marks_ese'), 'ESE Marks', index + 2)
                total_marks = _optional_float_from_excel(row.get('total_marks'), 'Total Marks', index + 2)
            except ValueError as e:
                errors.append(str(e))
                continue
            
            # Validate required fields
            if not all([program_code, course_code, course_title, year, sem]):
                errors.append(f'Row {index + 2}: Program Code, Course Code, Course Title, Year, and Semester are required')
                continue
            
            # Get program
            try:
                program = allowed_programs.get(prog_code=program_code)
            except Program.DoesNotExist:
                errors.append(f'Row {index + 2}: Program with code "{program_code}" not found')
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
                CourseSyllabus.objects.get_or_create(course_code=course_code)
                created_courses.append(f"{program_code}-{course_code}")
            except Exception as e:
                errors.append(f'Row {index + 2}: Error - {str(e)}')
        
        if created_courses:
            message = f'Successfully imported {len(created_courses)} courses.'
            if errors:
                message += f' {len(errors)} errors encountered.'
            return JsonResponse({'success': True, 'message': message, 'created': len(created_courses), 'errors': errors[:10]})
        else:
            return JsonResponse({'success': False, 'error': f'No courses imported. Errors: {", ".join(errors[:5])}'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@course_management_access_required
@require_http_methods(["POST"])
def upload_syllabus(request, course_id):

    try:
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
        
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
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
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
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
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
        course = get_object_or_404(_get_course_scope(request.user), id=course_id)
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
