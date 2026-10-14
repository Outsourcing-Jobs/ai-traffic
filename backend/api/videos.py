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
        "title": "☁️ Cloud: Video Xe Cộ Giao Thông (traffic.mp4)",
        "url": "https://res.cloudinary.com/djesc4hru/video/upload/v1791972473/traffic.mp4",
        "description": "Video mẫu lưu lượng xe cộ chất lượng cao trên Cloudinary CDN"
    },
    {
        "title": "☁️ Cloud: Giao Thông Hà Nội - Ngã Tư (hanoi_ngatu_v1.mp4)",
        "url": "https://res.cloudinary.com/djesc4hru/video/upload/v1791771318/hanoi_ngatu_v1.mp4",
        "description": "Video thực tế ngã tư giao thông Hà Nội trên Cloudinary CDN"
    }
]


def init_default_videos():
    """Tự động đảm bảo 2 link video Cloud CDN mẫu luôn tồn tại trong CSDL"""
    try:
        from database.database import SessionLocal
        with SessionLocal() as db:
            # Xóa các link demo/placeholder cũ nếu có (ví dụ Roboflow)
            db.query(VideoSourceModel).filter(VideoSourceModel.url.like("%roboflow%")).delete(synchronize_session=False)

            for seed in DEFAULT_SEEDS:
                existing = db.query(VideoSourceModel).filter(VideoSourceModel.url == seed["url"]).first()
                if not existing:
                    new_item = VideoSourceModel(
                        title=seed["title"],
                        url=seed["url"],
                        description=seed["description"]
                    )
                    db.add(new_item)
            db.commit()
    except Exception as e:
        print(f"[Init Videos] Lỗi khởi tạo video sources: {e}")


@router.get("", response_model=List[VideoSourceResponse])
def list_video_sources(db: Session = Depends(get_db)):
    """Lấy danh sách các nguồn video (tự động đảm bảo các link Cloud chuẩn và quét file local nếu có)"""
    # 1. Đảm bảo 2 link video Cloud chuẩn luôn tồn tại trong DB
    for seed in DEFAULT_SEEDS:
        existing = db.query(VideoSourceModel).filter(VideoSourceModel.url == seed["url"]).first()
        if not existing:
            new_item = VideoSourceModel(
                title=seed["title"],
                url=seed["url"],
                description=seed["description"]
            )
            db.add(new_item)
    db.commit()

    # 2. Tự động quét các file video có trong data/videos/ (nếu có trên máy)
    supported_exts = {".mp4", ".avi", ".mkv", ".mov"}
    if VIDEOS_DIR.exists():
        for file_path in VIDEOS_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                rel_url = f"data/videos/{file_path.name}"
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
