from decimal import Decimal,ROUND_DOWN
from django.db import transaction
from django.db.models import Sum
from .models import LoyaltyProgram,CustomerLoyaltyAccount,LoyaltyLedger,WalletAccount,WalletTransaction

def get_accounts(customer):
    loyalty,_=CustomerLoyaltyAccount.objects.get_or_create(customer=customer)
    wallet,_=WalletAccount.objects.get_or_create(customer=customer)
    return loyalty,wallet


def refresh_customer_tier(account):
    from .models import LoyaltyTier
    tiers=LoyaltyTier.objects.filter(branch=account.customer.branch,is_active=True,min_lifetime_points__lte=account.lifetime_points).order_by('-min_lifetime_points','priority')
    tier=tiers.first()
    code=tier.code if tier else 'STANDARD'
    if account.tier!=code:
        account.tier=code;account.save(update_fields=['tier','updated_at'])
    return tier

def active_campaign_multiplier(order):
    from django.utils import timezone
    from .models import LoyaltyCampaign
    now=timezone.now();mult=Decimal('1');bonus=0
    for c in LoyaltyCampaign.objects.filter(branch=order.branch,is_active=True,starts_at__lte=now,ends_at__gte=now):
        if c.order_types and order.order_type not in c.order_types:continue
        mult*=Decimal(c.points_multiplier);bonus+=int(c.bonus_points)
    return mult,bonus

@transaction.atomic
def earn_order_points(order):
    if not order.customer_id:return None
    try:program=order.branch.loyalty_program
    except LoyaltyProgram.DoesNotExist:return None
    if not program.is_active or Decimal(program.amount_per_point)<=0:return None
    account,_=get_accounts(order.customer)
    if LoyaltyLedger.objects.filter(account=account,order=order,entry_type=LoyaltyLedger.Type.EARN).exists():return None
    from apps.payments.models import Payment,Refund
    paid=Decimal(order.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).aggregate(v=Sum('amount'))['v'] or 0)
    refunded=Decimal(Refund.objects.filter(payment__order=order).aggregate(v=Sum('amount'))['v'] or 0)
    basis=max(Decimal('0'),paid-refunded)
    account=CustomerLoyaltyAccount.objects.select_for_update().get(pk=account.pk)
    tier=refresh_customer_tier(account);tier_mult=Decimal(tier.points_multiplier) if tier else Decimal('1')
    campaign_mult,bonus=active_campaign_multiplier(order)
    base=(basis/Decimal(program.amount_per_point))
    points=int((base*tier_mult*campaign_mult).to_integral_value(rounding=ROUND_DOWN))+bonus
    if points<=0:return None
    account.points_balance+=points;account.lifetime_points+=points;account.save(update_fields=['points_balance','lifetime_points','updated_at'])
    refresh_customer_tier(account)
    return LoyaltyLedger.objects.create(account=account,order=order,entry_type=LoyaltyLedger.Type.EARN,points=points,balance_after=account.points_balance,note=f'Order #{order.order_number}')

@transaction.atomic
def redeem_points_to_wallet(customer,points,*,note='تبدیل امتیاز به کیف پول'):
    points=int(points);account,wallet=get_accounts(customer)
    try:program=customer.branch.loyalty_program
    except LoyaltyProgram.DoesNotExist:raise ValueError('باشگاه مشتریان فعال نیست')
    if points<program.min_redeem_points:raise ValueError('امتیاز کمتر از حداقل تبدیل است')
    account=CustomerLoyaltyAccount.objects.select_for_update().get(pk=account.pk);wallet=WalletAccount.objects.select_for_update().get(pk=wallet.pk)
    if account.points_balance<points:raise ValueError('امتیاز کافی نیست')
    amount=Decimal(points)*Decimal(program.point_wallet_value)
    account.points_balance-=points;account.save(update_fields=['points_balance','updated_at'])
    wallet.balance=Decimal(wallet.balance)+amount;wallet.save(update_fields=['balance','updated_at'])
    LoyaltyLedger.objects.create(account=account,entry_type=LoyaltyLedger.Type.REDEEM,points=-points,balance_after=account.points_balance,note=note)
    WalletTransaction.objects.create(wallet=wallet,transaction_type=WalletTransaction.Type.LOYALTY,amount=amount,balance_after=wallet.balance,note=note)
    return wallet

@transaction.atomic
def debit_wallet(customer,amount,*,order=None,reference=''):
    amount=Decimal(str(amount));_,wallet=get_accounts(customer);wallet=WalletAccount.objects.select_for_update().get(pk=wallet.pk)
    if amount<=0:raise ValueError('مبلغ کیف پول نامعتبر است')
    if Decimal(wallet.balance)<amount:raise ValueError('موجودی کیف پول کافی نیست')
    wallet.balance=Decimal(wallet.balance)-amount;wallet.save(update_fields=['balance','updated_at'])
    WalletTransaction.objects.create(wallet=wallet,order=order,transaction_type=WalletTransaction.Type.DEBIT,amount=-amount,balance_after=wallet.balance,reference=reference)
    return wallet

@transaction.atomic
def credit_wallet(customer,amount,*,order=None,reference='',refund=False,note=''):
    amount=Decimal(str(amount));_,wallet=get_accounts(customer);wallet=WalletAccount.objects.select_for_update().get(pk=wallet.pk)
    if amount<=0:raise ValueError('مبلغ کیف پول نامعتبر است')
    wallet.balance=Decimal(wallet.balance)+amount;wallet.save(update_fields=['balance','updated_at'])
    WalletTransaction.objects.create(wallet=wallet,order=order,transaction_type=WalletTransaction.Type.REFUND if refund else WalletTransaction.Type.CREDIT,amount=amount,balance_after=wallet.balance,reference=reference,note=note)
    return wallet
