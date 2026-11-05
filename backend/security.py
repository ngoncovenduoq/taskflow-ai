"""Browser-request safeguards for the localhost-only TaskFlow AI dashboard.

These checks reduce DNS-rebinding and cross-site request risks. They are not
authentication: never expose this application on a public network without an
independent authentication layer.
"""

from urllib.parse import urlsplit


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _host_and_port(scheme: str, authority: str) -> tuple[str, int] | None:
    """Parse one Host/Origin authority, rejecting userinfo and malformed ports."""
    if not authority or any(char in authority for char in "/?#@\\"):
        return None
    try:
        parsed = urlsplit(f"{scheme}://{authority}")
        if parsed.netloc != authority or not parsed.hostname:
            return None
        port = parsed.port
    except ValueError:
        return None
    return parsed.hostname.lower(), port or (443 if scheme == "https" else 80)


def is_allowed_browser_request(
    method: str,
    scheme: str,
    host: str,
    origin: str | None = None,
    fetch_site: str | None = None,
) -> bool:
    """Allow normal localhost traffic, but reject foreign hosts and unsafe origins."""
    scheme = scheme.lower()
    if scheme not in {"http", "https"}:
        return False
    authority = _host_and_port(scheme, host)
    if authority is None or authority[0] not in LOCAL_HOSTS:
        return False

    if method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return True

    if (fetch_site or "").lower() == "cross-site":
        return False

    if origin is not None:
        try:
            parsed = urlsplit(origin)
        except ValueError:
            return False
        if parsed.scheme != scheme or parsed.path or parsed.query or parsed.fragment:
            return False
        return _host_and_port(scheme, parsed.netloc) == authority

    # A browser reporting same-site without Origin does not prove same-origin.
    # Requests from curl/PowerShell usually have neither of these headers.
    return (fetch_site or "").lower() not in {"same-site"}
