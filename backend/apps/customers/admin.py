from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=('name','phone','phone_verified_at','branch','is_walk_in','updated_at')
    list_filter=('phone_verified_at','is_walk_in','branch')
    search_fields=('name','phone','phone_normalized')
