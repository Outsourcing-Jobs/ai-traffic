from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
# pyrefly: ignore [missing-import]
from database.database import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    camera_url = Column(Text, nullable=True)
    status = Column(String(50), default="idle")  # idle, running, stopped, completed
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)
    config_json = Column(Text, nullable=True)  # JSON chứa ROI polygon và counting lines

    # Quan hệ
    detections = relationship("DetectionModel", back_populates="session", cascade="all, delete-orphan")
    traffic_stats = relationship("TrafficStatModel", back_populates="session", cascade="all, delete-orphan")
    crossing_events = relationship("CrossingEventModel", back_populates="session", cascade="all, delete-orphan")
    violations = relationship("ViolationModel", back_populates="session", cascade="all, delete-orphan")



class DetectionModel(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # car, motorcycle, bus, truck
    detected_at = Column(DateTime, default=datetime.now)
    bbox_json = Column(Text, nullable=True)  # {"x1": 10, "y1": 20, "x2": 100, "y2": 150}
    speed_kmh = Column(Float, nullable=True)
    frame_number = Column(Integer, nullable=True)

    session = relationship("SessionModel", back_populates="detections")

    __table_args__ = (
        Index("idx_detections_session", "session_id"),
        Index("idx_detections_track", "session_id", "track_id"),
    )


class TrafficStatModel(Base):
    __tablename__ = "traffic_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    period_min = Column(Integer, default=1)
    car_count = Column(Integer, default=0)
    truck_count = Column(Integer, default=0)
    bus_count = Column(Integer, default=0)
    moto_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    avg_speed = Column(Float, default=0.0)
    max_speed = Column(Float, default=0.0)
    min_speed = Column(Float, default=0.0)

    session = relationship("SessionModel", back_populates="traffic_stats")

    __table_args__ = (
        Index("idx_stats_session_time", "session_id", "timestamp"),
    )


class CrossingEventModel(Base):
    __tablename__ = "crossing_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    vehicle_type = Column(String(50), nullable=True)
    speed_kmh = Column(Float, nullable=True)
    direction = Column(String(20), default="in")  # in, out
    crossed_at = Column(DateTime, default=datetime.now, nullable=False)
    line_id = Column(Integer, default=1)

    session = relationship("SessionModel", back_populates="crossing_events")

    __table_args__ = (
        Index("idx_crossing_session", "session_id"),
        Index("idx_crossing_time", "crossed_at"),
    )


class VideoSourceModel(Base):
    __tablename__ = "video_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class DatasetSampleModel(Base):
    __tablename__ = "dataset_samples"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, nullable=True)
    image_filename = Column(String(255), nullable=False)
    image_path = Column(Text, nullable=False)
    cloud_url = Column(Text, nullable=True)  # Link ảnh trên Cloudinary
    label_path = Column(Text, nullable=False)
    vehicles_count = Column(Integer, default=0)
    car_count = Column(Integer, default=0)
    moto_count = Column(Integer, default=0)
    bus_count = Column(Integer, default=0)
    truck_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class ViolationModel(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # car, motorcycle, bus, truck
    speed_kmh = Column(Float, nullable=False)
    speed_limit = Column(Float, nullable=False, default=50.0)
    evidence_image_path = Column(Text, nullable=False)
    cloud_url = Column(Text, nullable=True)  # Link ảnh Cloudinary
    violated_at = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(50), default="pending")  # pending, confirmed

    session = relationship("SessionModel", back_populates="violations")

    __table_args__ = (
        Index("idx_violation_session", "session_id"),
        Index("idx_violation_time", "violated_at"),
    )


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), default="admin")  # admin, operator, viewer
    created_at = Column(DateTime, default=datetime.now)


