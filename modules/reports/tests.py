from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program


User = get_user_model()


class WorkProgressReportTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_report",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.hod_user = User.objects.create_user(
            username="hod_mca",
            password="secret123",
            is_superuser=False,
            is_staff=True,
        )
        self.mca_program = Program.objects.create(
            prog_code="MCA",
            degree="MCA",
            branch="Computer Applications",
            prog_type="PG",
            prog_category="Science",
        )
        self.bca_program = Program.objects.create(
            prog_code="BCA",
            degree="BCA",
            branch="Computer Applications",
            prog_type="UG",
            prog_category="Science",
        )
        HodProgramMap.objects.create(user=self.hod_user, program=self.mca_program)
        CourseStructure.objects.create(
            program=self.mca_program,
            course_code="MCA101",
            course_title="MCA Course",
            year="I",
            sem="I",
        )
        CourseStructure.objects.create(
            program=self.bca_program,
            course_code="BCA101",
            course_title="BCA Course",
            year="I",
            sem="I",
        )
        CourseSyllabus.objects.create(
            course_code="MCA101",
            pdf=SimpleUploadedFile("mca101.pdf", b"%PDF-1.4", content_type="application/pdf"),
        )

    def test_hod_report_is_limited_to_mapped_programs(self):
        self.client.force_login(self.hod_user)

        response = self.client.get(reverse("reports:work_progress_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MCA101")
        self.assertNotContains(response, "BCA101")

    def test_admin_report_can_filter_by_upload_status(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:work_progress_report"), {"status": "not_uploaded"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BCA101")
        self.assertNotContains(response, "MCA101")

    def test_admin_report_search_is_case_insensitive(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:work_progress_report"), {"search": "mca"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MCA101")
        self.assertNotContains(response, "BCA101")

    def test_hod_report_search_is_case_insensitive(self):
        self.client.force_login(self.hod_user)

        response = self.client.get(reverse("reports:work_progress_report"), {"search": "MCA"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MCA101")
        self.assertNotContains(response, "BCA101")

    def test_partial_report_search_renders_results_panel(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:work_progress_report"), {"search": "mca", "partial": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports_table_partial.html")
        self.assertContains(response, "MCA101")
        self.assertNotContains(response, "BCA101")

    def test_hod_can_download_scoped_report_excel(self):
        self.client.force_login(self.hod_user)

        response = self.client.get(reverse("reports:download_work_progress_excel"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
