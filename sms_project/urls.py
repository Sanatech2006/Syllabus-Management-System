from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('modules.core.urls', namespace='core')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('modules.dashboard.urls')),
    path('courses/', include('modules.course_manage.urls', namespace='course_manage')),
    path('programs/', include('modules.program_manage.urls', namespace='program_manage')),
    path('uploads/', include('modules.upload_center.urls', namespace='upload_center')),
    path('users/', include('modules.user_manage.urls', namespace='user_manage')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)