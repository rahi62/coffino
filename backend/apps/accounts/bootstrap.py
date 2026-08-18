import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.businesses.models import Branch, Business


class BootstrapError(ValueError):
    pass


def validate_owner_password(password, *, user, business_name):
    password = str(password or "")
    if len(password) < 12:
        raise BootstrapError("Owner password must be at least 12 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise BootstrapError("Owner password must contain at least one Latin letter and one digit.")
    lowered = password.casefold()
    if user.username and user.username.casefold() in lowered:
        raise BootstrapError("Owner password must not contain the username.")
    normalized_business = "".join(str(business_name).casefold().split())
    if len(normalized_business) >= 4 and normalized_business in "".join(lowered.split()):
        raise BootstrapError("Owner password must not contain the business name.")
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        raise BootstrapError("Password validation failed: " + "; ".join(exc.messages)) from exc


def _one_or_none(queryset, duplicate_message):
    rows = list(queryset.order_by("id")[:2])
    if len(rows) > 1:
        raise BootstrapError(duplicate_message)
    return rows[0] if rows else None


@transaction.atomic
def bootstrap_business_owner(
    *,
    business_name,
    username,
    password="",
    email="",
    branch_name="Main",
    business_type="CAFE",
    deployment_type="SAAS",
    reset_password=False,
    require_empty=False,
):
    User = get_user_model()
    business_name = str(business_name or "").strip()
    username = str(username or "").strip()
    email = str(email or "").strip()
    branch_name = str(branch_name or "").strip()
    business_type = str(business_type or "CAFE").strip().upper()
    deployment_type = str(deployment_type or "SAAS").strip().upper()
    password = str(password or "")

    if require_empty and (Business.objects.exists() or User.objects.exists()):
        raise BootstrapError("Cafino has already been initialized. First-run setup is permanently closed for this database.")
    if not business_name or not username or not branch_name:
        raise BootstrapError("business-name, username, and branch-name must not be blank.")
    if len(business_name) > 160 or len(branch_name) > 160:
        raise BootstrapError("Business/branch name is too long.")
    if len(username) > 150:
        raise BootstrapError("Username is too long.")
    if len(email) > 254:
        raise BootstrapError("Email is too long.")
    if len(business_type) > 32:
        raise BootstrapError("business-type is too long.")
    if deployment_type not in {"LOCAL", "SAAS", "DEDICATED"}:
        raise BootstrapError("deployment-type is invalid.")

    business = _one_or_none(
        Business.objects.filter(name=business_name),
        "More than one business has this exact name; use a unique business name before bootstrapping.",
    )
    if business:
        if business.deployment_type != deployment_type:
            raise BootstrapError(
                f"Existing business deployment_type is {business.deployment_type}, not {deployment_type}."
            )
        if not business.is_active:
            business.is_active = True
            business.save(update_fields=["is_active", "updated_at"])
        business_created = False
    else:
        business = Business.objects.create(
            name=business_name,
            business_type=business_type,
            deployment_type=deployment_type,
            is_active=True,
        )
        business_created = True

    branch = _one_or_none(
        Branch.objects.filter(business=business, name=branch_name),
        "More than one branch has this exact name in the business; resolve duplicates first.",
    )
    if branch:
        branch_created = False
        if not branch.is_active:
            branch.is_active = True
            branch.save(update_fields=["is_active", "updated_at"])
    else:
        branch = Branch.objects.create(business=business, name=branch_name, is_active=True)
        branch_created = True

    existing = User.objects.filter(username=username).first()
    if existing:
        if existing.business_id != business.id or existing.role != User.Role.OWNER:
            raise BootstrapError("Username already belongs to another business or non-OWNER account.")
        changed = []
        if not existing.is_active:
            existing.is_active = True
            changed.append("is_active")
        if email and existing.email != email:
            existing.email = email
            changed.append("email")
        if reset_password:
            if not password:
                raise BootstrapError("Password is required when reset-password is used.")
            validate_owner_password(password, user=existing, business_name=business_name)
            existing.set_password(password)
            changed.append("password")
        if changed:
            existing.save(update_fields=changed)
        return {
            "business": business,
            "branch": branch,
            "owner": existing,
            "business_created": business_created,
            "branch_created": branch_created,
            "owner_created": False,
        }

    if not password:
        raise BootstrapError("Owner password is required.")
    candidate = User(
        username=username,
        email=email,
        business=business,
        branch=None,
        role=User.Role.OWNER,
        is_active=True,
    )
    validate_owner_password(password, user=candidate, business_name=business_name)
    candidate.set_password(password)
    candidate.save()
    return {
        "business": business,
        "branch": branch,
        "owner": candidate,
        "business_created": business_created,
        "branch_created": branch_created,
        "owner_created": True,
    }
