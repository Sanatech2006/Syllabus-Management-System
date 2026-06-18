from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from modules.program_manage.models import Program
from modules.course_management.models import CourseStructure, CourseSyllabus


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
