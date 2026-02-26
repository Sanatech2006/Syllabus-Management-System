from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.program_management, name='program_management'),
    path('add/', views.add_program, name='add_program'),
    path('logout/', views.logout_view, name='logout'),



]
