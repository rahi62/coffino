from dataclasses import dataclass
from urllib.parse import urljoin

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from apps.core.network_safety import post_json


OTP_DELIVERY_ERROR = "ارسال کد یک‌بارمصرف انجام نشد. کمی بعد دوباره تلاش کنید."


class OtpDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class OtpDeliveryResult:
    accepted: bool
    provider_code: str = ""


@dataclass(frozen=True)
class ParsGreenRuntimeConfig:
    api_base_url: str
    api_key: str
    add_name: bool
    timeout_seconds: int


class OtpSender:
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        raise NotImplementedError


class DisabledOtpSender(OtpSender):
    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        raise OtpDeliveryError(OTP_DELIVERY_ERROR)


def pars_green_env_config() -> ParsGreenRuntimeConfig:
    return ParsGreenRuntimeConfig(
        api_base_url=str(getattr(settings, "PARSGREEN_API_BASE_URL", "https://sms.parsgreen.ir")),
        api_key=str(getattr(settings, "PARSGREEN_API_KEY", "") or ""),
        add_name=bool(getattr(settings, "PARSGREEN_OTP_ADD_NAME", True)),
        timeout_seconds=int(getattr(settings, "PARSGREEN_TIMEOUT_SECONDS", 10)),
    )


def pars_green_db_config():
    """Return (row_exists, runtime_config_or_none).

    Once a database row exists it is authoritative. Disabled or incomplete
    database configuration therefore fails closed instead of falling back to env.
    Before the migration/table exists, env behavior remains backward compatible.
    """
    from .models import PlatformOtpProviderConfig

    try:
        row = PlatformOtpProviderConfig.objects.filter(
            provider=PlatformOtpProviderConfig.Provider.PARSGREEN
        ).first()
    except (OperationalError, ProgrammingError):
        return False, None

    if row is None:
        return False, None
    if not row.enabled:
        return True, None

    api_key = row.get_api_key()
    if not api_key:
        return True, None

    return True, ParsGreenRuntimeConfig(
        api_base_url=row.api_base_url,
        api_key=api_key,
        add_name=row.add_name,
        timeout_seconds=row.timeout_seconds,
    )


class ParsGreenOtpSender(OtpSender):
    def __init__(self, config: ParsGreenRuntimeConfig | None = None):
        self.config = config or pars_green_env_config()

    def send(self, *, mobile: str, code: str, correlation_id: str) -> OtpDeliveryResult:
        config = self.config
        if not config.api_key:
            raise OtpDeliveryError(OTP_DELIVERY_ERROR)

        endpoint = urljoin(config.api_base_url.rstrip("/") + "/", "Apiv2/Message/SendOtp")
        try:
            response = post_json(
                endpoint,
                {
                    "Mobile": mobile,
                    "SmsCode": code,
                    "AddName": config.add_name,
                },
                headers={"Authorization": f"basic apikey:{config.api_key}"},
                timeout=config.timeout_seconds,
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
        return OtpDeliveryResult(
            accepted=True,
            provider_code=str(response.get("R_Code", "")),
        )


def sender_from_platform_config(row) -> OtpSender:
    if not row.enabled or not row.credentials_configured:
        return DisabledOtpSender()
    return ParsGreenOtpSender(
        ParsGreenRuntimeConfig(
            api_base_url=row.api_base_url,
            api_key=row.get_api_key(),
            add_name=row.add_name,
            timeout_seconds=row.timeout_seconds,
        )
    )


def get_otp_sender() -> OtpSender:
    # Production-only: never allow a fake/custom sender to bypass real SMS delivery.
    # The global DB provider takes precedence; absent DB config uses the
    # configured ParsGreen provider only when explicitly enabled.
    row_exists, db_config = pars_green_db_config()
    if row_exists:
        return ParsGreenOtpSender(db_config) if db_config else DisabledOtpSender()

    if getattr(settings, "PARSGREEN_OTP_ENABLED", False):
        return ParsGreenOtpSender()
    return DisabledOtpSender()
