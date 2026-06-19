from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course_management", "0002_alter_coursestructure_course_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coursestructure",
            name="credit",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
