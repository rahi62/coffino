from django.core.exceptions import PermissionDenied
from django.db import models

from apps.accounts.permissions import has_perm
from apps.businesses.models import Business, Branch


def tenant_business(user):
    """Return the user's business. Only a Django superuser is platform-global."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return None
    if getattr(user, "business_id", None):
        return user.business
    if getattr(user, "branch_id", None):
        return user.branch.business
    return None


def require_tenant_business(user):
    if getattr(user, "is_superuser", False):
        return None
    business=tenant_business(user)
    if business is None:
        raise PermissionDenied("کاربر به کسب‌وکار معتبری متصل نیست.")
    return business


def can_access_business(user,business):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    own=tenant_business(user)
    return bool(own and business and own.pk==business.pk)


def can_access_branch(user,branch,*,cross_permission="branches.dashboard"):
    if not user or not user.is_authenticated or branch is None:
        return False
    if user.is_superuser:
        return True
    own_business=tenant_business(user)
    if own_business is None or branch.business_id!=own_business.id:
        return False
    if not getattr(user,"branch_id",None):
        # A business owner may use their sole active branch without cross-branch privileges.
        # This does not grant access to another business or multiple-branch navigation.
        if getattr(user,'role',None)=='OWNER' and branch.is_active:
            # Preserve access to the original business branch when another
            # branch is created but MULTI_BRANCH is disabled. This does not
            # grant access to newly created sibling branches.
            primary=Branch.objects.filter(business=own_business).order_by('created_at','pk').first()
            if primary and branch.pk==primary.pk:
                return True
            active=Branch.objects.filter(business=own_business,is_active=True)
            if active.count()==1 and active.filter(pk=branch.pk).exists():
                return True
        return has_perm(user,cross_permission)
    return branch.id==user.branch_id or has_perm(user,cross_permission)


def assert_business_access(user,business):
    if not can_access_business(user,business):
        raise PermissionDenied("دسترسی به این کسب‌وکار مجاز نیست.")
    return business


def assert_branch_access(user,branch,*,cross_permission="branches.dashboard"):
    if not can_access_branch(user,branch,cross_permission=cross_permission):
        raise PermissionDenied("دسترسی به این شعبه مجاز نیست.")
    return branch


def infer_business_id(obj,depth=0,seen=None):
    """Best-effort tenant inference for related model instances used in serializer writes."""
    if obj is None or depth>5 or not hasattr(obj,"_meta"):
        return None
    seen=seen or set()
    key=(obj._meta.label_lower,getattr(obj,"pk",None))
    if key in seen:
        return None
    seen.add(key)

    label=obj._meta.label_lower
    if label=="businesses.business":
        return obj.pk
    if label=="businesses.branch":
        return obj.business_id

    if hasattr(obj,"business_id") and getattr(obj,"business_id",None):
        return obj.business_id
    if hasattr(obj,"branch_id") and getattr(obj,"branch_id",None):
        try:
            return obj.branch.business_id
        except Exception:
            return None

    preferred=("branch","business","hall","table","order","invoice","supplier","product","item","formula","customer","payment","register","shift")
    field_names={f.name:f for f in obj._meta.fields if getattr(f,"is_relation",False) and not getattr(f,"many_to_many",False)}
    for name in preferred:
        f=field_names.get(name)
        if not f:
            continue
        try:
            rel=getattr(obj,name,None)
        except Exception:
            rel=None
        result=infer_business_id(rel,depth+1,seen)
        if result:
            return result
    return None


def infer_branch_id(obj,depth=0,seen=None):
    if obj is None or depth>5 or not hasattr(obj,"_meta"):
        return None
    seen=seen or set()
    key=(obj._meta.label_lower,getattr(obj,"pk",None))
    if key in seen:
        return None
    seen.add(key)

    label=obj._meta.label_lower
    if label=="businesses.branch":
        return obj.pk
    if hasattr(obj,"branch_id") and getattr(obj,"branch_id",None):
        return obj.branch_id

    preferred=("hall","table","order","invoice","supplier","product","item","formula","customer","payment","register","shift")
    field_names={f.name:f for f in obj._meta.fields if getattr(f,"is_relation",False) and not getattr(f,"many_to_many",False)}
    for name in preferred:
        if name not in field_names:
            continue
        try:
            rel=getattr(obj,name,None)
        except Exception:
            rel=None
        result=infer_branch_id(rel,depth+1,seen)
        if result:
            return result
    return None


def assert_related_values_scope(user,validated_data,*,cross_permission="branches.dashboard"):
    if getattr(user,"is_superuser",False):
        return
    business=require_tenant_business(user)
    for value in validated_data.values():
        if not hasattr(value,"_meta"):
            continue
        business_id=infer_business_id(value)
        if business_id and business_id!=business.id:
            raise PermissionDenied("رکورد مرتبط خارج از کسب‌وکار شماست.")
        branch_id=infer_branch_id(value)
        if branch_id and getattr(user,"branch_id",None) and branch_id!=user.branch_id and not has_perm(user,cross_permission):
            raise PermissionDenied("رکورد مرتبط خارج از شعبه مجاز شماست.")


def scope_queryset(qs,user,*,branch_path,business_path,cross_permission="branches.dashboard"):
    """Scope an arbitrary queryset by tenant. Secure default for users without a tenant."""
    if not user or not user.is_authenticated:
        return qs.none()
    if user.is_superuser:
        return qs
    business=tenant_business(user)
    if business is None:
        return qs.none()
    if getattr(user,"branch_id",None) and not has_perm(user,cross_permission):
        return qs.filter(**{branch_path:user.branch}).distinct()
    return qs.filter(**{business_path:business}).distinct()


def resolve_branch_for_user(user,branch_id=None,*,cross_permission="branches.dashboard"):
    """Resolve a branch from an explicit id or the user's branch, then enforce access."""
    if branch_id is None:
        if getattr(user,"branch_id",None):
            branch=user.branch
        else:
            business=tenant_business(user)
            if business and getattr(user,"role",None)=="OWNER":
                active=Branch.objects.filter(business=business,is_active=True)
                branch=active.first() if active.count()==1 else None
                if branch is None and not has_perm(user,cross_permission):
                    # Deterministic original branch; never choose arbitrary
                    # list order or grant cross-branch access.
                    primary=Branch.objects.filter(business=business).order_by('created_at','pk').first()
                    branch=primary if primary and primary.is_active else None
                if branch is None:
                    raise PermissionDenied("شعبه را انتخاب کنید یا دسترسی شعبه اصلی را بررسی کنید.")
            else:
                raise PermissionDenied("شناسه شعبه لازم است.")
    else:
        branch=Branch.objects.select_related("business").get(pk=branch_id)
    if not branch.is_active:
        raise PermissionDenied("شعبه غیرفعال است؛ شعبه فعال دیگری انتخاب کنید.")
    return assert_branch_access(user,branch,cross_permission=cross_permission)
