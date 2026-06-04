from django.urls import path
from . import views

app_name = 'course_manage'

urlpatterns = [
    path('', views.home, name='home'),
    path('course-management/', views.course_management, name='course_management'),
    path('view_course_pdf/<str:course_code>/', views.view_course_pdf, name='view_course_pdf'),
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('add-course/', views.add_course, name='add_course'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('get-program-details/', views.get_program_details, name='get_program_details'),
    path('get-branches/', views.get_branches, name='get_branches'),
]