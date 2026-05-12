import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from modules.program_manage.models import Program

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
        user = get_user_model().objects.create_user(
            username="tester",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(user)

    def _create_program(self, **overrides):
        data = {
            "prog_type": "UG",
            "prog_category": "Arts",
            "degree": "B.A English",
            "branch": "English",
            "prog_code": "BAENG",
        }
        data.update(overrides)
        return Program.objects.create(**data)

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
        self._create_program()
        CourseStr.objects.create(course_code="23PEN2CC5", course_title="Existing")

        response = self.client.post(
            reverse("upload_center:add_course"),
            {
                "course_code": "23 pen2cc5",
                "course_title": "Duplicate",
                "prog_code": "BAENG",
                "prog_type": "UG",
                "prog_category": "Arts",
                "degree": "B.A English",
                "branch": "English",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CourseStr.objects.filter(course_code="23PEN2CC5").count(), 1)
        messages = list(response.context["messages"])
        self.assertTrue(any("already exists" in str(message) for message in messages))

    def test_add_course_rejects_when_program_is_missing(self):
        response = self.client.post(
            reverse("upload_center:add_course"),
            {
                "course_code": "24ENG101",
                "course_title": "Poetry",
                "prog_type": "UG",
                "prog_category": "Arts",
                "degree": "B.A English",
                "branch": "English",
                "prog_code": "BAENG",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CourseStr.objects.filter(course_code="24ENG101").exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("does not exist in Program Management" in str(message) for message in messages))

    def test_add_course_allows_when_program_exists(self):
        self._create_program()

        response = self.client.post(
            reverse("upload_center:add_course"),
            {
                "course_code": "24ENG101",
                "course_title": "Poetry",
                "prog_type": "UG",
                "prog_category": "Arts",
                "degree": "B.A English",
                "branch": "English",
                "prog_code": "BAENG",
            },
        )

        self.assertRedirects(response, reverse("upload_center:upload_center"))
        course = CourseStr.objects.get(course_code="24ENG101")
        self.assertEqual(course.degree, "B.A English")

    def test_upload_center_does_not_show_replace_pdf_button(self):
        CourseStr.objects.create(course_code="11UBA1401", course_title="Test Course")
        CourseContent.objects.create(
            course_code="11UBA1401",
            pdf=SimpleUploadedFile("syllabus.pdf", b"%PDF-file", content_type="application/pdf"),
        )

        response = self.client.get(reverse("upload_center:upload_center"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Replace PDF")

    def test_upload_center_filters_by_selected_year(self):
        CourseStr.objects.create(
            year="2022",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            course_code="22ENG101",
            part="I",
            course_category="Core",
            course_title="Poetry",
        )
        CourseStr.objects.create(
            year="2023",
            prog_type="PG",
            prog_category="Science",
            prog_code="MSCHEM",
            branch="Chemistry",
            sem="II",
            course_code="23CHE501",
            part="II",
            course_category="Elective",
            course_title="Organic Chemistry",
        )

        response = self.client.get(reverse("upload_center:upload_center"), {"year": "2022"})

        self.assertEqual(response.status_code, 200)
        courses = list(response.context["courses"])
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].course_code, "22ENG101")

    def test_get_filter_options_limits_related_upload_filters_by_year(self):
        CourseStr.objects.create(
            year="2022",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            course_code="22ENG101",
            part="I",
            course_category="Core",
            course_title="Poetry",
            hrs_per_week=3,
            credit=4,
            marks_cia=25,
            marks_ese=75,
            total_marks=100,
        )
        CourseStr.objects.create(
            year="2022",
            prog_type="PG",
            prog_category="Science",
            prog_code="MSCHEM",
            branch="Chemistry",
            sem="II",
            course_code="22CHE501",
            part="II",
            course_category="Elective",
            course_title="Organic Chemistry",
            hrs_per_week=5,
            credit=3,
            marks_cia=40,
            marks_ese=60,
            total_marks=100,
        )
        CourseStr.objects.create(
            year="2023",
            prog_type="UG",
            prog_category="Science",
            prog_code="BSCPHY",
            branch="Physics",
            sem="III",
            course_code="23PHY201",
            part="III",
            course_category="Core",
            course_title="Mechanics",
            hrs_per_week=6,
            credit=5,
            marks_cia=50,
            marks_ese=50,
            total_marks=100,
        )

        response = self.client.get(reverse("upload_center:get_filter_options"), {"year": "2022"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["prog_types"], ["PG", "UG"])
        self.assertEqual(data["prog_codes"], ["BAENG", "MSCHEM"])
        self.assertEqual(data["branches"], ["Chemistry", "English"])
        self.assertEqual(data["course_codes"], ["22CHE501", "22ENG101"])
        self.assertEqual(data["hrs_per_week_options"], ["3", "5"])

    def test_edit_course_prefills_existing_data(self):
        course = CourseStr.objects.create(
            year="2022",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            course_code="22ENG101",
            part="I",
            course_category="Core",
            course_title="Poetry",
        )

        response = self.client.get(reverse("upload_center:edit_course", args=[course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="22ENG101"')
        self.assertContains(response, 'value="Poetry"')
        self.assertContains(response, "Update Course")

    def test_edit_course_updates_record_and_resets_status(self):
        self._create_program()
        self._create_program(
            prog_type="PG",
            prog_category="Science",
            degree="M.Sc Chemistry",
            branch="Chemistry",
            prog_code="MSCHEM",
        )
        course = CourseStr.objects.create(
            year="2022",
            prog_type="UG",
            prog_category="Arts",
            prog_code="BAENG",
            branch="English",
            sem="I",
            course_code="22ENG101",
            part="I",
            course_category="Core",
            course_title="Poetry",
            is_saved=True,
            is_finalized=True,
        )
        CourseContent.objects.create(course_code="22ENG101")

        response = self.client.post(
            reverse("upload_center:edit_course", args=[course.id]),
            {
                "prog_type": "PG",
                "prog_category": "Science",
                "degree": "M.Sc Chemistry",
                "prog_code": "MSCHEM",
                "branch": "Chemistry",
                "sem": "II",
                "course_code": "22CHE501",
                "part": "II",
                "course_category": "Elective",
                "course_title": "Organic Chemistry",
                "hrs_per_week": "5",
                "credit": "3",
                "marks_cia": "40",
                "marks_ese": "60",
                "total_marks": "100",
            },
        )

        self.assertRedirects(response, reverse("upload_center:upload_center"))
        course.refresh_from_db()
        self.assertEqual(course.course_code, "22CHE501")
        self.assertEqual(course.prog_type, "PG")
        self.assertEqual(course.degree, "M.Sc Chemistry")
        self.assertFalse(course.is_saved)
        self.assertFalse(course.is_finalized)
        self.assertTrue(CourseContent.objects.filter(course_code="22CHE501").exists())
