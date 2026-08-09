import hashlib,secrets
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import GiftCard,GiftCardTransaction

def _hash(code):return hashlib.sha256(str(code).strip().upper().encode()).hexdigest()

@transaction.atomic
def issue_card(*,branch,amount,expires_at=None,purchaser_name='',recipient_name='',note=''):
    amount=Decimal(str(amount))
    if amount<=0:raise ValueError('مبلغ کارت هدیه باید مثبت باشد')
    code='CF-'+secrets.token_hex(6).upper()
    card=GiftCard.objects.create(branch=branch,code_hash=_hash(code),code_last4=code[-4:],initial_balance=amount,balance=amount,expires_at=expires_at,purchaser_name=purchaser_name,recipient_name=recipient_name,note=note)
    GiftCardTransaction.objects.create(card=card,transaction_type=GiftCardTransaction.Type.ISSUE,amount=amount,balance_after=amount,reference='ISSUE')
    return card,code

def find_card(branch,code,*,for_update=False):
    qs=GiftCard.objects.select_for_update() if for_update else GiftCard.objects
    try:card=qs.get(branch=branch,code_hash=_hash(code),is_active=True)
    except GiftCard.DoesNotExist:raise ValueError('کارت هدیه معتبر نیست')
    if card.expires_at and card.expires_at<=timezone.now():raise ValueError('کارت هدیه منقضی شده است')
    return card

@transaction.atomic
def debit_card(*,branch,code,amount,order=None):
    amount=Decimal(str(amount));card=find_card(branch,code,for_update=True)
    if amount<=0 or Decimal(card.balance)<amount:raise ValueError('موجودی کارت هدیه کافی نیست')
    card.balance=Decimal(card.balance)-amount;card.save(update_fields=['balance','updated_at'])
    GiftCardTransaction.objects.create(card=card,order=order,transaction_type=GiftCardTransaction.Type.DEBIT,amount=-amount,balance_after=card.balance,reference=f'Order #{getattr(order,"order_number","")}')
    return card

@transaction.atomic
def refund_card(*,card,amount,order=None,reference=''):
    amount=Decimal(str(amount));card=GiftCard.objects.select_for_update().get(pk=card.pk)
    if amount<=0:raise ValueError('مبلغ برگشت نامعتبر است')
    card.balance=Decimal(card.balance)+amount;card.save(update_fields=['balance','updated_at'])
    GiftCardTransaction.objects.create(card=card,order=order,transaction_type=GiftCardTransaction.Type.REFUND,amount=amount,balance_after=card.balance,reference=reference)
    return card
