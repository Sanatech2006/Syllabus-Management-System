from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.contrib.auth.decorators import login_required

# Import models from other apps
from modules.program_manage.models import Program
from modules.course_management.models import CourseStructure, CourseSyllabus


@login_required
def view_syllabus(request):
    """View to browse and download syllabi - accessible to all authenticated users"""
    
    # Get filter parameters
    program_id = request.GET.get('program')
    year = request.GET.get('year')
    sem = request.GET.get('sem')
    search = request.GET.get('search', '')
    
    # Base queryset - only courses that have syllabi
    all_courses = CourseStructure.objects.select_related('program').all()
    
    # Filter only courses that have syllabi
    courses_with_syllabus = []
    for course in all_courses:
        if CourseSyllabus.objects.filter(course_code=course.course_code).exists():
            courses_with_syllabus.append(course)
    
    # Apply filters
    filtered_courses = courses_with_syllabus
    if program_id:
        filtered_courses = [c for c in filtered_courses if str(c.program.id) == program_id]
    if year:
        filtered_courses = [c for c in filtered_courses if c.year == year]
    if sem:
        filtered_courses = [c for c in filtered_courses if c.sem == sem]
    if search:
        filtered_courses = [
            c for c in filtered_courses 
            if search.lower() in c.course_code.lower() or 
               search.lower() in c.course_title.lower()
        ]
    
    # Get filter options
    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    
    # Get unique years and semesters from courses with syllabi
    years = sorted(set([c.year for c in courses_with_syllabus if c.year]))
    sems = sorted(set([c.sem for c in courses_with_syllabus if c.sem]))
    
    context = {
        'courses': filtered_courses,
        'programs': programs,
        'years': years,
        'sems': sems,
        'selected_program': program_id,
        'selected_year': year,
        'selected_sem': sem,
        'search_query': search,
        'total_courses': len(filtered_courses),
    }
    
    return render(request, 'view_syllabus.html', context)


@login_required
def download_syllabus(request, course_id):
    """Download syllabus PDF for a specific course"""
    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        syllabus = get_object_or_404(CourseSyllabus, course_code=course.course_code)
        
        if not syllabus.pdf:
            return JsonResponse({'success': False, 'error': 'No syllabus file available.'})
        
        # Serve the PDF file
        response = HttpResponse(syllabus.pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{course.course_code}_Syllabus.pdf"'
        return response
        
    except CourseSyllabus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Syllabus not found for this course.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})