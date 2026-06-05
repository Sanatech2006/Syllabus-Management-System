from django.apps import AppConfig


class CourseManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.course_management'
    label = 'course_management'
    verbose_name = 'Course Management'