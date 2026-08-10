from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.customers.models import Customer
from apps.orders.models import Order
from apps.takeaway.models import PagerDevice,TakeawayProfile
from apps.notifications.models import Notification,PagerProviderConfig
from apps.notifications.services import enqueue_order_ready,process_notification
from apps.notifications.tasks import process_pending_notifications
from unittest.mock import patch
class NotificationTests(TestCase):
    def test_ready_event_is_deduped(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');c=Customer.objects.create(branch=br,name='C',phone='0912')
        o=Order.objects.create(branch=br,order_number=1,order_type='TAKEAWAY',customer=c);TakeawayProfile.objects.create(order=o,pickup_number='1',customer_phone='0912')
        enqueue_order_ready(o);enqueue_order_ready(o)
        self.assertEqual(Notification.objects.filter(order=o,event='ORDER_READY').count(),2)

    def test_pager_ready_event_is_queued_and_sent_by_adapter(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M')
        pager=PagerDevice.objects.create(branch=br,number='۱۲')
        PagerProviderConfig.objects.create(branch=br,endpoint_url='https://pager.example.test/call',is_active=True)
        order=Order.objects.create(branch=br,order_number=2,order_type='TAKEAWAY')
        TakeawayProfile.objects.create(order=order,pickup_number='2',pager=pager,ready_notification_method='PAGER')
        rows=enqueue_order_ready(order)
        notification=next(row for row in rows if row.channel==Notification.Channel.PAGER)
        self.assertEqual(notification.status,Notification.Status.PENDING)
        with patch('apps.notifications.services.urllib.request.urlopen') as urlopen:
            response=urlopen.return_value.__enter__.return_value
            response.status=200
            process_notification(notification)
        notification.refresh_from_db()
        self.assertEqual(notification.status,Notification.Status.SENT)

    def test_dine_in_ready_event_does_not_enqueue_customer_notification(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M')
        order=Order.objects.create(branch=br,order_number=3,order_type='DINE_IN')
        self.assertEqual(enqueue_order_ready(order),[])
        self.assertFalse(Notification.objects.filter(order=order).exists())

    @patch('apps.notifications.tasks.process_pending')
    def test_worker_processes_global_pending_queue(self,mock_process_pending):
        mock_process_pending.return_value=[object(),object()]
        self.assertEqual(process_pending_notifications.run(),2)
        mock_process_pending.assert_called_once_with(limit=100,allow_global=True)
