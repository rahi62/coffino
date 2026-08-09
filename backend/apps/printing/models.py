from django.db import models
from apps.core.models import TimeStampedModel

class PrinterDevice(TimeStampedModel):
    class Kind(models.TextChoices):
        RECEIPT='RECEIPT','فیش'
        KITCHEN='KITCHEN','آشپزخانه'
        BAR='BAR','بار'
        GENERAL='GENERAL','عمومی'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='printers')
    name=models.CharField(max_length=120)
    system_name=models.CharField(max_length=250,blank=True)
    kind=models.CharField(max_length=16,choices=Kind.choices,default=Kind.RECEIPT)
    paper_width=models.PositiveIntegerField(default=80)
    is_active=models.BooleanField(default=True)
    def __str__(self):return self.name

class PrintTemplate(TimeStampedModel):
    class DocumentType(models.TextChoices):
        RECEIPT='RECEIPT','رسید مشتری'
        KITCHEN='KITCHEN','تیکت آشپزخانه'
        BAR='BAR','تیکت بار'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='print_templates')
    name=models.CharField(max_length=120)
    document_type=models.CharField(max_length=16,choices=DocumentType.choices)
    header=models.TextField(blank=True)
    footer=models.TextField(blank=True)
    show_tax=models.BooleanField(default=True)
    show_service_charge=models.BooleanField(default=True)
    show_customer=models.BooleanField(default=True)
    is_default=models.BooleanField(default=False)

class PrintJob(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING='PENDING','در انتظار'
        PRINTED='PRINTED','چاپ شده'
        FAILED='FAILED','خطا'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='print_jobs')
    printer=models.ForeignKey(PrinterDevice,null=True,blank=True,on_delete=models.SET_NULL,related_name='jobs')
    document_type=models.CharField(max_length=16)
    entity_type=models.CharField(max_length=40,blank=True)
    entity_id=models.CharField(max_length=64,blank=True)
    payload=models.JSONField(default=dict)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING)
    error=models.TextField(blank=True)
    printed_at=models.DateTimeField(null=True,blank=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
