from django.contrib import admin

from .models import VerifierProgramMap


@admin.register(VerifierProgramMap)
class VerifierProgramMapAdmin(admin.ModelAdmin):
    list_display = ("user", "program", "created_at", "updated_at")
    search_fields = ("user__username", "program__prog_code", "program__branch")
