from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.accounts.admin import PlatformOtpProviderConfigAdmin, PlatformOtpProviderConfigForm
from apps.accounts.models import PlatformOtpProviderConfig
from apps.accounts.otp_providers import OtpDeliveryResult


User = get_user_model()


class PlatformOtpProviderAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlatformOtpProviderConfigAdmin(PlatformOtpProviderConfig, self.site)
        self.superuser = User.objects.create_superuser(
            username="otp-admin",
            email="otp-admin@example.test",
            password="Admin-Strong-2026!",
        )

    def make_config(self):
        config = PlatformOtpProviderConfig.objects.create(
            provider=PlatformOtpProviderConfig.Provider.PARSGREEN,
            enabled=True,
            api_base_url="https://sms.parsgreen.ir",
            add_name=True,
            timeout_seconds=10,
            test_mobile="09123456789",
        )
        config.set_api_key("stored-api-key")
        config.set_signature("stored-signature")
        config.save()
        return config

    def test_edit_form_blank_secret_fields_preserve_existing_credentials(self):
        config = self.make_config()
        original_key = config.api_key_encrypted
        original_signature = config.signature_encrypted

        form = PlatformOtpProviderConfigForm(
            data={
                "provider": PlatformOtpProviderConfig.Provider.PARSGREEN,
                "enabled": "on",
                "api_base_url": "https://sms.parsgreen.ir",
                "api_key": "",
                "signature": "",
                "add_name": "on",
                "timeout_seconds": "10",
                "test_mobile": "0912 345 6789",
            },
            instance=config,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertEqual(saved.api_key_encrypted, original_key)
        self.assertEqual(saved.signature_encrypted, original_signature)
        self.assertEqual(saved.get_api_key(), "stored-api-key")
        self.assertEqual(saved.get_signature(), "stored-signature")
        self.assertEqual(saved.test_mobile, "09123456789")

    def test_admin_form_never_initializes_secret_fields_with_plaintext(self):
        config = self.make_config()
        form = PlatformOtpProviderConfigForm(instance=config)

        self.assertEqual(form["api_key"].value(), None)
        self.assertEqual(form["signature"].value(), None)
        self.assertNotIn("stored-api-key", form.as_p())
        self.assertNotIn("stored-signature", form.as_p())

    def test_http_provider_endpoint_is_rejected(self):
        form = PlatformOtpProviderConfigForm(
            data={
                "provider": PlatformOtpProviderConfig.Provider.PARSGREEN,
                "enabled": "on",
                "api_base_url": "http://sms.example.test",
                "api_key": "key",
                "signature": "signature",
                "add_name": "on",
                "timeout_seconds": "10",
                "test_mobile": "09123456789",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("api_base_url", form.errors)

    def test_timeout_outside_safe_range_is_rejected(self):
        form = PlatformOtpProviderConfigForm(
            data={
                "provider": PlatformOtpProviderConfig.Provider.PARSGREEN,
                "enabled": "on",
                "api_base_url": "https://sms.parsgreen.ir",
                "api_key": "key",
                "signature": "signature",
                "add_name": "on",
                "timeout_seconds": "600",
                "test_mobile": "09123456789",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("timeout_seconds", form.errors)

    def test_only_superuser_can_manage_global_provider(self):
        request = RequestFactory().get("/admin/accounts/platformotpproviderconfig/")
        request.user = self.superuser
        self.assertTrue(self.admin.has_module_permission(request))
        self.assertTrue(self.admin.has_view_permission(request))
        self.assertTrue(self.admin.has_change_permission(request))

        business_user = User.objects.create_user(
            username="staff-no-global-otp",
            password="Staff-Strong-2026!",
            is_staff=True,
            is_superuser=False,
        )
        # The custom User model requires a tenant for non-superusers; avoid saving
        # an invalid user and assert with an unsaved staff-like principal instead.
        business_user.delete()
        limited = Mock(is_superuser=False)
        request.user = limited
        self.assertFalse(self.admin.has_module_permission(request))
        self.assertFalse(self.admin.has_view_permission(request))
        self.assertFalse(self.admin.has_change_permission(request))

    @patch("apps.accounts.admin.sender_from_platform_config")
    def test_admin_test_action_uses_test_mobile_without_exposing_code(self, sender_factory):
        config = self.make_config()
        sender = sender_factory.return_value
        sender.send.return_value = OtpDeliveryResult(accepted=True, provider_code="0")
        self.admin.message_user = Mock()

        request = RequestFactory().post("/admin/accounts/platformotpproviderconfig/")
        request.user = self.superuser
        self.admin.send_test_otp(request, PlatformOtpProviderConfig.objects.filter(pk=config.pk))

        sender.send.assert_called_once()
        kwargs = sender.send.call_args.kwargs
        self.assertEqual(kwargs["mobile"], "09123456789")
        self.assertRegex(kwargs["code"], r"^\d{6}$")
        self.assertEqual(len(kwargs["correlation_id"]), 36)

        visible_messages = " ".join(str(call.args[1]) for call in self.admin.message_user.call_args_list)
        self.assertNotIn(kwargs["code"], visible_messages)
