from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Program


class ProgramManageTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="tester",
            password="secret123",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(user)

    def test_program_management_filters_by_selected_year(self):
        Program.objects.create(year="2023-2024", prog_type="UG", prog_category="Arts", prog_code="BAENG", branch="English")
        Program.objects.create(year="2024-2025", prog_type="PG", prog_category="Science", prog_code="MSCHEM", branch="Chemistry")

        response = self.client.get(reverse("program_manage:program_management"), {"year": "2023-2024"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(response.context["page_obj"].object_list[0].prog_code, "BAENG")

    def test_get_filter_options_limits_related_program_filters_by_year(self):
        Program.objects.create(year="2023-2024", prog_type="UG", prog_category="Arts", prog_code="BAENG", branch="English")
        Program.objects.create(year="2023-2024", prog_type="PG", prog_category="Science", prog_code="MSCHEM", branch="Chemistry")
        Program.objects.create(year="2024-2025", prog_type="UG", prog_category="Science", prog_code="BSCPHY", branch="Physics")

        response = self.client.get(reverse("program_manage:get_filter_options"), {"year": "2023-2024"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["prog_types"], ["PG", "UG"])
        self.assertEqual(data["prog_codes"], ["BAENG", "MSCHEM"])
        self.assertEqual(data["branches"], ["Chemistry", "English"])
