from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

def upload_center(request):
    return render(request, 'upload_center.html')

def add_course(request):
    if request.method == 'POST':
        file = request.FILES.get('course_file')

        if file:
            # TODO: handle/save the file here
            messages.success(request, f'"{file.name}" uploaded successfully!')
        else:
            messages.error(request, 'No file selected.')

        return redirect('upload_center')

    return redirect('upload_center')
