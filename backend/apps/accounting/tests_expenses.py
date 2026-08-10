from django.test import TestCase
from django.utils import timezone

from apps.accounting.models import BankAccount
from apps.accounting.services import create_expense
from apps.businesses.models import Business, Branch


class ExpenseBankAccountTests(TestCase):
    def setUp(self):
        business = Business.objects.create(name='کسب‌وکار آزمایشی')
        self.branch = Branch.objects.create(business=business, name='شعبه اصلی')
        self.other_branch = Branch.objects.create(business=business, name='شعبه دوم')

    def test_card_expense_is_linked_to_its_branch_account(self):
        account = BankAccount.objects.create(branch=self.branch, title='کارت هزینه')
        expense = create_expense(
            branch=self.branch, title='هزینه آزمایشی', amount=1000, occurred_at=timezone.now(),
            payment_method='POS', bank_account=account,
        )
        self.assertEqual(expense.bank_account_id, account.id)

    def test_foreign_account_cannot_be_used_for_an_expense(self):
        account = BankAccount.objects.create(branch=self.other_branch, title='کارت شعبه دوم')
        with self.assertRaisesMessage(ValueError, 'برای این شعبه'):
            create_expense(
                branch=self.branch, title='هزینه آزمایشی', amount=1000, occurred_at=timezone.now(),
                payment_method='POS', bank_account=account,
            )
