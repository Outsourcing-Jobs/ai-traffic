import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "traffic.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Cộng 7 tiếng cho các bản ghi cũ trước 16h hôm nay
    cur.execute("UPDATE crossing_events SET crossed_at = datetime(crossed_at, '+7 hours') WHERE crossed_at < '2026-10-08 16:00:00'")
    cur.execute("UPDATE traffic_stats SET timestamp = datetime(timestamp, '+7 hours') WHERE timestamp < '2026-10-08 16:00:00'")
    cur.execute("UPDATE sessions SET started_at = datetime(started_at, '+7 hours') WHERE started_at < '2026-10-08 16:00:00'")
    conn.commit()
    print(f"Updated {cur.rowcount} rows in traffic.db to GMT+7")
    conn.close()
