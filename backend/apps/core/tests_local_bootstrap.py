from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.businesses.models import Branch, Business
from apps.catalog.models import Product


class LocalFirstRunBootstrapTests(TestCase):
    endpoint = "/api/v1/local/bootstrap/"

    def get_status(self):
        with patch("apps.core.api.local_bootstrap._local_bootstrap_enabled", return_value=True):
            return self.client.get(self.endpoint)

    def post_setup(self, **changes):
        payload = {
            "business_name": "Pilot Cafe",
            "branch_name": "شعبه اصلی",
            "business_type": "CAFE",
            "username": "owner",
            "email": "owner@example.test",
            "password": "Strong-Local-2026!",
            "password_confirmation": "Strong-Local-2026!",
        }
        payload.update(changes)
        with patch("apps.core.api.local_bootstrap._local_bootstrap_enabled", return_value=True):
            return self.client.post(self.endpoint, payload, content_type="application/json")

    def test_fresh_database_reports_setup_required(self):
        response = self.get_status()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"available": True, "needs_setup": True})

    def test_first_run_creates_only_business_branch_and_owner(self):
        response = self.post_setup()
        self.assertEqual(response.status_code, 201)

        business = Business.objects.get(name="Pilot Cafe")
        branch = Branch.objects.get(business=business, name="شعبه اصلی")
        owner = get_user_model().objects.get(username="owner")
        self.assertEqual(business.deployment_type, "LOCAL")
        self.assertTrue(branch.is_active)
        self.assertEqual(owner.business_id, business.id)
        self.assertIsNone(owner.branch_id)
        self.assertEqual(owner.role, get_user_model().Role.OWNER)
        self.assertTrue(owner.check_password("Strong-Local-2026!"))
        self.assertEqual(Product.objects.count(), 0, "First-run setup must never seed demo products.")

        status_response = self.get_status()
        self.assertEqual(status_response.json(), {"available": True, "needs_setup": False})
        second = self.post_setup(business_name="Hijack")
        self.assertEqual(second.status_code, 409)
        self.assertFalse(Business.objects.filter(name="Hijack").exists())

    def test_password_confirmation_mismatch_rolls_back_everything(self):
        response = self.post_setup(password_confirmation="different")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Business.objects.count(), 0)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_weak_password_rolls_back_everything(self):
        response = self.post_setup(password="short1", password_confirmation="short1")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Business.objects.count(), 0)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_real_enablement_is_closed_on_non_local_postgres_ci_profile(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 404)
