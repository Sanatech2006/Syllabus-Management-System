from django.shortcuts import render
from django.db.models import Sum, Count
from modules.upload_center.models import CourseStr


def dashboard(request):
    current_courses = CourseStr.objects.all()

    # --- Basic Stats ---
    total_programs = current_courses.values('prog_code').distinct().count()
    total_courses = current_courses.count()
    total_subjects = total_courses

    # UG = prog_code starts with 'U', PG = everything else
    ug_courses = current_courses.filter(prog_code__istartswith='U').count()
    pg_courses = current_courses.exclude(prog_code__istartswith='U').count()

    # prog_category is NULL in your data — count by prog_code prefix instead
    arts_courses = current_courses.filter(prog_code__istartswith='U').count()   # adjust if you have arts codes
    science_courses = current_courses.exclude(prog_code__istartswith='U').count()  # adjust as needed

    # --- Course Category --- (these are fine, all are 'Core' currently)
    core_courses = current_courses.filter(course_category__iexact='Core').count()
    elective_courses = current_courses.filter(course_category__iexact='Elective').count()
    lab_courses = current_courses.filter(course_category__iexact='Lab').count()

    # --- Credits --- (Decimal fields work fine with Sum)
    total_credits = current_courses.aggregate(Sum('credit'))['credit__sum'] or 0
    sem1_credits = current_courses.filter(sem='I').aggregate(Sum('credit'))['credit__sum'] or 0
    sem2_credits = current_courses.filter(sem='II').aggregate(Sum('credit'))['credit__sum'] or 0
    sem3_credits = current_courses.filter(sem='III').aggregate(Sum('credit'))['credit__sum'] or 0
    sem4_credits = current_courses.filter(sem='IV').aggregate(Sum('credit'))['credit__sum'] or 0
    avg_credits = round(float(total_credits) / 4, 2) if total_credits else 0

    # --- Marks ---
    total_cia = current_courses.aggregate(Sum('marks_cia'))['marks_cia__sum'] or 0
    total_ese = current_courses.aggregate(Sum('marks_ese'))['marks_ese__sum'] or 0
    total_marks = total_cia + total_ese

    if total_marks:
        cia_percent = round((total_cia / total_marks) * 100)
        ese_percent = round((total_ese / total_marks) * 100)
    else:
        cia_percent = 0
        ese_percent = 0

    # --- Program Distribution ---
    # branch values in DB are '-', None, or full names like 'International Finance'
    # So group by prog_code instead — get top 4 programs by course count
    program_dist = (
        current_courses
        .values('prog_code')
        .annotate(count=Count('id'))
        .order_by('-count')[:4]
    )

    # Build a dict for easy access, pad to 4 entries
    prog_list = list(program_dist)
    def get_prog(index):
        return prog_list[index] if index < len(prog_list) else {'prog_code': '-', 'count': 0}

    prog1 = get_prog(0)
    prog2 = get_prog(1)
    prog3 = get_prog(2)
    prog4 = get_prog(3)

    # --- Recent ---
    recent_courses = current_courses.order_by('-id')[:5]

    context = {
        'total_programs': total_programs,
        'total_courses': total_courses,
        'total_subjects': total_subjects,

        'ug_courses': ug_courses,
        'pg_courses': pg_courses,

        'arts_courses': arts_courses,
        'science_courses': science_courses,

        'core_courses': core_courses,
        'elective_courses': elective_courses,
        'lab_courses': lab_courses,

        'total_credits': total_credits,
        'sem1_credits': float(sem1_credits),
        'sem2_credits': float(sem2_credits),
        'sem3_credits': float(sem3_credits),
        'sem4_credits': float(sem4_credits),
        'avg_credits': avg_credits,

        'cia_percent': cia_percent,
        'ese_percent': ese_percent,

        # Dynamic program distribution instead of hardcoded CSE/ECE/ME/CE
        'prog1_code': prog1['prog_code'],
        'prog1_count': prog1['count'],
        'prog2_code': prog2['prog_code'],
        'prog2_count': prog2['count'],
        'prog3_code': prog3['prog_code'],
        'prog3_count': prog3['count'],
        'prog4_code': prog4['prog_code'],
        'prog4_count': prog4['count'],

        'recent_courses': recent_courses,
    }

    return render(request, 'dashboard.html', context)