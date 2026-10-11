from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.otp_providers import OtpDeliveryResult
from apps.accounts.models import OtpChallenge
from apps.accounts.otp import request_otp, verify_otp
from apps.businesses.models import Branch, Business


User = get_user_model()


@override_settings(
    CAF_INO_OTP_SEND_LIMIT_PER_HOUR=100,
)
class SaasRegistrationApiTests(APITestCase):
    PASSWORD = "Cafino-Owner-Strong-2026!"

    def setUp(self):
        sender_patch = patch("apps.accounts.otp.get_otp_sender")
        sender_patch.start().return_value.send.return_value = OtpDeliveryResult(accepted=True, provider_code="0")
        self.addCleanup(sender_patch.stop)
        cache.clear()
        rate = patch("apps.accounts.throttles.RegistrationThrottle.rate", "100/hour", create=True)
        rate.start()
        self.addCleanup(rate.stop)

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

    def test_registration_can_login_and_reach_authenticated_onboarding_context(self):
        registered = self.client.post("/api/v1/auth/register/", self.payload(), format="json")
        self.assertEqual(registered.status_code, status.HTTP_201_CREATED)

        logged_in = self.client.post(
            "/api/token/",
            {"username": "new-owner", "password": self.PASSWORD},
            format="json",
            REMOTE_ADDR="203.0.113.34",
        )
        self.assertEqual(logged_in.status_code, status.HTTP_200_OK)
        self.assertTrue(logged_in.data["access"])
        self.assertTrue(logged_in.data["refresh"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {logged_in.data['access']}")
        me = self.client.get("/api/v1/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "new-owner")
        self.assertEqual(me.data["role"], User.Role.OWNER)
        self.assertEqual(me.data["business_id"], registered.data["business"]["id"])
        self.assertTrue(me.data["mobile_verified"])

        context = self.client.get("/api/v1/settings/context/")
        self.assertEqual(context.status_code, status.HTTP_200_OK)
        self.assertEqual(context.data["business"]["id"], registered.data["business"]["id"])
        self.assertEqual(
            {row["id"] for row in context.data["branches"]},
            {registered.data["branch"]["id"]},
        )

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


    def test_registered_owner_user_management_stays_inside_own_tenant(self):
        other_business = Business.objects.create(name="Tenant Users B", deployment_type="SAAS")
        other_branch = Branch.objects.create(business=other_business, name="Foreign")
        other_user = User.objects.create_user(
            username="foreign-cashier",
            password="Foreign-Password-2026!",
            business=other_business,
            branch=other_branch,
            role=User.Role.CASHIER,
        )

        registered = self.client.post("/api/v1/auth/register/", self.payload(), format="json")
        self.assertEqual(registered.status_code, status.HTTP_201_CREATED)
        owner = User.objects.get(pk=registered.data["user"]["id"])
        own_branch = Branch.objects.get(pk=registered.data["branch"]["id"])
        self.client.force_authenticate(owner)

        own_create = self.client.post(
            "/api/v1/settings/users/create/",
            {
                "username": "own-cashier",
                "password": "Own-Cashier-2026!",
                "role": User.Role.CASHIER,
                "branch": own_branch.id,
            },
            format="json",
        )
        self.assertEqual(own_create.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(username="own-cashier")
        self.assertEqual(created_user.business_id, owner.business_id)
        self.assertEqual(created_user.branch_id, own_branch.id)

        foreign_branch_create = self.client.post(
            "/api/v1/settings/users/create/",
            {
                "username": "cross-tenant-user",
                "password": "Cross-Tenant-2026!",
                "role": User.Role.CASHIER,
                "branch": other_branch.id,
            },
            format="json",
        )
        self.assertEqual(foreign_branch_create.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="cross-tenant-user").exists())

        foreign_reset = self.client.post(
            f"/api/v1/settings/users/{other_user.id}/password/",
            {"password": "Changed-Foreign-2027!"},
            format="json",
        )
        self.assertEqual(foreign_reset.status_code, status.HTTP_403_FORBIDDEN)
        other_user.refresh_from_db()
        self.assertTrue(other_user.check_password("Foreign-Password-2026!"))

        own_reset = self.client.post(
            f"/api/v1/settings/users/{created_user.id}/password/",
            {"password": "Changed-Own-2027!"},
            format="json",
        )
        self.assertEqual(own_reset.status_code, status.HTTP_200_OK)
        created_user.refresh_from_db()
        self.assertTrue(created_user.check_password("Changed-Own-2027!"))

    def test_registered_owner_gets_owner_context_and_cannot_cross_tenant_boundaries(self):
        other_business = Business.objects.create(name="Tenant B", deployment_type="SAAS")
        other_branch = Branch.objects.create(
            business=other_business, name="Branch B", phone="02100000000"
        )
        registered = self.client.post("/api/v1/auth/register/", self.payload(), format="json")
        self.assertEqual(registered.status_code, status.HTTP_201_CREATED)
        owner = User.objects.get(pk=registered.data["user"]["id"])
        own_business = owner.business
        own_branch = own_business.branches.get()

        self.client.force_authenticate(owner)

        permissions = self.client.get("/api/v1/permissions/me/")
        self.assertEqual(permissions.status_code, status.HTTP_200_OK)
        self.assertEqual(permissions.data["role"], User.Role.OWNER)
        self.assertTrue(permissions.data["permissions"]["settings.manage"])
        self.assertTrue(permissions.data["permissions"]["business.manage"])
        self.assertTrue(permissions.data["permissions"]["branches.manage"])

        context = self.client.get("/api/v1/settings/context/")
        self.assertEqual(context.status_code, status.HTTP_200_OK)
        self.assertEqual(context.data["business"]["id"], own_business.id)
        self.assertEqual({row["id"] for row in context.data["branches"]}, {own_branch.id})
        self.assertNotEqual(context.data["business"]["id"], other_business.id)

        foreign_read = self.client.get(f"/api/v1/branches/{other_branch.id}/")
        foreign_write = self.client.patch(
            f"/api/v1/branches/{other_branch.id}/",
            {"phone": "02199999999"},
            format="json",
        )
        self.assertEqual(foreign_read.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(foreign_write.status_code, status.HTTP_404_NOT_FOUND)
        other_branch.refresh_from_db()
        self.assertEqual(other_branch.phone, "02100000000")

        foreign_onboarding = self.client.post(
            "/api/v1/settings/onboarding/apply/",
            {
                "preset": "CAFE",
                "branch": other_branch.id,
                "deployment_type": "SAAS",
            },
            format="json",
        )
        self.assertEqual(foreign_onboarding.status_code, status.HTTP_400_BAD_REQUEST)
