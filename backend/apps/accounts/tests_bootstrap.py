import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.businesses.models import Branch, Business


class BootstrapBusinessOwnerTests(TestCase):
    PASSWORD = "Cafino-Owner-Strong-2026!"

    def run_command(self, **extra):
        options = {
            "business_name": "Pilot Cafe",
            "username": "pilot-owner",
            "email": "owner@example.test",
            "branch_name": "Main",
            "deployment_type": "SAAS",
        }
        options.update(extra)
        output = StringIO()
        with patch.dict(os.environ, {"CAF_INO_BOOTSTRAP_OWNER_PASSWORD": self.PASSWORD}, clear=False):
            call_command("bootstrap_business_owner", stdout=output, **options)
        return output.getvalue()

    def test_creates_business_branch_and_owner_without_demo_data(self):
        text = self.run_command()
        business = Business.objects.get(name="Pilot Cafe")
        branch = Branch.objects.get(business=business, name="Main")
        user = get_user_model().objects.get(username="pilot-owner")

        self.assertEqual(business.deployment_type, "SAAS")
        self.assertTrue(branch.is_active)
        self.assertEqual(user.business_id, business.id)
        self.assertEqual(user.role, get_user_model().Role.OWNER)
        self.assertIsNone(user.branch_id)
        self.assertTrue(user.check_password(self.PASSWORD))
        self.assertIn("Bootstrap complete", text)

    def test_is_idempotent_and_does_not_reset_existing_password(self):
        self.run_command()
        user = get_user_model().objects.get(username="pilot-owner")
        user.set_password("Another-Existing-Password-2026!")
        user.save()

        text = self.run_command()
        self.assertEqual(Business.objects.filter(name="Pilot Cafe").count(), 1)
        self.assertEqual(Branch.objects.filter(business__name="Pilot Cafe", name="Main").count(), 1)
        self.assertEqual(get_user_model().objects.filter(username="pilot-owner").count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Another-Existing-Password-2026!"))
        self.assertIn("OWNER already exists", text)

    def test_rejects_username_owned_by_another_tenant(self):
        other = Business.objects.create(name="Other", deployment_type="SAAS")
        get_user_model().objects.create_user(
            username="pilot-owner",
            password=self.PASSWORD,
            business=other,
            role=get_user_model().Role.OWNER,
        )
        with patch.dict(os.environ, {"CAF_INO_BOOTSTRAP_OWNER_PASSWORD": self.PASSWORD}, clear=False):
            with self.assertRaises(CommandError):
                call_command(
                    "bootstrap_business_owner",
                    business_name="Pilot Cafe",
                    username="pilot-owner",
                    deployment_type="SAAS",
                )
        self.assertFalse(Business.objects.filter(name="Pilot Cafe").exists())
