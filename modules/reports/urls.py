from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.work_progress_report, name='work_progress_report'),
    path('download-excel/', views.download_work_progress_excel, name='download_work_progress_excel'),
    path('verification-report/', views.verification_report, name='verification_report'),
    path('verification-filter-options/', views.verification_filter_options, name='verification_filter_options'),
    path('verification-assignment-details/<int:verifier_id>/', views.verification_assignment_details, name='verification_assignment_details'),
    path('verification-sync-assignments/', views.verification_sync_assignments, name='verification_sync_assignments'),
    path('verification-delete-assignment/<int:course_id>/', views.verification_delete_assignment, name='verification_delete_assignment'),
    path("verification/report/filter-options/", views.verification_report_filter_options, name="verification_report_filter_options"),
    path("verification/report/download-excel/", views.download_verification_report_excel, name="download_verification_report_excel"),
]
