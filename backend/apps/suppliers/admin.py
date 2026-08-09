from django.contrib import admin
from .models import Supplier
for m in [Supplier]: admin.site.register(m)
