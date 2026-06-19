from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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

    def test_hod_can_access_dashboard_course_and_upload_center(self):
        self.client.force_login(self.hod_user)

        dashboard_response = self.client.get("/dashboard/")
        course_response = self.client.get(reverse("course_manage:course_management"))
        upload_response = self.client.get(reverse("upload_center:upload_center"))

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(course_response.status_code, 200)
        self.assertEqual(upload_response.status_code, 200)

    def test_hod_cannot_access_admin_only_sections(self):
        self.client.force_login(self.hod_user)

        restricted_urls = [
            reverse("program_manage:program_management"),
            reverse("user_manage:user_management"),
            reverse("reports:work_progress_report"),
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

    def test_hod_role_login_allows_standard_user_accounts(self):
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
