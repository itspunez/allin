import base64
import json
import urllib.parse
import yaml

SCHEMES = {"vless", "vmess", "trojan", "ss"}

def _split_lines(text: str):
    return [x.strip() for x in text.splitlines() if x.strip()]

def _parse_vless(url):
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    return {
        "protocol": "vless",
        "host": u.hostname or "",
        "port": int(u.port or 0),
        "id": u.username or "",
        "security": (q.get("security") or [""])[0],
        "sni": (q.get("sni") or [""])[0],
        "path": (q.get("path") or [""])[0],
        "type": (q.get("type") or q.get("network") or [""])[0],
        "remark": urllib.parse.unquote(u.fragment or ""),
        "raw": url,
    }

def _parse_trojan(url):
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    return {
        "protocol": "trojan",
        "host": u.hostname or "",
        "port": int(u.port or 0),
        "id": u.username or "",
        "security": (q.get("security") or [""])[0],
        "sni": (q.get("sni") or [""])[0],
        "path": (q.get("path") or [""])[0],
        "type": (q.get("type") or q.get("network") or [""])[0],
        "remark": urllib.parse.unquote(u.fragment or ""),
        "raw": url,
    }

def _parse_ss(url):
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    return {
        "protocol": "ss",
        "host": u.hostname or "",
        "port": int(u.port or 0),
        "id": u.username or "",
        "security": (q.get("security") or [""])[0],
        "sni": (q.get("sni") or [""])[0],
        "path": (q.get("path") or [""])[0],
        "type": "",
        "remark": urllib.parse.unquote(u.fragment or ""),
        "raw": url,
    }

def _parse_vmess(url):
    payload = url[len("vmess://"):]
    payload += "=" * (-len(payload) % 4)
    try:
        obj = json.loads(base64.b64decode(payload).decode("utf-8"))
    except Exception:
        return None
    return {
        "protocol": "vmess",
        "host": obj.get("add", ""),
        "port": int(obj.get("port", 0) or 0),
        "id": obj.get("id", ""),
        "security": obj.get("scy", ""),
        "sni": obj.get("sni", ""),
        "path": obj.get("path", ""),
        "type": obj.get("net", ""),
        "remark": obj.get("ps", ""),
        "raw": url,
    }

def parse_url(url):
    scheme = url.split("://", 1)[0].lower()
    if scheme == "vless":
        return _parse_vless(url)
    if scheme == "vmess":
        return _parse_vmess(url)
    if scheme == "trojan":
        return _parse_trojan(url)
    if scheme == "ss":
        return _parse_ss(url)
    return None

def parse_text(text: str):
    out = []
    # URL-oriented subscriptions
    for line in _split_lines(text):
        item = parse_url(line)
        if item:
            out.append(item)

    # Clash/Mihomo-style YAML
    try:
        doc = yaml.safe_load(text)
        if isinstance(doc, dict) and isinstance(doc.get("proxies"), list):
            for p in doc["proxies"]:
                if not isinstance(p, dict):
                    continue
                typ = str(p.get("type", "")).lower()
                if typ not in SCHEMES:
                    continue
                out.append({
                    "protocol": typ,
                    "host": str(p.get("server", "")),
                    "port": int(p.get("port", 0) or 0),
                    "id": str(p.get("uuid") or p.get("password") or ""),
                    "security": str(p.get("security") or p.get("tls") or ""),
                    "sni": str(p.get("servername") or p.get("sni") or ""),
                    "path": str((p.get("ws-opts") or {}).get("path", "")) if isinstance(p.get("ws-opts"), dict) else "",
                    "type": str(p.get("network") or p.get("type") or ""),
                    "remark": str(p.get("name") or ""),
                    "raw": "",
                })
    except Exception:
        pass

    return out
