# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Bắt buộc cho SQLite với FastAPI đa luồng
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Tự động cập nhật các bản ghi cũ sang giờ GMT+7
try:
    import sqlite3
    from config import DB_PATH
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as _conn:
            _cur = _conn.cursor()
            _cur.execute("UPDATE crossing_events SET crossed_at = datetime(crossed_at, '+7 hours') WHERE crossed_at < '2026-10-08 16:00:00'")
            _cur.execute("UPDATE traffic_stats SET timestamp = datetime(timestamp, '+7 hours') WHERE timestamp < '2026-10-08 16:00:00'")
            _cur.execute("UPDATE sessions SET started_at = datetime(started_at, '+7 hours') WHERE started_at < '2026-10-08 16:00:00'")
            _conn.commit()
            try:
                _cur.execute("ALTER TABLE dataset_samples ADD COLUMN cloud_url TEXT")
                _conn.commit()
            except Exception:
                pass
except Exception:
    pass



def get_db():
    """Dependency cung cấp db session cho FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
