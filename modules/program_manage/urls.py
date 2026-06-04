from django.urls import path
from . import views

app_name = 'program_manage'

urlpatterns = [
    
    # Main page
    path('', views.program_management, name='program_management'),
    
    # AJAX endpoints
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    path('get-program/<int:program_id>/', views.get_program, name='get_program'),
    path('add/', views.add_program, name='add_program'),
    path('edit/<int:program_id>/', views.edit_program, name='edit_program'),
    path('delete/<int:program_id>/', views.delete_program, name='delete_program'),
    
    # Excel operations
    path('download-sample/', views.download_sample_excel, name='download_sample'),
    path('download-programs/', views.download_programs_excel, name='download_programs'),
    path('upload-programs/', views.upload_programs_excel, name='upload_programs'),
]