from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser

urlpatterns = [
    path('', include('modules.core.urls', namespace='core')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('modules.dashboard.urls', namespace='dashboard')),
    path('programs/', include('modules.program_manage.urls', namespace='program_manage')),
    path('users/', include('modules.user_manage.urls', namespace='user_manage')),
    path('hod-management/', include('modules.hod_management.urls')),
    path('course-management/', include('modules.course_management.urls', namespace='course_management')),
    path('view-syllabus/', include('modules.view_syllabus.urls', namespace='view_syllabus')), 
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
