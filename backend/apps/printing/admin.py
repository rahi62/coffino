from django.contrib import admin
from .models import PrinterDevice, PrintTemplate, PrintJob
admin.site.register(PrinterDevice);admin.site.register(PrintTemplate);admin.site.register(PrintJob)
