from decimal import Decimal
from django.db import transaction
from django.db.models import F,Q
from django.utils import timezone
from .models import InventoryItem, InventoryLot, StockMovement

@transaction.atomic
def receive_stock(*,item,quantity,unit_cost,movement_type,reason='',reference_type='',reference_id='',lot_number='',expires_at=None,notes=''):
    quantity=Decimal(str(quantity));unit_cost=Decimal(str(unit_cost))
    if quantity<=0:raise ValueError('مقدار ورود موجودی باید مثبت باشد')
    item=InventoryItem.objects.select_for_update().get(pk=item.pk)
    old_qty=Decimal(item.current_stock);old_cost=Decimal(item.average_cost);new_qty=old_qty+quantity
    item.current_stock=new_qty
    item.average_cost=((old_qty*old_cost)+(quantity*unit_cost))/new_qty if new_qty else Decimal('0')
    item.save(update_fields=['current_stock','average_cost','updated_at'])
    lot=None
    if item.lot_tracked or lot_number or expires_at:
        lot_number=lot_number or f'{reference_type or "LOT"}-{reference_id or timezone.now().strftime("%Y%m%d%H%M%S%f")}'
        lot,created=InventoryLot.objects.select_for_update().get_or_create(
            item=item,lot_number=lot_number,
            defaults={'quantity_received':quantity,'quantity_remaining':quantity,'unit_cost':unit_cost,'expires_at':expires_at,'source_type':reference_type,'source_id':str(reference_id or ''),'notes':notes}
        )
        if not created:
            old_remaining=Decimal(lot.quantity_remaining);old_cost=Decimal(lot.unit_cost);new_remaining=old_remaining+quantity
            lot.quantity_received=Decimal(lot.quantity_received)+quantity
            lot.quantity_remaining=new_remaining
            lot.unit_cost=((old_remaining*old_cost)+(quantity*unit_cost))/new_remaining if new_remaining else unit_cost
            if expires_at:lot.expires_at=expires_at
            lot.save(update_fields=['quantity_received','quantity_remaining','unit_cost','expires_at','updated_at'])
    StockMovement.objects.create(item=item,movement_type=movement_type,quantity=quantity,unit_cost=unit_cost,reason=reason,reference_type=reference_type,reference_id=str(reference_id or ''),lot=lot)
    return {'item':item,'lot':lot,'quantity':quantity,'unit_cost':unit_cost}

@transaction.atomic
def consume_stock(*,item,quantity,movement_type,reason='',reference_type='',reference_id='',allow_expired=False,allow_blocked=False):
    quantity=Decimal(str(quantity))
    if quantity<=0:raise ValueError('مقدار مصرف موجودی باید مثبت باشد')
    item=InventoryItem.objects.select_for_update().get(pk=item.pk)
    if Decimal(item.current_stock)<quantity:raise ValueError(f'موجودی {item.name} کافی نیست')
    allocations=[];remaining=quantity
    if item.lot_tracked:
        qs=InventoryLot.objects.select_for_update().filter(item=item,quantity_remaining__gt=0)
        if not allow_blocked:qs=qs.filter(is_blocked=False)
        if not allow_expired:qs=qs.filter(Q(expires_at__isnull=True)|Q(expires_at__gt=timezone.now()))
        lots=list(qs.order_by(F('expires_at').asc(nulls_last=True),'received_at','id'))
        available=sum((Decimal(x.quantity_remaining) for x in lots),Decimal('0'))
        if available<quantity:raise ValueError(f'موجودی قابل‌مصرف Lot برای {item.name} کافی نیست؛ Lot منقضی/مسدود یا مغایرت موجودی را بررسی کنید')
        for lot in lots:
            if remaining<=0:break
            take=min(remaining,Decimal(lot.quantity_remaining))
            lot.quantity_remaining=Decimal(lot.quantity_remaining)-take;lot.save(update_fields=['quantity_remaining','updated_at'])
            StockMovement.objects.create(item=item,movement_type=movement_type,quantity=-take,unit_cost=lot.unit_cost,reason=reason,reference_type=reference_type,reference_id=str(reference_id or ''),lot=lot)
            allocations.append({'lot':lot,'quantity':take,'unit_cost':Decimal(lot.unit_cost)})
            remaining-=take
    else:
        cost=Decimal(item.average_cost)
        StockMovement.objects.create(item=item,movement_type=movement_type,quantity=-quantity,unit_cost=cost,reason=reason,reference_type=reference_type,reference_id=str(reference_id or ''))
        allocations.append({'lot':None,'quantity':quantity,'unit_cost':cost})
        remaining=Decimal('0')
    item.current_stock=Decimal(item.current_stock)-quantity;item.save(update_fields=['current_stock','updated_at'])
    return allocations

@transaction.atomic
def restore_reference_stock(*,reference_type,reference_id,return_reference_type,reason='Return'):
    if StockMovement.objects.filter(reference_type=return_reference_type,reference_id=str(reference_id)).exists():return []
    original=list(StockMovement.objects.select_for_update().select_related('item','lot').filter(reference_type=reference_type,reference_id=str(reference_id),quantity__lt=0))
    restored=[]
    for movement in original:
        qty=abs(Decimal(movement.quantity));item=InventoryItem.objects.select_for_update().get(pk=movement.item_id)
        item.current_stock=Decimal(item.current_stock)+qty;item.save(update_fields=['current_stock','updated_at'])
        lot=None
        if movement.lot_id:
            lot=InventoryLot.objects.select_for_update().get(pk=movement.lot_id)
            lot.quantity_remaining=Decimal(lot.quantity_remaining)+qty;lot.save(update_fields=['quantity_remaining','updated_at'])
        StockMovement.objects.create(item=item,movement_type=StockMovement.Type.RETURN,quantity=qty,unit_cost=movement.unit_cost,reason=reason,reference_type=return_reference_type,reference_id=str(reference_id),lot=lot)
        restored.append(movement)
    return restored
