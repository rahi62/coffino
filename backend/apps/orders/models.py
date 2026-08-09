from django.db import models
from apps.core.models import TimeStampedModel

class Order(TimeStampedModel):
    class Type(models.TextChoices):
        DINE_IN="DINE_IN","داخل سالن"
        TAKEAWAY="TAKEAWAY","بیرون‌بر"
        PICKUP="PICKUP","تحویل حضوری"
        DELIVERY="DELIVERY","ارسال"
        DRIVE_THROUGH="DRIVE_THROUGH","دریافت خودرو"
        CATERING="CATERING","کترینگ"
    class Status(models.TextChoices):
        DRAFT="DRAFT","پیش‌نویس"
        CONFIRMED="CONFIRMED","تأیید شده"
        IN_PROGRESS="IN_PROGRESS","در حال آماده‌سازی"
        READY="READY","آماده"
        COMPLETED="COMPLETED","تکمیل"
        CANCELLED="CANCELLED","لغو"
    class PaymentStatus(models.TextChoices):
        UNPAID="UNPAID","پرداخت نشده"
        PARTIAL="PARTIALLY_PAID","بخشی/تسویه ناقص"
        PAID="PAID","پرداخت شده"
        PARTIALLY_REFUNDED="PARTIALLY_REFUNDED","بخشی برگشت"
        REFUNDED="REFUNDED","برگشت کامل" 
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='orders')
    order_number=models.PositiveIntegerField()
    order_type=models.CharField(max_length=24,choices=Type.choices)
    status=models.CharField(max_length=24,choices=Status.choices,default=Status.DRAFT)
    payment_status=models.CharField(max_length=24,choices=PaymentStatus.choices,default=PaymentStatus.UNPAID)
    customer=models.ForeignKey('customers.Customer',null=True,blank=True,on_delete=models.SET_NULL)
    table_session=models.ForeignKey('dining.TableSession',null=True,blank=True,on_delete=models.SET_NULL,related_name='orders')
    subtotal=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    discount_total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    discount_rule=models.ForeignKey('discounts.DiscountRule',null=True,blank=True,on_delete=models.SET_NULL,related_name='orders')
    discount_reason=models.CharField(max_length=250,blank=True)
    tax_total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    service_charge_total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    delivery_fee_total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    grand_total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    notes=models.TextField(blank=True)
    idempotency_key=models.CharField(max_length=100,null=True,blank=True)
    idempotency_fingerprint=models.CharField(max_length=64,blank=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
    class Meta:
        unique_together=('branch','order_number')
        constraints=[models.UniqueConstraint(fields=['branch','idempotency_key'],condition=models.Q(idempotency_key__isnull=False),name='uniq_order_idempotency_per_branch')]
        ordering=['-created_at']

class OrderItem(TimeStampedModel):
    class Status(models.TextChoices):
        NEW="NEW","جدید"
        PREPARING="PREPARING","در حال آماده‌سازی"
        READY="READY","آماده"
        HANDED_OVER="HANDED_OVER","تحویل"
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey('catalog.Product',on_delete=models.PROTECT)
    product_name=models.CharField(max_length=160)
    quantity=models.DecimalField(max_digits=10,decimal_places=3,default=1)
    unit_price=models.DecimalField(max_digits=14,decimal_places=0)
    unit_cost_snapshot=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    line_total=models.DecimalField(max_digits=14,decimal_places=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.NEW)
    notes=models.CharField(max_length=250,blank=True)

class ApprovalRequest(TimeStampedModel):
    class Type(models.TextChoices):
        DISCOUNT='DISCOUNT','تخفیف'
        VOID='VOID','لغو سفارش'
    class Status(models.TextChoices):
        PENDING='PENDING','در انتظار'
        APPROVED='APPROVED','تأیید'
        REJECTED='REJECTED','رد'
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='approval_requests')
    request_type=models.CharField(max_length=20,choices=Type.choices)
    requested_by=models.ForeignKey('accounts.User',on_delete=models.PROTECT,related_name='requested_approvals')
    approved_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.PROTECT,related_name='decided_approvals')
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING)
    amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    percent=models.DecimalField(max_digits=6,decimal_places=2,default=0)
    reason=models.CharField(max_length=250)
    decided_at=models.DateTimeField(null=True,blank=True)
