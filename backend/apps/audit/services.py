from .models import AuditLog
def log_action(*,actor=None,branch=None,action,entity=None,description='',before=None,after=None,metadata=None,request=None):
    ip=None
    if request:
        ip=(request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip() or request.META.get('REMOTE_ADDR'))
    return AuditLog.objects.create(
        actor=actor,branch=branch or getattr(actor,'branch',None),action=action,
        entity_type=entity.__class__.__name__ if entity else '',
        entity_id=str(getattr(entity,'pk','')) if entity else '',
        description=description,before=before or {},after=after or {},metadata=metadata or {},ip_address=ip
    )
