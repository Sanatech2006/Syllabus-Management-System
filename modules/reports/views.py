import io

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from modules.course_management.access import course_management_access_required, get_accessible_programs
from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program


def _distinct_non_empty(queryset, field_name):
    return list(
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _base_course_queryset(user):
    courses = CourseStructure.objects.select_related('program')
    if user.is_superuser:
        return courses
    return courses.filter(program_id__in=get_accessible_programs(user).values_list('id', flat=True))


def _base_program_queryset(user):
    if user.is_superuser:
        return Program.objects.filter(is_active=True)
    return get_accessible_programs(user)


def _base_hod_queryset(user):
    User = get_user_model()
    if user.is_superuser:
        return User.objects.filter(hodprogrammap__isnull=False).distinct().order_by('username')
    return User.objects.filter(id__in=HodProgramMap.objects.filter(
        program_id__in=get_accessible_programs(user).values_list('id', flat=True)
    ).values_list('user_id', flat=True)).distinct().order_by('username')


def _display_user_name(user):
    return user.get_full_name() or user.username


def _apply_report_filters(queryset, filters):
    year = filters.get('year')
    if year and year != '__all__':
        queryset = queryset.filter(year=year)

    program = filters.get('program')
    if program and program != '__all__':
        queryset = queryset.filter(program_id=program)

    hod = filters.get('hod')
    if hod and hod != '__all__':
        queryset = queryset.filter(program__hodprogrammap__user_id=hod)

    search = (filters.get('search') or '').strip()
    if search:
        search_query = (
            Q(course_code__icontains=search)
            | Q(course_title__icontains=search)
            | Q(program__prog_code__icontains=search)
            | Q(program__branch__icontains=search)
            | Q(program__hodprogrammap__user__username__icontains=search)
            | Q(program__hodprogrammap__user__first_name__icontains=search)
            | Q(program__hodprogrammap__user__last_name__icontains=search)
        )
        queryset = queryset.filter(search_query)

    status = filters.get('status')
    if status in {'uploaded', 'not_uploaded'}:
        uploaded_codes = CourseSyllabus.objects.filter(pdf__isnull=False).exclude(pdf='').values_list(
            'course_code', flat=True
        )
        queryset = queryset.filter(course_code__in=uploaded_codes) if status == 'uploaded' else queryset.exclude(
            course_code__in=uploaded_codes
        )

    return queryset.distinct()


def _decorate_courses(courses):
    uploaded_by_code = {
        syllabus.course_code: syllabus
        for syllabus in CourseSyllabus.objects.filter(course_code__in=[course.course_code for course in courses])
    }
    hod_map = {}
    mappings = HodProgramMap.objects.select_related('user').filter(
        program_id__in={course.program_id for course in courses}
    )
    for mapping in mappings:
        hod_map.setdefault(mapping.program_id, []).append(_display_user_name(mapping.user))

    for course in courses:
        course.get_content = uploaded_by_code.get(course.course_code)
        course.hod_names = ', '.join(sorted(set(hod_map.get(course.program_id, [])))) or '—'
        yield course


def _report_rows(course_list):
    rows = []
    for course in course_list:
        content = course.get_content
        rows.append({
            'Year': course.year or '',
            'Program': course.program.prog_code if course.program else '',
            'Branch': course.program.branch if course.program else '',
            'HOD': course.hod_names if course.hod_names != '—' else '',
            'Course Code': course.course_code or '',
            'Course Title': course.course_title or '',
            'Semester': course.sem or '',
            'Status': 'Uploaded' if content and content.pdf else 'Not Uploaded',
            'Uploaded On': content.created_at.strftime('%d-%m-%Y') if content and content.created_at else '',
        })
    return rows


@course_management_access_required
def work_progress_report(request):
    per_page = int(request.GET.get('per_page', 100))
    page = request.GET.get('page', 1)
    is_partial = request.GET.get('partial') == '1'
    filters = {
        'year': request.GET.get('year', '__all__'),
        'program': request.GET.get('program', '__all__'),
        'hod': request.GET.get('hod', '__all__'),
        'status': request.GET.get('status', '__all__'),
        'search': request.GET.get('search', ''),
    }

    base_queryset = _base_course_queryset(request.user)
    filtered_queryset = _apply_report_filters(base_queryset, filters).order_by(
        'program__prog_code', 'year', 'sem', 'course_code'
    )
    course_list = list(_decorate_courses(filtered_queryset))

    paginator = Paginator(course_list, per_page)
    page_obj = paginator.get_page(page)

    total = len(course_list)
    uploaded = sum(1 for course in course_list if course.get_content and course.get_content.pdf)
    percentage = round((uploaded / total) * 100, 2) if total else 0
    no_of_programs = len({course.program_id for course in course_list})

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('per_page', None)

    context = {
        'courses': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'total': total,
        'uploaded': uploaded,
        'percentage': percentage,
        'no_of_programs': no_of_programs,
        'years': _distinct_non_empty(base_queryset, 'year'),
        'programs': _base_program_queryset(request.user).order_by('prog_code'),
        'hods': [
            {'id': hod.id, 'name': _display_user_name(hod)}
            for hod in _base_hod_queryset(request.user)
        ],
        'selected_year': filters['year'],
        'selected_program': filters['program'],
        'selected_hod': filters['hod'],
        'selected_status': filters['status'],
        'selected_search': filters['search'],
        'pagination_query': query_params.urlencode(),
    }
    if is_partial:
        html = render_to_string('reports_table_partial.html', context, request=request)
        return HttpResponse(html)
    return render(request, 'reports.html', context)


@course_management_access_required
def download_work_progress_excel(request):
    filters = {
        'year': request.GET.get('year', '__all__'),
        'program': request.GET.get('program', '__all__'),
        'hod': request.GET.get('hod', '__all__'),
        'status': request.GET.get('status', '__all__'),
        'search': request.GET.get('search', ''),
    }
    courses = list(_decorate_courses(_apply_report_filters(
        _base_course_queryset(request.user), filters
    ).order_by('program__prog_code', 'year', 'sem', 'course_code')))

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(_report_rows(courses)).to_excel(writer, sheet_name='Work Progress Report', index=False)
    output.seek(0)

    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Work_Progress_Report.xlsx"'
    return response
