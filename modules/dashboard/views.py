from django.shortcuts import render
from django.db.models import Sum
from modules.upload_center.models import CourseStr

def dashboard(request):

    total_programs = CourseStr.objects.values('prog_code').distinct().count()
    total_courses = CourseStr.objects.count()
    total_subjects = CourseStr.objects.count()
    total_credits = CourseStr.objects.aggregate(Sum('credit'))['credit__sum'] or 0

    recent_courses = CourseStr.objects.order_by('-id')[:5]

    context = {
        'total_programs': total_programs,
        'total_courses': total_courses,
        'total_subjects': total_subjects,
        'total_credits': total_credits,
        'recent_courses': recent_courses,
    }

    return render(request, 'dashboard.html', context)