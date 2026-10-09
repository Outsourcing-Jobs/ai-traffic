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

DEFAULT_SEEDS = [
    {
        "title": "Cloud CDN: Video Cao Tốc Mẫu (Roboflow)",
        "url": "https://media.roboflow.com/supervision/video/vehicles.mp4",
        "description": "Video mẫu xe cộ chất lượng cao trên Cloud CDN trực tiếp"
    },
    {
        "title": "Local Mẫu: data/videos/traffic.mp4",
        "url": "data/videos/traffic.mp4",
        "description": "File video lưu cục bộ trong máy"
    }
]


@router.get("", response_model=List[VideoSourceResponse])
def list_video_sources(db: Session = Depends(get_db)):
    """Lấy danh sách các nguồn video (tự động quét các file trong data/videos và CSDL)"""
    # 1. Tự động quét các file video có trong data/videos/
    supported_exts = {".mp4", ".avi", ".mkv", ".mov"}
    if VIDEOS_DIR.exists():
        for file_path in VIDEOS_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                rel_url = f"data/videos/{file_path.name}"
                # Kiểm tra đã có trong DB chưa
                existing = db.query(VideoSourceModel).filter(VideoSourceModel.url == rel_url).first()
                if not existing:
                    file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 1)
                    new_src = VideoSourceModel(
                        title=f"📁 Local: {file_path.name} ({file_size_mb} MB)",
                        url=rel_url,
                        description=f"File video cục bộ trong data/videos/{file_path.name}"
                    )
                    db.add(new_src)
        db.commit()

    items = db.query(VideoSourceModel).order_by(VideoSourceModel.id.asc()).all()

    # Nếu DB chưa có bản ghi nào, tự động seed các link Cloud mẫu ban đầu
    if len(items) == 0:
        for seed in DEFAULT_SEEDS:
            new_item = VideoSourceModel(
                title=seed["title"],
                url=seed["url"],
                description=seed["description"]
            )
            db.add(new_item)
        db.commit()
        items = db.query(VideoSourceModel).order_by(VideoSourceModel.id.asc()).all()

    return items


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
