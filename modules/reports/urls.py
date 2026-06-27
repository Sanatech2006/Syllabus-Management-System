from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.work_progress_report, name='work_progress_report'),
    path('download-excel/', views.download_work_progress_excel, name='download_work_progress_excel'),
]
