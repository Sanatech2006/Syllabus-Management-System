import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from modules.upload_center.models import CourseStr
from modules.upload_center.models import CourseContent


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

    def test_get_filter_options_limits_related_course_filters_by_year(self):
        CourseStr.objects.create(
            year="2022",
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
            year="2022",
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
            year="2023",
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

        response = self.client.get(reverse("course_manage:get_filter_options"), {"year": "2022"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["prog_types"], ["PG", "UG"])
        self.assertEqual(data["prog_codes"], ["BAENG", "MSCHEM"])
        self.assertEqual(data["branches"], ["Chemistry", "English"])
