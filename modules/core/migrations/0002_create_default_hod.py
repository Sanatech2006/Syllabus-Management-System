from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_hod(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    if not User.objects.filter(username='hod').exists():
        User.objects.create(
            username='hod',
            password=make_password('hodjmc'),
            email='hod@jmc.edu',
            first_name='HOD',
            last_name='JMC',
            is_staff=True,
            is_superuser=False,
            is_active=True,
        )


def delete_default_hod(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='hod').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_create_default_admin'),
    ]

    operations = [
        migrations.RunPython(create_default_hod, delete_default_hod),
    ]
