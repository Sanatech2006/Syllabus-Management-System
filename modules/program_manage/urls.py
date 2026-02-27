from django.urls import path
from .views import login_page, logout_view, program_management, add_program

urlpatterns = [
    path('login/', login_page, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', program_management, name='program_management'),
    path('add/', add_program, name='add_program'),
]