from django.contrib import admin
from .models import Hall,Table,TableSession,TableTransferLog
for model in [Hall,Table,TableSession,TableTransferLog]:
    try: admin.site.register(model)
    except admin.sites.AlreadyRegistered: pass
