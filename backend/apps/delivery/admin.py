from django.contrib import admin
from .models import DeliveryZone,DeliveryAddress,CourierProfile,DeliveryAssignment
for m in [DeliveryZone,DeliveryAddress,CourierProfile,DeliveryAssignment]:admin.site.register(m)
