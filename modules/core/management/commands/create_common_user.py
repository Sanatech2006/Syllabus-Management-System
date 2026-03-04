import os 
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        username = os.environ.get('COMMON_USERNAME', 'admin')
        password = os.environ.get('COMMON_PASSWORD', 'admin123')
        email = os.environ.get('COMMON_EMAIL', 'admin@example.com')
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created common user: {username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )