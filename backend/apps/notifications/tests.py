from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.customers.models import Customer
from apps.orders.models import Order
from apps.takeaway.models import TakeawayProfile
from apps.notifications.models import Notification
from apps.notifications.services import enqueue_order_ready
class NotificationTests(TestCase):
    def test_ready_event_is_deduped(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');c=Customer.objects.create(branch=br,name='C',phone='0912')
        o=Order.objects.create(branch=br,order_number=1,order_type='TAKEAWAY',customer=c);TakeawayProfile.objects.create(order=o,pickup_number='1',customer_phone='0912')
        enqueue_order_ready(o);enqueue_order_ready(o)
        self.assertEqual(Notification.objects.filter(order=o,event='ORDER_READY').count(),2)
