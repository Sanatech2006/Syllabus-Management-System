from django.contrib import admin
from django.urls import path, include
from modules.upload_center import views
from django.conf import settings
from django.conf.urls.static import static
from modules.program_manage.views import login_page, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_page, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', include('modules.dashboard.urls')), 
    path('courses/', include('modules.course_manage.urls')), 
    path('programs/', include('modules.program_manage.urls')),
    path('uploads/', include('modules.upload_center.urls')),
    path('users/', include('modules.user_manage.urls')), 
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

