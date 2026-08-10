from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.dining.models import Hall, Table, TableSession
from apps.kitchen.models import KitchenTicket, PreparationStation
from apps.cashier.models import CashMovement, CashRegister, CashShift
from apps.orders.services import checkout_order
from apps.core.serializers import OrderSerializer
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

    def test_unpaid_dine_in_order_creates_ticket_when_product_has_station(self):
        o=checkout_order(
            branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="DINE_IN",
            user=self.u,defer_payment=True,
        )
        self.assertEqual(o.payment_status,"UNPAID")
        self.assertEqual(o.status,"CONFIRMED")
        self.assertEqual(o.kitchen_tickets.count(),1)
        self.assertEqual(OrderSerializer(o).data['outstanding_amount'],"100")

    def test_order_response_includes_live_kitchen_status(self):
        o=checkout_order(branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="TAKEAWAY",payment_method="POS",user=self.u)
        ticket=o.kitchen_tickets.get()
        ticket.status=KitchenTicket.Status.PREPARING
        ticket.save(update_fields=['status','updated_at'])
        self.assertEqual(OrderSerializer(o).data['kitchen_statuses'],[
            {'station_id':ticket.station_id,'station_name':'Bar','status':'PREPARING'}
        ])
        self.assertEqual(OrderSerializer(o).data['outstanding_amount'],"0")

    def test_kitchen_ticket_response_includes_order_and_payment_status(self):
        order=checkout_order(
            branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="DINE_IN",
            user=self.u,defer_payment=True,
        )
        kitchen_user=User.objects.create_user(
            username='ticket-status-kitchen',password='x',business=order.branch.business,
            branch=self.br,role=User.Role.KITCHEN,
        )
        self.client.force_login(kitchen_user)

        response=self.client.get('/api/v1/kitchen-tickets/')

        self.assertEqual(response.status_code,200)
        ticket=response.json()[0]
        self.assertEqual(ticket['order_status'],'CONFIRMED')
        self.assertEqual(ticket['payment_status'],'UNPAID')

    def test_kitchen_can_mark_ready_ticket_as_delivered_without_settling_order(self):
        order=checkout_order(
            branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="DINE_IN",
            user=self.u,defer_payment=True,
        )
        ticket=order.kitchen_tickets.get()
        ticket.status=KitchenTicket.Status.READY
        ticket.save(update_fields=['status','updated_at'])
        order.status='READY'
        order.save(update_fields=['status','updated_at'])
        kitchen_user=User.objects.create_user(
            username='kitchen-user',password='x',business=order.branch.business,
            branch=self.br,role=User.Role.KITCHEN,
        )
        self.client.force_login(kitchen_user)

        response=self.client.post(f'/api/v1/kitchen-tickets/{ticket.id}/done/')

        self.assertEqual(response.status_code,200)
        ticket.refresh_from_db();order.refresh_from_db()
        self.assertEqual(ticket.status,KitchenTicket.Status.DONE)
        self.assertEqual(order.status,'READY')
        self.assertEqual(order.payment_status,'UNPAID')

    def test_kitchen_delivery_completes_a_paid_order_after_last_ticket(self):
        order=checkout_order(
            branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="TAKEAWAY",
            payment_method="POS",user=self.u,
        )
        ticket=order.kitchen_tickets.get()
        ticket.status=KitchenTicket.Status.READY
        ticket.save(update_fields=['status','updated_at'])
        order.status='READY'
        order.save(update_fields=['status','updated_at'])
        kitchen_user=User.objects.create_user(
            username='kitchen-paid-user',password='x',business=order.branch.business,
            branch=self.br,role=User.Role.KITCHEN,
        )
        self.client.force_login(kitchen_user)

        response=self.client.post(f'/api/v1/kitchen-tickets/{ticket.id}/done/')

        self.assertEqual(response.status_code,200)
        ticket.refresh_from_db();order.refresh_from_db()
        self.assertEqual(ticket.status,KitchenTicket.Status.DONE)
        self.assertEqual(order.status,'COMPLETED')

    def test_unpaid_order_can_be_settled_from_order_endpoint(self):
        o=checkout_order(branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="DINE_IN",user=self.u,defer_payment=True)
        self.client.force_login(self.u)
        response=self.client.post(
            f'/api/v1/orders/{o.id}/settle/',
            {'require_full':True,'payments':[{'method':'POS','amount':'100','reference_number':'123'}]},
            content_type='application/json',
        )
        self.assertEqual(response.status_code,201)
        o.refresh_from_db()
        self.assertEqual(o.payment_status,'PAID')

    def test_mixed_settlement_accepts_persian_digits_and_records_cash_movement(self):
        order=checkout_order(branch=self.br,items=[{"product":self.p,"quantity":1}],order_type="DINE_IN",user=self.u,defer_payment=True)
        register=CashRegister.objects.create(branch=self.br,name='صندوق آزمون')
        CashShift.objects.create(register=register,cashier=self.u,opening_balance=0,is_open=True)
        self.client.force_login(self.u)

        response=self.client.post(
            f'/api/v1/orders/{order.id}/settle/',
            {'require_full':True,'payments':[
                {'method':'POS','amount':'۴۰','tendered_amount':'۴۰','reference_number':'۱۲۳'},
                {'method':'CASH','amount':'۶۰','tendered_amount':'۶۰'},
            ]},
            content_type='application/json',
        )

        self.assertEqual(response.status_code,201)
        order.refresh_from_db()
        self.assertEqual(order.payment_status,'PAID')
        self.assertEqual(CashMovement.objects.filter(payment__order=order,movement_type=CashMovement.Type.SALE).count(),1)

    def test_dine_in_checkout_opens_selected_free_table_once(self):
        hall=Hall.objects.create(branch=self.br,name='سالن')
        table=Table.objects.create(hall=hall,number='۱',status=Table.Status.FREE)
        self.client.force_login(self.u)
        payload={
            'branch':self.br.id,'items':[{'product':self.p.id,'quantity':1}],
            'order_type':'DINE_IN','table':table.id,
            'payments':[{'method':'POS','amount':'100'}],
        }
        first=self.client.post('/api/v1/checkout/',payload,content_type='application/json',HTTP_IDEMPOTENCY_KEY='dine-in-1')
        second=self.client.post('/api/v1/checkout/',payload,content_type='application/json',HTTP_IDEMPOTENCY_KEY='dine-in-1')
        self.assertEqual(first.status_code,201)
        self.assertEqual(second.status_code,201)
        self.assertEqual(TableSession.objects.filter(table=table,is_open=True).count(),1)
        table.refresh_from_db()
        self.assertEqual(table.status,Table.Status.OCCUPIED)
