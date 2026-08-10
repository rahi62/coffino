from django.contrib import admin
from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils.translation import override

import config.urls  # Ensures admin auto-discovery and localization has run.
from config.admin_localization import FIELD_LABELS, MODEL_LABELS


class AdminLocalizationTests(SimpleTestCase):
    def test_registered_cafino_models_have_persian_labels(self):
        with override('fa'):
            models = [
                model for model in admin.site._registry
                if model._meta.app_label not in {'auth', 'contenttypes', 'sessions'}
            ]
            missing = [model._meta.label for model in models if model._meta.label not in MODEL_LABELS]
            self.assertEqual(missing, [])
            self.assertTrue(all(any('\u0600' <= char <= '\u06ff' for char in str(model._meta.verbose_name)) for model in models))

    def test_registered_cafino_fields_have_persian_label_mapping(self):
        models = [
            model for model in admin.site._registry
            if model._meta.app_label not in {'auth', 'contenttypes', 'sessions'}
        ]
        missing = sorted({field.name for model in models for field in model._meta.fields if field.name not in FIELD_LABELS})
        self.assertEqual(missing, [])

    def test_english_remains_available_for_future_locales(self):
        from apps.orders.models import Order
        with override('en'):
            self.assertEqual(str(Order._meta.verbose_name), 'order')

    def test_admin_defaults_to_persian_without_browser_language_detection(self):
        self.assertEqual(settings.LANGUAGE_CODE, 'fa')
        self.assertNotIn('django.middleware.locale.LocaleMiddleware', settings.MIDDLEWARE)

    def test_businesses_is_the_first_admin_section(self):
        from apps.accounts.models import User
        request = RequestFactory().get('/admin/')
        request.user = User(username='admin', is_active=True, is_staff=True, is_superuser=True)
        app_list = admin.site.get_app_list(request)
        self.assertEqual(app_list[0]['app_label'], 'businesses')
        self.assertEqual(
            [model['object_name'] for model in app_list[0]['models'][:3]],
            ['Business', 'Branch', 'BusinessModule'],
        )

    def test_default_admin_fieldset_keeps_an_empty_title(self):
        from apps.accounts.models import User
        from apps.businesses.models import Business
        request = RequestFactory().get('/admin/')
        request.user = User(username='admin', is_active=True, is_staff=True, is_superuser=True)
        fieldsets = admin.site._registry[Business].get_fieldsets(request)
        self.assertIsNone(fieldsets[0][0])


class AdminUserChangeFormTests(TestCase):
    def test_superuser_user_change_form_uses_keyword_only_change_argument(self):
        from apps.accounts.models import User
        user = User.objects.create_superuser(username='admin', password='safe-password')
        request = RequestFactory().get(f'/admin/accounts/user/{user.pk}/change/')
        request.user = user
        form = admin.site._registry[User].get_form(request, user, change=True)
        self.assertIn('business', form.base_fields)
