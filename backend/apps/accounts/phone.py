import re

from django.core.exceptions import ValidationError


_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_iran_mobile(value: str) -> str:
    raw = str(value or "").translate(_DIGIT_TRANSLATION).strip()
    compact = re.sub(r"[\s\-()]", "", raw)
    if compact.startswith("+98"):
        compact = "0" + compact[3:]
    elif compact.startswith("0098"):
        compact = "0" + compact[4:]
    elif compact.startswith("98"):
        compact = "0" + compact[2:]
    elif len(compact) == 10 and compact.startswith("9"):
        compact = "0" + compact

    if not re.fullmatch(r"09\d{9}", compact):
        raise ValidationError("شماره همراه معتبر نیست؛ نمونه صحیح: ۰۹۱۲۳۴۵۶۷۸۹")
    return compact


def mask_mobile(value: str) -> str:
    mobile = normalize_iran_mobile(value)
    return f"{mobile[:4]}***{mobile[-4:]}"
