import base64
import re
import requests

UA = "proxy-aggregator/1.0"

def fetch_url(url: str, timeout: int = 25) -> tuple[bytes, str]:
    # URL fragments are client-side and are intentionally not sent to the server.
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": UA, "Accept": "*/*"},
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.content, response.headers.get("content-type", "")

def _b64decode_loose(text: str) -> str | None:
    s = re.sub(r"\s+", "", text)
    if len(s) < 16:
        return None
    # Avoid treating ordinary URLs as base64.
    if re.search(r"[^A-Za-z0-9+/=_-]", s):
        return None
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    try:
        raw = base64.b64decode(s, validate=False)
        decoded = raw.decode("utf-8", errors="replace")
    except Exception:
        return None
    if any(x in decoded for x in ("vless://", "vmess://", "trojan://", "ss://", "proxies:", "proxy-groups:")):
        return decoded
    return None

def decode_subscription(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace").strip()
    decoded = _b64decode_loose(text)
    if decoded:
        return decoded
    return text
