from django.contrib import admin
from .models import BankAccount, FiscalSettings, ExpenseCategory, Expense, FixedOverhead
for m in [BankAccount, ExpenseCategory, Expense, FixedOverhead]: admin.site.register(m)

try:
    admin.site.register(FiscalSettings)
except admin.sites.AlreadyRegistered:
    pass
