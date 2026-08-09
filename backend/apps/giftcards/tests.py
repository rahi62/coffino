from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.giftcards.services import issue_card,debit_card,refund_card

class GiftCardTests(TestCase):
    def test_issue_debit_refund(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        card,code=issue_card(branch=br,amount=1000)
        self.assertNotIn(code,card.code_hash)
        debit_card(branch=br,code=code,amount=400)
        card.refresh_from_db();self.assertEqual(card.balance,Decimal('600'))
        refund_card(card=card,amount=100)
        card.refresh_from_db();self.assertEqual(card.balance,Decimal('700'))
