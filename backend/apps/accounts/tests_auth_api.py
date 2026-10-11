from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.otp_providers import OtpDeliveryResult
from apps.accounts.models import OtpChallenge, User
from apps.businesses.models import Branch, Business


@override_settings(
    CAF_INO_OTP_SEND_LIMIT_PER_HOUR=100,
    CAF_INO_OTP_VERIFY_LIMIT_PER_HOUR=100,
)
class AuthenticationApiTests(TestCase):
    PASSWORD = "Legacy-Password-2026!"

    def setUp(self):
        sender_patch = patch("apps.accounts.otp.get_otp_sender")
        sender_patch.start().return_value.send.return_value = OtpDeliveryResult(accepted=True, provider_code="0")
        self.addCleanup(sender_patch.stop)
        cache.clear()
        self.business = Business.objects.create(name="کافه احراز هویت", deployment_type="SAAS")
        self.branch = Branch.objects.create(business=self.business, name="مرکزی")
        self.user = User.objects.create_user(
            username="legacy-owner",
            email="owner@example.test",
            password=self.PASSWORD,
            mobile="09123456789",
            mobile_verified_at=timezone.now(),
            business=self.business,
            role=User.Role.OWNER,
        )
        self.client = APIClient()

    def password_login(self):
        return self.client.post(
            "/api/token/",
            {"username": self.user.username, "password": self.PASSWORD},
            format="json",
            REMOTE_ADDR="203.0.113.40",
        )

    def test_legacy_password_login_and_valid_refresh_keep_same_token_shape(self):
        logged_in = self.password_login()

        self.assertEqual(logged_in.status_code, status.HTTP_200_OK)
        self.assertEqual(set(logged_in.data), {"access", "refresh"})
        refreshed = self.client.post(
            "/api/token/refresh/", {"refresh": logged_in.data["refresh"]}, format="json"
        )
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertTrue(refreshed.data["access"])

    def test_invalid_refresh_fails_safely(self):
        response = self.client.post("/api/token/refresh/", {"refresh": "not-a-token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("traceback", str(response.data).lower())

    def test_otp_login_for_active_verified_user_issues_token_pair(self):
        with patch("apps.accounts.otp.generate_otp_code", return_value="123456"):
            requested = self.client.post(
                "/api/v1/auth/login/otp/request/",
                {"mobile": "+989123456789"},
                format="json",
                REMOTE_ADDR="203.0.113.41",
            )
        self.assertEqual(requested.status_code, status.HTTP_200_OK)

        verified = self.client.post(
            "/api/v1/auth/login/otp/verify/",
            {"challenge_id": requested.data["challenge_id"], "code": "123456"},
            format="json",
            REMOTE_ADDR="203.0.113.41",
        )

        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.assertEqual(set(verified.data), {"access", "refresh"})
        access_client = APIClient()
        access_client.credentials(HTTP_AUTHORIZATION=f"Bearer {verified.data['access']}")
        self.assertEqual(access_client.get("/api/v1/me/").status_code, status.HTTP_200_OK)

        replay = self.client.post(
            "/api/v1/auth/login/otp/verify/",
            {"challenge_id": requested.data["challenge_id"], "code": "123456"}, format="json",
        )
        self.assertEqual(replay.status_code, 400)

    def test_otp_cannot_login_user_disabled_after_request(self):
        with patch("apps.accounts.otp.generate_otp_code", return_value="123456"):
            requested = self.client.post("/api/v1/auth/login/otp/request/", {
                "mobile": self.user.mobile,
            }, format="json")
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post("/api/v1/auth/login/otp/verify/", {
            "challenge_id": requested.data["challenge_id"], "code": "123456",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_or_unverified_mobile_gets_same_generic_request_response(self):
        User.objects.create_user(
            username="unverified",
            password=self.PASSWORD,
            mobile="09120000000",
            business=self.business,
            role=User.Role.MANAGER,
        )
        responses = []
        for mobile in ("09120000000", "09129999999"):
            response = self.client.post(
                "/api/v1/auth/login/otp/request/",
                {"mobile": mobile},
                format="json",
                REMOTE_ADDR="203.0.113.42",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            responses.append(response.data)

        self.assertEqual(responses[0]["detail"], responses[1]["detail"])
        self.assertEqual(set(responses[0]), set(responses[1]))
        self.assertEqual(
            OtpChallenge.objects.filter(purpose=OtpChallenge.Purpose.STAFF_LOGIN).count(), 0
        )

    def test_old_access_and_refresh_tokens_are_rejected_after_invalidation(self):
        pair = self.password_login().data
        access_client = APIClient()
        access_client.credentials(HTTP_AUTHORIZATION=f"Bearer {pair['access']}")
        self.assertEqual(access_client.get("/api/v1/me/").status_code, status.HTTP_200_OK)

        self.user.tokens_invalid_before = timezone.now() + timedelta(milliseconds=1)
        self.user.save(update_fields=["tokens_invalid_before"])

        self.assertEqual(access_client.get("/api/v1/me/").status_code, status.HTTP_401_UNAUTHORIZED)
        refreshed = self.client.post(
            "/api/token/refresh/", {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(refreshed.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_exposes_identity_context_without_sensitive_fields(self):
        pair = self.password_login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {pair['access']}")

        response = self.client.get("/api/v1/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["mobile"], self.user.mobile)
        self.assertTrue(response.data["mobile_verified"])
        self.assertEqual(response.data["business_id"], self.business.id)
        self.assertIsNone(response.data["branch_id"])
        self.assertNotIn("password", response.data)
        self.assertNotIn("permission_overrides", response.data)

    def test_login_immediately_after_invalidation_issues_usable_tokens(self):
        self.user.tokens_invalid_before = timezone.now()
        self.user.save(update_fields=["tokens_invalid_before"])
        pair = self.password_login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {pair['access']}")
        self.assertEqual(self.client.get("/api/v1/me/").status_code, 200)
        self.client.credentials()
        self.assertEqual(self.client.post(
            "/api/token/refresh/", {"refresh": pair["refresh"]}, format="json",
        ).status_code, 200)

    def test_password_login_is_throttled(self):
        cache.clear()
        with patch("apps.accounts.throttles.AuthLoginThrottle.rate", "2/hour", create=True):
            for _ in range(2):
                response = self.client.post(
                    "/api/token/",
                    {"username": "missing", "password": "wrong"},
                    format="json",
                    REMOTE_ADDR="203.0.113.49",
                )
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            blocked = self.client.post(
                "/api/token/",
                {"username": "missing", "password": "wrong"},
                format="json",
                REMOTE_ADDR="203.0.113.49",
            )
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
