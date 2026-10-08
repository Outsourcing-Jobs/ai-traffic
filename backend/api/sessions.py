import json
from datetime import datetime
from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import SessionModel
from database.schemas import SessionCreate, SessionResponse, SessionUpdateConfig
from video_manager import video_manager

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các phiên giám sát (có phân trang)"""
    return db.query(SessionModel).order_by(SessionModel.id.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """Tạo mới một phiên giám sát"""
    new_session = SessionModel(
        name=data.name,
        camera_url=data.camera_url,
        config_json=data.config_json,
        status="idle",
        started_at=datetime.now()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một phiên giám sát"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")
    return session


@router.put("/{session_id}/config", response_model=SessionResponse)
def update_session_config(session_id: int, payload: SessionUpdateConfig, db: Session = Depends(get_db)):
    """Cập nhật cấu hình ROI, vạch đếm cho phiên giám sát"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")

    config_str = payload.config.model_dump_json()
    session.config_json = config_str
    db.commit()
    db.refresh(session)

    # Nếu session đang chạy, cập nhật pipeline ngay lập tức
    runner = video_manager.get_runner(session_id)
    if runner:
        runner.pipeline.configure(payload.config.model_dump())

    return session


@router.post("/{session_id}/start")
def start_session_processing(session_id: int, db: Session = Depends(get_db)):
    """Bắt đầu chạy phân tích video cho phiên giám sát"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")

    if not session.camera_url:
        raise HTTPException(status_code=400, detail="Phiên chưa có đường dẫn video nguồn")

    # Khởi chạy video manager
    video_manager.start_session(
        session_id=session.id,
        video_source=session.camera_url,
        config_json=session.config_json
    )

    session.status = "running"
    session.started_at = datetime.now()
    db.commit()

    return {"message": "Đã bắt đầu xử lý phiên giám sát", "session_id": session_id, "status": "running"}


@router.post("/{session_id}/stop")
def stop_session_processing(session_id: int, db: Session = Depends(get_db)):
    """Dừng chạy phân tích video"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")

    video_manager.stop_session(session_id)

    session.status = "stopped"
    session.ended_at = datetime.now()
    db.commit()

    return {"message": "Đã dừng phiên giám sát", "session_id": session_id, "status": "stopped"}


@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Xóa một phiên giám sát và toàn bộ dữ liệu liên quan"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên giám sát")

    video_manager.stop_session(session_id)
    db.delete(session)
    db.commit()

    return {"message": "Đã xóa phiên thành công"}
