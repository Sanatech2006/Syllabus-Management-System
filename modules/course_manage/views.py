from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from modules.upload_center.models import CourseStr, CourseContent
from django.http import HttpResponse, FileResponse, Http404
import os
from django.conf import settings

def home(request):
    return redirect('course_management')   # or render('some_home.html')

def course_management(request):
    year = request.GET.get('year')
    prog_type = request.GET.get('prog_type')
    course_category = request.GET.get('course_category')
    prog_code = request.GET.get('prog_code')
    part = request.GET.get('part')
    sem = request.GET.get('sem')
    course_code_title = request.GET.get('course_code_title')
    
    # Only finalized courses visible here
    courses = CourseStr.objects.filter(is_finalized=True)
    
    if year: courses = courses.filter(year=year)
    if prog_type: courses = courses.filter(prog_type=prog_type)
    if course_category: courses = courses.filter(course_category=course_category)
    if prog_code: courses = courses.filter(prog_code=prog_code)
    if part: courses = courses.filter(part=part)
    if sem: courses = courses.filter(sem=sem)
    if course_code_title: courses = courses.filter(course_code=course_code_title)
    
    context = {
        'courses': courses,
        # Filters from finalized only for consistency
        'years': list(CourseStr.objects.filter(is_finalized=True).values_list('year', flat=True).distinct()),
        'prog_types': list(CourseStr.objects.filter(is_finalized=True).values_list('prog_type', flat=True).distinct()),
        'course_categories': list(CourseStr.objects.filter(is_finalized=True).values_list('course_category', flat=True).distinct()),
        'prog_codes': list(CourseStr.objects.filter(is_finalized=True).values_list('prog_code', flat=True).distinct()),
        'parts': list(CourseStr.objects.filter(is_finalized=True).values_list('part', flat=True).distinct()),
        'semesters': list(CourseStr.objects.filter(is_finalized=True).values_list('sem', flat=True).distinct()),
        'course_code_titles': list(CourseStr.objects.filter(is_finalized=True).values('course_code', 'course_title').distinct())
    }
    
    return render(request, 'cou_manage.html', context)

def view_course_pdf(request, course_code):
    course_code = course_code.strip()

    try:
        course = CourseContent.objects.get(course_code=course_code)
    except CourseContent.DoesNotExist:
        raise Http404("Course not found")

    # ✅ USE THE FILEFIELD
    if not course.pdf:
        raise Http404("PDF not uploaded for this course")

    full_path = course.pdf.path  # Django already resolves MEDIA_ROOT

    if not os.path.isfile(full_path):
        raise Http404("PDF file not found on server")

    return FileResponse(open(full_path, "rb"), content_type="application/pdf")


def debug_pdf_path(request, course_code):
    # Normalize incoming course_code to show correct debug info
    code = course_code.strip()
    course_content = get_object_or_404(CourseContent, course_code__iexact=code)
    path_in_db = course_content.course_content  # What string is stored?
    
    full_path = os.path.join(settings.MEDIA_ROOT, path_in_db)
    
    return HttpResponse(f"""
    <h2>DEBUG INFO for {course_code}</h2>
    <p>DB Path: <strong>{path_in_db}</strong></p>
    <p>MEDIA_ROOT: <strong>{settings.MEDIA_ROOT}</strong></p>
    <p>Full Path: <strong>{full_path}</strong></p>
    <p>File Exists: <strong>{os.path.exists(full_path)}</strong></p>
    """)
