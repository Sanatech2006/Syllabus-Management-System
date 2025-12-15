from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import CourseStr, CourseContent

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


@csrf_exempt
@require_http_methods(["POST"])
def upload_course_content(request):
    try:
        data = json.loads(request.body)
        course_code = data.get('course_code')
        file_content = data.get('file_content', '')
        
        if not course_code:
            return JsonResponse({'error': 'Missing course_code'}, status=400)
        
        # CLEAN NUL CHARACTERS - FIXES POSTGRES ERROR
        clean_content = file_content.replace('\x00', '').replace('\0', '')
        
        # Save or update course content
        content_obj, created = CourseContent.objects.update_or_create(
            course_code=course_code,
            defaults={'course_content': clean_content}
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Content {"saved" if created else "updated"} for {course_code}',
            'course_code': course_code
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Your existing views...
