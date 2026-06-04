from django.db import models
from django.db.models import Q
from django.conf import settings

# =========================
# COURSE STRUCTURE
# =========================

class CourseStructure(models.Model):

    # 📌 COURSE IDENTIFIER (FIRST)
    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=200, blank=True, null=True)

    # 📌 PROGRAM LINK
    program = models.ForeignKey(
        'program_manage.Program',
        on_delete=models.CASCADE,
        related_name="courses"
    )

    # 📌 ACADEMIC DETAILS
    year = models.CharField(max_length=10, blank=True, null=True)
    sem = models.CharField(max_length=10, blank=True, null=True)

    # 📌 COURSE INFO
    course_category = models.CharField(max_length=20, blank=True, null=True)
    part = models.CharField(max_length=10, blank=True, null=True)

    hrs_per_week = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    credit = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    # 📌 MARKS
    marks_cia = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    marks_ese = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    # 📌 STATUS
    is_saved = models.BooleanField(default=False)
    is_finalized = models.BooleanField(default=False)

    # 📌 TIMESTAMP
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_structure"
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["program", "course_code"],
                name="unique_program_course"
            )
        ]

    def __str__(self):
        return f"{self.course_code} - {self.course_title}"


# =========================
# COURSE SYLLABUS
# =========================

class CourseSyllabus(models.Model):

    # 📌 COURSE IDENTIFIER (FIRST)
    course_code = models.CharField(max_length=20, unique=True)

    # 📌 CONTENT
    course_content = models.TextField(blank=True, null=True)

    # 📌 PDF FILE
    pdf = models.FileField(
        upload_to="course_pdfs/",
        blank=True,
        null=True
    )

    # 📌 TIMESTAMP
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_syllabus"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course_code} - Syllabus"