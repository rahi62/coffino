from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.accounting.models import FiscalSettings
from apps.accounting.pricing import calculate_fiscal_totals

class FiscalPricingTests(TestCase):
    def test_tax_and_service_are_calculated_after_discount(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        FiscalSettings.objects.create(branch=br,tax_enabled=True,tax_rate=10,service_charge_enabled=True,service_charge_rate=10,service_charge_order_types=['DINE_IN'])
        x=calculate_fiscal_totals(branch=br,order_type='DINE_IN',subtotal=Decimal('1000'),discount=Decimal('100'))
        self.assertEqual(x['service_charge_total'],Decimal('90'))
        self.assertEqual(x['tax_total'],Decimal('99'))
        self.assertEqual(x['grand_total'],Decimal('1089'))

    def test_takeaway_can_skip_service_charge(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        FiscalSettings.objects.create(branch=br,service_charge_enabled=True,service_charge_rate=10,service_charge_order_types=['DINE_IN'])
        x=calculate_fiscal_totals(branch=br,order_type='TAKEAWAY',subtotal=Decimal('1000'),discount=0)
        self.assertEqual(x['service_charge_total'],Decimal('0'))
