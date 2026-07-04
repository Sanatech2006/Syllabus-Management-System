import io

import pandas as pd
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from modules.core.decorators import admin_required
from modules.course_management.access import course_management_access_required, get_accessible_programs, is_hod_user
from modules.core.roles import is_verifier_user
from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program
from .models import CourseVerification


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


def _normalize_part_value(value):
    if value is None:
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
        return str(int(float(text)))
    except (ValueError, TypeError):
        return text


def _normalize_semester_value(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        sem_int = int(float(text))
    except (ValueError, TypeError):
        return None

    if 1 <= sem_int <= 6:
        return str(sem_int)
    return None


def _part_lookup_values(value):
    normalized = _normalize_part_value(value)
    if not normalized:
        return []

    numeric_to_roman = {
        "1": "I",
        "2": "II",
        "3": "III",
        "4": "IV",
        "5": "V",
    }
    lookup_values = {str(value).strip(), normalized}
    roman_value = numeric_to_roman.get(str(normalized))
    if roman_value:
        lookup_values.add(roman_value)
    return [item for item in lookup_values if item]


def _verification_base_courses(user):
    courses = CourseStructure.objects.select_related("program")
    if user.is_superuser or is_verifier_user(user):
        return courses
    accessible_ids = get_accessible_programs(user).values_list("id", flat=True)
    return courses.filter(program_id__in=accessible_ids)


def _apply_verification_filters(queryset, filters, prefix="", exclude_field=None):
    year = filters.get("year")
    if exclude_field != "year" and year and year != "__all__":
        queryset = queryset.filter(**{f"{prefix}year": year})

    program = filters.get("program")
    if exclude_field != "program" and program and program != "__all__":
        queryset = queryset.filter(**{f"{prefix}program_id": program})

    prog_type = filters.get("prog_type")
    if exclude_field != "prog_type" and prog_type and prog_type != "__all__":
        queryset = queryset.filter(**{f"{prefix}program__prog_type": prog_type})

    prog_category = filters.get("prog_category")
    if exclude_field != "prog_category" and prog_category and prog_category != "__all__":
        queryset = queryset.filter(**{f"{prefix}program__prog_category": prog_category})

    degree = filters.get("degree")
    if exclude_field != "degree" and degree and degree != "__all__":
        queryset = queryset.filter(**{f"{prefix}program__degree": degree})

    branch = filters.get("branch")
    if exclude_field != "branch" and branch and branch != "__all__":
        queryset = queryset.filter(**{f"{prefix}program__branch__icontains": branch})

    sem = filters.get("sem")
    if exclude_field != "sem" and sem and sem != "__all__":
        queryset = queryset.filter(**{f"{prefix}sem": sem})

    part = filters.get("part")
    if exclude_field != "part" and part and part != "__all__":
        queryset = queryset.filter(**{f"{prefix}part__in": _part_lookup_values(part)})

    course_category = filters.get("course_category")
    if exclude_field != "course_category" and course_category and course_category != "__all__":
        queryset = queryset.filter(**{f"{prefix}course_category": course_category})

    course_title = filters.get("course_title")
    if exclude_field != "course_title" and course_title and course_title != "__all__":
        queryset = queryset.filter(
            Q(**{f"{prefix}course_code__icontains": course_title})
            | Q(**{f"{prefix}course_title__icontains": course_title})
        )

    syllabus_status = filters.get("syllabus_status")
    if exclude_field != "syllabus_status" and syllabus_status in {"uploaded", "not_uploaded"}:
        uploaded_codes = CourseSyllabus.objects.filter(pdf__isnull=False).exclude(pdf="").values_list(
            "course_code", flat=True
        )
        course_code_field = f"{prefix}course_code"
        queryset = queryset.filter(**{f"{course_code_field}__in": uploaded_codes}) if syllabus_status == "uploaded" else queryset.exclude(
            **{f"{course_code_field}__in": uploaded_codes}
        )

    return queryset


def _distinct_non_empty_related(queryset, field_name):
    return list(
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _build_verification_filter_options(base_queryset, filters):
    option_querysets = {
        field: _apply_verification_filters(base_queryset, filters, prefix="", exclude_field=field)
        for field in (
            "year",
            "program",
            "prog_type",
            "prog_category",
            "degree",
            "branch",
            "sem",
            "part",
            "course_category",
            "course_title",
        )
    }

    programs = (
        Program.objects.filter(
            id__in=option_querysets["program"].values_list("program_id", flat=True)
        )
        .distinct()
        .order_by("prog_code")
    )

    courses = option_querysets["course_title"].order_by("course_code")
    courses_list = []
    seen_courses = set()
    for course in courses:
        if course.course_code in seen_courses:
            continue
        seen_courses.add(course.course_code)
        courses_list.append({
            "code": course.course_code,
            "title": course.course_title or "",
        })

    return {
        "years": _distinct_non_empty_related(option_querysets["year"], "year"),
        "prog_types": _distinct_non_empty_related(option_querysets["prog_type"], "program__prog_type"),
        "prog_categories": _distinct_non_empty_related(option_querysets["prog_category"], "program__prog_category"),
        "degrees": _distinct_non_empty_related(option_querysets["degree"], "program__degree"),
        "branches": _distinct_non_empty_related(option_querysets["branch"], "program__branch"),
        "programs": [
            {
                "id": program.id,
                "code": program.prog_code,
                "degree": program.degree,
                "branch": program.branch,
            }
            for program in programs
        ],
        "sems": _distinct_non_empty_related(option_querysets["sem"], "sem"),
        "parts": sorted({
            normalized_part
            for normalized_part in (
                _normalize_part_value(part_value)
                for part_value in _distinct_non_empty_related(option_querysets["part"], "part")
            )
            if normalized_part
        }, key=lambda item: int(item) if str(item).isdigit() else str(item)),
        "course_categories": _distinct_non_empty_related(option_querysets["course_category"], "course_category"),
        "course_options": courses_list,
    }


def _verification_stats(queryset):
    return {
        "ug_verified": queryset.filter(course__program__prog_type="UG").count(),
        "pg_verified": queryset.filter(course__program__prog_type="PG").count(),
        "arts_verified": queryset.filter(course__program__prog_category="Arts").count(),
        "science_verified": queryset.filter(course__program__prog_category="Science").count(),
    }


def _verification_record_map(user, course_ids):
    records = CourseVerification.objects.select_related("course", "verifier").filter(
        verifier=user,
        course_id__in=course_ids,
    )
    return {record.course_id: record for record in records}


@login_required
@require_http_methods(["GET", "POST"])
def verification_center(request):
    if request.user.is_superuser:
        messages.info(request, "Use Verification Report for admin review.")
        return redirect("reports:verification_report")

    if not is_verifier_user(request.user):
        messages.error(request, "You do not have permission to access that section.")
        return redirect("/dashboard/")

    per_page = int(request.GET.get("per_page", 100))
    page = request.GET.get("page", 1)
    filters = {
        "year": request.GET.get("year", ""),
        "program": request.GET.get("program", "__all__"),
        "prog_type": request.GET.get("prog_type", "__all__"),
        "prog_category": request.GET.get("prog_category", "__all__"),
        "degree": request.GET.get("degree", "__all__"),
        "branch": request.GET.get("branch", "__all__"),
        "sem": request.GET.get("sem", "__all__"),
        "part": request.GET.get("part", "__all__"),
        "course_category": request.GET.get("course_category", "__all__"),
        "course_title": request.GET.get("course_title", "__all__"),
        "syllabus_status": request.GET.get("syllabus_status", "__all__"),
    }
    has_applied_filters = bool(request.GET.get("year"))

    base_queryset = _verification_base_courses(request.user)
    filtered_queryset = _apply_verification_filters(base_queryset, filters) if has_applied_filters else base_queryset
    filtered_queryset = filtered_queryset.order_by("program__prog_code", "year", "sem", "course_code")
    paginator = Paginator(filtered_queryset, per_page)
    page_obj = paginator.get_page(page)

    if request.method == "POST":
        action = request.POST.get("action", "save")
        selected_ids = {int(value) for value in request.POST.getlist("verified_courses") if str(value).isdigit()}

        with transaction.atomic():
            for course_id in selected_ids:
                defaults = {
                    "is_verified": True,
                    "status": CourseVerification.STATUS_SUBMITTED if action == "finish" else CourseVerification.STATUS_DRAFT,
                    "finished_at": timezone.now() if action == "finish" else None,
                }
                CourseVerification.objects.update_or_create(
                    course_id=course_id,
                    verifier=request.user,
                    defaults=defaults,
                )

        messages.success(
            request,
            "Verification submitted successfully." if action == "finish" else "Verification saved successfully.",
        )
        return redirect(request.get_full_path())

    verification_map = _verification_record_map(request.user, [course.id for course in page_obj])
    for course in page_obj:
        verification_record = verification_map.get(course.id)
        course.verification_record = verification_record
        course.is_verified_checked = bool(verification_record and verification_record.is_verified)
    filter_options = _build_verification_filter_options(base_queryset, filters)

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_params.pop("per_page", None)

    context = {
        "courses": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "pagination_query": query_params.urlencode(),
        "has_applied_filters": has_applied_filters,
        "selected_year": filters["year"],
        "selected_program": filters["program"],
        "selected_prog_type": filters["prog_type"],
        "selected_prog_category": filters["prog_category"],
        "selected_degree": filters["degree"],
        "selected_branch": filters["branch"],
        "selected_sem": filters["sem"],
        "selected_part": filters["part"],
        "selected_course_category": filters["course_category"],
        "selected_course_title": filters["course_title"],
        "selected_syllabus_status": filters["syllabus_status"],
        "verification_map": verification_map,
        "all_courses_for_search": filter_options["course_options"],
        "all_courses_list": filter_options["course_options"],
        "page_mode": "center",
        "post_action_url": request.path,
        **filter_options,
        **_verification_stats(
            CourseVerification.objects.select_related("course", "course__program").filter(
                verifier=request.user,
                status=CourseVerification.STATUS_SUBMITTED,
                is_verified=True,
            )
        ),
    }
    return render(request, "verification_page.html", context)


@admin_required
def verification_report(request):
    per_page = int(request.GET.get("per_page", 100))
    page = request.GET.get("page", 1)
    filters = {
        "year": request.GET.get("year", ""),
        "program": request.GET.get("program", "__all__"),
        "prog_type": request.GET.get("prog_type", "__all__"),
        "prog_category": request.GET.get("prog_category", "__all__"),
        "degree": request.GET.get("degree", "__all__"),
        "branch": request.GET.get("branch", "__all__"),
        "sem": request.GET.get("sem", "__all__"),
        "part": request.GET.get("part", "__all__"),
        "course_category": request.GET.get("course_category", "__all__"),
        "course_title": request.GET.get("course_title", "__all__"),
        "syllabus_status": request.GET.get("syllabus_status", "__all__"),
    }
    has_applied_filters = bool(request.GET.get("year"))

    base_queryset = CourseVerification.objects.select_related("course", "course__program", "verifier").filter(
        status=CourseVerification.STATUS_SUBMITTED,
        is_verified=True,
    )
    filtered_queryset = _apply_verification_filters(base_queryset, filters, prefix="course__") if has_applied_filters else base_queryset.none()
    filtered_queryset = filtered_queryset.order_by("course__program__prog_code", "course__year", "course__sem", "course__course_code", "updated_at")

    paginator = Paginator(filtered_queryset, per_page)
    page_obj = paginator.get_page(page)
    filter_options = _build_verification_filter_options(
        _verification_base_courses(request.user),
        filters,
    )

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_params.pop("per_page", None)

    context = {
        "records": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "pagination_query": query_params.urlencode(),
        "has_applied_filters": has_applied_filters,
        "selected_year": filters["year"],
        "selected_program": filters["program"],
        "selected_prog_type": filters["prog_type"],
        "selected_prog_category": filters["prog_category"],
        "selected_degree": filters["degree"],
        "selected_branch": filters["branch"],
        "selected_sem": filters["sem"],
        "selected_part": filters["part"],
        "selected_course_category": filters["course_category"],
        "selected_course_title": filters["course_title"],
        "selected_syllabus_status": filters["syllabus_status"],
        "all_courses_for_search": filter_options["course_options"],
        "all_courses_list": filter_options["course_options"],
        "page_mode": "report",
        "post_action_url": request.path,
        **filter_options,
        **_verification_stats(base_queryset),
    }
    return render(request, "verification_page.html", context)


def _verification_query_options(user, filters):
    base_queryset = _verification_base_courses(user)
    return _build_verification_filter_options(base_queryset, filters)


@login_required
def verification_filter_options(request):
    if not (request.user.is_superuser or is_verifier_user(request.user)):
        return JsonResponse({"error": "Permission denied"}, status=403)

    filters = {
        "year": request.GET.get("year", ""),
        "program": request.GET.get("program", "__all__"),
        "prog_type": request.GET.get("prog_type", "__all__"),
        "prog_category": request.GET.get("prog_category", "__all__"),
        "degree": request.GET.get("degree", "__all__"),
        "branch": request.GET.get("branch", "__all__"),
        "sem": request.GET.get("sem", "__all__"),
        "part": request.GET.get("part", "__all__"),
        "course_category": request.GET.get("course_category", "__all__"),
        "course_title": request.GET.get("course_title", "__all__"),
    }
    return JsonResponse(_verification_query_options(request.user, filters))
