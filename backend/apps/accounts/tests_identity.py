from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import OtpChallenge, User
from apps.accounts.phone import mask_mobile, normalize_iran_mobile
from apps.businesses.models import Branch, Business


class IranianMobileNormalizationTests(TestCase):
    def test_normalizes_supported_iran_mobile_formats(self):
        variants = [
            "09123456789",
            "+989123456789",
            "00989123456789",
            "۹۱۲۳۴۵۶۷۸۹",
            "٠٩١٢٣٤٥٦٧٨٩",
            " 0912 345 6789 ",
        ]

        self.assertEqual(
            [normalize_iran_mobile(value) for value in variants],
            ["09123456789"] * len(variants),
        )
        self.assertEqual(mask_mobile("+989123456789"), "0912***6789")

    def test_rejects_non_mobile_and_malformed_values(self):
        invalid_values = ["", "02112345678", "0912345678", "091234567890", "08123456789", "hello"]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_iran_mobile(value)


class MobileIdentityModelTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="کافه آزمون")
        self.branch = Branch.objects.create(business=self.business, name="شعبه اصلی")

    def test_non_null_user_mobile_is_globally_unique(self):
        User.objects.create_user(
            username="owner-one",
            password="Passphrase123!",
            business=self.business,
            role=User.Role.OWNER,
            mobile="09123456789",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="owner-two",
                    password="Passphrase123!",
                    business=self.business,
                    role=User.Role.OWNER,
                    mobile="09123456789",
                )

    def test_legacy_users_and_customers_remain_valid_with_null_fields(self):
        user = User.objects.create_user(
            username="legacy-owner",
            password="Passphrase123!",
            business=self.business,
            role=User.Role.OWNER,
        )
        self.assertIsNone(user.mobile)
        self.assertIsNone(user.mobile_verified_at)
        self.assertIsNone(user.tokens_invalid_before)

    def test_otp_challenge_has_no_raw_code_field_and_reports_expiry(self):
        challenge = OtpChallenge.objects.create(
            mobile="09123456789",
            purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
            code_hash="hashed-value",
            expires_at=timezone.now() - timedelta(seconds=1),
            next_send_at=timezone.now(),
        )

        field_names = {field.name for field in OtpChallenge._meta.get_fields()}
        self.assertNotIn("code", field_names)
        self.assertNotIn("otp", field_names)
        self.assertTrue(challenge.is_expired)
        self.assertFalse(challenge.is_consumed)
