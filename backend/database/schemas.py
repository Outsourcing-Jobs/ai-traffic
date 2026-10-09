from datetime import datetime
from typing import Optional, List, Dict, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


# ==========================================
# Cấu hình ROI & Vạch đếm Schemas
# ==========================================
class CountingLineSchema(BaseModel):
    id: int = 1
    name: str = "Vạch chính"
    p1: List[int] = Field(..., description="[x, y] điểm đầu")
    p2: List[int] = Field(..., description="[x, y] điểm cuối")
    direction_in: Optional[str] = "down"
    direction_out: Optional[str] = "up"


class HomographyConfigSchema(BaseModel):
    source_pixels: List[List[float]] = Field(default=[], description="4 điểm pixel trên video")
    target_meters: List[List[float]] = Field(default=[], description="4 điểm tương ứng đơn vị mét")


class ROIConfigSchema(BaseModel):
    counting_lines: List[CountingLineSchema] = []
    roi_polygon: List[List[int]] = []  # Danh sách các điểm [[x1, y1], [x2, y2], ...]
    homography: Optional[HomographyConfigSchema] = None
    speed_limit: Optional[float] = 50.0  # Tốc độ giới hạn cho phép (km/h)



# ==========================================
# Session Schemas
# ==========================================
class SessionCreate(BaseModel):
    name: str = Field(..., example="Giám sát Ngã tư 01")
    camera_url: Optional[str] = Field(None, example="data/videos/traffic.mp4")
    config_json: Optional[str] = None


class SessionUpdateConfig(BaseModel):
    config: ROIConfigSchema


class SessionResponse(BaseModel):
    id: int
    name: str
    camera_url: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    config_json: Optional[str]

    class Config:
        from_attributes = True


# ==========================================
# Crossing Events Schemas
# ==========================================
class CrossingEventCreate(BaseModel):
    session_id: int
    track_id: int
    vehicle_type: str
    speed_kmh: Optional[float] = None
    direction: str = "in"
    line_id: int = 1


class CrossingEventResponse(BaseModel):
    id: int
    session_id: int
    track_id: int
    vehicle_type: Optional[str]
    speed_kmh: Optional[float]
    direction: Optional[str]
    crossed_at: datetime
    line_id: Optional[int]

    class Config:
        from_attributes = True


# ==========================================
# Traffic Stats & Dashboard Schemas
# ==========================================
class TrafficStatResponse(BaseModel):
    id: int
    session_id: int
    timestamp: datetime
    period_min: int
    car_count: int
    truck_count: int
    bus_count: int
    moto_count: int
    total_count: int
    avg_speed: float
    max_speed: float
    min_speed: float

    class Config:
        from_attributes = True


class KPISummaryResponse(BaseModel):
    total_vehicles: int = 0
    avg_speed: float = 0.0
    vehicles_per_minute: float = 0.0
    congestion_level: str = "FLUID"  # FLUID, MODERATE, CONGESTED
    congestion_text: str = "Thông thoáng"
    active_vehicles: int = 0
    speed_limit: float = 50.0
    by_type: Dict[str, int] = {
        "car": 0,
        "motorcycle": 0,
        "bus": 0,
        "truck": 0
    }


# ==========================================
# Speed Violations Schemas
# ==========================================
class ViolationResponse(BaseModel):
    id: int
    session_id: int
    track_id: int
    vehicle_type: str
    speed_kmh: float
    speed_limit: float
    evidence_image_path: str
    cloud_url: Optional[str] = None
    violated_at: datetime
    status: str

    class Config:
        from_attributes = True


class ViolationSummaryResponse(BaseModel):
    total_violations: int = 0
    highest_speed: float = 0.0
    violation_rate_pct: float = 0.0
    by_type: Dict[str, int] = {
        "car": 0,
        "motorcycle": 0,
        "bus": 0,
        "truck": 0
    }



# ==========================================
# Video Sources Schemas (Cloud URLs)
# ==========================================
class VideoSourceCreate(BaseModel):
    title: str = Field(..., example="Cao tốc Hà Nội - Hải Phòng")
    url: str = Field(..., example="https://res.cloudinary.com/.../traffic.mp4")
    description: Optional[str] = None


class VideoSourceResponse(BaseModel):
    id: int
    title: str
    url: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
