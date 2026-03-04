import openpyxl
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from openpyxl.styles import Font, PatternFill
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json, os
from .models import CourseStr, CourseContent
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def upload_center(request):
    courses = CourseStr.objects.all().order_by('-created_at')
    for course in courses:
        course.has_pdf = CourseContent.objects.filter(
            course_code=course.course_code,
            pdf__isnull=False
        ).exists()

    prog_code = request.GET.get("prog_code")
    branch = request.GET.get("branch")
    year = request.GET.get("year")
    prog_type = request.GET.get("prog_type")
    prog_category = request.GET.get("prog_category")
    sem = request.GET.get("sem")
    course_code = request.GET.get("course_code")
    category = request.GET.get("course_category")
    title = request.GET.get("course_title")

    filters_used = any([prog_code, branch, year, prog_type, prog_category, sem, course_code, category, title])

    if course_code:
        filtered = courses.filter(course_code__iexact=course_code.strip())
        if not filtered.exists():
            messages.error(request, "Please give the correct subject code.")
            courses = CourseStr.objects.none()
        else:
            courses = filtered
            messages.success(request, "Course filtered successfully.")

    elif filters_used:
        if prog_code:
            courses = courses.filter(prog_code=prog_code)
        if branch:
            courses = courses.filter(branch=branch)
        if year:
            courses = courses.filter(year=year)
        if prog_type:
            courses = courses.filter(prog_type=prog_type)
        if prog_category:
            courses = courses.filter(prog_category=prog_category)
        if sem:
            courses = courses.filter(sem=sem)
        if category:
            courses = courses.filter(course_category=category)
        if title:
            courses = courses.filter(course_title__icontains=title)

        if not courses.exists():
            messages.warning(request, "No such course available.")
        else:
            messages.success(request, "Course filtered successfully.")

    finalized = request.session.get('courses_finalized', False)
    branches = CourseStr.objects.exclude(branch__isnull=True)\
        .exclude(branch='')\
        .values_list('branch', flat=True)\
        .distinct()\
        .order_by('branch')

    return render(request, 'upload_center.html', {
        'courses': courses,
        'finalized': finalized,
        'branches': branches,
    })


def upload_course_content(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        course_code = request.POST.get('course_code', '').strip()
        pdf_file = request.FILES['pdf_file']

        if not course_code:
            messages.error(request, 'Missing course code.')
            return redirect('upload_center:upload_center')

        safe_code = course_code.replace(' ', '')
        course_content, created = CourseContent.objects.get_or_create(course_code=safe_code)
        course_content.pdf = pdf_file
        course_content.save()

        verb = "Created" if created else "Updated"
        messages.success(request, f'PDF {verb.lower()} for {safe_code}.')
        return redirect('upload_center:upload_center')

    messages.error(request, 'No file uploaded.')
    return redirect('upload_center:upload_center')


def delete_course(request, course_id):
    if request.method == 'POST':
        try:
            course = CourseStr.objects.get(id=course_id)
            course.delete()
            messages.success(request, 'Course deleted successfully.')
        except CourseStr.DoesNotExist:
            messages.error(request, 'Course not found.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('upload_center:upload_center')


def add_course(request):
    if request.method == "POST":
        prog_code = (request.POST.get("prog_code") or '').strip()
        branch = (request.POST.get("branch") or '').strip()
        year = (request.POST.get("year") or '').strip()
        prog_type = (request.POST.get("prog_type") or '').strip()
        sem = (request.POST.get("sem") or '').strip()

        course_code = (request.POST.get("course_code") or '').strip()
        part = (request.POST.get("part") or '').strip()
        course_category = (request.POST.get("course_category") or '').strip()
        course_title = (request.POST.get("course_title") or '').strip()
        hrs_per_week = request.POST.get("hrs_per_week")
        credit = request.POST.get("credit")
        marks_cia = request.POST.get("marks_cia")
        marks_ese = request.POST.get("marks_ese")
        total_marks = request.POST.get("total_marks")

        CourseStr.objects.create(
            year=year,
            prog_type=prog_type,
            prog_code=prog_code,
            branch=branch,
            sem=sem,
            course_code=course_code,
            part=part,
            course_category=course_category,
            course_title=course_title,
            hrs_per_week=hrs_per_week or 0,
            credit=credit or 0,
            marks_cia=marks_cia or 0,
            marks_ese=marks_ese or 0,
            total_marks=total_marks or 0,
            is_finalized=True,
        )

        if "add_next" in request.POST:
            context = {
                "prog_code": prog_code,
                "year": year,
                "prog_type": prog_type,
                "sem": sem,
            }
            return render(request, "add_course.html", context)
        else:
            return redirect('upload_center:upload_center')

    return render(request, "add_course.html")


def save_courses(request):
    if request.method == "POST":
        CourseStr.objects.filter(is_saved=False).update(is_saved=True)
        messages.success(request, "Courses saved successfully.")
    return redirect('upload_center:upload_center')


def finalize_courses(request):
    if request.method == "POST":
        request.session['courses_finalized'] = True
        updated_count = CourseStr.objects.filter(is_finalized=False).update(is_finalized=True)
        if updated_count > 0:
            messages.success(request, f"{updated_count} courses have been finalized.")
        else:
            messages.info(request, "All courses are already finalized.")
    return redirect('course_manage:course_management')


def download_template(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Course Template"

    headings = [
        'prog_code', 'year', 'prog_type', 'sem', 'course_code',
        'part', 'course_category', 'course_title', 'hrs_per_week',
        'credit', 'marks_cia', 'marks_ese', 'total_marks'
    ]

    for col_num, heading in enumerate(headings, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = heading
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column_letter].width = min(max_length + 2, 40)

    ws.freeze_panes = 'A2'

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="course_upload_template.xlsx"'
    wb.save(response)
    return response