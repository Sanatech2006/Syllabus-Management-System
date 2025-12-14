from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

def upload_center(request):
    # FETCH DATA FOR TABLE DISPLAY
    courses = CourseStr.objects.all().order_by('-created_at')[:20]
    return render(request, 'upload_center.html', {'courses': courses})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CourseStr

def add_course(request):
    if request.method == 'POST':
        # Helper function to safely convert to decimal or None
        def get_decimal(value):
            if value == '' or value is None:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        CourseStr.objects.create(
            prog_code=request.POST.get('prog_code', ''),
            year=request.POST.get('year', ''),
            prog_type=request.POST.get('prog_type', ''),
            sem=request.POST.get('sem', ''),
            course_code=request.POST.get('course_code', ''),
            part=request.POST.get('part', ''),
            course_category=request.POST.get('course_category', ''),
            course_title=request.POST.get('course_title', ''),
            hrs_per_week=get_decimal(request.POST.get('hrs_per_week')),
            credit=get_decimal(request.POST.get('credit')),
            marks_cia=get_decimal(request.POST.get('marks_cia')),
            marks_ese=get_decimal(request.POST.get('marks_ese')),
            total_marks=get_decimal(request.POST.get('total_marks')),
        )
        
        messages.success(request, 'Course structure saved successfully!')
        return redirect('upload_center')
    
    return redirect('upload_center')


