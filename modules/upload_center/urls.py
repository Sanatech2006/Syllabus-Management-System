from django.urls import path
from . import views

urlpatterns = [
    path('upload-center/', views.upload_center, name='upload_center'),
    path('upload-center/add-course/', views.add_course, name='add_course'),
    path('upload-content/', views.upload_course_content, name='upload_course_content'),
    path('upload-pdf/', views.upload_course_content, name='upload_course_content'),


]
