from django.core.management.base import BaseCommand
from apps.notifications.services import process_pending
class Command(BaseCommand):
    help='Process pending Cafino notifications/SMS'
    def handle(self,*args,**opts):
        rows=process_pending(limit=100,allow_global=True)
        self.stdout.write(self.style.SUCCESS(f'Processed {len(rows)} notifications'))
