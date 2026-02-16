from django.contrib import admin
from django.urls import path, include
from modules.upload_center import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('modules.course_manage.urls')),
    path('', include('modules.upload_center.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

