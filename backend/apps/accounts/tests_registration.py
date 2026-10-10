from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import OtpChallenge
from apps.accounts.otp import request_otp, verify_otp
from apps.businesses.models import Branch, Business


User = get_user_model()


@override_settings(
    CAF_INO_OTP_SENDER="apps.accounts.otp_providers.FakeOtpSender",
    CAF_INO_OTP_SEND_LIMIT_PER_HOUR=100,
)
class SaasRegistrationApiTests(APITestCase):
    PASSWORD = "Cafino-Owner-Strong-2026!"

    def verified_grant(self, mobile="09123456789"):
        with patch("apps.accounts.otp.generate_otp_code", return_value="123456"):
            requested = request_otp(
                mobile=mobile,
                purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
                request_ip="203.0.113.30",
            )
        return verify_otp(
            challenge_id=requested.challenge_id,
            code="123456",
            expected_purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
        )

    def payload(self, **changes):
        payload = {
            "business_name": "کافه ثبت‌نام",
            "business_type": "CAFE",
            "branch_name": "شعبه اصلی",
            "branch_phone": "02112345678",
            "copy_owner_mobile_to_branch": False,
            "username": "new-owner",
            "email": "owner@example.test",
            "password": self.PASSWORD,
            "password_confirmation": self.PASSWORD,
            "verification_grant": self.verified_grant(),
        }
        payload.update(changes)
        return payload

    def test_registration_otp_request_and_verify_are_public_and_return_safe_payloads(self):
        with patch("apps.accounts.otp.generate_otp_code", return_value="123456"):
            requested = self.client.post(
                "/api/v1/auth/register/otp/request/",
                {"mobile": "+989123456789"},
                format="json",
                REMOTE_ADDR="203.0.113.31",
            )

        self.assertEqual(requested.status_code, status.HTTP_200_OK)
        self.assertEqual(requested.data["mobile"], "0912***6789")
        self.assertNotIn("code", requested.data)
        verified = self.client.post(
            "/api/v1/auth/register/otp/verify/",
            {"challenge_id": requested.data["challenge_id"], "code": "123456"},
            format="json",
            REMOTE_ADDR="203.0.113.31",
        )
        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.assertTrue(verified.data["verification_grant"])

    def test_success_creates_exact_saas_tenant_and_owner_without_sensitive_response(self):
        response = self.client.post("/api/v1/auth/register/", self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Business.objects.count(), 1)
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        business = Business.objects.get()
        branch = Branch.objects.get()
        owner = User.objects.get()
        self.assertEqual(business.deployment_type, "SAAS")
        self.assertTrue(business.is_active)
        self.assertEqual(branch.business_id, business.id)
        self.assertEqual(branch.phone, "02112345678")
        self.assertEqual(owner.role, User.Role.OWNER)
        self.assertEqual(owner.business_id, business.id)
        self.assertIsNone(owner.branch_id)
        self.assertEqual(owner.mobile, "09123456789")
        self.assertIsNotNone(owner.mobile_verified_at)
        self.assertTrue(owner.check_password(self.PASSWORD))
        self.assertEqual(response.data["next"], "onboarding")
        self.assertNotIn("password", str(response.data).lower())
        self.assertNotIn("permission_overrides", str(response.data))

    def test_owner_mobile_is_copied_to_branch_only_when_explicitly_selected(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            self.payload(branch_phone="", copy_owner_mobile_to_branch=True),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Branch.objects.get().phone, "09123456789")

    def test_duplicate_username_email_and_verified_mobile_are_rejected(self):
        existing_business = Business.objects.create(name="کسب‌وکار موجود")
        User.objects.create_user(
            username="taken-owner",
            email="Taken@Example.test",
            password=self.PASSWORD,
            mobile="09121111111",
            mobile_verified_at=timezone.now(),
            business=existing_business,
            role=User.Role.OWNER,
        )

        cases = [
            ({"username": "TAKEN-OWNER", "email": "other@example.test"}, "نام کاربری"),
            ({"username": "unique-one", "email": "taken@example.TEST"}, "ایمیل"),
            ({"username": "unique-two", "email": "two@example.test"}, "شماره همراه"),
        ]
        for index, (changes, expected) in enumerate(cases):
            mobile = "09121111111" if index == 2 else f"0912000000{index}"
            response = self.client.post(
                "/api/v1/auth/register/",
                self.payload(verification_grant=self.verified_grant(mobile), **changes),
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(expected, str(response.data))

    def test_weak_password_and_confirmation_mismatch_have_persian_errors(self):
        for changes, expected in [
            ({"password": "short1", "password_confirmation": "short1"}, "گذرواژه"),
            ({"password_confirmation": "Different-Strong-2026!"}, "یکسان"),
        ]:
            response = self.client.post(
                "/api/v1/auth/register/", self.payload(**changes), format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(expected, str(response.data))

    def test_privileged_or_tenant_binding_fields_are_rejected(self):
        forbidden = {
            "role": "OWNER",
            "business_id": 99,
            "branch_id": 99,
            "deployment_type": "LOCAL",
            "permission_overrides": {"*": True},
            "enabled_modules": ["POS"],
        }
        for field, value in forbidden.items():
            response = self.client.post(
                "/api/v1/auth/register/", self.payload(**{field: value}), format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_failure_after_tenant_creation_rolls_back_everything_and_grant_consumption(self):
        payload = self.payload()
        challenge = OtpChallenge.objects.get()

        with patch(
            "apps.accounts.registration.User.objects.create_user",
            side_effect=RuntimeError("forced user creation failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post("/api/v1/auth/register/", payload, format="json")

        self.assertEqual(Business.objects.count(), 0)
        self.assertEqual(Branch.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        challenge.refresh_from_db()
        self.assertIsNone(challenge.consumed_at)

    def test_registration_grant_cannot_be_reused_or_attach_to_existing_tenant(self):
        existing = Business.objects.create(name="کسب‌وکار دیگر")
        payload = self.payload()
        payload["business_id"] = existing.id
        rejected = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(existing.users.count(), 0)

        payload.pop("business_id")
        created = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        reused = self.client.post(
            "/api/v1/auth/register/",
            {**payload, "username": "second-owner", "email": "second@example.test"},
            format="json",
        )
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_owner_can_only_list_own_business_and_branch(self):
        other_business = Business.objects.create(name="کسب‌وکار دیگر")
        other_branch = Branch.objects.create(business=other_business, name="شعبه دیگر")
        registered = self.client.post("/api/v1/auth/register/", self.payload(), format="json")
        owner = User.objects.get(pk=registered.data["user"]["id"])
        own_business = owner.business
        own_branch = own_business.branches.get()

        self.client.force_authenticate(owner)
        businesses = self.client.get("/api/v1/businesses/")
        branches = self.client.get("/api/v1/branches/")

        self.assertEqual(businesses.status_code, status.HTTP_200_OK)
        self.assertEqual({row["id"] for row in businesses.data}, {own_business.id})
        self.assertEqual(branches.status_code, status.HTTP_200_OK)
        self.assertEqual({row["id"] for row in branches.data}, {own_branch.id})
        self.assertNotIn(other_business.id, {row["id"] for row in businesses.data})
        self.assertNotIn(other_branch.id, {row["id"] for row in branches.data})
