from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from modules.core.roles import VERIFIER_GROUP_NAME, get_user_role_labels
from modules.program_manage.models import Program
from modules.verification_management.models import VerifierProgramMap


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
            prog_code="FIRST",
            degree="B.Sc",
            branch="Computer Science",
            prog_type="UG",
            prog_category="Science",
            is_active=True,
        )
        Program.objects.create(
            prog_code="SECOND",
            degree="M.Sc",
            branch="Mathematics",
            prog_type="PG",
            prog_category="Science",
            is_active=True,
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("verification_management:verification_management"),
            {"search": "SECOND", "per_page": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0]["prog_code"], "SECOND")

    def test_add_mapping_grants_verifier_role_without_replacing_hod(self):
        verifier_group = Group.objects.create(name=VERIFIER_GROUP_NAME)
        hod_user = User.objects.create_user(
            username="hod_user",
            password="password123",
            is_staff=True,
        )
        program = Program.objects.create(
            prog_code="MBA",
            degree="MBA",
            branch="Management",
            prog_type="PG",
            prog_category="Arts",
            is_active=True,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("verification_management:add_mapping"),
            {
                "user_id": hod_user.id,
                "program_ids": [program.id],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        hod_user.refresh_from_db()
        self.assertTrue(hod_user.is_staff)
        self.assertTrue(hod_user.groups.filter(name=VERIFIER_GROUP_NAME).exists())
        self.assertEqual(get_user_role_labels(hod_user), ["Head of Department", "Verifier"])
        self.assertTrue(VerifierProgramMap.objects.filter(user=hod_user, program=program).exists())
