from django.shortcuts import render
from django.db.models import Sum, Count
from modules.upload_center.models import CourseStr
from django.db.models import Q

def dashboard(request):
    # Filter for CURRENT finalized courses only
    current_courses = CourseStr.objects.filter(is_finalized=True)
    
    total_programs = current_courses.values('prog_code').distinct().count()
    total_courses = current_courses.count()
    total_subjects = current_courses.count()
    ug_courses = current_courses.filter(prog_code__startswith='U').count()
    pg_courses = current_courses.exclude(prog_code__startswith='U').count()
    arts_courses = current_courses.filter(
        prog_category__iexact='Arts'
    ).count()
    science_courses = current_courses.filter(
        prog_category__iexact='Science'
    ).count()
    total_credits = current_courses.aggregate(Sum('credit'))['credit__sum'] or 0
    recent_courses = current_courses.order_by('-id')[:5]

    context = {
        'total_programs': total_programs,
        'total_courses': total_courses,
        'total_subjects': total_subjects,
        'ug_courses': ug_courses,
        'pg_courses': pg_courses,
        'arts_courses': arts_courses,  
        'science_courses': science_courses,  
        'total_credits': total_credits,
        'recent_courses': recent_courses,
    }

    return render(request, 'dashboard.html', context)
