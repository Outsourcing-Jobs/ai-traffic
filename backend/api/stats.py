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
from database.models import TrafficStatModel, CrossingEventModel, SessionModel, ViolationModel
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

    # Đọc speed_limit đã lưu trong session.config_json
    speed_limit = 50.0
    if session.config_json:
        try:
            cfg = json.loads(session.config_json)
            if "speed_limit" in cfg:
                speed_limit = float(cfg["speed_limit"])
        except Exception:
            pass

    # Đánh giá tình trạng ùn tắc từ runner (khi đang chạy phân tích)
    congestion_level = "FLUID"
    congestion_text = "Thông thoáng"
    active_vehicles = 0

    runner = video_manager.get_runner(session_id)
    if runner and runner.is_running:
        cong = runner.get_congestion_info()
        congestion_level = cong.get("congestion_level", "FLUID")
        congestion_text = cong.get("congestion_text", "Thông thoáng")
        active_vehicles = cong.get("active_vehicles", 0)
        speed_limit = runner.pipeline.speed_limit
    else:
        congestion_level = "FLUID"
        congestion_text = "Tạm dừng giám sát"

    return KPISummaryResponse(
        total_vehicles=total_vehicles,
        avg_speed=round(float(avg_speed), 1),
        vehicles_per_minute=vpm,
        congestion_level=congestion_level,
        congestion_text=congestion_text,
        active_vehicles=active_vehicles,
        speed_limit=speed_limit,
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


@router.get("/export/violations-csv")
def export_violations_csv(session_id: int, db: Session = Depends(get_db)):
    """Xuất biên bản vi phạm tốc độ dưới dạng file CSV chuẩn UTF-8 BOM cho Excel"""
    violations = db.query(ViolationModel).filter(
        ViolationModel.session_id == session_id
    ).order_by(ViolationModel.violated_at.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "STT",
        "Mã Phiên",
        "ID Phương Tiện (Track ID)",
        "Loại Phương Tiện",
        "Vận Tốc Đo Được (km/h)",
        "Tốc Độ Giới Hạn (km/h)",
        "Vượt Quá (km/h)",
        "Thời Điểm Vi Phạm",
        "Link Bằng Chứng (Cloud / File)",
        "Trạng Thái Xử Lý"
    ])

    vehicle_names = {
        "car": "Ô tô con",
        "motorcycle": "Xe máy",
        "bus": "Xe buýt / Khách",
        "truck": "Xe tải"
    }

    for idx, v in enumerate(violations, 1):
        vtype_vn = vehicle_names.get(v.vehicle_type, v.vehicle_type or "Không xác định")
        over_speed = max(0.0, v.speed_kmh - v.speed_limit)
        time_str = v.violated_at.strftime("%Y-%m-%d %H:%M:%S") if v.violated_at else ""
        link = v.cloud_url or f"/api/violations/image/{v.evidence_image_path}"
        
        writer.writerow([
            idx,
            v.session_id,
            v.track_id,
            vtype_vn,
            f"{v.speed_kmh:.1f}",
            f"{v.speed_limit:.1f}",
            f"+{over_speed:.1f}",
            time_str,
            link,
            "Chờ xử phạt" if v.status == "pending" else "Đã xử lý"
        ])

    csv_data = output.getvalue()
    bom_csv_bytes = b"\xef\xbb\xbf" + csv_data.encode("utf-8")

    filename = f"bien_ban_vi_pham_session_{session_id}.csv"
    return StreamingResponse(
        io.BytesIO(bom_csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
