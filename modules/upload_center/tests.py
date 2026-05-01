import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CourseContent, CourseStr


class UploadCenterTests(TestCase):
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

    def test_reupload_overwrites_existing_pdf_without_renaming(self):
        CourseStr.objects.create(course_code="11 uba 1401", course_title="Test Course")

        first_pdf = SimpleUploadedFile("first.pdf", b"%PDF-first", content_type="application/pdf")
        second_pdf = SimpleUploadedFile("second.pdf", b"%PDF-second", content_type="application/pdf")

        self.client.post(
            reverse("upload_center:upload_course_content"),
            {"course_code": "11 uba 1401", "pdf_file": first_pdf},
        )
        self.client.post(
            reverse("upload_center:upload_course_content"),
            {"course_code": "11UBA1401", "pdf_file": second_pdf},
        )

        content = CourseContent.objects.get(course_code="11UBA1401")
        self.assertEqual(content.pdf.name, "course_pdfs/11UBA1401.pdf")

        with content.pdf.open("rb") as saved_pdf:
            self.assertEqual(saved_pdf.read(), b"%PDF-second")

    def test_delete_removes_pdf_and_content_for_course_code(self):
        course = CourseStr.objects.create(course_code="23PEN2CC8", course_title="One")
        pdf_file = SimpleUploadedFile("syllabus.pdf", b"%PDF-content", content_type="application/pdf")
        content = CourseContent.objects.create(course_code="23PEN2CC8", pdf=pdf_file)
        pdf_name = content.pdf.name

        self.client.post(reverse("upload_center:delete_course", args=[course.id]))
        self.assertFalse(CourseContent.objects.filter(course_code="23PEN2CC8").exists())
        self.assertFalse(content.pdf.storage.exists(pdf_name))

    def test_add_course_rejects_duplicate_course_code(self):
        CourseStr.objects.create(course_code="23PEN2CC5", course_title="Existing")

        response = self.client.post(
            reverse("upload_center:add_course"),
            {
                "course_code": "23 pen2cc5",
                "course_title": "Duplicate",
                "prog_code": "BAENG",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CourseStr.objects.filter(course_code="23PEN2CC5").count(), 1)
        messages = list(response.context["messages"])
        self.assertTrue(any("already exists" in str(message) for message in messages))

    def test_upload_center_does_not_show_replace_pdf_button(self):
        CourseStr.objects.create(course_code="11UBA1401", course_title="Test Course")
        CourseContent.objects.create(
            course_code="11UBA1401",
            pdf=SimpleUploadedFile("syllabus.pdf", b"%PDF-file", content_type="application/pdf"),
        )

        response = self.client.get(reverse("upload_center:upload_center"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Replace PDF")
