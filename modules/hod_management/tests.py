from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from modules.hod_management.models import HodProgramMap
from modules.program_manage.models import Program


User = get_user_model()


class HodManagementTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="viewer",
            password="password123",
        )

        self.hod_user = User.objects.create_user(
            username="hod_staff",
            password="password123",
        )
        self.hod_user.is_staff = True
        self.hod_user.save(update_fields=["is_staff"])

        self.mapped_hod = User.objects.create_user(
            username="hod_mapped",
            password="password123",
        )

        self.program_one = Program.objects.create(
            prog_code="BAENG",
            degree="B.A English",
            branch="English",
            prog_type="UG",
            prog_category="Arts",
            is_active=True,
        )
        self.program_two = Program.objects.create(
            prog_code="MSCHEM",
            degree="M.Sc Chemistry",
            branch="Chemistry",
            prog_type="PG",
            prog_category="Science",
            is_active=True,
        )
        self.program_three = Program.objects.create(
            prog_code="BSCPHY",
            degree="B.Sc Physics",
            branch="Physics",
            prog_type="UG",
            prog_category="Science",
            is_active=True,
        )

        HodProgramMap.objects.create(user=self.mapped_hod, program=self.program_three)

    def test_hod_dropdown_includes_staff_and_mapped_hods(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("hod_management:hod_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hod_staff")
        self.assertContains(response, "hod_mapped")

    def test_add_mapping_accepts_multiple_programs(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("hod_management:add_mapping"),
            data={
                "user_id": self.hod_user.id,
                "program_ids": [self.program_one.id, self.program_two.id],
            },
        )

        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(HodProgramMap.objects.filter(user=self.hod_user).count(), 2)
        self.assertTrue(HodProgramMap.objects.filter(user=self.hod_user, program=self.program_one).exists())
        self.assertTrue(HodProgramMap.objects.filter(user=self.hod_user, program=self.program_two).exists())

    def test_edit_mapping_replaces_with_multiple_programs(self):
        existing_mapping = HodProgramMap.objects.create(user=self.hod_user, program=self.program_one)

        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("hod_management:edit_mapping", args=[existing_mapping.id]),
            data={
                "user_id": self.hod_user.id,
                "program_ids": [self.program_one.id, self.program_two.id],
            },
        )

        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(HodProgramMap.objects.filter(user=self.hod_user).count(), 2)
        self.assertTrue(HodProgramMap.objects.filter(user=self.hod_user, program=self.program_one).exists())
        self.assertTrue(HodProgramMap.objects.filter(user=self.hod_user, program=self.program_two).exists())
