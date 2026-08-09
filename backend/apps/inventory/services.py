from decimal import Decimal
from django.db import transaction
from .models import InventoryItem, StockMovement
from .lot_services import consume_stock, receive_stock, restore_reference_stock



@transaction.atomic
def consume_order_inventory(order):
    for oi in order.items.select_related("product__stock_item").prefetch_related("product__recipe_items__inventory_item"):
        product=oi.product;total_cost=Decimal('0')
        if product.stock_item_id:
            item=InventoryItem.objects.get(pk=product.stock_item_id)
            if item.branch_id!=order.branch_id:raise ValueError('Finished Good متعلق به شعبه سفارش نیست')
            allocations=consume_stock(item=item,quantity=oi.quantity,movement_type=StockMovement.Type.SALE,reason=f"Order #{order.order_number}",reference_type='OrderItem',reference_id=oi.id)
            total_cost=sum((a['quantity']*a['unit_cost'] for a in allocations),Decimal('0'))
        else:
            for recipe in product.recipe_items.all():
                qty=Decimal(str(recipe.quantity))*Decimal(str(oi.quantity))
                allocations=consume_stock(item=recipe.inventory_item,quantity=qty,movement_type=StockMovement.Type.SALE,reason=f"Order #{order.order_number}",reference_type='OrderItem',reference_id=oi.id)
                total_cost+=sum((a['quantity']*a['unit_cost'] for a in allocations),Decimal('0'))
        if Decimal(oi.quantity)>0:
            oi.unit_cost_snapshot=total_cost/Decimal(oi.quantity);oi.save(update_fields=['unit_cost_snapshot','updated_at'])


@transaction.atomic
def restore_order_inventory(order, reason='Order void'):
    restored=[]
    for oi in order.items.all():
        restored.extend(restore_reference_stock(reference_type='OrderItem',reference_id=oi.id,return_reference_type='OrderItemVoid',reason=reason))
    return restored

@transaction.atomic
def record_waste(*,item,quantity,reason,user=None,note=''):
    from .models import WasteRecord
    from apps.audit.services import log_action
    quantity=Decimal(str(quantity))
    if quantity<=0:raise ValueError('مقدار ضایعات باید مثبت باشد')
    locked=InventoryItem.objects.select_for_update().get(pk=item.pk)
    allocations=consume_stock(item=locked,quantity=quantity,movement_type=StockMovement.Type.WASTE,reason=reason,reference_type='WasteRecordPending',reference_id=f'{locked.id}-{user.id if user else 0}',allow_expired=True,allow_blocked=True)
    total=sum((x['quantity']*x['unit_cost'] for x in allocations),Decimal('0'));cost=(total/quantity) if quantity else Decimal('0')
    rec=WasteRecord.objects.create(branch=locked.branch,item=locked,quantity=quantity,unit_cost=cost,total_cost=total,reason=reason,note=note,created_by=user)
    StockMovement.objects.filter(reference_type='WasteRecordPending',reference_id=f'{locked.id}-{user.id if user else 0}').update(reference_type='WasteRecord',reference_id=str(rec.id))
    log_action(actor=user,branch=locked.branch,action='WASTE_RECORDED',entity=rec,description=reason,after={'item':locked.name,'quantity':str(quantity),'cost':str(rec.total_cost)})
    return rec

@transaction.atomic
def create_inventory_count(*,branch,title,lines,user=None,notes=''):
    from .models import InventoryCount, InventoryCountLine
    count=InventoryCount.objects.create(branch=branch,title=title,counted_by=user,notes=notes)
    seen=set()
    for row in lines:
        item=InventoryItem.objects.select_for_update().get(pk=row['item'].pk)
        if item.branch_id!=branch.id: raise ValueError('ماده اولیه متعلق به این شعبه نیست')
        if item.id in seen: raise ValueError('آیتم تکراری در شمارش')
        seen.add(item.id)
        counted=Decimal(str(row['counted_quantity']))
        if counted<0: raise ValueError('موجودی شمارش‌شده نمی‌تواند منفی باشد')
        system=Decimal(item.current_stock); variance=counted-system; cost=Decimal(item.average_cost)
        InventoryCountLine.objects.create(
            count=count,item=item,system_quantity=system,counted_quantity=counted,
            variance=variance,unit_cost_snapshot=cost,variance_value=variance*cost
        )
    return count

@transaction.atomic
def post_inventory_count(count,*,user=None):
    from django.utils import timezone
    from .models import InventoryCount
    from apps.audit.services import log_action
    count=InventoryCount.objects.select_for_update().prefetch_related('lines__item').get(pk=count.pk)
    if count.status!=InventoryCount.Status.DRAFT: raise ValueError('این شمارش قابل ثبت نیست')
    for line in count.lines.all():
        item=InventoryItem.objects.select_for_update().get(pk=line.item_id)
        live=Decimal(item.current_stock); snapshot=Decimal(line.system_quantity); counted=Decimal(line.counted_quantity)
        if live!=snapshot:
            raise ValueError(f'پس از شمارش برای {item.name} حرکت انبار ثبت شده است؛ این شمارش باید تازه‌سازی شود')
        variance=counted-snapshot
        line.variance=variance;line.unit_cost_snapshot=item.average_cost
        line.variance_value=variance*Decimal(item.average_cost)
        line.save(update_fields=['variance','unit_cost_snapshot','variance_value','updated_at'])
        if variance:
            if item.lot_tracked:raise ValueError(f'برای {item.name} که Lot-tracked است، مغایرت باید در سطح Lot اصلاح شود')
            item.current_stock=counted;item.save(update_fields=['current_stock','updated_at'])
            StockMovement.objects.create(
                item=item,movement_type=StockMovement.Type.ADJUSTMENT,quantity=variance,
                unit_cost=item.average_cost,reason=f'Physical Count: {count.title}',
                reference_type='InventoryCount',reference_id=str(count.id)
            )
    count.status=InventoryCount.Status.POSTED;count.posted_by=user;count.posted_at=timezone.now()
    count.save(update_fields=['status','posted_by','posted_at','updated_at'])
    log_action(actor=user,branch=count.branch,action='INVENTORY_COUNT_POSTED',entity=count,description=count.title,after={'lines':count.lines.count()})
    return count

@transaction.atomic
def post_stock_transfer(transfer,*,user=None):
    from django.utils import timezone
    from .models import StockTransfer
    from apps.audit.services import log_action
    transfer=StockTransfer.objects.select_for_update().prefetch_related('lines__source_item','lines__destination_item').get(pk=transfer.pk)
    if transfer.status!=StockTransfer.Status.DRAFT: raise ValueError('این انتقال قابل ثبت نیست')
    if transfer.source_branch_id==transfer.destination_branch_id: raise ValueError('شعبه مبدا و مقصد یکسان است')
    if not transfer.lines.exists(): raise ValueError('انتقال بدون آیتم است')
    for line in transfer.lines.all():
        qty=Decimal(line.quantity)
        if qty<=0:raise ValueError('مقدار انتقال باید مثبت باشد')
        src=InventoryItem.objects.select_for_update().get(pk=line.source_item_id);dst=InventoryItem.objects.select_for_update().get(pk=line.destination_item_id)
        if src.branch_id!=transfer.source_branch_id or dst.branch_id!=transfer.destination_branch_id:raise ValueError('نگاشت آیتم انتقال با شعبه سازگار نیست')
        allocations=consume_stock(item=src,quantity=qty,movement_type=StockMovement.Type.TRANSFER_OUT,reason=f'Transfer #{transfer.id}',reference_type='StockTransfer',reference_id=transfer.id)
        weighted=sum((a['quantity']*a['unit_cost'] for a in allocations),Decimal('0'))/qty
        for idx,a in enumerate(allocations,1):
            lot=a['lot'];lot_no=(lot.lot_number if lot else f'TR-{transfer.id}-{line.id}-{idx}')
            receive_stock(item=dst,quantity=a['quantity'],unit_cost=a['unit_cost'],movement_type=StockMovement.Type.TRANSFER_IN,reason=f'Transfer #{transfer.id}',reference_type='StockTransfer',reference_id=transfer.id,lot_number=lot_no if dst.lot_tracked else '',expires_at=getattr(lot,'expires_at',None))
        line.unit_cost_snapshot=weighted;line.save(update_fields=['unit_cost_snapshot','updated_at'])
    transfer.status=StockTransfer.Status.POSTED;transfer.posted_by=user;transfer.posted_at=timezone.now()
    transfer.save(update_fields=['status','posted_by','posted_at','updated_at'])
    log_action(actor=user,branch=transfer.source_branch,action='STOCK_TRANSFER_POSTED',entity=transfer,description=f'{transfer.source_branch} -> {transfer.destination_branch}',after={'lines':transfer.lines.count()})
    return transfer

@transaction.atomic
def create_lot_count(*,branch,title,lines,user=None,notes=''):
    from .models import LotInventoryCount,LotInventoryCountLine,InventoryLot
    count=LotInventoryCount.objects.create(branch=branch,title=title,counted_by=user,notes=notes)
    seen=set()
    for row in lines:
        lot=InventoryLot.objects.select_for_update().select_related('item').get(pk=row['lot'].pk)
        if lot.item.branch_id!=branch.id:raise ValueError('Lot متعلق به شعبه نیست')
        if lot.id in seen:raise ValueError('Lot تکراری است')
        seen.add(lot.id);counted=Decimal(str(row['counted_quantity']))
        if counted<0:raise ValueError('مقدار شمارش منفی نیست')
        system=Decimal(lot.quantity_remaining)
        LotInventoryCountLine.objects.create(count=count,lot=lot,system_quantity=system,counted_quantity=counted,variance=counted-system,variance_value=(counted-system)*Decimal(lot.unit_cost))
    return count

@transaction.atomic
def post_lot_count(count,*,user=None):
    from django.utils import timezone
    from .models import LotInventoryCount,InventoryLot
    from apps.audit.services import log_action
    count=LotInventoryCount.objects.select_for_update().prefetch_related('lines__lot__item').get(pk=count.pk)
    if count.status!=LotInventoryCount.Status.DRAFT:raise ValueError('شمارش Lot قابل ثبت نیست')
    touched=set()
    for line in count.lines.all():
        lot=InventoryLot.objects.select_for_update().get(pk=line.lot_id)
        live=Decimal(lot.quantity_remaining)
        if live!=Decimal(line.system_quantity):raise ValueError(f'Lot {lot.lot_number} بعد از شمارش تغییر کرده است')
        variance=Decimal(line.counted_quantity)-live
        lot.quantity_remaining=Decimal(line.counted_quantity);lot.save(update_fields=['quantity_remaining','updated_at'])
        line.variance=variance;line.variance_value=variance*Decimal(lot.unit_cost);line.save(update_fields=['variance','variance_value','updated_at'])
        if variance:
            StockMovement.objects.create(item=lot.item,movement_type=StockMovement.Type.ADJUSTMENT,quantity=variance,unit_cost=lot.unit_cost,reason=f'Lot Count: {count.title}',reference_type='LotInventoryCount',reference_id=str(count.id),lot=lot)
        touched.add(lot.item_id)
    for item_id in touched:
        item=InventoryItem.objects.select_for_update().get(pk=item_id)
        total=sum((Decimal(x.quantity_remaining) for x in item.lots.all()),Decimal('0'))
        item.current_stock=total;item.save(update_fields=['current_stock','updated_at'])
    count.status=LotInventoryCount.Status.POSTED;count.posted_by=user;count.posted_at=timezone.now();count.save(update_fields=['status','posted_by','posted_at','updated_at'])
    log_action(actor=user,branch=count.branch,action='LOT_COUNT_POSTED',entity=count,after={'lines':count.lines.count()})
    return count
