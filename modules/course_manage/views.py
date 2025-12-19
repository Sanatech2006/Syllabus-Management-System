from django.shortcuts import render
from modules.upload_center.models import CourseStr  # CORRECT import
from django.shortcuts import get_object_or_404
from modules.upload_center.models import CourseStr, CourseContent
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings

def home(request):
    return render(request, 'menus.html') 

def course_management(request):
    year = request.GET.get('year')
    prog_type = request.GET.get('prog_type')
    course_category = request.GET.get('course_category')
    prog_code = request.GET.get('prog_code')
    part = request.GET.get('part')
    sem = request.GET.get('sem')
    course_code_title = request.GET.get('course_code_title')
    
    courses = CourseStr.objects.all()
    
    if year: courses = courses.filter(year=year)
    if prog_type: courses = courses.filter(prog_type=prog_type)
    if course_category: courses = courses.filter(course_category=course_category)
    if prog_code: courses = courses.filter(prog_code=prog_code)
    if part: courses = courses.filter(part=part)
    if sem: courses = courses.filter(sem=sem)
    if course_code_title: courses = courses.filter(course_code=course_code_title)
    
    context = {
        'courses': courses,
        'years': list(CourseStr.objects.values_list('year', flat=True).distinct()),
        'prog_types': list(CourseStr.objects.values_list('prog_type', flat=True).distinct()),
        'course_categories': list(CourseStr.objects.values_list('course_category', flat=True).distinct()),
        'prog_codes': list(CourseStr.objects.values_list('prog_code', flat=True).distinct()),
        'parts': list(CourseStr.objects.values_list('part', flat=True).distinct()),
        'semesters': list(CourseStr.objects.values_list('sem', flat=True).distinct()),
        'course_code_titles': list(CourseStr.objects.values('course_code', 'course_title').distinct())
    }
    
    return render(request, 'cou_manage.html', context)

def view_course_pdf(request, course_code):
    course_content = get_object_or_404(CourseContent, course_code=course_code)
    stored_path = course_content.course_content  # "course_pdfs/CS501.pdf"
    
    # Always save to static/ but store relative path
    full_path = os.path.join(settings.BASE_DIR, 'static', stored_path)
    
    if not os.path.exists(full_path):
        return HttpResponse(f"PDF not found at: {full_path}", status=404)
    
    with open(full_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{course_code}.pdf"'
    return response


def debug_pdf_path(request, course_code):
    course_content = get_object_or_404(CourseContent, course_code=course_code)
    path_in_db = course_content.course_content  # What string is stored?
    
    full_path = os.path.join(settings.MEDIA_ROOT, path_in_db)
    
    return HttpResponse(f"""
    <h2>DEBUG INFO for {course_code}</h2>
    <p>DB Path: <strong>{path_in_db}</strong></p>
    <p>MEDIA_ROOT: <strong>{settings.MEDIA_ROOT}</strong></p>
    <p>Full Path: <strong>{full_path}</strong></p>
    <p>File Exists: <strong>{os.path.exists(full_path)}</strong></p>
    """)
