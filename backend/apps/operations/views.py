import re
from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.accounts.permissions import has_perm
from apps.businesses.models import Branch, Business
from apps.core.tenancy import tenant_business
from .models import DeviceEvent, DeviceInstallation, DiagnosticRequest, ReleasePolicy
from .serializers import DeviceSerializer, DiagnosticRequestSerializer, ReleasePolicySerializer
from .services import (
    HEX64,authenticate_device_token,next_diagnostic_request,policy_for_device,
    register_device,safe_event_text,sanitize_diagnostic_snapshot,
)


class OpsDeviceThrottle(AnonRateThrottle):
    scope='ops_device'


def _reject_unknown(request,allowed):
    unknown=set(request.data.keys())-set(allowed)
    if unknown:
        return Response({'detail':'Payload contains unsupported fields.','fields':sorted(unknown)},status=400)
    return None


def _bearer(request):
    value=str(request.headers.get('Authorization') or '')
    if not value.lower().startswith('bearer '):
        return ''
    return value.split(' ',1)[1].strip()


def _device_or_401(request):
    device=authenticate_device_token(_bearer(request))
    if not device:
        return None,Response({'detail':'Invalid device token.'},status=401)
    return device,None


def _scope_devices(user):
    qs=DeviceInstallation.objects.select_related('business','branch').all()
    if user.is_superuser:
        return qs
    if not has_perm(user,'operations.view'):
        return qs.none()
    business=tenant_business(user)
    return qs.filter(business=business) if business else qs.none()


def _can_manage_device(user,device):
    if user.is_superuser:
        return True
    if not has_perm(user,'operations.manage'):
        return False
    business=tenant_business(user)
    return bool(business and device.business_id==business.id)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OpsDeviceThrottle])
def device_register(request):
    rejected=_reject_unknown(request,{
        'license_document','machine_hash','installation_id','current_version','channel',
        'platform','arch','telemetry_enabled',
    })
    if rejected:return rejected
    document=request.data.get('license_document')
    if len(str(document))>16000:
        return Response({'detail':'License document too large.'},status=400)
    try:
        device,token=register_device(
            document=document,
            machine_hash=request.data.get('machine_hash',''),
            installation_id=request.data.get('installation_id',''),
            current_version=request.data.get('current_version',''),
            channel=request.data.get('channel','stable'),
            platform=request.data.get('platform',''),
            arch=request.data.get('arch',''),
            telemetry_enabled=bool(request.data.get('telemetry_enabled',False)),
        )
    except RuntimeError:
        return Response({'detail':'Operations license verifier is not configured.'},status=503)
    except ValueError as exc:
        return Response({'detail':str(exc)},status=400)
    return Response({
        'device_id':device.id,
        'installation_id':str(device.installation_id),
        'device_token':token,
        'policy':policy_for_device(device),
    },status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OpsDeviceThrottle])
def device_heartbeat(request):
    rejected=_reject_unknown(request,{
        'current_version','channel','platform','arch','app_health','telemetry_enabled',
        'last_backup_at','last_backup_ok','last_update_status',
    })
    if rejected:return rejected
    device,error=_device_or_401(request)
    if error:return error
    health=str(request.data.get('app_health') or DeviceInstallation.Health.UNKNOWN)
    if health not in dict(DeviceInstallation.Health.choices):
        return Response({'detail':'Invalid app_health.'},status=400)
    channel=str(request.data.get('channel') or device.release_channel)
    if channel not in dict(DeviceInstallation.Channel.choices):
        return Response({'detail':'Invalid release channel.'},status=400)
    device.current_version=str(request.data.get('current_version') or device.current_version)[:40]
    device.release_channel=channel
    device.platform=str(request.data.get('platform') or device.platform)[:32]
    device.arch=str(request.data.get('arch') or device.arch)[:32]
    device.app_health=health
    device.telemetry_enabled=bool(request.data.get('telemetry_enabled',device.telemetry_enabled))
    device.last_update_status=str(request.data.get('last_update_status') or '')[:32]
    backup_at=request.data.get('last_backup_at')
    if backup_at:
        from django.utils.dateparse import parse_datetime
        parsed=parse_datetime(str(backup_at))
        if parsed is None:
            return Response({'detail':'Invalid last_backup_at.'},status=400)
        device.last_backup_at=parsed
    if 'last_backup_ok' in request.data:
        device.last_backup_ok=bool(request.data.get('last_backup_ok'))
    device.last_seen_at=timezone.now()
    device.save()
    diagnostic=next_diagnostic_request(device)
    return Response({
        'ok':True,
        'policy':policy_for_device(device),
        'diagnostic_request_id':str(diagnostic.request_id) if diagnostic else None,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([OpsDeviceThrottle])
def device_policy(request):
    device,error=_device_or_401(request)
    if error:return error
    return Response(policy_for_device(device))


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OpsDeviceThrottle])
def device_event(request):
    rejected=_reject_unknown(request,{'event_type','severity','app_version','component','code','fingerprint','occurred_at'})
    if rejected:return rejected
    device,error=_device_or_401(request)
    if error:return error
    if not device.telemetry_enabled:
        return Response({'detail':'Telemetry is disabled for this installation.'},status=403)
    event_type=str(request.data.get('event_type') or '')
    severity=str(request.data.get('severity') or DeviceEvent.Severity.INFO)
    if event_type not in dict(DeviceEvent.Type.choices) or severity not in dict(DeviceEvent.Severity.choices):
        return Response({'detail':'Invalid event type or severity.'},status=400)
    fingerprint=str(request.data.get('fingerprint') or '').lower()
    if fingerprint and not HEX64.fullmatch(fingerprint):
        return Response({'detail':'Invalid event fingerprint.'},status=400)
    try:
        component=safe_event_text(request.data.get('component',''),48)
        code=safe_event_text(request.data.get('code',''),80)
    except ValueError as exc:
        return Response({'detail':str(exc)},status=400)
    occurred_at=timezone.now()
    if request.data.get('occurred_at'):
        from django.utils.dateparse import parse_datetime
        parsed=parse_datetime(str(request.data.get('occurred_at')))
        if parsed is None:
            return Response({'detail':'Invalid occurred_at.'},status=400)
        occurred_at=parsed
    event=DeviceEvent.objects.create(
        installation=device,event_type=event_type,severity=severity,
        app_version=str(request.data.get('app_version') or device.current_version)[:40],
        component=component,code=code,fingerprint=fingerprint,occurred_at=occurred_at,
    )
    if event_type==DeviceEvent.Type.CRASH:
        device.last_crash_at=event.occurred_at
        device.save(update_fields=['last_crash_at','updated_at'])
    return Response({'ok':True,'event_id':event.id},status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OpsDeviceThrottle])
def device_diagnostic_submit(request):
    rejected=_reject_unknown(request,{'request_id','snapshot'})
    if rejected:return rejected
    device,error=_device_or_401(request)
    if error:return error
    diagnostic=get_object_or_404(DiagnosticRequest,request_id=request.data.get('request_id'),installation=device)
    if diagnostic.status!=DiagnosticRequest.Status.PENDING or diagnostic.is_expired():
        return Response({'detail':'Diagnostic request is not active.'},status=409)
    try:
        snapshot=sanitize_diagnostic_snapshot(request.data.get('snapshot'))
    except ValueError as exc:
        return Response({'detail':str(exc)},status=400)
    diagnostic.snapshot=snapshot
    diagnostic.status=DiagnosticRequest.Status.COMPLETED
    diagnostic.completed_at=timezone.now()
    diagnostic.save(update_fields=['snapshot','status','completed_at','updated_at'])
    return Response({'ok':True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def management_devices(request):
    if not has_perm(request.user,'operations.view'):
        return Response({'detail':'Permission denied.'},status=403)
    return Response(DeviceSerializer(_scope_devices(request.user),many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def management_assign_device(request,pk):
    if not request.user.is_superuser:
        return Response({'detail':'Platform admin required.'},status=403)
    device=get_object_or_404(DeviceInstallation,pk=pk)
    business=None;branch=None
    if request.data.get('business') is not None:
        business=get_object_or_404(Business,pk=request.data.get('business'))
    if request.data.get('branch') is not None:
        branch=get_object_or_404(Branch.objects.select_related('business'),pk=request.data.get('branch'))
        if business and branch.business_id!=business.id:
            return Response({'detail':'Branch does not belong to business.'},status=400)
        business=business or branch.business
    device.business=business;device.branch=branch
    device.save(update_fields=['business','branch','updated_at'])
    return Response(DeviceSerializer(device).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def management_request_diagnostic(request,pk):
    device=get_object_or_404(DeviceInstallation,pk=pk)
    if not _can_manage_device(request.user,device):
        return Response({'detail':'Permission denied.'},status=403)
    device.diagnostic_requests.filter(status=DiagnosticRequest.Status.PENDING).update(status=DiagnosticRequest.Status.CANCELLED)
    diagnostic=DiagnosticRequest.objects.create(
        installation=device,
        requested_by_label=(request.user.get_full_name() or request.user.username)[:160],
        expires_at=timezone.now()+timedelta(hours=24),
    )
    return Response(DiagnosticRequestSerializer(diagnostic).data,status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def management_diagnostics(request,pk):
    device=get_object_or_404(DeviceInstallation,pk=pk)
    if not (request.user.is_superuser or (has_perm(request.user,'operations.view') and device in _scope_devices(request.user))):
        return Response({'detail':'Permission denied.'},status=403)
    return Response(DiagnosticRequestSerializer(device.diagnostic_requests.all()[:20],many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def management_summary(request):
    if not has_perm(request.user,'operations.view'):
        return Response({'detail':'Permission denied.'},status=403)
    qs=_scope_devices(request.user)
    now=timezone.now();day=now-timedelta(hours=24);week=now-timedelta(days=7)
    events=DeviceEvent.objects.filter(installation__in=qs,occurred_at__gte=day)
    versions=list(qs.values('current_version','release_channel','app_health').annotate(count=Count('id')).order_by('-count')[:50])
    event_counts=list(events.values('event_type','app_version').annotate(count=Count('id')).order_by('-count')[:50])
    return Response({
        'devices_total':qs.count(),
        'online_now':qs.filter(last_seen_at__gte=now-timedelta(minutes=15)).count(),
        'seen_24h':qs.filter(last_seen_at__gte=day).count(),
        'seen_7d':qs.filter(last_seen_at__gte=week).count(),
        'degraded':qs.filter(app_health=DeviceInstallation.Health.DEGRADED).count(),
        'versions':versions,
        'events_24h':event_counts,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def management_policies(request):
    if not has_perm(request.user,'operations.view'):
        return Response({'detail':'Permission denied.'},status=403)
    return Response(ReleasePolicySerializer(ReleasePolicy.objects.all(),many=True).data)


@api_view(['PUT','PATCH'])
@permission_classes([IsAuthenticated])
def management_policy_detail(request,channel):
    if not request.user.is_superuser:
        return Response({'detail':'Platform admin required.'},status=403)
    if channel not in {'stable','beta'}:
        return Response({'detail':'Invalid channel.'},status=404)
    policy,_=ReleasePolicy.objects.get_or_create(channel=channel)
    serializer=ReleasePolicySerializer(policy,data=request.data,partial=request.method=='PATCH')
    serializer.is_valid(raise_exception=True)
    serializer.save(channel=channel)
    return Response(serializer.data)
