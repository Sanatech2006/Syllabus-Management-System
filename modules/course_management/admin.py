from django.contrib import admin
from .models import CourseStructure, CourseSyllabus

@admin.register(CourseStructure)
class CourseStructureAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_title', 'program', 'year', 'sem', 'credit']
    list_filter = ['program', 'year', 'sem', 'course_category']
    search_fields = ['course_code', 'course_title', 'program__prog_code']
    raw_id_fields = ['program']

@admin.register(CourseSyllabus)
class CourseSyllabusAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'created_at', 'updated_at']
    search_fields = ['course_code']