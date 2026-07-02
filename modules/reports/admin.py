from django.contrib import admin

from .models import CourseVerification


@admin.register(CourseVerification)
class CourseVerificationAdmin(admin.ModelAdmin):
    list_display = ("course", "verifier", "status", "is_verified", "finished_at", "updated_at")
    list_filter = ("status", "is_verified", "verifier")
    search_fields = ("course__course_code", "course__course_title", "verifier__username")
