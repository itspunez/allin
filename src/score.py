from datetime import datetime, timezone

def freshness(last_seen):
    try:
        dt = datetime.fromisoformat(last_seen)
        age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 0.0
    if age <= 1: return 100.0
    if age <= 6: return 90.0
    if age <= 24: return 75.0
    if age <= 72: return 50.0
    if age <= 168: return 25.0
    return 5.0

def reliability(source):
    fc = max(int(source.get("fetch_count", 0)), 1)
    return min(100.0, 100.0 * int(source.get("success_count", 0)) / fc)

def score_config(config, source_map, source_count):
    # Data-quality score only; no endpoint connectivity probing.
    f = freshness(config.get("last_seen", ""))
    related = []
    # source_ids are injected by exporter/main
    for sid in config.get("source_ids", []):
        if sid in source_map:
            related.append(reliability(source_map[sid]) * (float(source_map[sid].get("weight",100))/100.0))
    src = max(related) if related else 0.0
    diversity = min(100.0, source_count * 25.0)
    return round(f * 0.45 + src * 0.45 + diversity * 0.10, 2)
