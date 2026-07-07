from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from modules.core.roles import VERIFIER_GROUP_NAME, get_user_role
from modules.course_management.access import is_hod_user
from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program


User = get_user_model()


class UserRoleManagementTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(self.admin_user)

    def test_can_create_verifier_user_from_user_management(self):
        response = self.client.post(
            reverse("user_manage:add_user"),
            {
                "first_name": "Verifier",
                "username": "verifier",
                "password": "secret123",
                "role": "verifier",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        user = User.objects.get(username="verifier")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.groups.filter(name=VERIFIER_GROUP_NAME).exists())
        self.assertEqual(get_user_role(user), "verifier")
        self.assertFalse(is_hod_user(user))

    def test_editing_user_role_updates_verifier_group(self):
        verifier_group = Group.objects.create(name=VERIFIER_GROUP_NAME)
        user = User.objects.create_user(
            username="existing_verifier",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )
        user.groups.add(verifier_group)

        response = self.client.post(
            reverse("user_manage:edit_user", args=[user.id]),
            {
                "first_name": "Existing",
                "username": "existing_verifier",
                "role": "hod",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertFalse(user.groups.filter(name=VERIFIER_GROUP_NAME).exists())
        self.assertEqual(get_user_role(user), "hod")
        self.assertTrue(is_hod_user(user))

    def test_hod_can_also_be_assigned_verifier_role(self):
        response = self.client.post(
            reverse("user_manage:add_user"),
            {
                "first_name": "Combined",
                "username": "combined_user",
                "password": "secret123",
                "role": "hod",
                "additional_role": "verifier",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        user = User.objects.get(username="combined_user")
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name=VERIFIER_GROUP_NAME).exists())
        self.assertEqual(get_user_role(user), "hod")
        self.assertTrue(is_hod_user(user))

    def test_editing_user_can_add_verifier_role_to_hod(self):
        user = User.objects.create_user(
            username="hod_user",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )

        response = self.client.post(
            reverse("user_manage:edit_user", args=[user.id]),
            {
                "first_name": "HOD",
                "username": "hod_user",
                "role": "hod",
                "additional_role": "verifier",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.groups.filter(name=VERIFIER_GROUP_NAME).exists())
        self.assertEqual(get_user_role(user), "hod")

    def test_mapped_hod_displays_as_hod_without_staff_flag(self):
        user = User.objects.create_user(
            username="mapped_hod",
            password="secret123",
            is_superuser=False,
            is_staff=False,
        )
        program = Program.objects.create(
            prog_code="MCA",
            branch="Computer Applications",
            degree="MCA",
            prog_type="PG",
            prog_category="Science",
        )
        HodProgramMap.objects.create(user=user, program=program)

        self.assertEqual(get_user_role(user), "hod")

    def test_user_management_filters_users_by_role(self):
        verifier_group = Group.objects.create(name=VERIFIER_GROUP_NAME)
        program = Program.objects.create(
            prog_code="MBA",
            branch="Management",
            degree="MBA",
            prog_type="PG",
            prog_category="Arts",
        )

        hod_user = User.objects.create_user(
            username="hod_user",
            password="secret123",
            is_staff=True,
        )
        HodProgramMap.objects.create(user=hod_user, program=program)

        verifier_user = User.objects.create_user(
            username="verifier_user",
            password="secret123",
        )
        verifier_user.groups.add(verifier_group)

        standard_user = User.objects.create_user(
            username="standard_user",
            password="secret123",
        )

        response = self.client.get(reverse("user_manage:user_management"), {"role": "verifier"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_role"], "verifier")
        self.assertEqual([user.username for user in response.context["users"]], ["verifier_user"])
