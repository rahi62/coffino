from decimal import Decimal

from django.test import TestCase

from apps.accounting.models import BankAccount
from apps.businesses.models import Branch, Business
from apps.purchasing.models import PurchaseInvoice, SupplierPayment
from apps.purchasing.services import pay_supplier
from apps.suppliers.models import Supplier


class SupplierPaymentBankAccountTests(TestCase):
    def setUp(self):
        business = Business.objects.create(name="کسب‌وکار آزمایشی")
        self.branch = Branch.objects.create(business=business, name="شعبهٔ اصلی")
        self.other_branch = Branch.objects.create(business=business, name="شعبهٔ دوم")
        self.supplier = Supplier.objects.create(branch=self.branch, name="تأمین‌کننده")
        self.invoice = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_date="2026-08-11",
            status=PurchaseInvoice.Status.POSTED,
            total_amount=Decimal("100000"),
        )

    def test_payment_records_selected_branch_bank_account(self):
        account = BankAccount.objects.create(branch=self.branch, title="کارت خرید")

        payment = pay_supplier(
            invoice=self.invoice,
            amount=Decimal("100000"),
            method="POS",
            bank_account=account,
        )

        self.assertEqual(payment.bank_account_id, account.id)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal("100000"))

    def test_payment_rejects_bank_account_from_another_branch(self):
        account = BankAccount.objects.create(branch=self.other_branch, title="کارت شعبهٔ دوم")

        with self.assertRaisesMessage(ValueError, "برای این شعبه فعال نیست"):
            pay_supplier(
                invoice=self.invoice,
                amount=Decimal("100000"),
                method="POS",
                bank_account=account,
            )

        self.assertEqual(SupplierPayment.objects.count(), 0)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal("0"))
