import openpyxl
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from openpyxl.styles import Font, PatternFill
from .models import CourseStr, CourseContent
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def upload_center(request):
    courses = CourseStr.objects.all().order_by('-created_at')

    # Set has_pdf dynamically
    for course in courses:
        course.has_pdf = CourseContent.objects.filter(
            course_code=course.course_code,
            pdf__isnull=False
        ).exists()
    years = CourseStr.objects.values_list('year', flat=True).distinct().order_by('-year')
    return render(request, 'upload_center.html', {
        'courses': courses,
        'years':years,
    })


# 🔵 Upload → Blue "Uploaded"
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

        # RESET STATES
        CourseStr.objects.filter(course_code=safe_code).update(
            is_saved=False,
            is_finalized=False
        )

        messages.success(request, f'PDF uploaded for {safe_code}.')
        return redirect('upload_center:upload_center')

    messages.error(request, 'No file uploaded.')
    return redirect('upload_center:upload_center')


# 🟢 Save → Green "Saved"
def save_courses(request):
    if request.method == "POST":
        courses = CourseStr.objects.all()

        for course in courses:
            has_pdf = CourseContent.objects.filter(
                course_code=course.course_code,
                pdf__isnull=False
            ).exists()

            if has_pdf and not course.is_finalized:
                course.is_saved = True
                course.save()

        messages.success(request, "Courses saved successfully.")

    return redirect('upload_center:upload_center')


# ⚪ Save & Confirm → Grey "Uploaded ✔"
def finalize_courses(request):
    if request.method == "POST":
        count = CourseStr.objects.filter(is_saved=True).update(is_finalized=True)

        if count > 0:
            messages.success(request, f"{count} courses uploaded successfully.")
        else:
            messages.info(request, "No saved courses to upload.")

    return redirect('upload_center:upload_center')


def delete_course(request, course_id):
    if request.method == 'POST':
        try:
            course = CourseStr.objects.get(id=course_id)
            course.delete()
            messages.success(request, 'Course deleted successfully.')
        except CourseStr.DoesNotExist:
            messages.error(request, 'Course not found.')

    return redirect('upload_center:upload_center')


def add_course(request):
    if request.method == "POST":
        CourseStr.objects.create(
            year=request.POST.get("year"),
            prog_type=request.POST.get("prog_type"),
            prog_code=request.POST.get("prog_code"),
            branch=request.POST.get("branch"),
            sem=request.POST.get("sem"),
            course_code=request.POST.get("course_code"),
            part=request.POST.get("part"),
            course_category=request.POST.get("course_category"),
            course_title=request.POST.get("course_title"),
            hrs_per_week=request.POST.get("hrs_per_week") or 0,
            credit=request.POST.get("credit") or 0,
            marks_cia=request.POST.get("marks_cia") or 0,
            marks_ese=request.POST.get("marks_ese") or 0,
            total_marks=request.POST.get("total_marks") or 0,
        )

        return redirect('upload_center:upload_center')

    return render(request, "add_course.html")


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

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="course_upload_template.xlsx"'
    wb.save(response)
    return response