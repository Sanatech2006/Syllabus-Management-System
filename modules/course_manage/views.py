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
    # Fix 1: Change to match template filter names
    course_code = request.GET.get('course_code')
    course_title = request.GET.get('course_title')
    
    # Only finalized courses visible here
    courses = CourseStr.objects.filter(is_finalized=True)
    
    if year: courses = courses.filter(year=year)
    if prog_type: courses = courses.filter(prog_type=prog_type)
    if course_category: courses = courses.filter(course_category=course_category)
    if prog_code: courses = courses.filter(prog_code=prog_code)
    if part: courses = courses.filter(part=part)
    if sem: courses = courses.filter(sem=sem)
    # Fix 2: Use the new filter variables
    if course_code: courses = courses.filter(course_code=course_code)
    if course_title: courses = courses.filter(course_title=course_title)
    
    # Get unique values, excluding empty/null ones
    context = {
        'courses': courses,
        # Add exclude empty to avoid blank options showing up
        'years': list(CourseStr.objects.filter(is_finalized=True).exclude(year__isnull=True).exclude(year='').values_list('year', flat=True).distinct().order_by('year')),
        'prog_types': list(CourseStr.objects.filter(is_finalized=True).exclude(prog_type__isnull=True).exclude(prog_type='').values_list('prog_type', flat=True).distinct().order_by('prog_type')),
        'course_categories': list(CourseStr.objects.filter(is_finalized=True).exclude(course_category__isnull=True).exclude(course_category='').values_list('course_category', flat=True).distinct().order_by('course_category')),
        'prog_codes': list(CourseStr.objects.filter(is_finalized=True).exclude(prog_code__isnull=True).exclude(prog_code='').values_list('prog_code', flat=True).distinct().order_by('prog_code')),
        'parts': list(CourseStr.objects.filter(is_finalized=True).exclude(part__isnull=True).exclude(part='').values_list('part', flat=True).distinct().order_by('part')),
        'semesters': list(CourseStr.objects.filter(is_finalized=True).exclude(sem__isnull=True).exclude(sem='').values_list('sem', flat=True).distinct().order_by('sem')),
        # Fix 3: Add separate querysets for course_code and course_title
        'course_codes': list(CourseStr.objects.filter(is_finalized=True).exclude(course_code__isnull=True).exclude(course_code='').values_list('course_code', flat=True).distinct().order_by('course_code')),
        'course_titles': list(CourseStr.objects.filter(is_finalized=True).exclude(course_title__isnull=True).exclude(course_title='').values_list('course_title', flat=True).distinct().order_by('course_title')),
        # Keep this for backward compatibility if needed elsewhere
        'course_code_titles': list(CourseStr.objects.filter(is_finalized=True).exclude(course_code__isnull=True).exclude(course_code='').values('course_code', 'course_title').distinct().order_by('course_code'))
    }
    
    print("=== DEBUG: Filter Values ===")
    print("Years:", list(CourseStr.objects.filter(is_finalized=True).values_list('year', flat=True).distinct()))
    print("Prog Types:", list(CourseStr.objects.filter(is_finalized=True).values_list('prog_type', flat=True).distinct()))
    print("Course Categories:", list(CourseStr.objects.filter(is_finalized=True).values_list('course_category', flat=True).distinct()))
    print("Prog Codes:", list(CourseStr.objects.filter(is_finalized=True).values_list('prog_code', flat=True).distinct()))
    print("Parts:", list(CourseStr.objects.filter(is_finalized=True).values_list('part', flat=True).distinct()))
    print("Semesters:", list(CourseStr.objects.filter(is_finalized=True).values_list('sem', flat=True).distinct()))
    print("Course Codes:", list(CourseStr.objects.filter(is_finalized=True).values_list('course_code', flat=True).distinct()))
    print("Course Titles:", list(CourseStr.objects.filter(is_finalized=True).values_list('course_title', flat=True).distinct()))
    print("=== END DEBUG ===")
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

def get_filter_options(request):
    """AJAX endpoint to get filter options based on selected filters"""
    
    # Get selected filter values from request
    year = request.GET.get('year')
    prog_type = request.GET.get('prog_type')
    course_category = request.GET.get('course_category')
    prog_code = request.GET.get('prog_code')
    part = request.GET.get('part')
    sem = request.GET.get('sem')
    course_code = request.GET.get('course_code')
    course_title = request.GET.get('course_title')
    
    # Start with all finalized courses
    queryset = CourseStr.objects.filter(is_finalized=True)
    
    # Apply filters based on what's already selected
    if year:
        queryset = queryset.filter(year=year)
    if prog_type:
        queryset = queryset.filter(prog_type=prog_type)
    if course_category:
        queryset = queryset.filter(course_category=course_category)
    if prog_code:
        queryset = queryset.filter(prog_code=prog_code)
    if part:
        queryset = queryset.filter(part=part)
    if sem:
        queryset = queryset.filter(sem=sem)
    if course_code:
        queryset = queryset.filter(course_code=course_code)
    if course_title:
        queryset = queryset.filter(course_title=course_title)
    
    # Get distinct values for each filter based on the filtered queryset
    options = {
        'years': list(queryset.exclude(year__isnull=True).exclude(year='').values_list('year', flat=True).distinct().order_by('year')),
        'prog_types': list(queryset.exclude(prog_type__isnull=True).exclude(prog_type='').values_list('prog_type', flat=True).distinct().order_by('prog_type')),
        'course_categories': list(queryset.exclude(course_category__isnull=True).exclude(course_category='').values_list('course_category', flat=True).distinct().order_by('course_category')),
        'prog_codes': list(queryset.exclude(prog_code__isnull=True).exclude(prog_code='').values_list('prog_code', flat=True).distinct().order_by('prog_code')),
        'parts': list(queryset.exclude(part__isnull=True).exclude(part='').values_list('part', flat=True).distinct().order_by('part')),
        'semesters': list(queryset.exclude(sem__isnull=True).exclude(sem='').values_list('sem', flat=True).distinct().order_by('sem')),
        'course_codes': list(queryset.exclude(course_code__isnull=True).exclude(course_code='').values_list('course_code', flat=True).distinct().order_by('course_code')),
        'course_titles': list(queryset.exclude(course_title__isnull=True).exclude(course_title='').values_list('course_title', flat=True).distinct().order_by('course_title')),
    }
    
    return JsonResponse(options)