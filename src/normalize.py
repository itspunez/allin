import hashlib
import json

def _s(v):
    return str(v or "").strip()

def normalize(item):
    x = {k: _s(v) for k, v in item.items()}
    x["protocol"] = x["protocol"].lower()
    x["host"] = x["host"].lower().rstrip(".")
    x["security"] = x["security"].lower()
    x["type"] = x["type"].lower()
    x["sni"] = x["sni"].lower().rstrip(".")
    try:
        x["port"] = int(x["port"])
    except Exception:
        x["port"] = 0

    identity = "|".join([
        x["protocol"], x["host"], str(x["port"]), x["id"],
        x["security"], x["sni"], x["path"], x["type"]
    ])
    x["fingerprint"] = hashlib.sha256(identity.encode()).hexdigest()
    return x

def canonical_json(item):
    return json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
