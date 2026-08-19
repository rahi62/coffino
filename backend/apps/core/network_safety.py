import ipaddress
import json
import socket
import urllib.request
from urllib.parse import urlparse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unsafe_ip(value):
    ip = ipaddress.ip_address(value)
    return (
        ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_private
    )


def validate_http_target(url, *, allow_private=False, require_https=False, resolve=True):
    parsed = urlparse(str(url or ""))
    allowed_schemes = {"https"} if require_https else {"http", "https"}
    if parsed.scheme not in allowed_schemes or not parsed.hostname:
        if require_https:
            raise ValueError("Provider URL must be a valid HTTPS URL.")
        raise ValueError("Provider URL must be a valid HTTP/HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials inside provider URLs are not allowed.")

    # Even config-only checks (resolve=False) must reject literal private IPs.
    # Hostname DNS is intentionally deferred until live/send time so a temporary
    # DNS outage does not make a saved configuration look syntactically invalid.
    try:
        if _unsafe_ip(parsed.hostname) and not allow_private:
            raise ValueError("Private/internal provider addresses are blocked in server deployments.")
    except ValueError as exc:
        if str(exc).startswith("Private/internal"):
            raise
        # Hostname rather than an IP literal; DNS handling continues below when requested.
        pass

    if not resolve:
        return parsed

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("Provider hostname cannot be resolved.") from exc
    if not addresses:
        raise ValueError("Provider hostname did not resolve to an address.")

    for item in addresses:
        try:
            address = item[4][0]
            if _unsafe_ip(address) and not allow_private:
                raise ValueError("Private/internal provider addresses are blocked in server deployments.")
        except ValueError as exc:
            if str(exc).startswith("Private/internal"):
                raise
            continue
    return parsed


def no_redirect_opener():
    return urllib.request.build_opener(NoRedirect())


def post_json(
    url,
    payload,
    *,
    headers=None,
    timeout=15,
    allow_private=False,
    require_https=False,
    max_response_bytes=1024 * 1024,
):
    validate_http_target(url, allow_private=allow_private, require_https=require_https)
    request = urllib.request.Request(
        str(url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})},
        method="POST",
    )
    opener = no_redirect_opener()
    with opener.open(request, timeout=max(1, min(int(timeout or 15), 120))) as response:
        code = int(getattr(response, "status", 200) or 200)
        if code < 200 or code >= 300:
            raise ValueError(f"Provider returned HTTP {code}.")
        raw = response.read(max_response_bytes + 1)
        if len(raw) > max_response_bytes:
            raise ValueError("Provider response exceeded the safe size limit.")
        if not raw.strip():
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Provider returned invalid JSON.") from exc
