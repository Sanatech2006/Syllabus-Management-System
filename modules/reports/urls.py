from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.work_progress_report, name='work_progress_report'),
]
