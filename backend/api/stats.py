from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

from database.database import get_db
from database.models import TrafficStatModel, CrossingEventModel, SessionModel
from database.schemas import TrafficStatResponse, CrossingEventResponse, KPISummaryResponse
from video_manager import video_manager

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["Statistics"])


@router.get("/summary", response_model=KPISummaryResponse)
def get_session_summary(session_id: int, db: Session = Depends(get_db)):
    """Lấy tổng hợp chỉ số KPI (cho các thẻ Cards trên UI)"""
    # Kiểm tra session tồn tại
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")

    # Tổng số lượt xe
    total_vehicles = db.query(func.count(CrossingEventModel.id)).filter(
        CrossingEventModel.session_id == session_id
    ).scalar() or 0

    # Tốc độ trung bình
    avg_speed = db.query(func.avg(CrossingEventModel.speed_kmh)).filter(
        CrossingEventModel.session_id == session_id,
        CrossingEventModel.speed_kmh > 0
    ).scalar() or 0.0

    # Phân loại theo loại xe
    by_type_rows = db.query(
        CrossingEventModel.vehicle_type,
        func.count(CrossingEventModel.id)
    ).filter(
        CrossingEventModel.session_id == session_id
    ).group_by(CrossingEventModel.vehicle_type).all()

    by_type = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}
    for vtype, count in by_type_rows:
        if vtype in by_type:
            by_type[vtype] = count

    # Tính xe/phút ước tính
    vpm = 0.0
    if session.started_at:
        from datetime import datetime
        now = session.ended_at or datetime.now()
        duration_min = max((now - session.started_at).total_seconds() / 60.0, 0.1)
        vpm = round(total_vehicles / duration_min, 1)

    return KPISummaryResponse(
        total_vehicles=total_vehicles,
        avg_speed=round(float(avg_speed), 1),
        vehicles_per_minute=vpm,
        by_type=by_type
    )


@router.get("/stats", response_model=List[TrafficStatResponse])
def get_traffic_stats_history(
    session_id: int,
    limit: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lấy lịch sử thống kê theo phút (phục vụ vẽ biểu đồ Line/Bar chart)"""
    return db.query(TrafficStatModel).filter(
        TrafficStatModel.session_id == session_id
    ).order_by(TrafficStatModel.timestamp.asc()).limit(limit).all()


@router.get("/crossings", response_model=List[CrossingEventResponse])
def get_recent_crossings(
    session_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các xe vừa đi qua vạch đếm mới nhất"""
    return db.query(CrossingEventModel).filter(
        CrossingEventModel.session_id == session_id
    ).order_by(CrossingEventModel.crossed_at.desc()).limit(limit).all()


@router.get("/live-counts")
def get_live_counts(session_id: int):
    """Lấy số đếm xe tức thời (In / Out) từ bộ nhớ pipeline"""
    runner = video_manager.get_runner(session_id)
    if not runner:
        return {"in": 0, "out": 0, "total": 0, "status": "idle"}
    counts = runner.pipeline.get_counts()
    counts["status"] = "running"
    return counts
