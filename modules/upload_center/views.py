from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json, os
from .models import CourseStr, CourseContent
from django.conf import settings
from django.http import HttpResponseRedirect

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


def upload_course_content(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        course_code = request.POST.get('course_code')
        pdf_file = request.FILES['pdf_file']

        if not course_code:
            messages.error(request, 'Missing course code.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        # Build relative and absolute paths
        filename = f"{course_code}.pdf"
        relative_path = os.path.join('course_pdfs', filename)
        full_path = os.path.join(settings.BASE_DIR, 'static', relative_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        CourseContent.objects.update_or_create(
            course_code=course_code,
            defaults={'course_content': relative_path},
        )

        messages.success(request, f'PDF uploaded successfully for {course_code}.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    messages.error(request, 'No file uploaded.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
