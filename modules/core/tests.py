from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from modules.core.roles import VERIFIER_GROUP_NAME


User = get_user_model()


class RoleAccessTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_test",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.hod_user = User.objects.create_user(
            username="hod_test",
            password="secret123",
            is_superuser=False,
            is_staff=True,
        )

    def test_hod_can_access_dashboard_and_course_management(self):
        self.client.force_login(self.hod_user)

        dashboard_response = self.client.get("/dashboard/")
        course_response = self.client.get(reverse("course_management:course_management"))

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(course_response.status_code, 200)

    def test_hod_verifier_menu_shows_course_management_and_verification_report(self):
        verifier_group = Group.objects.create(name=VERIFIER_GROUP_NAME)
        self.hod_user.groups.add(verifier_group)
        self.client.force_login(self.hod_user)

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Course Management")
        self.assertContains(response, "Verification Report")

    def test_hod_cannot_access_admin_only_sections(self):
        self.client.force_login(self.hod_user)

        restricted_urls = [
            reverse("program_manage:program_management"),
            reverse("user_manage:user_management"),
        ]

        for url in restricted_urls:
            response = self.client.get(url)
            self.assertRedirects(response, "/dashboard/")

    def test_admin_can_access_admin_only_sections(self):
        self.client.force_login(self.admin_user)

        restricted_urls = [
            reverse("program_manage:program_management"),
            reverse("user_manage:user_management"),
            reverse("reports:work_progress_report"),
        ]

        for url in restricted_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_admin_role_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("core:login"),
            {
                "username": "admin_test",
                "password": "secret123",
                "role": "admin",
                "next": "/dashboard/",
            },
        )

        self.assertRedirects(response, "/dashboard/")

    def test_hod_role_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("core:login"),
            {
                "username": "hod_test",
                "password": "secret123",
                "role": "hod",
                "next": "/dashboard/",
            },
        )

        self.assertRedirects(response, "/dashboard/")

    def test_hod_role_login_rejects_standard_user_accounts(self):
        standard_user = User.objects.create_user(
            username="hod_like_user",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )

        response = self.client.post(
            reverse("core:login"),
            {
                "username": standard_user.username,
                "password": "secret123",
                "role": "hod",
                "next": "/dashboard/",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "do not match the selected role")
        self.assertFalse(response.context["user"].is_authenticated)

    def test_verifier_role_login_redirects_to_dashboard(self):
        verifier_group = Group.objects.create(name=VERIFIER_GROUP_NAME)
        verifier_user = User.objects.create_user(
            username="verifier",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )
        verifier_user.groups.add(verifier_group)

        response = self.client.post(
            reverse("core:login"),
            {
                "username": "verifier",
                "password": "secret123",
                "role": "verifier",
                "next": "/dashboard/",
            },
        )

        self.assertRedirects(response, "/dashboard/")

    def test_hod_cannot_sign_in_through_admin_role(self):
        response = self.client.post(
            reverse("core:login"),
            {
                "username": "hod_test",
                "password": "secret123",
                "role": "admin",
                "next": "/dashboard/",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "do not match the selected role")
        self.assertFalse(response.context["user"].is_authenticated)

    def test_home_page_logs_out_existing_user_and_shows_guest_view(self):
        self.client.force_login(self.hod_user)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
