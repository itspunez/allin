import base64
import json
from pathlib import Path
from .score import score_config

def render(c):
    # Prefer original URL representation when available.
    if c.get("raw"):
        return c["raw"]
    return ""

def export_all(db):
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)

    sources = db.source_stats()
    source_map = {s["id"]: s for s in sources}

    configs = db.configs()
    for c in configs:
        rows = db.conn.execute(
            "SELECT source_id FROM config_sources WHERE fingerprint=?",
            (c["fingerprint"],)
        ).fetchall()
        c["source_ids"] = [r["source_id"] for r in rows]
        c["source_count"] = len(c["source_ids"])
        c["score"] = score_config(c, source_map, c["source_count"])

    configs.sort(key=lambda x: (-x["score"], x["fingerprint"]))

    by_protocol = {}
    for c in configs:
        by_protocol.setdefault(c["protocol"], []).append(c)

    for name, items in {
        "all.txt": configs,
        "top100.txt": configs[:100],
        "fast.txt": configs[:100],
        "vless.txt": by_protocol.get("vless", []),
        "vmess.txt": by_protocol.get("vmess", []),
        "trojan.txt": by_protocol.get("trojan", []),
        "ss.txt": by_protocol.get("ss", []),
    }.items():
        lines = [render(c) for c in items]
        lines = [x for x in lines if x]
        (out / name).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    public_configs = []
    for c in configs:
        item = dict(c)
        item.pop("raw", None)
        public_configs.append(item)

    (out / "configs.json").write_text(
        json.dumps(public_configs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    public_sources = []
    for s in sources:
        item = dict(s)
        item.pop("url", None)
        public_sources.append(item)

    (out / "sources.json").write_text(
        json.dumps(public_sources, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    sub = "\n".join(x for x in (render(c) for c in configs) if x)
    encoded = base64.b64encode(sub.encode()).decode()
    (out / "subscription.b64").write_text(encoded + "\n", encoding="utf-8")

    return {
        "configs": len(configs),
        "sources": len(sources),
        "top100": min(100, len(configs))
    }
