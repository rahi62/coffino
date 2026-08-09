from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.customers.models import Customer
from apps.loyalty.models import LoyaltyProgram
from apps.loyalty.services import credit_wallet,redeem_points_to_wallet,get_accounts
class WalletTests(TestCase):
    def test_wallet_credit_and_loyalty_conversion(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');c=Customer.objects.create(branch=br,name='C',phone='1')
        LoyaltyProgram.objects.create(branch=br,amount_per_point=100,point_wallet_value=10,min_redeem_points=5)
        account,wallet=get_accounts(c);account.points_balance=10;account.save(update_fields=['points_balance'])
        redeem_points_to_wallet(c,5);wallet.refresh_from_db();account.refresh_from_db();self.assertEqual(wallet.balance,Decimal('50'));self.assertEqual(account.points_balance,5)
        credit_wallet(c,100);wallet.refresh_from_db();self.assertEqual(wallet.balance,Decimal('150'))
