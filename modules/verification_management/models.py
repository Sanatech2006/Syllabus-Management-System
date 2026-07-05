from django.db import models
from django.conf import settings

class VerifierProgramMap(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    program = models.ForeignKey(
        'program_manage.Program',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = "verifier_program_map"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "program"],
                name="unique_verifier_program"
            )
        ]
