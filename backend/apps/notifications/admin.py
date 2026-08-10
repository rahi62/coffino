from django.contrib import admin
from .models import PagerProviderConfig,SmsProviderConfig,Notification,PushProviderConfig,PushSubscription
for model in [SmsProviderConfig,PagerProviderConfig,Notification,PushProviderConfig,PushSubscription]:
    try: admin.site.register(model)
    except admin.sites.AlreadyRegistered: pass
