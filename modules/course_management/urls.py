from django.urls import path
from . import views

app_name = 'course_management'

urlpatterns = [
    
    # Main page
    path('', views.course_management, name='course_management'),
    
    # AJAX endpoints
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    path('get-course/<int:course_id>/', views.get_course, name='get_course'),
    path('add/', views.add_course, name='add_course'),
    path('edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete/<int:course_id>/', views.delete_course, name='delete_course'),
    
    # Excel operations
    path('download-sample/', views.download_sample_excel, name='download_sample'),
    path('download-courses/', views.download_courses_excel, name='download_courses'),
    path('upload-courses/', views.upload_courses_excel, name='upload_courses'),
    
    # Syllabus operations
    path('upload-syllabus/<int:course_id>/', views.upload_syllabus, name='upload_syllabus'),
    path('download-syllabus/<int:course_id>/', views.download_syllabus, name='download_syllabus'),
    path('delete-syllabus/<int:syllabus_id>/', views.delete_syllabus, name='delete_syllabus'),
]