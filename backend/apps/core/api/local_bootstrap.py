from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.bootstrap import BootstrapError, bootstrap_business_owner
from apps.businesses.models import Business


def _local_bootstrap_enabled():
    engine = str(settings.DATABASES.get("default", {}).get("ENGINE") or "")
    return str(getattr(settings, "ENVIRONMENT", "")).lower() == "local" and engine.endswith("sqlite3")


def _needs_setup():
    User = get_user_model()
    return not Business.objects.exists() and not User.objects.exists()


@api_view(["GET", "POST"])
@permission_classes([permissions.AllowAny])
def local_bootstrap(request):
    if not _local_bootstrap_enabled():
        return Response({"detail": "Local first-run setup is not available in this deployment."}, status=404)

    needs_setup = _needs_setup()
    if request.method == "GET":
        return Response({"available": True, "needs_setup": needs_setup})

    if not needs_setup:
        return Response(
            {"detail": "Cafino has already been initialized. First-run setup is closed."},
            status=status.HTTP_409_CONFLICT,
        )

    data = request.data or {}
    password = str(data.get("password") or "")
    confirmation = str(data.get("password_confirmation") or "")
    if password != confirmation:
        return Response({"detail": "Password confirmation does not match."}, status=400)

    try:
        result = bootstrap_business_owner(
            business_name=data.get("business_name"),
            username=data.get("username"),
            email=data.get("email") or "",
            branch_name=data.get("branch_name") or "Main",
            business_type=data.get("business_type") or "CAFE",
            deployment_type="LOCAL",
            password=password,
            require_empty=True,
        )
    except BootstrapError as exc:
        return Response({"detail": str(exc)}, status=400)

    return Response(
        {
            "ok": True,
            "business": {"id": result["business"].id, "name": result["business"].name},
            "branch": {"id": result["branch"].id, "name": result["branch"].name},
            "owner": {"id": result["owner"].id, "username": result["owner"].username},
        },
        status=status.HTTP_201_CREATED,
    )
