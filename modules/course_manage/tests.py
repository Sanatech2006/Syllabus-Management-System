import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from modules.program_manage.models import Program
from modules.upload_center.models import CourseContent, CourseStr


class CourseManageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.client.force_login(user)

    def test_view_course_pdf_serves_current_pdf_inline(self):
        pdf_file = SimpleUploadedFile("syllabus.pdf", b"%PDF-inline", content_type="application/pdf")
        CourseContent.objects.create(course_code="11UBA1401", pdf=pdf_file)

        response = self.client.get(reverse("course_manage:view_course_pdf", args=["11uba1401"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline;", response["Content-Disposition"])

    def test_get_filter_options_limits_related_course_filters_by_degree(self):
        Program.objects.create(degree="B.A English", prog_type="UG", prog_category="Arts", prog_code="BAENG", branch="English")
        Program.objects.create(degree="B.A English", prog_type="PG", prog_category="Science", prog_code="MSCHEM", branch="Chemistry")
        Program.objects.create(degree="B.Sc Physics", prog_type="UG", prog_category="Science", prog_code="BSCPHY", branch="Physics")

        CourseStr.objects.create(
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            part="I",
            course_code="22ENG101",
            course_category="Core",
            course_title="Poetry",
            is_finalized=True,
        )
        CourseStr.objects.create(
            prog_type="PG",
            prog_category="Science",
            prog_code="MSCHEM",
            branch="Chemistry",
            sem="I",
            part="I",
            course_code="22CHE501",
            course_category="Elective",
            course_title="Organic Chemistry",
            is_finalized=True,
        )
        CourseStr.objects.create(
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCPHY",
            branch="Physics",
            sem="II",
            part="II",
            course_code="23PHY201",
            course_category="Core",
            course_title="Mechanics",
            is_finalized=True,
        )

        response = self.client.get(reverse("course_manage:get_filter_options"), {"degree": "B.A English"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["prog_types"], ["PG", "UG"])
        self.assertEqual(data["prog_codes"], ["BAENG", "MSCHEM"])
        self.assertEqual(data["branches"], ["Chemistry", "English"])
        self.assertEqual(data["degrees"], ["B.A English", "B.Sc Physics"])

    def test_course_management_shows_degree_from_program_management(self):
        Program.objects.create(
            degree="B.A English",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
        )
        CourseStr.objects.create(
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            part="I",
            course_code="24ENG101",
            course_category="Core",
            course_title="Poetry",
            is_finalized=True,
        )

        response = self.client.get(reverse("course_manage:course_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "B.A English")

    def test_course_management_disables_view_button_when_pdf_is_missing(self):
        CourseStr.objects.create(
            year="2024",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            part="I",
            course_code="24ENG101",
            course_category="Core",
            course_title="Poetry",
            is_finalized=True,
        )

        response = self.client.get(reverse("course_manage:course_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'title="PDF not available"')
        self.assertContains(response, "disabled")

    def test_course_management_keeps_view_button_active_when_pdf_exists(self):
        CourseStr.objects.create(
            year="2024",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            part="I",
            course_code="24ENG102",
            course_category="Core",
            course_title="Drama",
            is_finalized=True,
        )
        CourseContent.objects.create(
            course_code="24ENG102",
            pdf=SimpleUploadedFile("syllabus.pdf", b"%PDF-active", content_type="application/pdf"),
        )

        response = self.client.get(reverse("course_manage:course_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "onclick=\"viewPDF('24ENG102')\"")
