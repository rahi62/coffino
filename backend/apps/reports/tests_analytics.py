from django.test import TestCase

from apps.businesses.models import Business, Branch
from apps.catalog.models import Product
from apps.orders.services import checkout_order
from apps.reports.analytics import sales_analytics


class SalesAnalyticsTests(TestCase):
    def test_sales_summary_and_groupings_are_returned(self):
        business = Business.objects.create(name='کافهٔ آزمایشی')
        branch = Branch.objects.create(business=business, name='شعبهٔ اصلی')
        product = Product.objects.create(branch=branch, name='لاته', price=125000)
        order = checkout_order(
            branch=branch,
            items=[{'product': product, 'quantity': 2}],
            order_type='TAKEAWAY',
            payment_method='POS',
        )

        report = sales_analytics(branch)

        self.assertEqual(report['summary']['orders'], 1)
        self.assertEqual(report['summary']['gross_sales'], order.grand_total)
        self.assertEqual(report['summary']['items'], 2)
        self.assertEqual(report['by_order_type'][0]['order_type'], 'TAKEAWAY')
        self.assertEqual(report['by_day'][0]['orders'], 1)
