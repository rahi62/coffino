from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import ProductionBatch, ProductionBatchIngredient
from apps.inventory.models import InventoryItem, StockMovement
from apps.inventory.lot_services import consume_stock, receive_stock
from apps.audit.services import log_action

@transaction.atomic
def post_production_batch(batch,*,user=None):
    batch=ProductionBatch.objects.select_for_update().select_related('formula__output_item').prefetch_related('formula__ingredients__inventory_item').get(pk=batch.pk)
    if batch.status!=ProductionBatch.Status.DRAFT: raise ValueError('Batch قابل ثبت نیست')
    if batch.formula.branch_id!=batch.branch_id: raise ValueError('فرمول متعلق به این شعبه نیست')
    multiplier=Decimal(batch.multiplier)
    if multiplier<=0: raise ValueError('ضریب تولید باید مثبت باشد')
    total_cost=Decimal('0')
    snapshots=[]
    for row in batch.formula.ingredients.all():
        qty=Decimal(row.quantity)*multiplier
        item=InventoryItem.objects.select_for_update().get(pk=row.inventory_item_id)
        if item.branch_id!=batch.branch_id: raise ValueError('مواد اولیه فرمول متعلق به شعبه نیست')
        if item.current_stock<qty: raise ValueError(f'موجودی {item.name} برای تولید کافی نیست')
        allocations=consume_stock(item=item,quantity=qty,movement_type=StockMovement.Type.PRODUCTION,reason=f'Production Batch #{batch.id}',reference_type='ProductionBatch',reference_id=batch.id)
        total=sum((a['quantity']*a['unit_cost'] for a in allocations),Decimal('0'));cost=(total/qty) if qty else Decimal('0')
        snapshots.append((item,qty,cost,total));total_cost+=total

    output=InventoryItem.objects.select_for_update().get(pk=batch.formula.output_item_id)
    if output.branch_id!=batch.branch_id: raise ValueError('محصول خروجی باید متعلق به شعبه Batch باشد')
    output_qty=Decimal(batch.formula.output_quantity)*multiplier
    if output_qty<=0: raise ValueError('خروجی فرمول باید مثبت باشد')
    unit_cost=total_cost/output_qty
    receive_stock(item=output,quantity=output_qty,unit_cost=unit_cost,movement_type=StockMovement.Type.PRODUCTION,reason=f'Production Batch #{batch.id}',reference_type='ProductionBatch',reference_id=batch.id,lot_number=f'PB-{batch.id}-{batch.batch_number}' if batch.batch_number else f'PB-{batch.id}',expires_at=batch.expires_at)
    for item,qty,cost,total in snapshots:
        ProductionBatchIngredient.objects.create(batch=batch,inventory_item=item,quantity=qty,unit_cost=cost,total_cost=total)

    batch.produced_quantity=output_qty;batch.total_cost=total_cost;batch.unit_cost=unit_cost
    batch.status=ProductionBatch.Status.POSTED;batch.posted_by=user;batch.posted_at=timezone.now()
    batch.save(update_fields=['produced_quantity','total_cost','unit_cost','status','posted_by','posted_at','updated_at'])
    log_action(actor=user,branch=batch.branch,action='PRODUCTION_BATCH_POSTED',entity=batch,description=batch.formula.name,after={'produced_quantity':str(output_qty),'total_cost':str(total_cost)})
    return batch
