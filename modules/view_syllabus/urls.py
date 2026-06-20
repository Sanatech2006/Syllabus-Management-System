from django.urls import path
from . import views

app_name = 'view_syllabus'

urlpatterns = [
    # Main view syllabus page
    path('', views.view_syllabus, name='view_syllabus'),
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    
    # Download syllabus
    path('view/<int:course_id>/', views.view_syllabus_pdf, name='view_syllabus_pdf'),
    path('download/<int:course_id>/', views.download_syllabus, name='download_syllabus'),
]
