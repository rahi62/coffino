from django.contrib import admin
from .models import PaymentGatewayConfig,GatewayIntent
admin.site.register(PaymentGatewayConfig);admin.site.register(GatewayIntent)
