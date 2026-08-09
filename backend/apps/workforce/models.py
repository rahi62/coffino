from django.db import models
from apps.core.models import TimeStampedModel
class StaffSchedule(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='staff_schedules')
    user=models.ForeignKey('accounts.User',on_delete=models.CASCADE,related_name='staff_schedules')
    work_date=models.DateField()
    starts_at=models.TimeField()
    ends_at=models.TimeField()
    notes=models.CharField(max_length=250,blank=True)
    class Meta: unique_together=('user','work_date','starts_at')
class Attendance(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='attendance')
    user=models.ForeignKey('accounts.User',on_delete=models.CASCADE,related_name='attendance')
    clock_in=models.DateTimeField()
    clock_out=models.DateTimeField(null=True,blank=True)
    source=models.CharField(max_length=30,default='APP')
    note=models.CharField(max_length=250,blank=True)
    def duration_minutes(self):
        if not self.clock_out:return None
        return int((self.clock_out-self.clock_in).total_seconds()//60)
