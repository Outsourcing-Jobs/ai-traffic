import csv
import io
import json
from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
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

    # Tính xe/phút và xe/giờ quy đổi ước tính
    vpm = 0.0
    vph = 0.0
    if session.started_at:
        from datetime import datetime
        now = session.ended_at or datetime.now()
        duration_min = max((now - session.started_at).total_seconds() / 60.0, 0.1)
        vpm = round(total_vehicles / duration_min, 1)
        vph = round(vpm * 60.0, 0)

    active_vehicles = 0

    return KPISummaryResponse(
        total_vehicles=total_vehicles,
        avg_speed=round(float(avg_speed), 1),
        vehicles_per_minute=vpm,
        vehicles_per_hour=vph,
        active_vehicles=active_vehicles,
        by_type=by_type
    )


@router.get("/stats", response_model=List[TrafficStatResponse])
def get_traffic_stats_history(
    session_id: int,
    limit: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lấy lịch sử thống kê theo phút (phục vụ vẽ biểu đồ Line/Bar chart kèm quy đổi xe/giờ)"""
    records = db.query(TrafficStatModel).filter(
        TrafficStatModel.session_id == session_id
    ).order_by(TrafficStatModel.timestamp.asc()).limit(limit).all()

    # Tính toán lưu lượng quy đổi (xe/giờ) cho từng bản ghi chu kỳ
    results = []
    for r in records:
        flow_per_hour = int(r.total_count * (60.0 / max(r.period_min, 1)))
        stat_item = TrafficStatResponse.model_validate(r)
        stat_item.flow_rate_per_hour = flow_per_hour
        results.append(stat_item)
    return results


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


@router.get("/export/csv")
def export_crossings_csv(session_id: int, db: Session = Depends(get_db)):
    """Xuất danh sách lưu lượng xe qua vạch dưới dạng file CSV chuẩn UTF-8 BOM cho Excel"""
    events = db.query(CrossingEventModel).filter(
        CrossingEventModel.session_id == session_id
    ).order_by(CrossingEventModel.crossed_at.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Tiêu đề cột chuẩn Tiếng Việt
    writer.writerow([
        "STT",
        "Mã Phiên",
        "ID Phương Tiện (Track ID)",
        "Loại Phương Tiện",
        "Vận Tốc Đo Được (km/h)",
        "Hướng Di Chuyển",
        "Mã Vạch Đếm",
        "Thời Điểm Đi Qua"
    ])

    vehicle_names = {
        "car": "Ô tô con",
        "motorcycle": "Xe máy",
        "bus": "Xe buýt / Khách",
        "truck": "Xe tải"
    }

    for idx, ev in enumerate(events, 1):
        vtype_vn = vehicle_names.get(ev.vehicle_type, ev.vehicle_type or "Không xác định")
        speed_str = f"{ev.speed_kmh:.1f}" if ev.speed_kmh is not None and ev.speed_kmh > 0 else "N/A"
        time_str = ev.crossed_at.strftime("%Y-%m-%d %H:%M:%S") if ev.crossed_at else ""
        writer.writerow([
            idx,
            ev.session_id,
            ev.track_id,
            vtype_vn,
            speed_str,
            "Đi vào (IN)" if ev.direction == "in" else "Đi ra (OUT)",
            ev.line_id or 1,
            time_str
        ])

    csv_data = output.getvalue()
    # Thêm UTF-8 BOM (\xef\xbb\xbf) để Excel tự nhận diện Tiếng Việt không lỗi font
    bom_csv_bytes = b"\xef\xbb\xbf" + csv_data.encode("utf-8")

    filename = f"bao_cao_luu_luong_session_{session_id}.csv"
    return StreamingResponse(
        io.BytesIO(bom_csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
