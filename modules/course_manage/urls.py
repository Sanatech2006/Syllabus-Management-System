from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('course-management/', views.course_management, name='course_management'),
    path('pdf/<str:course_code>/', views.view_course_pdf, name='view_course_pdf'),
]
