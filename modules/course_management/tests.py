import io

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from modules.program_manage.models import Program
from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap


class CourseManagementSyllabusTests(TestCase):
    def setUp(self):
        # Create admin user and force login
        self.user = get_user_model().objects.create_user(
            username="admin_tester",
            password="secretpassword",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(self.user)

        # Create a test program
        self.program = Program.objects.create(
            degree="B.Sc Computer Science",
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCCS",
            branch="Computer Science"
        )
        self.program2 = Program.objects.create(
            degree="M.Sc Computer Science",
            prog_type="PG",
            prog_category="Science",
            prog_code="MSCCS",
            branch="Computer Science"
        )

    def test_add_course_creates_syllabus_record(self):
        """Test that adding a course automatically creates a CourseSyllabus record."""
        url = reverse("course_management:add_course")
        data = {
            "program_id": self.program.id,
            "course_code": "CS101",
            "course_title": "Introduction to CS",
            "year": "I",
            "sem": "I",
            "course_category": "Core",
            "part": "III",
            "hrs_per_week": "4",
            "credit": "4",
            "marks_cia": "25",
            "marks_ese": "75",
            "total_marks": "100",
        }

        # Verify no syllabus exists initially
        self.assertFalse(CourseSyllabus.objects.filter(course_code="CS101").exists())

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Verify syllabus record is created simultaneously
        self.assertTrue(CourseSyllabus.objects.filter(course_code="CS101").exists())
        syllabus = CourseSyllabus.objects.get(course_code="CS101")
        self.assertFalse(syllabus.pdf)

    def test_edit_course_code_syncs_syllabus_record(self):
        """Test that updating a course's code updates the syllabus record code."""
        # Create course and corresponding syllabus
        course = CourseStructure.objects.create(
            program=self.program,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        CourseSyllabus.objects.create(course_code="CS101")

        url = reverse("course_management:edit_course", args=[course.id])
        data = {
            "program_id": self.program.id,
            "course_code": "CS102",  # Updated course code
            "course_title": "Introduction to CS (Revised)",
            "year": "I",
            "sem": "I",
            "course_category": "Core",
            "part": "III",
            "hrs_per_week": "4",
            "credit": "4",
            "marks_cia": "25",
            "marks_ese": "75",
            "total_marks": "100",
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Verify new syllabus record is created/updated and old one is gone
        self.assertTrue(CourseSyllabus.objects.filter(course_code="CS102").exists())
        self.assertFalse(CourseSyllabus.objects.filter(course_code="CS101").exists())

    def test_edit_course_code_with_shared_code(self):
        """Test that renaming a course code does not remove syllabus if another course still uses old code."""
        # Two courses sharing the same code in different programs
        course1 = CourseStructure.objects.create(
            program=self.program,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        course2 = CourseStructure.objects.create(
            program=self.program2,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        CourseSyllabus.objects.create(course_code="CS101")

        # Edit course1's code to CS102
        url = reverse("course_management:edit_course", args=[course1.id])
        data = {
            "program_id": self.program.id,
            "course_code": "CS102",
            "course_title": "Introduction to CS",
            "year": "I",
            "sem": "I",
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # CS101 should still have its syllabus record because course2 still uses CS101
        self.assertTrue(CourseSyllabus.objects.filter(course_code="CS101").exists())
        # CS102 should also have its syllabus record
        self.assertTrue(CourseSyllabus.objects.filter(course_code="CS102").exists())

    def test_delete_course_cleans_up_syllabus_record(self):
        """Test that deleting the last course with a code deletes the syllabus record."""
        course = CourseStructure.objects.create(
            program=self.program,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        CourseSyllabus.objects.create(course_code="CS101")

        url = reverse("course_management:delete_course", args=[course.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Syllabus should be deleted because no other course uses CS101
        self.assertFalse(CourseSyllabus.objects.filter(course_code="CS101").exists())

    def test_delete_course_with_shared_code(self):
        """Test that deleting a course does not delete syllabus if another course still uses that code."""
        course1 = CourseStructure.objects.create(
            program=self.program,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        course2 = CourseStructure.objects.create(
            program=self.program2,
            course_code="CS101",
            course_title="Introduction to CS",
            year="I",
            sem="I"
        )
        CourseSyllabus.objects.create(course_code="CS101")

        url = reverse("course_management:delete_course", args=[course1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # CS101 syllabus should still exist since course2 still exists
        self.assertTrue(CourseSyllabus.objects.filter(course_code="CS101").exists())

    def test_upload_courses_excel_accepts_hyphen_numeric_placeholders(self):
        """Hyphen placeholders in optional numeric columns should import as blanks."""
        excel_buffer = io.BytesIO()
        pd.DataFrame(
            [
                {
                    "program_code": "BSCCS",
                    "course_code": "CS201",
                    "course_title": "Data Structures",
                    "year": "II",
                    "sem": "III",
                    "course_category": "Core",
                    "part": "III",
                    "hrs_per_week": "-",
                    "credit": "--",
                    "marks_cia": "-",
                    "marks_ese": "--",
                    "total_marks": "-",
                }
            ]
        ).to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        upload = SimpleUploadedFile(
            "courses.xlsx",
            excel_buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.post(reverse("course_management:upload_courses"), {"excel_file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        course = CourseStructure.objects.get(program=self.program, course_code="CS201")
        self.assertIsNone(course.hrs_per_week)
        self.assertIsNone(course.credit)
        self.assertIsNone(course.marks_cia)
        self.assertIsNone(course.marks_ese)
        self.assertIsNone(course.total_marks)


class HodScopedCourseManagementTests(TestCase):
    def setUp(self):
        self.hod_user = get_user_model().objects.create_user(
            username="hod_math",
            password="secretpassword",
            is_staff=True,
            is_superuser=False,
        )
        self.math_program = Program.objects.create(
            degree="B.Sc Mathematics",
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCMATH",
            branch="Mathematics"
        )
        self.physics_program = Program.objects.create(
            degree="B.Sc Physics",
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCPHY",
            branch="Physics"
        )
        HodProgramMap.objects.create(user=self.hod_user, program=self.math_program)
        self.math_course = CourseStructure.objects.create(
            program=self.math_program,
            course_code="MATH101",
            course_title="Algebra",
            year="I",
            sem="I",
        )
        self.physics_course = CourseStructure.objects.create(
            program=self.physics_program,
            course_code="PHYS101",
            course_title="Mechanics",
            year="I",
            sem="I",
        )
        self.client.force_login(self.hod_user)

    def test_hod_course_management_shows_only_assigned_programs(self):
        response = self.client.get(reverse("course_management:course_management"))

        self.assertEqual(response.status_code, 200)
        returned_codes = [course.course_code for course in response.context["courses"].object_list]
        self.assertIn("MATH101", returned_codes)
        self.assertNotIn("PHYS101", returned_codes)

        returned_program_codes = list(response.context["programs"].values_list("prog_code", flat=True))
        self.assertEqual(returned_program_codes, ["BSCMATH"])

    def test_hod_cannot_access_course_outside_assigned_program(self):
        response = self.client.get(reverse("course_management:get_course", args=[self.physics_course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])

    def test_hod_cannot_add_course_to_unassigned_program(self):
        response = self.client.post(
            reverse("course_management:add_course"),
            {
                "program_id": self.physics_program.id,
                "course_code": "PHYS102",
                "course_title": "Waves",
                "year": "I",
                "sem": "II",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
