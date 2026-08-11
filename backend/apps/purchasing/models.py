from django.db import models
from apps.core.models import TimeStampedModel
class PurchaseInvoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT="DRAFT","پیش نویس"; POSTED="POSTED","ثبت شده"; CANCELLED="CANCELLED","لغو"
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="purchase_invoices")
    supplier=models.ForeignKey("suppliers.Supplier",on_delete=models.PROTECT,related_name="invoices")
    invoice_number=models.CharField(max_length=80,blank=True)
    invoice_date=models.DateField()
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT)
    total_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    paid_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    notes=models.TextField(blank=True)
    created_by=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL)
    @property
    def balance_due(self): return self.total_amount-self.paid_amount

class PurchaseItem(TimeStampedModel):
    invoice=models.ForeignKey(PurchaseInvoice,on_delete=models.CASCADE,related_name="items")
    inventory_item=models.ForeignKey("inventory.InventoryItem",on_delete=models.PROTECT,related_name="purchase_items")
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2)
    line_total=models.DecimalField(max_digits=14,decimal_places=0)
    lot_number=models.CharField(max_length=100,blank=True)
    expires_at=models.DateTimeField(null=True,blank=True)

class SupplierPayment(TimeStampedModel):
    supplier=models.ForeignKey("suppliers.Supplier",on_delete=models.PROTECT,related_name="payments")
    purchase_invoice=models.ForeignKey(PurchaseInvoice,null=True,blank=True,on_delete=models.SET_NULL,related_name="supplier_payments")
    bank_account=models.ForeignKey("accounting.BankAccount",null=True,blank=True,on_delete=models.SET_NULL,related_name="supplier_payments")
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    method=models.CharField(max_length=24,default="CASH")
    reference=models.CharField(max_length=120,blank=True)
    paid_at=models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
