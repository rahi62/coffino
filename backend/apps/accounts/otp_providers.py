import base64
from dataclasses import dataclass
from urllib.parse import urljoin

from django.conf import settings
from django.utils.module_loading import import_string

from apps.core.network_safety import post_json


OTP_DELIVERY_ERROR = "ارسال کد یک‌بارمصرف انجام نشد. کمی بعد دوباره تلاش کنید."


class OtpDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class OtpDeliveryResult:
    accepted: bool
    provider_code: str = ""


class OtpSender:
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        raise NotImplementedError


class DisabledOtpSender(OtpSender):
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        raise OtpDeliveryError(OTP_DELIVERY_ERROR)


class FakeOtpSender(OtpSender):
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        return OtpDeliveryResult(accepted=True, provider_code="FAKE")


class ParsGreenOtpSender(OtpSender):
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        api_key = str(getattr(settings, "PARSGREEN_API_KEY", "") or "")
        signature = str(getattr(settings, "PARSGREEN_SIGNATURE", "") or "")
        if not api_key or not signature:
            raise OtpDeliveryError(OTP_DELIVERY_ERROR)

        credentials = base64.b64encode(f"{api_key}:{signature}".encode("utf-8")).decode("ascii")
        base_url = str(getattr(settings, "PARSGREEN_API_BASE_URL", "https://sms.parsgreen.ir"))
        endpoint = urljoin(base_url.rstrip("/") + "/", "Apiv2/Message/SendOtp")
        try:
            response = post_json(
                endpoint,
                {
                    "Mobile": mobile,
                    "SmsCode": code,
                    "AddName": bool(getattr(settings, "PARSGREEN_OTP_ADD_NAME", True)),
                },
                headers={"Authorization": f"Basic {credentials}"},
                timeout=int(getattr(settings, "PARSGREEN_TIMEOUT_SECONDS", 10)),
                allow_private=False,
                require_https=True,
            )
        except OtpDeliveryError:
            raise
        except Exception as exc:
            raise OtpDeliveryError(OTP_DELIVERY_ERROR) from exc

        if not isinstance(response, dict) or not isinstance(response.get("R_Success"), bool):
            raise OtpDeliveryError(OTP_DELIVERY_ERROR)
        if response["R_Success"] is not True:
            raise OtpDeliveryError(OTP_DELIVERY_ERROR)
        return OtpDeliveryResult(accepted=True, provider_code=str(response.get("R_Code", "")))


def get_otp_sender() -> OtpSender:
    sender_path = getattr(
        settings,
        "CAF_INO_OTP_SENDER",
        "apps.accounts.otp_providers.DisabledOtpSender",
    )
    return import_string(sender_path)()
