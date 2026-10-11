from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import OtpChallenge, PlatformOtpProviderConfig, User
from apps.accounts.otp import (
    OtpCooldownError,
    OtpDeliveryError,
    OtpInvalidError,
    OtpRateLimitError,
    consume_verification_grant,
    request_otp,
    verify_otp,
)
from apps.accounts.otp_providers import DisabledOtpSender, ParsGreenOtpSender, get_otp_sender
from apps.businesses.models import Business


@override_settings(
    CAF_INO_OTP_SENDER="apps.accounts.otp_providers.FakeOtpSender",
    CAF_INO_OTP_TTL_SECONDS=300,
    CAF_INO_OTP_RESEND_SECONDS=60,
    CAF_INO_OTP_MAX_ATTEMPTS=5,
    CAF_INO_OTP_SEND_LIMIT_PER_HOUR=5,
    CAF_INO_OTP_VERIFY_LIMIT_PER_HOUR=20,
)
class OtpLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.business = Business.objects.create(name="کافه OTP")

    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_successful_verification_returns_single_use_purpose_bound_grant(self, _generate):
        result = request_otp(
            mobile="+989123456789",
            purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
            request_ip="203.0.113.10",
        )

        grant = verify_otp(
            challenge_id=result.challenge_id,
            code="123456",
            expected_purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
        )
        verified = consume_verification_grant(
            grant,
            purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
        )

        self.assertEqual(verified.mobile, "09123456789")
        self.assertEqual(verified.purpose, OtpChallenge.Purpose.SAAS_REGISTRATION)
        with self.assertRaises(OtpInvalidError):
            consume_verification_grant(grant, purpose=OtpChallenge.Purpose.SAAS_REGISTRATION)

    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_bad_code_increments_attempts_and_fifth_failure_locks_challenge(self, _generate):
        result = request_otp(
            mobile="09123456789",
            purpose=OtpChallenge.Purpose.STAFF_LOGIN,
            request_ip="203.0.113.11",
        )

        for attempt in range(5):
            with self.assertRaises(OtpInvalidError):
                verify_otp(
                    challenge_id=result.challenge_id,
                    code="000000",
                    expected_purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                )
            challenge = OtpChallenge.objects.get(uuid=result.challenge_id)
            self.assertEqual(challenge.failed_attempts, attempt + 1)

        with self.assertRaises(OtpInvalidError):
            verify_otp(
                challenge_id=result.challenge_id,
                code="123456",
                expected_purpose=OtpChallenge.Purpose.STAFF_LOGIN,
            )

    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_expired_challenge_is_rejected(self, _generate):
        result = request_otp(
            mobile="09123456789",
            purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
            request_ip="203.0.113.12",
        )
        OtpChallenge.objects.filter(uuid=result.challenge_id).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        with self.assertRaises(OtpInvalidError):
            verify_otp(
                challenge_id=result.challenge_id,
                code="123456",
                expected_purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
            )

    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_resend_cooldown_reuses_one_active_challenge(self, _generate):
        first = request_otp(
            mobile="09123456789",
            purpose=OtpChallenge.Purpose.CUSTOMER_VERIFY,
            business=self.business,
            request_ip="203.0.113.13",
        )

        with self.assertRaises(OtpCooldownError):
            request_otp(
                mobile="+989123456789",
                purpose=OtpChallenge.Purpose.CUSTOMER_VERIFY,
                business=self.business,
                request_ip="203.0.113.13",
            )

        self.assertEqual(OtpChallenge.objects.count(), 1)
        self.assertEqual(OtpChallenge.objects.get().uuid, first.challenge_id)

    @override_settings(CAF_INO_OTP_SEND_LIMIT_PER_HOUR=2, CAF_INO_OTP_RESEND_SECONDS=0)
    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_rate_limit_uses_normalized_phone_and_ip(self, _generate):
        for mobile in ("09123456789", "+989123456789"):
            request_otp(
                mobile=mobile,
                purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                request_ip="203.0.113.14",
            )

        with self.assertRaises(OtpRateLimitError):
            request_otp(
                mobile="00989123456789",
                purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                request_ip="203.0.113.14",
            )

        self.assertEqual(OtpChallenge.objects.count(), 1)

    @patch("apps.accounts.otp.get_otp_sender")
    @patch("apps.accounts.otp.generate_otp_code", return_value="123456")
    def test_ambiguous_provider_failure_is_not_immediately_resent(self, _generate, get_sender):
        get_sender.return_value.send.side_effect = TimeoutError("provider timed out with SECRET")

        with self.assertRaises(OtpDeliveryError) as raised:
            request_otp(
                mobile="09123456789",
                purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                request_ip="203.0.113.15",
            )

        self.assertNotIn("SECRET", str(raised.exception))
        challenge = OtpChallenge.objects.get()
        self.assertEqual(challenge.delivery_status, OtpChallenge.DeliveryStatus.FAILED)
        with self.assertRaises(OtpCooldownError):
            request_otp(
                mobile="09123456789",
                purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                request_ip="203.0.113.15",
            )
        self.assertEqual(OtpChallenge.objects.count(), 1)


@override_settings(
    PARSGREEN_API_BASE_URL="https://sms.parsgreen.ir",
    PARSGREEN_API_KEY="api-key",
    PARSGREEN_SIGNATURE="signature",
    PARSGREEN_OTP_ADD_NAME=True,
    PARSGREEN_TIMEOUT_SECONDS=7,
)
class ParsGreenOtpSenderTests(TestCase):
    @patch("apps.accounts.otp_providers.post_json")
    def test_sender_matches_official_send_otp_contract(self, post_json):
        post_json.return_value = {
            "R_Success": True,
            "R_Code": 0,
            "R_Error": "",
            "R_Message": "accepted",
        }

        result = ParsGreenOtpSender().send(
            mobile="09123456789",
            code="123456",
            correlation_id="safe-correlation",
        )

        args, kwargs = post_json.call_args
        self.assertEqual(args[0], "https://sms.parsgreen.ir/Apiv2/Message/SendOtp")
        self.assertEqual(args[1], {"Mobile": "09123456789", "SmsCode": "123456", "AddName": True})
        self.assertTrue(kwargs["require_https"])
        self.assertFalse(kwargs["allow_private"])
        self.assertEqual(kwargs["timeout"], 7)
        self.assertEqual(kwargs["headers"]["Authorization"], "basic apikey:api-key")
        self.assertTrue(result.accepted)
        self.assertEqual(result.provider_code, "0")

    @patch("apps.accounts.otp_providers.post_json", return_value={"unexpected": True})
    def test_malformed_provider_response_fails_safely(self, _post_json):
        with self.assertRaises(OtpDeliveryError) as raised:
            ParsGreenOtpSender().send(
                mobile="09123456789", code="123456", correlation_id="safe-correlation"
            )
        self.assertEqual(str(raised.exception), "ارسال کد یک‌بارمصرف انجام نشد. کمی بعد دوباره تلاش کنید.")

    @patch("apps.accounts.otp_providers.post_json")
    def test_provider_declared_error_is_normalized(self, post_json):
        post_json.return_value = {
            "R_Success": False,
            "R_Code": 42,
            "R_Error": "SECRET_PROVIDER_DETAIL",
            "R_Message": "failed",
        }

        with self.assertRaises(OtpDeliveryError) as raised:
            ParsGreenOtpSender().send(
                mobile="09123456789", code="123456", correlation_id="safe-correlation"
            )

        self.assertNotIn("SECRET_PROVIDER_DETAIL", str(raised.exception))



class PlatformOtpProviderConfigTests(TestCase):
    def test_secrets_are_encrypted_and_never_stored_as_plaintext(self):
        config = PlatformOtpProviderConfig(provider=PlatformOtpProviderConfig.Provider.PARSGREEN)
        config.set_api_key("plain-api-key")
        config.set_signature("plain-signature")
        config.full_clean()
        config.save()

        self.assertNotIn("plain-api-key", config.api_key_encrypted)
        self.assertNotIn("plain-signature", config.signature_encrypted)
        self.assertEqual(config.get_api_key(), "plain-api-key")
        self.assertEqual(config.get_signature(), "plain-signature")
        self.assertTrue(config.credentials_configured)

    @override_settings(
        CAF_INO_OTP_SENDER="apps.accounts.otp_providers.DisabledOtpSender",
        PARSGREEN_API_KEY="env-key",
        PARSGREEN_SIGNATURE="env-signature",
    )
    def test_enabled_database_config_overrides_disabled_env_sender(self):
        config = PlatformOtpProviderConfig.objects.create(
            provider=PlatformOtpProviderConfig.Provider.PARSGREEN,
            enabled=True,
            api_base_url="https://sms.parsgreen.ir",
        )
        config.set_api_key("db-key")
        config.set_signature("db-signature")
        config.save()

        sender = get_otp_sender()
        self.assertIsInstance(sender, ParsGreenOtpSender)
        self.assertEqual(sender.config.api_key, "db-key")

    @override_settings(
        CAF_INO_OTP_SENDER="apps.accounts.otp_providers.ParsGreenOtpSender",
        PARSGREEN_API_KEY="env-key",
        PARSGREEN_SIGNATURE="env-signature",
    )
    def test_disabled_database_row_fails_closed_even_when_env_is_enabled(self):
        PlatformOtpProviderConfig.objects.create(
            provider=PlatformOtpProviderConfig.Provider.PARSGREEN,
            enabled=False,
        )
        self.assertIsInstance(get_otp_sender(), DisabledOtpSender)

    @override_settings(
        CAF_INO_OTP_SENDER="apps.accounts.otp_providers.ParsGreenOtpSender",
        PARSGREEN_API_KEY="env-key",
        PARSGREEN_SIGNATURE="env-signature",
    )
    def test_missing_database_row_keeps_backward_compatible_env_fallback(self):
        sender = get_otp_sender()
        self.assertIsInstance(sender, ParsGreenOtpSender)
        self.assertEqual(sender.config.api_key, "env-key")

    @override_settings(
        CAF_INO_OTP_SENDER="apps.accounts.otp_providers.DisabledOtpSender",
    )
    def test_enabled_database_row_with_api_key_is_ready_without_signature(self):
        config = PlatformOtpProviderConfig.objects.create(
            provider=PlatformOtpProviderConfig.Provider.PARSGREEN,
            enabled=True,
        )
        config.set_api_key("configured-key")
        config.save()
        self.assertIsInstance(get_otp_sender(), ParsGreenOtpSender)
