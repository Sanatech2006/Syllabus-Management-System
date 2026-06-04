from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import Trim, Lower
from modules.course_manage.models import CourseStructure  # Changed import

def dashboard(request):
    current_courses = CourseStructure.objects.filter(is_finalized=True)  # Changed from CourseStr

    total_programs = current_courses.values('program__prog_code').distinct().count()  # Changed to use ForeignKey
    total_courses = current_courses.count()
    total_subjects = total_courses

    # Now using program__prog_code through the ForeignKey relationship
    ug_courses = current_courses.filter(program__prog_type='UG').count()  # Changed logic
    pg_courses = current_courses.filter(program__prog_type='PG').count()  # Changed logic

    arts_courses = current_courses.filter(program__prog_category='Arts').count()  # Changed logic
    science_courses = current_courses.filter(program__prog_category='Science').count()  # Changed logic

    normalized_courses = current_courses.annotate(
        clean_cat=Lower(Trim('course_category')),
        clean_sem=Trim('sem')
    )

    core_courses = normalized_courses.filter(clean_cat='core').count()
    elective_courses = normalized_courses.filter(clean_cat='elective').count()
    lab_courses = normalized_courses.filter(clean_cat='lab').count()

    total_credits = current_courses.aggregate(total=Sum('credit'))['total'] or 0
    sem1_credits = normalized_courses.filter(clean_sem='I').aggregate(total=Sum('credit'))['total'] or 0
    sem2_credits = normalized_courses.filter(clean_sem='II').aggregate(total=Sum('credit'))['total'] or 0
    sem3_credits = normalized_courses.filter(clean_sem='III').aggregate(total=Sum('credit'))['total'] or 0
    sem4_credits = normalized_courses.filter(clean_sem='IV').aggregate(total=Sum('credit'))['total'] or 0

    semester_count = 4
    avg_credits = round(float(total_credits) / semester_count, 2) if total_credits else 0

    total_cia = current_courses.aggregate(total=Sum('marks_cia'))['total'] or 0
    total_ese = current_courses.aggregate(total=Sum('marks_ese'))['total'] or 0
    total_marks = total_cia + total_ese

    if total_marks:
        cia_percent = round((total_cia / total_marks) * 100)
        ese_percent = round((total_ese / total_marks) * 100)
    else:
        cia_percent = 0
        ese_percent = 0

    # Changed to use program__prog_code through ForeignKey
    program_dist = (
        current_courses
        .values('program__prog_code')  # Changed field name
        .annotate(count=Count('id'))
        .order_by('-count')[:4]
    )

    prog_list = list(program_dist)

    while len(prog_list) < 4:
        prog_list.append({'program__prog_code': '-', 'count': 0})  # Changed key name

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
        'prog1_code': prog_list[0]['program__prog_code'],  # Changed key name
        'prog1_count': prog_list[0]['count'],
        'prog2_code': prog_list[1]['program__prog_code'],  # Changed key name
        'prog2_count': prog_list[1]['count'],
        'prog3_code': prog_list[2]['program__prog_code'],  # Changed key name
        'prog3_count': prog_list[2]['count'],
        'prog4_code': prog_list[3]['program__prog_code'],  # Changed key name
        'prog4_count': prog_list[3]['count'],
        'recent_courses': recent_courses,
    }

    return render(request, 'dashboard.html', context)