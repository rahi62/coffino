from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.delivery.models import DeliveryZone,CourierProfile,DeliveryAddress,DeliveryAssignment
from apps.delivery.services import delivery_quote,assign_courier,update_delivery_status
from apps.orders.models import Order

class DeliveryTests(TestCase):
    def setUp(self):
        b=Business.objects.create(name='B');self.br=Branch.objects.create(business=b,name='Main')
        self.zone=DeliveryZone.objects.create(branch=self.br,name='Near',code='N',delivery_fee=300,min_order_amount=1000,free_delivery_above=5000)

    def test_quote_and_free_threshold(self):
        self.assertEqual(delivery_quote(self.zone,Decimal('2000')),Decimal('300'))
        self.assertEqual(delivery_quote(self.zone,Decimal('6000')),Decimal('0'))
        with self.assertRaises(ValueError): delivery_quote(self.zone,Decimal('500'))

    def test_courier_lifecycle(self):
        order=Order.objects.create(branch=self.br,order_number=1,order_type='DELIVERY',subtotal=2000,grand_total=2300)
        address=DeliveryAddress.objects.create(branch=self.br,zone=self.zone,recipient_name='A',phone='1',address='Street')
        assignment=DeliveryAssignment.objects.create(order=order,address=address,zone=self.zone,delivery_fee=300)
        courier=CourierProfile.objects.create(branch=self.br,name='Courier')
        assignment=assign_courier(assignment,courier)
        self.assertEqual(assignment.status,DeliveryAssignment.Status.ASSIGNED)
        assignment=update_delivery_status(assignment,DeliveryAssignment.Status.PICKED_UP)
        assignment=update_delivery_status(assignment,DeliveryAssignment.Status.DELIVERED)
        order.refresh_from_db();courier.refresh_from_db()
        self.assertEqual(order.status,Order.Status.COMPLETED)
        self.assertEqual(courier.status,CourierProfile.Status.AVAILABLE)
