from django.db import models

class CourseStr(models.Model):
    prog_code = models.CharField(max_length=20, blank=True, null=True)
    year = models.CharField(max_length=10, blank=True, null=True)
    prog_type = models.CharField(max_length=5, blank=True, null=True)  # UG/PG
    sem = models.CharField(max_length=10, blank=True, null=True)       # Semester
    course_code = models.CharField(max_length=20, blank=True, null=True)
    part = models.CharField(max_length=10, blank=True, null=True)      # Part I/II/etc.
    course_category = models.CharField(max_length=20, blank=True, null=True)
    course_title = models.CharField(max_length=200, blank=True, null=True)
    hrs_per_week = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    credit = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    marks_cia = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # Continuous Internal Assessment
    marks_ese = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # End Semester Exam
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_str'  # Exact table name
        verbose_name = 'Course Structure'
        verbose_name_plural = 'Course Structures'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course_code} - {self.course_title}"
