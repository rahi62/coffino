from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.otp_providers import OtpDeliveryResult
from apps.accounts.models import OtpChallenge, User
from apps.businesses.models import Business


@override_settings(
    CAF_INO_OTP_SEND_LIMIT_PER_HOUR=100,
    CAF_INO_OTP_VERIFY_LIMIT_PER_HOUR=100,
)
class PasswordRecoveryApiTests(TestCase):
    OLD_PASSWORD = "Legacy-Password-2026!"
    NEW_PASSWORD = "Changed-Password-2026!"

    def setUp(self):
        sender_patch = patch("apps.accounts.otp.get_otp_sender")
        sender_patch.start().return_value.send.return_value = OtpDeliveryResult(accepted=True, provider_code="0")
        self.addCleanup(sender_patch.stop)
        cache.clear()
        self.business = Business.objects.create(name="کافه بازیابی", deployment_type="SAAS")
        self.user = User.objects.create_user(
            username="recover-owner",
            email="recover@example.test",
            password=self.OLD_PASSWORD,
            mobile="09123456789",
            mobile_verified_at=timezone.now(),
            business=self.business,
            role=User.Role.OWNER,
        )
        self.client = APIClient()

    def _forgot(self, identifier):
        with patch("apps.accounts.otp.generate_otp_code", return_value="123456"):
            return self.client.post(
                "/api/v1/auth/password/forgot/",
                {"identifier": identifier},
                format="json",
                REMOTE_ADDR="203.0.113.80",
            )

    def _verify(self, challenge_id, code="123456"):
        return self.client.post(
            "/api/v1/auth/password/otp/verify/",
            {"challenge_id": challenge_id, "code": code},
            format="json",
            REMOTE_ADDR="203.0.113.80",
        )

    def test_forgot_is_enumeration_safe_for_existing_and_missing_accounts(self):
        existing = self._forgot(self.user.username)
        missing = self._forgot("missing-account")

        self.assertEqual(existing.status_code, status.HTTP_200_OK)
        self.assertEqual(missing.status_code, status.HTTP_200_OK)
        self.assertEqual(existing.data["detail"], missing.data["detail"])
        self.assertEqual(set(existing.data), set(missing.data))
        self.assertNotEqual(existing.data["challenge_id"], missing.data["challenge_id"])

    def test_username_email_and_mobile_can_resolve_one_verified_account(self):
        for index, identifier in enumerate(
            [self.user.username, self.user.email.upper(), "+989123456789"]
        ):
            cache.clear()
            OtpChallenge.objects.all().delete()
            response = self._forgot(identifier)
            self.assertEqual(response.status_code, 200, identifier)
            self.assertEqual(
                OtpChallenge.objects.filter(
                    purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
                    user=self.user,
                ).count(),
                1,
                identifier,
            )

    def test_ambiguous_legacy_email_does_not_create_recovery_challenge(self):
        User.objects.create_user(
            username="recover-other",
            email="RECOVER@example.test",
            password=self.OLD_PASSWORD,
            business=self.business,
            role=User.Role.MANAGER,
        )
        response = self._forgot("recover@example.test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            OtpChallenge.objects.filter(
                purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY
            ).count(),
            0,
        )

    def test_valid_otp_reset_changes_password_and_invalidates_old_tokens(self):
        login = self.client.post(
            "/api/token/",
            {"username": self.user.username, "password": self.OLD_PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

        requested = self._forgot(self.user.username)
        verified = self._verify(requested.data["challenge_id"])
        self.assertEqual(verified.status_code, 200)

        reset = self.client.post(
            "/api/v1/auth/password/reset/",
            {
                "verification_grant": verified.data["verification_grant"],
                "password": self.NEW_PASSWORD,
                "password_confirmation": self.NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(reset.status_code, 200)

        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.OLD_PASSWORD))
        self.assertTrue(self.user.check_password(self.NEW_PASSWORD))
        self.assertIsNotNone(self.user.tokens_invalid_before)

        old_access = APIClient()
        old_access.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(old_access.get("/api/v1/me/").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/token/refresh/",
                {"refresh": login.data["refresh"]},
                format="json",
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/token/",
                {"username": self.user.username, "password": self.NEW_PASSWORD},
                format="json",
            ).status_code,
            200,
        )

    def test_recovery_grant_is_single_use(self):
        requested = self._forgot(self.user.mobile)
        verified = self._verify(requested.data["challenge_id"])
        payload = {
            "verification_grant": verified.data["verification_grant"],
            "password": self.NEW_PASSWORD,
            "password_confirmation": self.NEW_PASSWORD,
        }
        self.assertEqual(
            self.client.post("/api/v1/auth/password/reset/", payload, format="json").status_code,
            200,
        )
        replay = self.client.post("/api/v1/auth/password/reset/", payload, format="json")
        self.assertEqual(replay.status_code, 400)

    def test_successful_reset_invalidates_other_verified_recovery_grants(self):
        first_request = self._forgot(self.user.username)
        first_verified = self._verify(first_request.data["challenge_id"])
        self.assertEqual(first_verified.status_code, 200)

        cache.clear()
        second_request = self._forgot(self.user.username)
        second_verified = self._verify(second_request.data["challenge_id"])
        self.assertEqual(second_verified.status_code, 200)
        self.assertNotEqual(
            first_verified.data["verification_grant"],
            second_verified.data["verification_grant"],
        )

        first_reset = self.client.post(
            "/api/v1/auth/password/reset/",
            {
                "verification_grant": first_verified.data["verification_grant"],
                "password": self.NEW_PASSWORD,
                "password_confirmation": self.NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(first_reset.status_code, 200)

        second_reset = self.client.post(
            "/api/v1/auth/password/reset/",
            {
                "verification_grant": second_verified.data["verification_grant"],
                "password": "Another-Strong-Password-2027!",
                "password_confirmation": "Another-Strong-Password-2027!",
            },
            format="json",
        )
        self.assertEqual(second_reset.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.NEW_PASSWORD))

    def test_weak_password_rolls_back_grant_consumption(self):
        requested = self._forgot(self.user.username)
        verified = self._verify(requested.data["challenge_id"])
        weak = {
            "verification_grant": verified.data["verification_grant"],
            "password": "short1",
            "password_confirmation": "short1",
        }
        rejected = self.client.post("/api/v1/auth/password/reset/", weak, format="json")
        self.assertEqual(rejected.status_code, 400)

        accepted = self.client.post(
            "/api/v1/auth/password/reset/",
            {
                "verification_grant": verified.data["verification_grant"],
                "password": self.NEW_PASSWORD,
                "password_confirmation": self.NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(accepted.status_code, 200)

    def test_unknown_challenge_or_wrong_code_fails_without_account_disclosure(self):
        requested = self._forgot("missing-account")
        response = self._verify(requested.data["challenge_id"], code="000000")
        self.assertEqual(response.status_code, 400)
        self.assertIn("معتبر", str(response.data))
