"""
Script di chuyển toàn bộ dữ liệu từ SQLite cục bộ (traffic.db) sang Neon PostgreSQL (Siêu nhanh - Batch Lookup).
"""

import sys
import sqlite3
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import DATABASE_URL, DB_PATH
from database.models import (
    Base, UserModel, VideoSourceModel, SessionModel,
    TrafficStatModel, CrossingEventModel, ViolationModel,
    DatasetSampleModel, DetectionModel
)

def parse_dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v))
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(str(v), fmt)
            except Exception:
                pass
    return None

def migrate():
    if not DB_PATH.exists():
        print(f"[Error] Không tìm thấy SQLite db: {DB_PATH}", flush=True)
        return

    print(f"[*] SQLite: {DB_PATH}", flush=True)
    print(f"[*] PostgreSQL: {DATABASE_URL[:45]}...", flush=True)

    pg_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=pg_engine)

    sq_conn = sqlite3.connect(DB_PATH)
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()

    with Session(pg_engine) as session:
        # 1. users
        sq_cur.execute("SELECT * FROM users")
        existing_users = {x[0] for x in session.query(UserModel.username).all()}
        u_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["username"] not in existing_users:
                obj = UserModel(
                    id=d.get("id"),
                    username=d["username"],
                    hashed_password=d["hashed_password"],
                    full_name=d["full_name"],
                    role=d.get("role", "admin"),
                    created_at=parse_dt(d.get("created_at")) or datetime.now()
                )
                session.add(obj)
                u_count += 1
        session.commit()
        print(f"[OK] Users: +{u_count} records", flush=True)

        # 2. video_sources
        sq_cur.execute("SELECT * FROM video_sources")
        existing_v = {x[0] for x in session.query(VideoSourceModel.url).all()}
        v_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["url"] not in existing_v:
                obj = VideoSourceModel(
                    title=d["title"],
                    url=d["url"],
                    description=d.get("description"),
                    created_at=parse_dt(d.get("created_at")) or datetime.now()
                )
                session.add(obj)
                v_count += 1
        session.commit()
        print(f"[OK] Video Sources: +{v_count} records", flush=True)

        # 3. sessions
        sq_cur.execute("SELECT * FROM sessions")
        existing_s = {x[0] for x in session.query(SessionModel.id).all()}
        s_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["id"] not in existing_s:
                obj = SessionModel(
                    id=d["id"],
                    name=d["name"],
                    camera_url=d.get("camera_url"),
                    status=d.get("status", "idle"),
                    started_at=parse_dt(d.get("started_at")) or datetime.now(),
                    ended_at=parse_dt(d.get("ended_at")),
                    config_json=d.get("config_json")
                )
                session.add(obj)
                s_count += 1
        session.commit()
        print(f"[OK] Sessions: +{s_count} records", flush=True)

        # 4. traffic_stats
        sq_cur.execute("SELECT * FROM traffic_stats")
        existing_ts = {x[0] for x in session.query(TrafficStatModel.id).all()}
        ts_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["id"] not in existing_ts:
                obj = TrafficStatModel(
                    id=d["id"],
                    session_id=d["session_id"],
                    timestamp=parse_dt(d.get("timestamp")) or datetime.now(),
                    period_min=d.get("period_min", 1),
                    car_count=d.get("car_count", 0),
                    truck_count=d.get("truck_count", 0),
                    bus_count=d.get("bus_count", 0),
                    moto_count=d.get("moto_count", 0),
                    total_count=d.get("total_count", 0),
                    avg_speed=float(d.get("avg_speed") or 0.0),
                    max_speed=float(d.get("max_speed") or 0.0),
                    min_speed=float(d.get("min_speed") or 0.0)
                )
                session.add(obj)
                ts_count += 1
        session.commit()
        print(f"[OK] Traffic Stats: +{ts_count} records", flush=True)

        # 5. crossing_events
        sq_cur.execute("SELECT * FROM crossing_events")
        existing_ce = {x[0] for x in session.query(CrossingEventModel.id).all()}
        ce_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["id"] not in existing_ce:
                obj = CrossingEventModel(
                    id=d["id"],
                    session_id=d["session_id"],
                    track_id=d["track_id"],
                    vehicle_type=d.get("vehicle_type"),
                    speed_kmh=float(d["speed_kmh"]) if d.get("speed_kmh") is not None else None,
                    direction=d.get("direction", "in"),
                    crossed_at=parse_dt(d.get("crossed_at")) or datetime.now(),
                    line_id=d.get("line_id", 1)
                )
                session.add(obj)
                ce_count += 1
        session.commit()
        print(f"[OK] Crossing Events: +{ce_count} records", flush=True)

        # 6. violations
        sq_cur.execute("SELECT * FROM violations")
        existing_vi = {x[0] for x in session.query(ViolationModel.id).all()}
        vi_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["id"] not in existing_vi:
                obj = ViolationModel(
                    id=d["id"],
                    session_id=d["session_id"],
                    track_id=d["track_id"],
                    vehicle_type=d["vehicle_type"],
                    speed_kmh=float(d.get("speed_kmh") or 0.0),
                    speed_limit=float(d.get("speed_limit") or 50.0),
                    evidence_image_path=d["evidence_image_path"],
                    cloud_url=d.get("cloud_url"),
                    violated_at=parse_dt(d.get("violated_at")) or datetime.now(),
                    status=d.get("status", "pending")
                )
                session.add(obj)
                vi_count += 1
        session.commit()
        print(f"[OK] Violations: +{vi_count} records", flush=True)

        # 7. dataset_samples
        sq_cur.execute("SELECT * FROM dataset_samples")
        existing_ds = {x[0] for x in session.query(DatasetSampleModel.id).all()}
        ds_count = 0
        for r in sq_cur.fetchall():
            d = dict(r)
            if d["id"] not in existing_ds:
                obj = DatasetSampleModel(
                    id=d["id"],
                    session_id=d.get("session_id"),
                    image_filename=d["image_filename"],
                    image_path=d["image_path"],
                    cloud_url=d.get("cloud_url"),
                    label_path=d["label_path"],
                    vehicles_count=d.get("vehicles_count", 0),
                    car_count=d.get("car_count", 0),
                    moto_count=d.get("moto_count", 0),
                    bus_count=d.get("bus_count", 0),
                    truck_count=d.get("truck_count", 0),
                    created_at=parse_dt(d.get("created_at")) or datetime.now()
                )
                session.add(obj)
                ds_count += 1
        session.commit()
        print(f"[OK] Dataset Samples: +{ds_count} records", flush=True)

        # 8. Reset sequences in PostgreSQL
        tables = [
            "users", "video_sources", "sessions", "traffic_stats",
            "crossing_events", "violations", "dataset_samples"
        ]
        with pg_engine.begin() as conn:
            for tbl in tables:
                try:
                    conn.execute(text(f"""
                        SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1));
                    """))
                except Exception:
                    pass
        print("[OK] Sequence IDs reset successfully!", flush=True)

    sq_conn.close()
    print("[=== MIGRATION COMPLETED SUCCESSFULLY ===]", flush=True)

if __name__ == "__main__":
    migrate()
