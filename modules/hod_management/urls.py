from django.urls import path
from . import views

app_name = 'hod_management'

urlpatterns = [
    # Main mapping views
    path('', views.hod_program_map_list, name='hod_program_map_list'),
    path('mappings/', views.hod_program_map_list, name='hod_program_map_list'),
    path('mappings/create/', views.hod_program_map_create, name='hod_program_map_create'),
    path('mappings/<int:pk>/edit/', views.hod_program_map_edit, name='hod_program_map_edit'),
    path('mappings/<int:pk>/delete/', views.hod_program_map_delete, name='hod_program_map_delete'),
    
    # API endpoints
    path('api/hod-programs/<int:user_id>/', views.get_hod_programs_api, name='get_hod_programs'),
]