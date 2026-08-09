from django.core import signing
from django.contrib.auth.hashers import make_password, check_password
from .models import User, ManagerOverrideCredential
from .permissions import has_perm

SALT='cafino.manager.override.v1'
MAX_AGE_SECONDS=120

def set_manager_pin(user,pin):
    pin=str(pin or '')
    if not pin.isdigit() or not 4 <= len(pin) <= 8:
        raise ValueError('PIN باید ۴ تا ۸ رقم باشد')
    cred,_=ManagerOverrideCredential.objects.get_or_create(user=user,defaults={'pin_hash':make_password(pin)})
    cred.pin_hash=make_password(pin);cred.is_active=True;cred.save()
    return cred

def issue_override(*,branch,pin,permission_code):
    candidates=User.objects.filter(branch=branch,is_active=True,role__in=[User.Role.OWNER,User.Role.MANAGER]).select_related('manager_override')
    for user in candidates:
        try: cred=user.manager_override
        except ManagerOverrideCredential.DoesNotExist: continue
        if cred.is_active and check_password(str(pin),cred.pin_hash) and has_perm(user,permission_code):
            return signing.dumps({'manager_id':user.id,'branch_id':branch.id,'permission':permission_code},salt=SALT,compress=True),user
    raise ValueError('PIN مدیر معتبر نیست')

def validate_override(token,*,branch,permission_code):
    if not token:return None
    try:data=signing.loads(token,salt=SALT,max_age=MAX_AGE_SECONDS)
    except signing.BadSignature:return None
    if int(data.get('branch_id',0))!=int(branch.id) or data.get('permission')!=permission_code:return None
    try:user=User.objects.get(pk=data['manager_id'],is_active=True)
    except User.DoesNotExist:return None
    return user if has_perm(user,permission_code) else None
