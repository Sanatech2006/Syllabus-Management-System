from django.conf import settings
from django.db import models


class CourseVerification(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
    )

    course = models.ForeignKey(
        "course_management.CourseStructure",
        on_delete=models.CASCADE,
        related_name="verification_records",
    )
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_records",
    )
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    finished_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_verification"
        ordering = ["-updated_at"]
        app_label = "reports"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "verifier"],
                name="unique_course_verifier_verification",
            )
        ]

    def __str__(self):
        return f"{self.course.course_code} verified by {self.verifier}"
