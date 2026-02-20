from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('course-management/', views.course_management, name='course_management'),
    path('view_course_pdf/<str:course_code>/', views.view_course_pdf, name='view_course_pdf'),
    path('pdf-debug/<str:course_code>/', views.debug_pdf_path, name='debug_pdf_path'),
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
]
