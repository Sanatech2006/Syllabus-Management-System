from django.db import models
from django.db.models import Q

from .storage import OverwriteStorage


def normalize_course_code(value):
    return (value or "").strip().upper().replace(" ", "")


class CourseStr(models.Model):
    prog_code = models.CharField(max_length=20, blank=True, null=True)
    branch = models.CharField(max_length=30, blank=True, null=True)     # Branch/Department
    year = models.CharField(max_length=10, blank=True, null=True)
    degree = models.CharField(max_length=50, blank=True, null=True)
    prog_type = models.CharField(max_length=5, blank=True, null=True)  # UG/PG
    prog_category=models.CharField(max_length=20, blank=True, null=True)  # Arts/Science.   
    sem = models.CharField(max_length=10, blank=True, null=True)       # Semester

    
    course_code = models.CharField(max_length=20, blank=True, null=True)  # Primary unique filter
    def get_content(self):
        return CourseContent.objects.filter(course_code=self.course_code).first()
    course_category = models.CharField(max_length=20, blank=True, null=True)
    part = models.CharField(max_length=10, blank=True, null=True)      # Part I/II/etc.
    course_title = models.CharField(max_length=200, blank=True, null=True)
    hrs_per_week = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    credit = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    marks_cia = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # Continuous Internal Assessment
    marks_ese = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # End Semester Exam
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    is_saved = models.BooleanField(default=False)
    is_finalized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_str'  # Exact table name
        verbose_name = 'Course Structure'
        verbose_name_plural = 'Course Structures'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['course_code'],
                condition=Q(course_code__isnull=False) & ~Q(course_code=''),
                name='unique_non_blank_course_code',
            ),
        ]

    def __str__(self):
        return f"{self.course_code} - {self.course_title}"
    
def course_pdf_upload_path(instance, filename):
    return f"course_pdfs/{normalize_course_code(instance.course_code)}.pdf"

class CourseContent(models.Model):
    course_code = models.CharField(max_length=20, blank=False, null=False)
    course_content = models.TextField(blank=True, null=True)
    
    pdf = models.FileField(
        upload_to=course_pdf_upload_path,
        storage=OverwriteStorage(),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_content'  # Exact table name
        verbose_name = 'Course Content'
        verbose_name_plural = 'Course Contents'
        ordering = ['-created_at']
        unique_together = ['course_code']  # One content per course code

    def __str__(self):
        return f"{self.course_code} - Course Content"

    def save(self, *args, **kwargs):
        self.course_code = normalize_course_code(self.course_code)
        super().save(*args, **kwargs)


def _normalize_course_str_code(sender, instance, **kwargs):
    instance.course_code = normalize_course_code(instance.course_code)


models.signals.pre_save.connect(_normalize_course_str_code, sender=CourseStr)
