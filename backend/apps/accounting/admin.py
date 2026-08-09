from django.contrib import admin
from .models import FiscalSettings, ExpenseCategory, Expense, FixedOverhead
for m in [ExpenseCategory, Expense, FixedOverhead]: admin.site.register(m)

try:
    admin.site.register(FiscalSettings)
except admin.sites.AlreadyRegistered:
    pass
