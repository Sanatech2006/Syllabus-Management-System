from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('course-management/', views.course_management, name='course_management'),
]
