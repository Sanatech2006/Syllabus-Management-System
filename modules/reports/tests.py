from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from modules.course_management.models import CourseStructure, CourseSyllabus
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program
from modules.core.roles import VERIFIER_GROUP_NAME
from modules.reports.models import CourseVerification
from modules.verification_management.models import VerifierProgramMap


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


class VerificationFlowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_verify",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.hod_user = User.objects.create_user(
            username="hod_verify",
            password="secret123",
            is_superuser=False,
            is_staff=True,
        )
        self.verifier_user = User.objects.create_user(
            username="verifier_verify",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )
        self.verifier_user.groups.add(Group.objects.create(name=VERIFIER_GROUP_NAME))
        self.program = Program.objects.create(
            prog_code="BSC",
            degree="B.Sc",
            branch="Computer Science",
            prog_type="UG",
            prog_category="Science",
        )
        self.other_program = Program.objects.create(
            prog_code="MCA",
            degree="MCA",
            branch="Computer Applications",
            prog_type="PG",
            prog_category="Science",
        )
        HodProgramMap.objects.create(user=self.hod_user, program=self.program)
        VerifierProgramMap.objects.create(user=self.verifier_user, program=self.program)
        self.course = CourseStructure.objects.create(
            program=self.program,
            course_code="CSC101",
            course_title="Programming Basics",
            year="I",
            sem="I",
            course_category="Core",
        )
        self.other_course = CourseStructure.objects.create(
            program=self.program,
            course_code="CSC102",
            course_title="Data Structures",
            year="I",
            sem="I",
            course_category="Core",
        )
        self.other_program_course = CourseStructure.objects.create(
            program=self.other_program,
            course_code="MCA101",
            course_title="MCA Foundations",
            year="I",
            sem="I",
            course_category="Core",
        )

    def test_verifier_verification_page_renders_checkbox(self):
        self.client.force_login(self.verifier_user)

        response = self.client.get(reverse("reports:verification_center"), {"year": "I"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="verified_courses"')

    def test_verifier_verification_page_shows_rows_without_filters(self):
        self.client.force_login(self.verifier_user)

        response = self.client.get(reverse("reports:verification_center"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programming Basics")
        self.assertNotContains(response, "MCA Foundations")
        self.assertContains(response, 'name="verified_courses"')

    def test_verifier_only_sees_mapped_program_courses(self):
        self.client.force_login(self.verifier_user)

        response = self.client.get(reverse("reports:verification_center"), {"year": "I"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programming Basics")
        self.assertNotContains(response, "MCA Foundations")

    def test_admin_verification_report_defaults_to_all_courses(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:verification_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BSC")
        self.assertContains(response, "MCA")
        self.assertContains(response, "Assigned")
        self.assertContains(response, "Not Assigned")

    def test_admin_verification_filter_options_include_course_choices(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:verification_filter_options"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("years", payload)
        self.assertIn("programs", payload)
        self.assertTrue(payload["years"])

    def test_admin_can_fetch_verifier_assignment_details(self):
        CourseVerification.objects.create(
            course=self.course,
            verifier=self.verifier_user,
            is_verified=False,
            status=CourseVerification.STATUS_DRAFT,
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("reports:verification_assignment_details", args=[self.verifier_user.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["verifier"]["id"], self.verifier_user.id)
        self.assertEqual(len(payload["courses"]), 1)
        self.assertEqual(payload["courses"][0]["code"], "CSC101")

    def test_admin_can_sync_verifier_assignments(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("reports:verification_sync_assignments"),
            {
                "verifier_id": self.verifier_user.id,
                "course_ids": [str(self.course.id), str(self.other_course.id)],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CourseVerification.objects.filter(course=self.course, verifier=self.verifier_user).exists())
        self.assertTrue(CourseVerification.objects.filter(course=self.other_course, verifier=self.verifier_user).exists())

    def test_save_and_finish_publishes_to_admin_report(self):
        self.client.force_login(self.verifier_user)

        response = self.client.post(
            reverse("reports:verification_center") + "?year=I",
            {
                "action": "finish",
                "verified_courses": [str(self.course.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        verification = CourseVerification.objects.get(course=self.course, verifier=self.verifier_user)
        self.assertTrue(verification.is_verified)
        self.assertEqual(verification.status, CourseVerification.STATUS_SUBMITTED)

        self.client.force_login(self.admin_user)
        report_response = self.client.get(reverse("reports:verification_report"), {"year": "I"})

        self.assertEqual(report_response.status_code, 200)
        self.assertContains(report_response, "BSC")
        self.assertContains(report_response, "Assigned")

    def test_save_only_updates_current_page_courses(self):
        CourseVerification.objects.create(
            course=self.other_course,
            verifier=self.hod_user,
            is_verified=True,
            status=CourseVerification.STATUS_SUBMITTED,
            finished_at=timezone.now(),
        )

        self.client.force_login(self.verifier_user)

        response = self.client.post(
            reverse("reports:verification_center") + "?year=I&per_page=1",
            {
                "action": "finish",
                "verified_courses": [str(self.course.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(CourseVerification.objects.filter(course=self.course, verifier=self.verifier_user).exists())
        self.assertFalse(CourseVerification.objects.filter(course=self.other_course, verifier=self.verifier_user).exists())

    def test_hod_can_open_verification_center(self):
        self.client.force_login(self.hod_user)

        response = self.client.get(reverse("reports:verification_center"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verification Report")
