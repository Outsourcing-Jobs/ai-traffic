import os
import json
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from database.database import SessionLocal
from database.models import ViolationModel, SessionModel, CrossingEventModel
from database.schemas import ViolationResponse, ViolationSummaryResponse
from config import VIOLATIONS_DIR
from video_manager import video_manager

router = APIRouter(prefix="/api/violations", tags=["Speed Violations"])


class SetSpeedLimitRequest(BaseModel):
    speed_limit: float = Field(..., ge=10.0, le=200.0, example=50.0)


@router.get("", response_model=List[ViolationResponse])
def get_violations(
    session_id: Optional[int] = Query(None, description="Lọc theo ID phiên"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Lấy danh sách các phương tiện vi phạm chạy quá tốc độ"""
    db = SessionLocal()
    try:
        query = db.query(ViolationModel)
        if session_id is not None:
            query = query.filter(ViolationModel.session_id == session_id)

        violations = (
            query.order_by(ViolationModel.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return violations
    finally:
        db.close()


@router.get("/summary", response_model=ViolationSummaryResponse)
def get_violations_summary(
    session_id: Optional[int] = Query(None, description="Lọc theo ID phiên")
):
    """Thống kê tổng quan số liệu vi phạm tốc độ (ITS Speed Enforcement KPI)"""
    db = SessionLocal()
    try:
        query = db.query(ViolationModel)
        crossing_query = db.query(CrossingEventModel)

        if session_id is not None:
            query = query.filter(ViolationModel.session_id == session_id)
            crossing_query = crossing_query.filter(CrossingEventModel.session_id == session_id)

        violations = query.all()
        total_crossings = crossing_query.count()

        total_violations = len(violations)
        highest_speed = 0.0
        by_type = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

        for v in violations:
            if v.speed_kmh and v.speed_kmh > highest_speed:
                highest_speed = v.speed_kmh
            vtype = v.vehicle_type.lower() if v.vehicle_type else "car"
            if vtype in by_type:
                by_type[vtype] += 1
            else:
                by_type["car"] += 1

        violation_rate = 0.0
        if total_crossings > 0:
            violation_rate = round((total_violations / total_crossings) * 100.0, 1)

        return ViolationSummaryResponse(
            total_violations=total_violations,
            highest_speed=round(highest_speed, 1),
            violation_rate_pct=violation_rate,
            by_type=by_type
        )
    finally:
        db.close()


@router.get("/image/{filename:path}")
def get_evidence_image(filename: str):
    """Xem file ảnh bằng chứng vi phạm tốc độ (chấp nhận cả tên file hoặc đường dẫn data/violations/...)"""
    clean_name = os.path.basename(filename)
    img_path = VIOLATIONS_DIR / clean_name
    if not img_path.exists():
        # Thử tìm trực tiếp nếu là relative path từ BASE_DIR
        from config import BASE_DIR
        alt_path = BASE_DIR / filename
        if alt_path.exists():
            return FileResponse(alt_path, media_type="image/jpeg")
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh bằng chứng vi phạm")
    return FileResponse(img_path, media_type="image/jpeg")


@router.post("/session/{session_id}/speed-limit")
def update_speed_limit(
    session_id: int,
    speed_limit: Optional[float] = Query(None, description="Tốc độ giới hạn (km/h)"),
    req: Optional[SetSpeedLimitRequest] = None
):
    """Cập nhật tốc độ giới hạn cho đoạn đường của phiên giám sát"""
    target_limit = speed_limit
    if target_limit is None and req is not None:
        target_limit = req.speed_limit
    if target_limit is None:
        target_limit = 50.0

    # 1. Cập nhật cho runner đang chạy realtime
    runner = video_manager.get_runner(session_id)
    if runner:
        runner.set_speed_limit(target_limit)

    # 2. Lưu vào CSDL
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")

        cfg = {}
        if session.config_json:
            try:
                cfg = json.loads(session.config_json)
            except Exception:
                cfg = {}
        cfg["speed_limit"] = target_limit
        session.config_json = json.dumps(cfg)
        db.commit()

        return {
            "success": True,
            "session_id": session_id,
            "speed_limit": target_limit,
            "message": f"Đã cập nhật tốc độ giới hạn: {target_limit} km/h"
        }
    finally:
        db.close()


@router.delete("/{violation_id}")
def delete_violation(violation_id: int):
    """Xóa 1 biên bản vi phạm"""
    db = SessionLocal()
    try:
        v = db.query(ViolationModel).filter(ViolationModel.id == violation_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Không tìm thấy biên bản vi phạm")
        db.delete(v)
        db.commit()
        return {"success": True, "message": "Đã xóa biên bản vi phạm"}
    finally:
        db.close()
