from django.db import transaction
from django.utils import timezone
from .models import Table,TableSession,TableTransferLog
from apps.audit.services import log_action

def get_or_open_table_session(*, table, branch, user=None):
    """Return the active session for a branch table, opening a free one safely."""
    table=Table.objects.select_for_update().select_related('hall__branch').get(pk=table.pk)
    if table.hall.branch_id!=branch.id:
        raise ValueError('میز متعلق به شعبه سفارش نیست')
    session=table.sessions.select_for_update().filter(is_open=True).first()
    if session:
        return session
    if table.status!=Table.Status.FREE:
        raise ValueError('این میز برای ثبت سفارش داخل سالن قابل انتخاب نیست')
    session=TableSession.objects.create(table=table,customer_count=1,opened_by=user)
    table.status=Table.Status.OCCUPIED
    table.save(update_fields=['status','updated_at'])
    return session

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
