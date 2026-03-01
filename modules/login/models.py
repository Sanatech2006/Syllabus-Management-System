from django.db import models
from django.conf import settings


class UserRole(models.Model):

    ADMIN = 1
    HOD = 2

    ROLE_CHOICES = (
        (ADMIN, "Admin"),
        (HOD, "HOD"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_profile"
    )

    role = models.IntegerField(choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"