from .models import PrintJob, PrintTemplate

def order_receipt_payload(order):
    customer=None
    try:
        fiscal=order.branch.fiscal_settings
        tax_label=fiscal.receipt_tax_label;service_label=fiscal.receipt_service_label
    except Exception:
        tax_label='مالیات';service_label='حق سرویس'
    if order.customer_id: customer={'name':order.customer.name,'phone':order.customer.phone}
    return {
        'document_type':'RECEIPT','order_id':order.id,'order_number':order.order_number,
        'branch':order.branch.name,'business':order.branch.business.name,
        'created_at':order.created_at.isoformat(),'order_type':order.order_type,
        'table':order.table_session.table.number if order.table_session_id else None,
        'customer':customer,
        'items':[{
            'name':x.product_name,'quantity':str(x.quantity),'unit_price':str(x.unit_price),
            'line_total':str(x.line_total),'notes':x.notes
        } for x in order.items.all()],
        'subtotal':str(order.subtotal),'discount_total':str(order.discount_total),
        'service_charge_total':str(order.service_charge_total),'delivery_fee_total':str(order.delivery_fee_total),'tax_total':str(order.tax_total),
        'grand_total':str(order.grand_total),'tax_label':tax_label,'service_label':service_label,
        'payments':[{'method':p.method,'amount':str(p.amount),'change':str(p.change_amount),'reference':p.reference_number,'payer_label':p.payer_label} for p in order.payments.all()],
    }

def create_receipt_job(order,*,printer=None,user=None):
    return PrintJob.objects.create(branch=order.branch,printer=printer,document_type='RECEIPT',entity_type='Order',entity_id=str(order.id),payload=order_receipt_payload(order),created_by=user)

def kitchen_ticket_payload(ticket):
    return {
        'document_type':'KITCHEN','ticket_id':ticket.id,'order_number':ticket.order.order_number,
        'station':ticket.station.name,'order_type':ticket.order.order_type,
        'table':ticket.order.table_session.table.number if ticket.order.table_session_id else None,
        'items':[{'name':x.product_name,'quantity':str(x.quantity),'notes':x.notes} for x in ticket.order.items.filter(product__preparation_station=ticket.station)]
    }

def create_kitchen_job(ticket,*,printer=None,user=None):
    return PrintJob.objects.create(branch=ticket.order.branch,printer=printer,document_type='KITCHEN',entity_type='KitchenTicket',entity_id=str(ticket.id),payload=kitchen_ticket_payload(ticket),created_by=user)
