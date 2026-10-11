import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class OwnerPasswordError(ValueError):
    pass


def validate_owner_password(password, *, user, business_name):
    password = str(password or "")
    if len(password) < 12:
        raise OwnerPasswordError("گذرواژه باید دست‌کم ۱۲ نویسه داشته باشد.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise OwnerPasswordError("گذرواژه باید دست‌کم یک حرف لاتین و یک عدد داشته باشد.")
    lowered = password.casefold()
    if user.username and user.username.casefold() in lowered:
        raise OwnerPasswordError("گذرواژه نباید شامل نام کاربری باشد.")
    normalized_business = "".join(str(business_name).casefold().split())
    if len(normalized_business) >= 4 and normalized_business in "".join(lowered.split()):
        raise OwnerPasswordError("گذرواژه نباید شامل نام کسب‌وکار باشد.")
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        raise OwnerPasswordError("گذرواژه شرایط امنیتی لازم را ندارد: " + "؛ ".join(exc.messages)) from exc
