from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Only create if this username doesn't already exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('admin123'),
            email='admin@jmc.edu',
            first_name='Admin',
            last_name='JMC',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )


def delete_default_admin(apps, schema_editor):
    # Reverse migration — remove the user if rolling back
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='admin').delete()


class Migration(migrations.Migration):

    # This runs AFTER Django's auth migrations are done
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0001_initial') if False else None,
    ]

    # Remove None from dependencies
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, delete_default_admin),
    ]
