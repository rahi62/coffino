from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.catalog.models import Category, Product
from apps.discounts.models import DiscountRule
from apps.discounts.services import find_best_discount
class DiscountRuleTests(TestCase):
    def test_best_rule_and_cap(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M')
        c=Category.objects.create(branch=br,name='Coffee');p=Product.objects.create(branch=br,category=c,name='Latte',price=1000)
        DiscountRule.objects.create(branch=br,name='20%',kind='PERCENT',value=20,max_discount=150,priority=10)
        r,a=find_best_discount(branch=br,subtotal=Decimal('1000'),lines=[{'product':p,'line_total':Decimal('1000')}])
        self.assertEqual(a,Decimal('150'))
        self.assertEqual(r.name,'20%')
