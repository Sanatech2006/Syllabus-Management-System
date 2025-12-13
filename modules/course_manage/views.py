from django.shortcuts import render

def home(request):
    return render(request, 'menus.html') 

def course_management(request):
    return render(request, 'cou_manage.html')

