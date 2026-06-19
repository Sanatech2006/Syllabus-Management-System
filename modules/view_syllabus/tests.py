from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program


class ViewSyllabusScopeTests(TestCase):
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
            branch="Mathematics",
        )
        self.physics_program = Program.objects.create(
            degree="B.Sc Physics",
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCPHY",
            branch="Physics",
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
        CourseSyllabus.objects.create(
            course_code="MATH101",
            pdf=SimpleUploadedFile("math101.pdf", b"%PDF-1.4 math syllabus", content_type="application/pdf"),
        )
        CourseSyllabus.objects.create(course_code="PHYS101")
        self.client.force_login(self.hod_user)

    def test_hod_only_sees_assigned_program_courses_in_syllabus_view(self):
        response = self.client.get(
            reverse("view_syllabus:view_syllabus"),
            {
                "program": self.math_program.id,
                "year": "I",
                "sem": "I",
                "view_mode": "structure",
            },
        )

        self.assertEqual(response.status_code, 200)
        returned_codes = [course.course_code for course in response.context["courses"]]
        self.assertIn("MATH101", returned_codes)
        self.assertNotIn("PHYS101", returned_codes)
