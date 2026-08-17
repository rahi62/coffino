import json

from django.core.serializers.json import DjangoJSONEncoder

from .models import AuditLog


def _business_for(*,actor=None,branch=None,entity=None):
    if branch is not None:
        return getattr(branch,'business',None)
    if entity is not None:
        if entity.__class__.__name__=='Business':
            return entity
        direct=getattr(entity,'business',None)
        if direct is not None:
            return direct
        entity_branch=getattr(entity,'branch',None)
        if entity_branch is not None:
            return getattr(entity_branch,'business',None)
    if actor is not None:
        business=getattr(actor,'business',None)
        if business is not None:
            return business
        actor_branch=getattr(actor,'branch',None)
        if actor_branch is not None:
            return getattr(actor_branch,'business',None)
    return None


def _json_safe(value):
    """Normalize audit snapshots before JSONField persistence.

    DRF serializer payloads may legitimately contain Decimal/UUID/date objects. Django's
    JSONField uses a strict JSON encoder by default, so convert them at the audit boundary
    instead of forcing every domain caller to remember serialization details.
    """
    return json.loads(json.dumps(value or {},cls=DjangoJSONEncoder))


def log_action(*,actor=None,branch=None,action,entity=None,description='',before=None,after=None,metadata=None,request=None):
    ip=None
    if request:
        ip=(request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip() or request.META.get('REMOTE_ADDR'))
    resolved_branch=branch or getattr(entity,'branch',None) or getattr(actor,'branch',None)
    return AuditLog.objects.create(
        business=_business_for(actor=actor,branch=resolved_branch,entity=entity),
        actor=actor,branch=resolved_branch,action=action,
        entity_type=entity.__class__.__name__ if entity else '',
        entity_id=str(getattr(entity,'pk','')) if entity else '',
        description=description,before=_json_safe(before),after=_json_safe(after),metadata=_json_safe(metadata),ip_address=ip
    )
