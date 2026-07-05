from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from modules.course_management.models import CourseStructure
from modules.program_manage.models import Program


User = get_user_model()


class VerificationManagementTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="password123",
            email="admin@example.com",
        )

    def test_verification_management_renders_report_filters(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("verification_management:verification_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verification Management")
        self.assertContains(response, "Program type")
        self.assertContains(response, "Program category")
        self.assertContains(response, "Degree")
        self.assertContains(response, "Branch")
        self.assertContains(response, "Program code")
        self.assertNotContains(response, "Syllabus Upload Status")
        self.assertNotContains(response, "Uploaded Syllabus")
        self.assertNotContains(response, "Not Uploaded Syllabus")
        self.assertNotContains(response, "Semester")

    def test_search_spans_all_pages(self):
        program = Program.objects.create(
            prog_code="BSCCS",
            degree="B.Sc",
            branch="Computer Science",
            prog_type="UG",
            prog_category="Science",
            is_active=True,
        )
        CourseStructure.objects.create(
            course_code="CS101",
            course_title="First Course",
            program=program,
            year="2024",
            sem="1",
        )
        CourseStructure.objects.create(
            course_code="CS102",
            course_title="Second Course",
            program=program,
            year="2024",
            sem="1",
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("verification_management:verification_management"),
            {"search": "Second Course", "per_page": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Second Course")
        self.assertNotContains(response, "First Course")
