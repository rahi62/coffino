from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.cashier.models import CashMovement
from apps.cashier.services import record_cash_movement
from apps.inventory.lot_services import receive_stock
from apps.inventory.models import InventoryItem, StockMovement
from apps.accounting.models import BankAccount
from apps.purchasing.models import PurchaseInvoice, PurchaseItem, SupplierPayment
from apps.suppliers.models import Supplier


def _validate_purchase_scope(*,branch,supplier,rows):
    if supplier.branch_id!=branch.id:
        raise ValueError('تأمین‌کننده باید متعلق به همان شعبه خرید باشد.')
    if not rows:
        raise ValueError('فاکتور خرید باید حداقل یک آیتم داشته باشد.')
    for row in rows:
        item=row['inventory_item']
        if item.branch_id!=branch.id:
            raise ValueError(f'کالای «{item.name}» متعلق به شعبه خرید نیست.')


@transaction.atomic
def create_purchase(*, branch, supplier, rows, invoice_date, user=None, invoice_number='', purchaser_name='', notes='', paid_amount=0, payment_method='CASH', bank_account=None):
    # Re-load mutable references under lock and validate domain isolation before writing anything.
    supplier=Supplier.objects.select_for_update().get(pk=supplier.pk)
    locked_rows=[]
    for row in rows:
        item=InventoryItem.objects.select_for_update().get(pk=row['inventory_item'].pk)
        locked_rows.append({**row,'inventory_item':item})
    _validate_purchase_scope(branch=branch,supplier=supplier,rows=locked_rows)

    invoice=PurchaseInvoice.objects.create(
        branch=branch,supplier=supplier,invoice_number=invoice_number,
        invoice_date=invoice_date,purchaser_name=purchaser_name.strip(),notes=notes,created_by=user
    )
    for row in locked_rows:
        qty=Decimal(str(row['quantity']))
        cost=Decimal(str(row['unit_cost']))
        if qty<=0 or cost<0:
            raise ValueError('مقادیر خرید نامعتبر است.')
        PurchaseItem.objects.create(
            invoice=invoice,inventory_item=row['inventory_item'],quantity=qty,unit_cost=cost,
            line_total=(qty*cost).quantize(Decimal('1')),
            lot_number=row.get('lot_number',''),expires_at=row.get('expires_at')
        )

    post_purchase(invoice)
    paid=Decimal(str(paid_amount or 0))
    if paid>0:
        pay_supplier(invoice=invoice,amount=paid,method=payment_method,bank_account=bank_account,user=user)
    return PurchaseInvoice.objects.prefetch_related('items').get(pk=invoice.pk)


@transaction.atomic
def post_purchase(invoice):
    invoice=PurchaseInvoice.objects.select_for_update().select_related('branch','supplier').get(pk=invoice.pk)
    if invoice.status!=PurchaseInvoice.Status.DRAFT:
        raise ValueError('فقط فاکتور پیش‌نویس قابل ثبت است.')
    if invoice.supplier.branch_id!=invoice.branch_id:
        raise ValueError('دامنه تأمین‌کننده و شعبه خرید ناسازگار است.')

    items=list(invoice.items.select_related('inventory_item').select_for_update())
    if not items:
        raise ValueError('فاکتور خرید بدون آیتم قابل ثبت نیست.')

    total=Decimal('0')
    for row in items:
        item=row.inventory_item
        if item.branch_id!=invoice.branch_id:
            raise ValueError(f'کالای «{item.name}» خارج از شعبه فاکتور است.')
        receive_stock(
            item=item,quantity=row.quantity,unit_cost=row.unit_cost,
            movement_type=StockMovement.Type.PURCHASE,
            reason=f'خرید از {invoice.supplier.name}',
            reference_type='PurchaseInvoice',reference_id=invoice.id,
            lot_number=row.lot_number,expires_at=row.expires_at
        )
        item.last_purchase_cost=row.unit_cost
        item.save(update_fields=['last_purchase_cost','updated_at'])
        total+=Decimal(row.line_total)

    invoice.total_amount=total
    invoice.status=PurchaseInvoice.Status.POSTED
    invoice.save(update_fields=['total_amount','status','updated_at'])
    return invoice


@transaction.atomic
def pay_supplier(*, invoice, amount, method='CASH', reference='', bank_account=None, user=None):
    invoice=PurchaseInvoice.objects.select_for_update().select_related('supplier','branch').get(pk=invoice.pk)
    supplier=Supplier.objects.select_for_update().get(pk=invoice.supplier_id)
    if supplier.branch_id!=invoice.branch_id:
        raise ValueError('دامنه تأمین‌کننده و شعبه فاکتور ناسازگار است.')

    amount=Decimal(str(amount))
    if invoice.status!=PurchaseInvoice.Status.POSTED:
        raise ValueError('فاکتور باید ابتدا ثبت نهایی شود.')
    due=Decimal(invoice.total_amount)-Decimal(invoice.paid_amount)
    if amount<=0 or amount>due:
        raise ValueError('مبلغ پرداخت نامعتبر است.')

    if bank_account:
        bank_account=BankAccount.objects.select_for_update().get(pk=bank_account.pk)
        if bank_account.branch_id!=invoice.branch_id or not bank_account.is_active:
            raise ValueError('کارت یا حساب بانکی انتخاب‌شده برای این شعبه فعال نیست.')

    payment=SupplierPayment.objects.create(
        supplier=supplier,purchase_invoice=invoice,amount=amount,method=method,
        bank_account=bank_account,reference=reference,created_by=user
    )
    invoice.paid_amount=Decimal(invoice.paid_amount)+amount
    invoice.save(update_fields=['paid_amount','updated_at'])

    if method=='CASH':
        record_cash_movement(
            branch=invoice.branch,movement_type=CashMovement.Type.SUPPLIER_PAYMENT,
            amount=amount,user=user,note=f'پرداخت به {supplier.name}',
            reference_type='SupplierPayment',reference_id=payment.id
        )
    return payment


def supplier_balance(supplier):
    posted=supplier.invoices.filter(status=PurchaseInvoice.Status.POSTED).aggregate(v=Sum('total_amount'))['v'] or 0
    paid=supplier.payments.aggregate(v=Sum('amount'))['v'] or 0
    return Decimal(supplier.opening_balance)+Decimal(posted)-Decimal(paid)
