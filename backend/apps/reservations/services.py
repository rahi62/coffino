from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Reservation
from apps.dining.models import Table,TableSession
from apps.audit.services import log_action

def _overlap_qs(branch,table,reserved_for,duration_minutes,exclude=None):
    start=reserved_for;end=reserved_for+timedelta(minutes=duration_minutes)
    qs=Reservation.objects.filter(branch=branch,table=table,status__in=[Reservation.Status.PENDING,Reservation.Status.CONFIRMED,Reservation.Status.SEATED])
    if exclude:qs=qs.exclude(pk=exclude.pk)
    conflicts=[]
    for x in qs:
        x_end=x.reserved_for+timedelta(minutes=x.duration_minutes)
        if x.reserved_for<end and x_end>start:conflicts.append(x)
    return conflicts

@transaction.atomic
def create_reservation(*,branch,customer_name,phone,party_size,reserved_for,duration_minutes=90,table=None,customer=None,source='STAFF',notes='',user=None):
    if isinstance(reserved_for,str):reserved_for=parse_datetime(reserved_for)
    if not reserved_for:raise ValueError('زمان رزرو نامعتبر است')
    if timezone.is_naive(reserved_for):reserved_for=timezone.make_aware(reserved_for,timezone.get_current_timezone())
    if party_size<=0:raise ValueError('تعداد نفرات نامعتبر است')
    if table and table.hall.branch_id!=branch.id:raise ValueError('میز متعلق به شعبه نیست')
    if table and table.capacity<party_size:raise ValueError('ظرفیت میز کمتر از تعداد مهمان است')
    if table and _overlap_qs(branch,table,reserved_for,duration_minutes):raise ValueError('این میز در بازه انتخاب‌شده رزرو است')
    r=Reservation.objects.create(branch=branch,table=table,customer=customer,customer_name=customer_name,phone=phone,party_size=party_size,reserved_for=reserved_for,duration_minutes=duration_minutes,source=source,notes=notes,created_by=user)
    if table:table.status=Table.Status.RESERVED;table.save(update_fields=['status','updated_at'])
    log_action(actor=user,branch=branch,action='RESERVATION_CREATED',entity=r,after={'reserved_for':reserved_for.isoformat(),'party_size':party_size})
    return r

@transaction.atomic
def seat_reservation(reservation,*,user=None):
    # Lock Reservation itself only. `table` is nullable, so PostgreSQL cannot apply
    # FOR UPDATE to the LEFT JOIN. The chosen Table row is locked explicitly below.
    r=Reservation.objects.select_for_update(of=('self',)).select_related('table').get(pk=reservation.pk)
    if r.status not in [Reservation.Status.PENDING,Reservation.Status.CONFIRMED]:raise ValueError('رزرو قابل پذیرش نیست')
    table=r.table
    if not table:raise ValueError('برای رزرو میز تعیین نشده است')
    table=Table.objects.select_for_update().get(pk=table.pk)
    if table.sessions.filter(is_open=True).exists():raise ValueError('میز در حال حاضر مشغول است')
    session=TableSession.objects.create(table=table,customer_count=r.party_size,opened_by=user)
    table.status=Table.Status.OCCUPIED;table.save(update_fields=['status','updated_at'])
    r.status=Reservation.Status.SEATED;r.seated_session=session;r.save(update_fields=['status','seated_session','updated_at'])
    log_action(actor=user,branch=r.branch,action='RESERVATION_SEATED',entity=r,after={'session':session.id})
    return r
