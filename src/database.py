import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).isoformat()

class DB:
    def __init__(self, path="state/aggregator.sqlite3"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT,
            weight REAL DEFAULT 100,
            enabled INTEGER DEFAULT 1,
            fetch_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            total_items INTEGER DEFAULT 0,
            unique_items INTEGER DEFAULT 0,
            last_error TEXT,
            last_success TEXT,
            first_seen TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS configs (
            fingerprint TEXT PRIMARY KEY,
            protocol TEXT,
            host TEXT,
            port INTEGER,
            id TEXT,
            security TEXT,
            sni TEXT,
            path TEXT,
            type TEXT,
            remark TEXT,
            raw TEXT,
            first_seen TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS config_sources (
            fingerprint TEXT,
            source_id TEXT,
            first_seen TEXT,
            last_seen TEXT,
            PRIMARY KEY (fingerprint, source_id)
        );
        """)
        self.conn.commit()

    def start_source(self, s):
        now = utcnow()
        self.conn.execute("""
        INSERT INTO sources(id,name,url,weight,enabled,fetch_count,first_seen,last_seen)
        VALUES(?,?,?,?,?,1,?,?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,url=excluded.url,weight=excluded.weight,
          enabled=excluded.enabled,fetch_count=sources.fetch_count+1,last_seen=excluded.last_seen
        """, (s["id"], s.get("name",""), s.get("url",""), s.get("weight",100),
              int(s.get("enabled", True)), now, now))
        self.conn.commit()

    def source_success(self, sid, total, unique):
        now = utcnow()
        self.conn.execute("""
        UPDATE sources
        SET success_count=success_count+1,total_items=?,unique_items=?,last_success=?,last_error=NULL,last_seen=?
        WHERE id=?
        """, (total, unique, now, now, sid))
        self.conn.commit()

    def source_error(self, sid, error):
        self.conn.execute("UPDATE sources SET last_error=? WHERE id=?", (str(error)[:1000], sid))
        self.conn.commit()

    def upsert_config(self, item, source_id):
        now = utcnow()
        self.conn.execute("""
        INSERT INTO configs(
          fingerprint,protocol,host,port,id,security,sni,path,type,remark,raw,first_seen,last_seen
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(fingerprint) DO UPDATE SET
          protocol=excluded.protocol,host=excluded.host,port=excluded.port,
          security=excluded.security,sni=excluded.sni,path=excluded.path,
          type=excluded.type,remark=excluded.remark,raw=excluded.raw,last_seen=excluded.last_seen
        """, (
            item["fingerprint"], item["protocol"], item["host"], item["port"], item["id"],
            item["security"], item["sni"], item["path"], item["type"], item["remark"],
            item.get("raw",""), now, now
        ))
        self.conn.execute("""
        INSERT INTO config_sources(fingerprint,source_id,first_seen,last_seen)
        VALUES(?,?,?,?)
        ON CONFLICT(fingerprint,source_id) DO UPDATE SET last_seen=excluded.last_seen
        """, (item["fingerprint"], source_id, now, now))
        self.conn.commit()

    def configs(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM configs").fetchall()]

    def source_stats(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM sources ORDER BY weight DESC,id").fetchall()]

    def source_count_for(self, fp):
        row = self.conn.execute("SELECT COUNT(*) c FROM config_sources WHERE fingerprint=?", (fp,)).fetchone()
        return int(row["c"])

    def close(self):
        self.conn.close()
