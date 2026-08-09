from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.kitchen.models import PreparationStation
from apps.orders.services import checkout_order
class HealthTest(TestCase):
    def test_health(self):
        r=self.client.get("/api/v1/health/");self.assertEqual(r.status_code,200)
class CheckoutServiceTest(TestCase):
    def setUp(self):
        b=Business.objects.create(name="T");self.br=Branch.objects.create(business=b,name="B");u=User.objects.create_user(username="u",password="x",branch=self.br);self.u=u
        st=PreparationStation.objects.create(branch=self.br,name="Bar",code="BAR");c=Category.objects.create(branch=self.br,name="Coffee");self.p=Product.objects.create(branch=self.br,category=c,name="Latte",price=100,preparation_station=st)
    def test_checkout_creates_paid_order_and_ticket(self):
        o=checkout_order(branch=self.br,items=[{"product":self.p,"quantity":2}],order_type="TAKEAWAY",payment_method="POS",user=self.u)
        self.assertEqual(o.grand_total,200);self.assertEqual(o.payment_status,"PAID");self.assertEqual(o.kitchen_tickets.count(),1)
