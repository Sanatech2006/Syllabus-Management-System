from django.db import models

class Program(models.Model):
    YEAR_CHOICES = [
        ('2023-2024', '2023-2024'),
        ('2024-2025', '2024-2025'),
    ]

    PROG_TYPE_CHOICES = [
        ('UG', 'UG'),
        ('PG', 'PG'),
    ]

    PROG_CATEGORY_CHOICES = [
        ('Arts', 'Arts'),
        ('Science', 'Science'),
    ]

    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    prog_type = models.CharField(max_length=5, choices=PROG_TYPE_CHOICES)
    prog_category = models.CharField(max_length=10, choices=PROG_CATEGORY_CHOICES)
    prog_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program'
        unique_together = (
            'year',
            'prog_type',
            'prog_category',
            'prog_code',
            'branch',
        )

    def __str__(self):
        return f"{self.branch} - {self.prog_code} ({self.year})"
