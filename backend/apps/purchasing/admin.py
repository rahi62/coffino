from django.contrib import admin
from .models import PurchaseInvoice, PurchaseItem, SupplierPayment
for m in [PurchaseInvoice, PurchaseItem, SupplierPayment]: admin.site.register(m)
