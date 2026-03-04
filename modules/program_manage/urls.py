from django.urls import path
from . import views

app_name = 'program_manage'

urlpatterns = [
    path('', views.program_management, name='program_management'),
    path('add/', views.add_program, name='add_program'),
    path('edit/<int:id>/', views.edit_program, name='edit_program'),
    path('delete/<int:id>/', views.delete_program, name='delete_program'),
]