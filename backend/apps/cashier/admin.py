from django.contrib import admin
from .models import CashRegister, CashShift, CashMovement, DailyClosing
for m in [CashRegister,CashShift,CashMovement]: admin.site.register(m)
