from rest_framework import serializers

from .phone import normalize_iran_mobile


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unknown = set(data.keys()) - set(self.fields.keys())
            if unknown:
                raise serializers.ValidationError(
                    {field: "ارسال این فیلد مجاز نیست." for field in sorted(unknown)}
                )
        return super().to_internal_value(data)


class RegistrationOtpRequestSerializer(StrictSerializer):
    mobile = serializers.CharField(max_length=32)

    def validate_mobile(self, value):
        try:
            return normalize_iran_mobile(value)
        except Exception as exc:
            raise serializers.ValidationError("شماره همراه معتبر نیست؛ نمونه صحیح: ۰۹۱۲۳۴۵۶۷۸۹") from exc


class OtpVerifySerializer(StrictSerializer):
    challenge_id = serializers.UUIDField()
    code = serializers.RegexField(r"^\d{6}$", error_messages={"invalid": "کد باید دقیقاً ۶ رقم باشد."})


class SaasRegistrationSerializer(StrictSerializer):
    BUSINESS_TYPES = (
        "CAFE",
        "RESTAURANT",
        "FAST_FOOD",
        "BAKERY",
        "PASTRY",
        "CATERING",
        "HOTEL_RESTAURANT",
        "OTHER",
    )

    business_name = serializers.CharField(max_length=160, trim_whitespace=True)
    business_type = serializers.ChoiceField(choices=BUSINESS_TYPES, default="CAFE")
    branch_name = serializers.CharField(max_length=160, trim_whitespace=True)
    branch_phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    copy_owner_mobile_to_branch = serializers.BooleanField(required=False, default=False)
    username = serializers.RegexField(
        r"^[\w.@+-]+$",
        max_length=150,
        error_messages={"invalid": "نام کاربری فقط می‌تواند شامل حروف، عدد و نشانه‌های . @ + - _ باشد."},
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirmation = serializers.CharField(write_only=True, trim_whitespace=False)
    verification_grant = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "گذرواژه و تکرار آن باید یکسان باشند."}
            )
        return attrs
