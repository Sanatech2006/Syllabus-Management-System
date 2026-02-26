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
        ('Aided', 'Aided'),
        ('SFM', 'SFM'),
        ('SFW', 'SFW'),
    ]

    SEM_CHOICES = [
        ('I', 'I'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
        ('V', 'V'),
        ('VI', 'VI'),
    ]

    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    prog_type = models.CharField(max_length=5, choices=PROG_TYPE_CHOICES)
    prog_category = models.CharField(max_length=10, choices=PROG_CATEGORY_CHOICES)
    branch = models.CharField(max_length=100)
    semester = models.CharField(max_length=5, choices=SEM_CHOICES)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program_master'
        unique_together = (
            'year',
            'prog_type',
            'prog_category',
            'branch',
            'semester',
        )

    def __str__(self):
        return f"{self.branch} - {self.semester} ({self.year})"
