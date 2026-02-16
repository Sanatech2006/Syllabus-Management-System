from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json, os
from .models import CourseStr, CourseContent
from django.conf import settings
from django.http import HttpResponseRedirect

def upload_center(request):
    # FETCH DATA FOR TABLE DISPLAY
    courses = CourseStr.objects.all().order_by('-created_at')[:20]
    finalized = request.session.get('courses_finalized', False)
    return render(request, 'upload_center.html', {'courses': courses, 'finalized': finalized})

def upload_course_content(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        course_code = request.POST.get('course_code', '').strip()
        pdf_file = request.FILES['pdf_file']

        if not course_code:
            messages.error(request, 'Missing course code.')
            return redirect('upload_center')

        safe_code = course_code.replace(' ', '')
        course_content, created = CourseContent.objects.get_or_create(
            course_code=safe_code
        )
        course_content.pdf = pdf_file  # Assign file to FileField
        course_content.save()  # Save to database
        
        verb = "Created" if created else "Updated"
        messages.success(request, f'PDF {verb.lower()} for {safe_code}.')
        return redirect('upload_center')

    messages.error(request, 'No file uploaded.')
    return redirect('upload_center')

def delete_course(request, course_id):
    """Delete a CourseStr entry by id. Expects POST."""
    if request.method == 'POST':
        try:
            course = CourseStr.objects.get(id=course_id)
            course.delete()
            messages.success(request, 'Course deleted successfully.')
        except CourseStr.DoesNotExist:
            messages.error(request, 'Course not found.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('upload_center')
def add_course(request):
    if request.method == "POST":
        # Shared 4 fields
        prog_code = (request.POST.get("prog_code") or '').strip()
        year = (request.POST.get("year") or '').strip()
        prog_type = (request.POST.get("prog_type") or '').strip()
        sem = (request.POST.get("sem") or '').strip()

        # 9 course fields
        course_code = (request.POST.get("course_code") or '').strip()
        part = (request.POST.get("part") or '').strip()
        course_category = (request.POST.get("course_category") or '').strip()
        course_title = (request.POST.get("course_title") or '').strip()
        hrs_per_week = request.POST.get("hrs_per_week")
        credit = request.POST.get("credit")
        marks_cia = request.POST.get("marks_cia")
        marks_ese = request.POST.get("marks_ese")
        total_marks = request.POST.get("total_marks")

        # Save one Course record
        CourseStr.objects.create(
            prog_code=prog_code,
            year=year,
            prog_type=prog_type,
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
        )

        # Check which button was clicked
        if "add_next" in request.POST:
            # Stay on same page, keep top fields
            context = {
                "prog_code": prog_code,
                "year": year,
                "prog_type": prog_type,
                "sem": sem,
            }
            return render(request, "add_course.html", context)
        else:
            # Save & confirm -> back to main Upload Center
            return redirect("upload_center")

    # GET: first time, empty form
    return render(request, "add_course.html")

def save_courses(request):
    if request.method == "POST":
        # Filter current batch (not all courses) - use session or form data
        CourseStr.objects.filter(is_saved=False).update(is_saved=True)  # Add filter!
        messages.success(request, "Courses saved successfully.")
    return redirect("upload_center")

def finalize_courses(request):
    if request.method == "POST":
        request.session['courses_finalized'] = True
        try:
            CourseStr.objects.filter(is_saved=True, is_finalized=False).update(is_finalized=True)
        except Exception:
            pass
        messages.success(request, "Courses finalized and ready in Course Management.")
    return redirect("course_management")  # Show confirmed courses!
