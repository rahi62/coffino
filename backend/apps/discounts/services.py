from decimal import Decimal
from django.utils import timezone
from .models import DiscountRule

def _eligible(rule,subtotal,products,code=None,now=None):
    now=now or timezone.now()
    if not rule.is_active:return False
    if rule.trigger==DiscountRule.Trigger.CODE and (not code or rule.code.lower()!=str(code).lower()):return False
    if rule.trigger==DiscountRule.Trigger.AUTO and code:return False
    if rule.starts_at and now<rule.starts_at:return False
    if rule.ends_at and now>rule.ends_at:return False
    if rule.weekdays and now.weekday() not in rule.weekdays:return False
    if Decimal(subtotal)<Decimal(rule.min_order_amount):return False
    ids={p.id for p in products}; cats={p.category_id for p in products}
    if rule.scope==DiscountRule.Scope.PRODUCT and rule.product_id not in ids:return False
    if rule.scope==DiscountRule.Scope.CATEGORY and rule.category_id not in cats:return False
    return True

def calculate_rule_discount(rule,*,subtotal,lines):
    subtotal=Decimal(subtotal)
    base=subtotal
    if rule.scope==DiscountRule.Scope.PRODUCT:
        base=sum((Decimal(line['line_total']) for line in lines if line['product'].id==rule.product_id),Decimal('0'))
    elif rule.scope==DiscountRule.Scope.CATEGORY:
        base=sum((Decimal(line['line_total']) for line in lines if line['product'].category_id==rule.category_id),Decimal('0'))
    discount=(base*Decimal(rule.value)/Decimal('100')) if rule.kind==DiscountRule.Kind.PERCENT else Decimal(rule.value)
    if Decimal(rule.max_discount)>0:discount=min(discount,Decimal(rule.max_discount))
    return max(Decimal('0'),min(discount,subtotal))

def find_best_discount(*,branch,subtotal,lines,code=None,allow_manager_rules=False):
    products=[x['product'] for x in lines]
    qs=DiscountRule.objects.filter(branch=branch,is_active=True).select_related('category','product').order_by('priority','id')
    eligible=[r for r in qs if _eligible(r,subtotal,products,code=code) and (allow_manager_rules or not r.requires_manager)]
    if not eligible:return None,Decimal('0')
    scored=[(calculate_rule_discount(r,subtotal=subtotal,lines=lines),r) for r in eligible]
    amount,rule=max(scored,key=lambda x:x[0])
    return rule,amount
