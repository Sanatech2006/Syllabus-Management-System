"""
Run this with: python fix_program_table.py
Place this file in: SMS/Syllabus-Management-System/
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_project.settings')
django.setup()

from django.db import connection

sql = """
CREATE TABLE IF NOT EXISTS "program" (
    "id" SERIAL PRIMARY KEY,
    "year" VARCHAR(20) NOT NULL,
    "prog_type" VARCHAR(5) NOT NULL,
    "prog_category" VARCHAR(10) NOT NULL,
    "prog_code" VARCHAR(20) NOT NULL,
    "branch" VARCHAR(100) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE ("year", "prog_type", "prog_category", "prog_code", "branch")
);
"""

with connection.cursor() as cursor:
    cursor.execute(sql)

print("SUCCESS: 'program' table created in PostgreSQL.")

# Also fix the migration record so Django thinks it's applied
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

recorder = MigrationRecorder(connection)
if not recorder.migration_qs.filter(app='program_manage', name='0001_initial').exists():
    recorder.record_applied('program_manage', '0001_initial')
    print("SUCCESS: Migration record fixed.")
else:
    print("INFO: Migration record already exists.")