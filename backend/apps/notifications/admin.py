from django.contrib import admin
from .models import SmsProviderConfig,Notification,PushProviderConfig,PushSubscription
for model in [SmsProviderConfig,Notification,PushProviderConfig,PushSubscription]:
    try: admin.site.register(model)
    except admin.sites.AlreadyRegistered: pass
