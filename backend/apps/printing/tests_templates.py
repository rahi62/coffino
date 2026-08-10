from django.test import TestCase

from apps.businesses.models import Business, Branch
from apps.catalog.models import Product
from apps.orders.services import checkout_order
from apps.printing.models import PrintTemplate
from apps.printing.services import kitchen_ticket_payload, order_receipt_payload
from apps.kitchen.models import PreparationStation, KitchenTicket


class ReceiptTemplatePayloadTests(TestCase):
    def test_default_branch_template_is_included_in_a_receipt_payload(self):
        business = Business.objects.create(name='کافه آزمایشی')
        branch = Branch.objects.create(business=business, name='شعبه اصلی')
        product = Product.objects.create(branch=branch, name='نوشیدنی', price=1000)
        PrintTemplate.objects.create(
            branch=branch, name='فیش ۸۰ میلی‌متری', document_type=PrintTemplate.DocumentType.RECEIPT,
            header='سپاس از خرید شما', footer='به امید دیدار', show_tax=False, is_default=True,
        )
        order = checkout_order(
            branch=branch, items=[{'product': product, 'quantity': 1}], order_type='TAKEAWAY', payment_method='POS'
        )
        payload = order_receipt_payload(order)
        self.assertEqual(payload['template']['name'], 'فیش ۸۰ میلی‌متری')
        self.assertEqual(payload['template']['header'], 'سپاس از خرید شما')
        self.assertFalse(payload['template']['show_tax'])

    def test_default_kitchen_template_is_included_in_a_ticket_payload(self):
        business = Business.objects.create(name='کافه آزمایشی')
        branch = Branch.objects.create(business=business, name='شعبه اصلی')
        station = PreparationStation.objects.create(branch=branch, name='آشپزخانه', code='KITCHEN')
        product = Product.objects.create(branch=branch, name='نوشیدنی', price=1000, preparation_station=station)
        PrintTemplate.objects.create(
            branch=branch, name='تیکت آشپزخانه', document_type=PrintTemplate.DocumentType.KITCHEN,
            header='بدون پیاز', footer='کنترل نهایی', is_default=True,
        )
        order = checkout_order(
            branch=branch, items=[{'product': product, 'quantity': 1}], order_type='TAKEAWAY', payment_method='POS'
        )
        ticket = KitchenTicket.objects.get(order=order, station=station)
        payload = kitchen_ticket_payload(ticket)
        self.assertEqual(payload['template']['header'], 'بدون پیاز')
