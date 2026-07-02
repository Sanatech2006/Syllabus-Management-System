from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.work_progress_report, name='work_progress_report'),
    path('download-excel/', views.download_work_progress_excel, name='download_work_progress_excel'),
    path('verification-center/', views.verification_center, name='verification_center'),
    path('verification-report/', views.verification_report, name='verification_report'),
    path('verification-filter-options/', views.verification_filter_options, name='verification_filter_options'),
]
