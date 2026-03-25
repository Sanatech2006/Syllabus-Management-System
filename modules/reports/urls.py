app_name = "reports"
from django.urls import path
from .views import work_progress_report

urlpatterns = [
    path('work-progress/', work_progress_report, name='work_progress_report'),
]