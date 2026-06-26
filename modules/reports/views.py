from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from modules.core.decorators import admin_required
from modules.course_management.models import CourseStructure, CourseSyllabus


@admin_required
def work_progress_report(request):
    # Build a list of courses with syllabus upload status.
    courses = CourseStructure.objects.select_related('program').order_by(
        'program__prog_code', 'year', 'sem', 'course_code'
    )

    # Annotate uploaded status by course_code.
    uploaded_course_codes = set(
        CourseSyllabus.objects.filter(pdf__isnull=False).exclude(pdf='').values_list(
            'course_code', flat=True
        )
    )

    course_list = []
    for course in courses:
        course.get_content = CourseSyllabus.objects.filter(course_code=course.course_code).first()
        course_list.append(course)

    page = request.GET.get('page', 1)
    paginator = Paginator(course_list, 20)
    page_obj = paginator.get_page(page)

    total = course_list.__len__()
    uploaded = sum(1 for course in course_list if course.get_content and course.get_content.pdf)
    percentage = round((uploaded / total) * 100, 2) if total else 0

    context = {
        'courses': page_obj,
        'page_obj': page_obj,
        'total': total,
        'uploaded': uploaded,
        'percentage': percentage,
    }
    return render(request, 'reports.html', context)
