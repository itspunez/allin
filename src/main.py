import os
import json
from pathlib import Path
import yaml
from .fetch import fetch_url, decode_subscription
from .parse import parse_text
from .normalize import normalize
from .database import DB
from .export import export_all

PLACEHOLDERS = {
    "",
    "https://YOUR-SUBSCRIPTION-URL-HERE",
}

def source_url(source):
    env_name = source.get("url_env")
    if env_name:
        return os.getenv(env_name, "").strip()
    return str(source.get("url", "")).strip()

def load_sources():
    with open("sources.yml", "r", encoding="utf-8") as f:
        manual = (yaml.safe_load(f) or {}).get("sources", [])
    discovered = []
    p = Path("state/discovered_sources.json")
    if p.exists():
        try:
            discovered = list(json.loads(p.read_text(encoding="utf-8")).values())
        except Exception:
            pass
    manual_ids = {s["id"] for s in manual}
    return manual + [s for s in discovered if s.get("id") not in manual_ids]

def main():
    db = DB()
    try:
        for source in load_sources():
            if not source.get("enabled", False):
                continue

            url = source_url(source)
            if url in PLACEHOLDERS:
                continue

            source = dict(source)
            source["url"] = url
            db.start_source(source)

            try:
                data, _ctype = fetch_url(url)
                text = decode_subscription(data)
                parsed = parse_text(text)

                unique = {}
                for item in parsed:
                    try:
                        n = normalize(item)
                    except Exception:
                        continue
                    if not n.get("host") or not n.get("port"):
                        continue
                    unique[n["fingerprint"]] = n

                for item in unique.values():
                    db.upsert_config(item, source["id"])

                db.source_success(source["id"], len(parsed), len(unique))
                print(f"[OK] {source['id']}: {len(parsed)} items, {len(unique)} unique")
            except Exception as exc:
                db.source_error(source["id"], exc)
                print(f"[ERR] {source['id']}: {type(exc).__name__}: {exc}")

        stats = export_all(db)
        print(f"Exported {stats['configs']} configs from {stats['sources']} sources")
    finally:
        db.close()

if __name__ == "__main__":
    main()
