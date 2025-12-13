from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('modules.course_manage.urls')),
    path('', include('modules.upload_center.urls')),
]
