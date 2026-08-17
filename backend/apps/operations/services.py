import base64
import hashlib
import json
import os
import re
import secrets
from datetime import timezone as dt_timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.businesses.models import Branch, Business
from .models import DeviceInstallation, DiagnosticRequest, ReleasePolicy

HEX64=re.compile(r'^[0-9a-f]{64}$')
SAFE_TEXT=re.compile(r'^[A-Za-z0-9_.:-]{0,80}$')


def canonicalize(value):
    if isinstance(value,list):
        return '['+','.join(canonicalize(x) for x in value)+']'
    if isinstance(value,dict):
        return '{'+','.join(json.dumps(str(k),ensure_ascii=False)+':'+canonicalize(value[k]) for k in sorted(value))+'}'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def _license_public_key_pem():
    direct=str(getattr(settings,'CAF_INO_LICENSE_PUBLIC_KEY_PEM','') or '').strip()
    if direct:
        return direct.replace('\\n','\n')
    path=str(getattr(settings,'CAF_INO_LICENSE_PUBLIC_KEY_PATH','') or '').strip()
    if path and os.path.isfile(path):
        with open(path,'r',encoding='utf-8') as handle:
            return handle.read()
    return ''


def verify_license_document(document,expected_machine_hash=''):
    if not isinstance(document,dict) or not isinstance(document.get('payload'),dict) or not document.get('signature'):
        raise ValueError('invalid_license_document')
    pem=_license_public_key_pem()
    if not pem:
        raise RuntimeError('operations_license_public_key_not_configured')
    payload=document['payload']
    if payload.get('product')!='cafino-local':
        raise ValueError('wrong_product')
    license_id=str(payload.get('license_id') or '').strip()
    machine_hash=str(payload.get('machine_hash') or '').strip().lower()
    if not license_id or not HEX64.fullmatch(machine_hash):
        raise ValueError('missing_license_fields')
    if expected_machine_hash and machine_hash!=str(expected_machine_hash).lower():
        raise ValueError('machine_mismatch')
    try:
        signature=base64.b64decode(str(document['signature']),validate=True)
        key=serialization.load_pem_public_key(pem.encode('utf-8'))
        key.verify(signature,canonicalize(payload).encode('utf-8'))
    except (ValueError,TypeError,InvalidSignature):
        raise ValueError('signature_invalid')
    now=timezone.now()
    for field,mode in [('not_before','future'),('expires_at','past')]:
        raw=payload.get(field)
        if not raw:
            continue
        parsed=parse_datetime(str(raw))
        if parsed is None:
            raise ValueError(f'invalid_{field}')
        if timezone.is_naive(parsed):
            parsed=timezone.make_aware(parsed,dt_timezone.utc)
        if mode=='future' and parsed>now:
            raise ValueError('license_not_active')
        if mode=='past' and parsed<now:
            raise ValueError('license_expired')
    return payload


def token_hash(token):
    return hashlib.sha256(str(token).encode('utf-8')).hexdigest()


def issue_device_token(device):
    token=secrets.token_urlsafe(48)
    device.token_hash=token_hash(token)
    device.save(update_fields=['token_hash','updated_at'])
    return token


def parse_uuid(value):
    import uuid
    try:
        return uuid.UUID(str(value))
    except Exception:
        raise ValueError('invalid_installation_id')


def _signed_business_assignment(payload):
    business=None;branch=None
    business_id=payload.get('business_id')
    branch_id=payload.get('branch_id')
    if business_id is not None:
        business=Business.objects.filter(pk=business_id,is_active=True).first()
    if branch_id is not None:
        branch=Branch.objects.filter(pk=branch_id,is_active=True).select_related('business').first()
        if branch and business and branch.business_id!=business.id:
            raise ValueError('signed_branch_business_mismatch')
        if branch and not business:
            business=branch.business
    return business,branch


@transaction.atomic
def register_device(*,document,machine_hash,installation_id,current_version='',channel='stable',platform='',arch='',telemetry_enabled=False):
    payload=verify_license_document(document,machine_hash)
    installation_uuid=parse_uuid(installation_id)
    license_id=str(payload['license_id'])[:120]
    machine_hash=str(payload['machine_hash']).lower()
    business,branch=_signed_business_assignment(payload)
    defaults={
        'installation_id':installation_uuid,
        'token_hash':secrets.token_hex(32),
        'customer_label':str(payload.get('customer') or '')[:160],
        'business':business,
        'branch':branch,
        'current_version':str(current_version or '')[:40],
        'release_channel':channel if channel in {'stable','beta'} else 'stable',
        'platform':str(platform or '')[:32],
        'arch':str(arch or '')[:32],
        'telemetry_enabled':bool(telemetry_enabled),
        'is_active':True,
        'last_seen_at':timezone.now(),
    }
    device,created=DeviceInstallation.objects.select_for_update().get_or_create(
        license_id=license_id,machine_hash=machine_hash,defaults=defaults
    )
    if not created:
        conflict=DeviceInstallation.objects.exclude(pk=device.pk).filter(installation_id=installation_uuid).exists()
        if conflict:
            raise ValueError('installation_id_conflict')
        device.installation_id=installation_uuid
        for key,value in defaults.items():
            if key not in {'installation_id','token_hash'}:
                setattr(device,key,value)
        device.save()
    token=issue_device_token(device)
    return device,token


def authenticate_device_token(raw_token):
    raw=str(raw_token or '').strip()
    if not raw or len(raw)>256:
        return None
    return DeviceInstallation.objects.select_related('business','branch').filter(token_hash=token_hash(raw),is_active=True).first()


def _semver(value):
    raw=str(value or '').strip()
    match=re.match(r'^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$',raw)
    if not match:
        return None
    return tuple(int(x) for x in match.groups())


def version_lt(left,right):
    a=_semver(left);b=_semver(right)
    return bool(a and b and a<b)


def rollout_bucket(installation_id,target_version):
    digest=hashlib.sha256(f'{installation_id}|{target_version}'.encode('utf-8')).digest()
    return int.from_bytes(digest[:4],'big')%100


def policy_for_device(device):
    policy=ReleasePolicy.objects.filter(channel=device.release_channel).first()
    if not policy:
        return {'managed':False,'channel':device.release_channel,'update_allowed':True,'current_blocked':False,'must_update':False,'core_operations_allowed':True,'remote_commands_allowed':False}
    blocked=[str(x) for x in (policy.blocked_versions or []) if isinstance(x,(str,int,float))][:100]
    current_blocked=device.current_version in blocked
    below_min=bool(policy.minimum_version and version_lt(device.current_version,policy.minimum_version))
    required_after=bool(policy.required_after and policy.required_after<=timezone.now())
    must_update=current_blocked or below_min or required_after
    eligible=rollout_bucket(device.installation_id,policy.target_version)<int(policy.rollout_percent or 0) if policy.target_version else False
    update_allowed=bool(policy.target_version and policy.target_version!=device.current_version and not policy.paused and (must_update or eligible))
    return {
        'managed':True,'channel':policy.channel,'target_version':policy.target_version,'minimum_version':policy.minimum_version,'rollback_version':policy.rollback_version,
        'rollout_percent':policy.rollout_percent,'rollout_bucket':rollout_bucket(device.installation_id,policy.target_version) if policy.target_version else None,
        'paused':policy.paused,'update_allowed':update_allowed,'must_update':must_update,'current_blocked':current_blocked,
        'core_operations_allowed':True,'remote_commands_allowed':False,'advisory_message':policy.advisory_message,
    }


def sanitize_diagnostic_snapshot(data):
    if not isinstance(data,dict):
        raise ValueError('invalid_diagnostic_snapshot')
    allowed={
        'app_version':(str,40),'release_channel':(str,12),'platform':(str,32),'arch':(str,32),
        'backend_healthy':(bool,None),'uptime_seconds':((int,float),None),'db_size_bytes':((int,float),None),
        'free_disk_bytes':((int,float),None),'backup_count':(int,None),'latest_backup_age_hours':((int,float,type(None)),None),
        'update_status':(str,32),'adapter_printer':(str,32),'adapter_pager':(str,32),'adapter_pos':(str,32),
    }
    unknown=set(data)-set(allowed)
    if unknown:
        raise ValueError('diagnostic_contains_disallowed_fields')
    clean={}
    for key,value in data.items():
        expected,max_len=allowed[key]
        if not isinstance(value,expected):
            raise ValueError(f'invalid_diagnostic_{key}')
        if isinstance(value,str):
            value=value[:max_len]
        elif isinstance(value,(int,float)) and value is not None:
            value=max(0,value)
        clean[key]=value
    return clean


def next_diagnostic_request(device):
    qs=device.diagnostic_requests.filter(status=DiagnosticRequest.Status.PENDING).order_by('created_at')
    for request in qs:
        if request.is_expired():
            request.status=DiagnosticRequest.Status.EXPIRED
            request.save(update_fields=['status','updated_at'])
            continue
        return request
    return None


def safe_event_text(value,max_len):
    text=str(value or '')[:max_len]
    if text and not SAFE_TEXT.fullmatch(text):
        raise ValueError('event_field_not_safe')
    return text
