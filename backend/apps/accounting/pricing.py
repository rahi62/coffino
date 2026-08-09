from decimal import Decimal, ROUND_HALF_UP
from .models import FiscalSettings

def _money(v):
    return Decimal(v).quantize(Decimal('1'),rounding=ROUND_HALF_UP)

def calculate_fiscal_totals(*,branch,order_type,subtotal,discount,delivery_fee=0):
    delivery=_money(Decimal(str(delivery_fee or 0)))
    try: cfg=branch.fiscal_settings
    except FiscalSettings.DoesNotExist:
        return {'tax_total':Decimal('0'),'service_charge_total':Decimal('0'),'delivery_fee_total':delivery,'grand_total':_money(Decimal(subtotal)-Decimal(discount)+delivery)}
    net=max(Decimal('0'),Decimal(subtotal)-Decimal(discount))
    service=Decimal('0')
    service_types=cfg.service_charge_order_types or ['DINE_IN']
    if cfg.service_charge_enabled and order_type in service_types:
        service=_money(net*Decimal(cfg.service_charge_rate)/Decimal('100'))
    tax=Decimal('0')
    if cfg.tax_enabled and Decimal(cfg.tax_rate)>0:
        rate=Decimal(cfg.tax_rate)
        delivery_tax_base=delivery if cfg.delivery_fee_taxable else Decimal('0')
        if cfg.prices_include_tax:
            included=_money(net*rate/(Decimal('100')+rate))
            extra_tax=_money((service+delivery_tax_base)*rate/Decimal('100'))
            tax=included+extra_tax
            grand=_money(net+service+delivery+extra_tax)
        else:
            tax=_money((net+service+delivery_tax_base)*rate/Decimal('100'))
            grand=_money(net+service+delivery+tax)
    else:
        grand=_money(net+service+delivery)
    return {'tax_total':tax,'service_charge_total':service,'delivery_fee_total':delivery,'grand_total':grand}
