from django.urls import path
from . import views

app_name = 'view_syllabus'

urlpatterns = [
    # Main view syllabus page
    path('', views.view_syllabus, name='view_syllabus'),
    
    # Download syllabus
    path('download/<int:course_id>/', views.download_syllabus, name='download_syllabus'),
]