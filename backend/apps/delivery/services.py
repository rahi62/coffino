from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import DeliveryZone,DeliveryAddress,CourierProfile,DeliveryAssignment
from apps.audit.services import log_action

def delivery_quote(zone,subtotal):
    subtotal=Decimal(str(subtotal))
    if not zone.is_active:raise ValueError('منطقه ارسال غیرفعال است')
    if subtotal<Decimal(zone.min_order_amount):raise ValueError('مبلغ سفارش کمتر از حداقل ارسال این منطقه است')
    fee=Decimal(zone.delivery_fee)
    if Decimal(zone.free_delivery_above)>0 and subtotal>=Decimal(zone.free_delivery_above):fee=Decimal('0')
    return fee

@transaction.atomic
def create_delivery_assignment(*,order,address,fee):
    if order.order_type!='DELIVERY':raise ValueError('Order از نوع DELIVERY نیست')
    if address.branch_id!=order.branch_id:raise ValueError('آدرس متعلق به شعبه نیست')
    obj,_=DeliveryAssignment.objects.get_or_create(order=order,defaults={'address':address,'zone':address.zone,'delivery_fee':fee})
    return obj

@transaction.atomic
def assign_courier(assignment,courier,*,user=None):
    x=DeliveryAssignment.objects.select_for_update(of=('self',)).select_related('order__branch').get(pk=assignment.pk)
    c=CourierProfile.objects.select_for_update().get(pk=courier.pk)
    if c.branch_id!=x.order.branch_id or not c.is_active:raise ValueError('پیک معتبر نیست')
    if x.order.status==x.order.Status.DRAFT:raise ValueError('سفارش هنوز در انتظار پرداخت/تأیید است')
    if x.status not in [DeliveryAssignment.Status.WAITING,DeliveryAssignment.Status.ASSIGNED]:raise ValueError('وضعیت ارسال قابل تخصیص نیست')
    x.courier=c;x.status=DeliveryAssignment.Status.ASSIGNED;x.assigned_at=timezone.now();x.save(update_fields=['courier','status','assigned_at','updated_at'])
    c.status=CourierProfile.Status.BUSY;c.save(update_fields=['status','updated_at'])
    log_action(actor=user,branch=x.order.branch,action='COURIER_ASSIGNED',entity=x,after={'courier':c.id})
    return x

@transaction.atomic
def update_delivery_status(assignment,status,*,user=None,note=''):
    # Lock only the assignment row. `courier` is nullable, so locking an outer-joined
    # related row is rejected by PostgreSQL (FOR UPDATE on nullable side of outer join).
    x=DeliveryAssignment.objects.select_for_update(of=('self',)).select_related('order__branch','courier').get(pk=assignment.pk)
    allowed={
      DeliveryAssignment.Status.ASSIGNED:{DeliveryAssignment.Status.PICKED_UP,DeliveryAssignment.Status.CANCELLED},
      DeliveryAssignment.Status.PICKED_UP:{DeliveryAssignment.Status.DELIVERED,DeliveryAssignment.Status.FAILED},
      DeliveryAssignment.Status.WAITING:{DeliveryAssignment.Status.CANCELLED},
    }
    if status not in allowed.get(x.status,set()):raise ValueError('تغییر وضعیت ارسال مجاز نیست')
    x.status=status;x.proof_note=note
    now=timezone.now()
    if status==DeliveryAssignment.Status.PICKED_UP:x.picked_up_at=now
    if status==DeliveryAssignment.Status.DELIVERED:
        x.delivered_at=now
        x.order.status=x.order.Status.COMPLETED;x.order.save(update_fields=['status','updated_at'])
        from apps.loyalty.services import earn_order_points
        earn_order_points(x.order)
        try:
            online=x.order.online_order;online.status='COMPLETED';online.save(update_fields=['status','updated_at'])
        except Exception:pass
    x.save()
    if x.courier and status in [DeliveryAssignment.Status.DELIVERED,DeliveryAssignment.Status.FAILED,DeliveryAssignment.Status.CANCELLED]:
        x.courier.status=CourierProfile.Status.AVAILABLE;x.courier.save(update_fields=['status','updated_at'])
    log_action(actor=user,branch=x.order.branch,action='DELIVERY_STATUS',entity=x,after={'status':status,'note':note})
    return x
