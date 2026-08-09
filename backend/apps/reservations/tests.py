from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.businesses.models import Business,Branch
from apps.dining.models import Hall,Table
from apps.reservations.services import create_reservation,seat_reservation
class ReservationTests(TestCase):
    def test_overlap_is_blocked_and_seat_opens_session(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');h=Hall.objects.create(branch=br,name='H');t=Table.objects.create(hall=h,number='1',capacity=4)
        at=timezone.now()+timedelta(days=1)
        r=create_reservation(branch=br,customer_name='A',phone='',party_size=2,reserved_for=at,table=t)
        with self.assertRaises(ValueError):create_reservation(branch=br,customer_name='B',phone='',party_size=2,reserved_for=at+timedelta(minutes=20),table=t)
        r.status='CONFIRMED';r.save(update_fields=['status']);seat_reservation(r);r.refresh_from_db();self.assertEqual(r.status,'SEATED');self.assertTrue(r.seated_session.is_open)
