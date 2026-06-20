from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.contrib.auth.decorators import login_required

# Import models from other apps
from modules.program_manage.models import Program
from modules.course_management.models import CourseStructure, CourseSyllabus


def view_syllabus(request):
    """View to browse and download syllabi - accessible to all authenticated users"""
    
    # Get filter parameters
    program_id = request.GET.get('program')
    year = request.GET.get('year')
    sem = request.GET.get('sem')
    view_mode = request.GET.get('view_mode', 'structure')
    has_applied_filters = bool(request.GET)
    
    if view_mode not in ('structure', 'syllabus'):
        view_mode = 'syllabus'
    
    # Base queryset
    all_courses = CourseStructure.objects.select_related('program').annotate(
        has_syllabus_pdf=models.Exists(
            CourseSyllabus.objects.filter(
                course_code=models.OuterRef('course_code'),
                pdf__isnull=False,
            ).exclude(pdf='')
        )
    )
    
    # Apply filters
    if has_applied_filters:
        # Start with all course structures. Only require an existing PDF when
        # the user explicitly selected the 'syllabus' view mode.
        filtered_courses = all_courses
        if view_mode == 'syllabus':
            filtered_courses = filtered_courses.filter(has_syllabus_pdf=True)

        if program_id and program_id != "__all__":
            filtered_courses = filtered_courses.filter(program_id=program_id)
        if year and year != "__all__":
            filtered_courses = filtered_courses.filter(year=year)
        if sem and sem != "__all__":
            filtered_courses = filtered_courses.filter(sem=sem)

        filtered_courses = filtered_courses.order_by('program__prog_code', 'year', 'sem', 'course_code')
    else:
        filtered_courses = CourseStructure.objects.none()
    
    # Get filter options
    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    
    # Get unique years and semesters from course structures
    years = list(
        CourseStructure.objects.exclude(year__isnull=True)
        .exclude(year='')
        .values_list('year', flat=True)
        .distinct()
        .order_by('year')
    )
    sems = list(
        CourseStructure.objects.exclude(sem__isnull=True)
        .exclude(sem='')
        .values_list('sem', flat=True)
        .distinct()
        .order_by('sem')
    )
    
    context = {
        'courses': filtered_courses,
        'programs': programs,
        'years': years,
        'sems': sems,
        'selected_program': program_id,
        'selected_year': year,
        'selected_sem': sem,
        'selected_view_mode': view_mode,
        'has_applied_filters': has_applied_filters,
        'total_courses': filtered_courses.count(),
    }
    
    return render(request, 'view_syllabus.html', context)


def view_syllabus_pdf(request, course_id):
    """Open syllabus PDF inline for a specific course"""
    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        syllabus = get_object_or_404(CourseSyllabus, course_code=course.course_code)
        
        if not syllabus.pdf:
            return JsonResponse({'success': False, 'error': 'No syllabus file available.'})
        
        response = HttpResponse(syllabus.pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{course.course_code}_Syllabus.pdf"'
        return response
        
    except CourseSyllabus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Syllabus not found for this course.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def download_syllabus(request, course_id):
    """Download syllabus PDF for a specific course"""
    try:
        course = get_object_or_404(CourseStructure, id=course_id)
        syllabus = get_object_or_404(CourseSyllabus, course_code=course.course_code)
        
        if not syllabus.pdf:
            return JsonResponse({'success': False, 'error': 'No syllabus file available.'})
        
        response = HttpResponse(syllabus.pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{course.course_code}_Syllabus.pdf"'
        return response
        
    except CourseSyllabus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Syllabus not found for this course.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_filter_options(request):
    """Retrieve distinct options for view syllabus filters dynamically based on selections"""
    year = request.GET.get('year')
    program_id = request.GET.get('program')
    
    # Base queryset for all courses
    qs = CourseStructure.objects.all()
    
    # 1. Years option (always all distinct years from CourseStructure)
    years = list(
        CourseStructure.objects.exclude(year__isnull=True)
        .exclude(year='')
        .values_list('year', flat=True)
        .distinct()
        .order_by('year')
    )
    
    # 2. Programs options (filtered by year if provided)
    if year and year != "__all__":
        qs_program = qs.filter(year=year)
    else:
        qs_program = qs
        
    program_ids = qs_program.values_list('program_id', flat=True).distinct()
    programs = Program.objects.filter(id__in=program_ids, is_active=True).order_by('prog_code')
    programs_list = [
        {
            'id': p.id,
            'code': p.prog_code,
            'degree': p.degree,
            'branch': p.branch
        }
        for p in programs
    ]
    
    # 3. Semesters options (filtered by year and program if provided)
    qs_sem = qs
    if year and year != "__all__":
        qs_sem = qs_sem.filter(year=year)
    if program_id and program_id != "__all__":
        qs_sem = qs_sem.filter(program_id=program_id)
        
    sems = list(
        qs_sem.exclude(sem__isnull=True)
        .exclude(sem='')
        .values_list('sem', flat=True)
        .distinct()
        .order_by('sem')
    )
    
    return JsonResponse({
        'years': years,
        'programs': programs_list,
        'sems': sems
    })