from django.test import TestCase

from apps.businesses.models import Branch, Business
from apps.dining.admin import HallAdminForm, TableAdminForm
from apps.dining.models import Hall


class DiningAdminScopeTests(TestCase):
    def setUp(self):
        self.business_a = Business.objects.create(name='کسب‌وکار اول')
        self.business_b = Business.objects.create(name='کسب‌وکار دوم')
        self.branch_a = Branch.objects.create(business=self.business_a, name='شعبه اول')
        self.branch_b = Branch.objects.create(business=self.business_b, name='شعبه دوم')
        self.hall_a = Hall.objects.create(branch=self.branch_a, name='سالن اول')
        self.hall_b = Hall.objects.create(branch=self.branch_b, name='سالن دوم')

    def test_hall_form_rejects_branch_from_another_business(self):
        form = HallAdminForm(data={'business': self.business_a.pk, 'branch': self.branch_b.pk, 'name': 'سالن نادرست'})
        self.assertFalse(form.is_valid())
        self.assertIn('branch', form.errors)

    def test_table_form_rejects_hall_from_another_business(self):
        form = TableAdminForm(data={
            'business': self.business_a.pk, 'hall': self.hall_b.pk,
            'number': '۱', 'capacity': 4, 'status': 'FREE',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('hall', form.errors)

    def test_hall_options_include_their_business_scope(self):
        form = TableAdminForm()
        self.assertIn(f'data-business-id="{self.business_a.pk}"', str(form['hall']))
