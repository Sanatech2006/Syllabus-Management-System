from django.db import models

def normalize_program_value(value):
    return (value or "").strip()

def normalize_program_code(value):
    return normalize_program_value(value).upper().replace(" ", "")

class Program(models.Model):

    PROG_TYPE_CHOICES = [
        ("UG", "UG"),
        ("PG", "PG"),
    ]

    PROG_CATEGORY_CHOICES = [
        ("Arts", "Arts"),
        ("Science", "Science"),
    ]

    prog_code = models.CharField(
        max_length=20,
        unique=True
    )

    degree = models.CharField(max_length=50)
    branch = models.CharField(max_length=100)

    prog_type = models.CharField(
        max_length=5,
        choices=PROG_TYPE_CHOICES
    )

    prog_category = models.CharField(
        max_length=10,
        choices=PROG_CATEGORY_CHOICES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "program_master"
        ordering = ["prog_code"]

    def __str__(self):
        return f"{self.prog_code} - {self.branch}"