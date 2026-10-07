import yaml
from urllib.parse import urlsplit

with open("sources.yml", encoding="utf-8") as f:
    doc = yaml.safe_load(f)

sources = doc.get("sources", [])
ids = set()
for s in sources:
    assert s["id"] not in ids, f"duplicate id: {s['id']}"
    ids.add(s["id"])
    u = s.get("url", "")
    if u:
        parsed = urlsplit(u)
        assert parsed.scheme in ("http", "https"), f"bad URL: {u}"

print(f"OK: {len(sources)} source entries")
