from django.db import transaction
from django.utils import timezone
from .models import Table,TableSession,TableTransferLog
from apps.audit.services import log_action

@transaction.atomic
def transfer_table_session(session,new_table,*,user=None):
    session=TableSession.objects.select_for_update().select_related('table__hall__branch').get(pk=session.pk,is_open=True)
    old=Table.objects.select_for_update().get(pk=session.table_id);new=Table.objects.select_for_update().select_related('hall__branch').get(pk=new_table.pk)
    if old.hall.branch_id!=new.hall.branch_id:raise ValueError('انتقال میز بین شعبه مجاز نیست')
    if new.status!=Table.Status.FREE:raise ValueError('میز مقصد آزاد نیست')
    session.table=new;session.save(update_fields=['table','updated_at'])
    old.status=Table.Status.FREE;old.save(update_fields=['status','updated_at'])
    new.status=Table.Status.OCCUPIED;new.save(update_fields=['status','updated_at'])
    TableTransferLog.objects.create(session=session,from_table=old,to_table=new,transferred_by=user)
    log_action(actor=user,branch=new.hall.branch,action='TABLE_TRANSFER',entity=session,after={'from':old.id,'to':new.id})
    return session
