from django.urls import path
from . import views

urlpatterns = [
    path('upload-center/', views.upload_center, name='upload_center'),
    path('upload-center/add-course/', views.add_course, name='add_course'),
    path('upload-center/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('upload-center/upload-pdf/', views.upload_course_content, name='upload_course_content'),
    path('upload-center/finalize/', views.finalize_courses, name='finalize_courses'),
    path("upload-center/save/", views.save_courses, name="save_courses"),
]
