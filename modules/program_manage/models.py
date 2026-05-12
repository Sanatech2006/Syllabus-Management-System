from django.db import models


def normalize_program_value(value):
    return (value or "").strip()


def normalize_program_code(value):
    return normalize_program_value(value).upper().replace(" ", "")


class Program(models.Model):

    PROG_TYPE_CHOICES = [
        ('UG', 'UG'),
        ('PG', 'PG'),
    ]

    PROG_CATEGORY_CHOICES = [
        ('Arts', 'Arts'),
        ('Science', 'Science'),
    ]

    degree = models.CharField(max_length=50)
    prog_type = models.CharField(max_length=5, choices=PROG_TYPE_CHOICES)
    prog_category = models.CharField(max_length=10, choices=PROG_CATEGORY_CHOICES)
    prog_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program'
        unique_together = (
            'prog_type',
            'prog_category',
            'degree',
            'branch',
            'prog_code',
        )

    def __str__(self):
        return f"{self.branch} - {self.prog_code} ({self.degree})"

    def save(self, *args, **kwargs):
        self.degree = normalize_program_value(self.degree)
        self.prog_type = normalize_program_value(self.prog_type).upper()
        self.prog_category = normalize_program_value(self.prog_category).title()
        self.branch = normalize_program_value(self.branch)
        self.prog_code = normalize_program_code(self.prog_code)
        super().save(*args, **kwargs)
