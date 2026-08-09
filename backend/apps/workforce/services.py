from django.db import transaction
from django.utils import timezone
from .models import Attendance
@transaction.atomic
def clock_in(user,branch):
    if Attendance.objects.filter(user=user,clock_out__isnull=True).exists():raise ValueError('حضور باز دارید')
    return Attendance.objects.create(branch=branch,user=user,clock_in=timezone.now())
@transaction.atomic
def clock_out(user):
    a=Attendance.objects.select_for_update().filter(user=user,clock_out__isnull=True).order_by('-clock_in').first()
    if not a:raise ValueError('حضور بازی پیدا نشد')
    a.clock_out=timezone.now();a.save(update_fields=['clock_out','updated_at']);return a
