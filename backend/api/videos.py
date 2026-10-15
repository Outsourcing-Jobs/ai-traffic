from typing import List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import VideoSourceModel
from database.schemas import VideoSourceCreate, VideoSourceResponse

router = APIRouter(prefix="/api/videos", tags=["Video Sources"])

from config import VIDEOS_DIR

DEFAULT_SEEDS = []


def init_default_videos():
    """Giữ hàm để tương thích khởi động (không tự động thêm seed)"""
    pass


@router.get("", response_model=List[VideoSourceResponse])
def list_video_sources(db: Session = Depends(get_db)):
    """Lấy danh sách các nguồn video trực tiếp từ CSDL"""
    return db.query(VideoSourceModel).order_by(VideoSourceModel.id.asc()).all()



@router.post("", response_model=VideoSourceResponse, status_code=201)
def add_video_source(payload: VideoSourceCreate, db: Session = Depends(get_db)):
    """Thêm một đường dẫn video Cloud mới vào CSDL"""
    new_src = VideoSourceModel(
        title=payload.title,
        url=payload.url.strip(),
        description=payload.description
    )
    db.add(new_src)
    db.commit()
    db.refresh(new_src)
    return new_src


@router.delete("/{video_id}")
def delete_video_source(video_id: int, db: Session = Depends(get_db)):
    """Xóa một nguồn video khỏi danh sách"""
    src = db.query(VideoSourceModel).filter(VideoSourceModel.id == video_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Không tìm thấy video")
    db.delete(src)
    db.commit()
    return {"message": "Đã xóa nguồn video thành công"}
