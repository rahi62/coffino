from django.test import TestCase

from apps.accounting.models import BankAccount
from apps.businesses.models import Business, Branch
from apps.catalog.models import Product
from apps.orders.services import checkout_order
from apps.payments.models import Payment


class BankAccountPaymentTests(TestCase):
    def setUp(self):
        business = Business.objects.create(name='کسب‌وکار آزمایشی')
        self.branch = Branch.objects.create(business=business, name='شعبه اصلی')
        self.other_branch = Branch.objects.create(business=business, name='شعبه دوم')
        self.product = Product.objects.create(branch=self.branch, name='نوشیدنی', price=1000)

    def test_pos_payment_keeps_the_selected_branch_account(self):
        account = BankAccount.objects.create(
            branch=self.branch, title='کارت‌خوان صندوق', bank_name='نمونه', identifier_last4='1234'
        )
        order = checkout_order(
            branch=self.branch, items=[{'product': self.product, 'quantity': 1}], order_type='TAKEAWAY',
            payments=[{'method': Payment.Method.POS, 'amount': 1000, 'bank_account': account.id}],
        )
        payment = order.payments.get()
        self.assertEqual(payment.bank_account_id, account.id)

    def test_a_bank_account_from_another_branch_is_rejected(self):
        foreign_account = BankAccount.objects.create(branch=self.other_branch, title='کارت‌خوان شعبه دوم')
        with self.assertRaisesMessage(ValueError, 'برای این شعبه'):
            checkout_order(
                branch=self.branch, items=[{'product': self.product, 'quantity': 1}], order_type='TAKEAWAY',
                payments=[{'method': Payment.Method.POS, 'amount': 1000, 'bank_account': foreign_account.id}],
            )
