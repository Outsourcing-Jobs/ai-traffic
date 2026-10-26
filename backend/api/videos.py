from typing import List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import VideoSourceModel
from database.schemas import VideoSourceCreate, VideoSourceResponse

router = APIRouter(prefix="/api/videos", tags=["Video Sources"])

from config import VIDEOS_DIR, BACKEND_DIR

DEFAULT_SEEDS = []


def sync_local_videos(db: Session):
    """Tự động quét thư mục data/videos và backend để đồng bộ video local vào CSDL"""
    supported_exts = {".mp4", ".avi", ".mkv", ".mov"}
    
    # 1. Quét trong data/videos/
    if VIDEOS_DIR.exists():
        for file in VIDEOS_DIR.glob("*.*"):
            if file.suffix.lower() in supported_exts:
                rel_url = f"data/videos/{file.name}"
                exists = db.query(VideoSourceModel).filter(
                    (VideoSourceModel.url == rel_url) | (VideoSourceModel.url == file.name)
                ).first()
                if not exists:
                    title = file.stem.replace("_", " ").title()
                    db.add(VideoSourceModel(
                        title=f"Video Local: {title} ({file.suffix.upper()})",
                        url=rel_url,
                        description=f"File video cục bộ trong data/videos/{file.name}"
                    ))

    # 2. Kiểm tra vehicles.mp4 tại backend
    sample_backend = BACKEND_DIR / "vehicles.mp4"
    if sample_backend.exists():
        exists = db.query(VideoSourceModel).filter(
            (VideoSourceModel.url == "vehicles.mp4") | (VideoSourceModel.url == str(sample_backend))
        ).first()
        if not exists:
            db.add(VideoSourceModel(
                title="Video Giao Thông Local (vehicles.mp4)",
                url="vehicles.mp4",
                description="Video mẫu giao thông cục bộ tại backend"
            ))

    db.commit()


def init_default_videos():
    """Tự động bổ sung nguồn video local và Camera IP RTSP vào CSDL nếu chưa có"""
    from database.database import SessionLocal
    db = SessionLocal()
    try:
        # Đồng bộ toàn bộ video local
        sync_local_videos(db)

        # Kiểm tra nguồn Camera IP RTSP
        rtsp_exists = db.query(VideoSourceModel).filter(VideoSourceModel.url.like("rtsp://%")).first()
        if not rtsp_exists:
            db.add(VideoSourceModel(
                title="Camera IP Giao Thông (RTSP Livestream Mẫu)",
                url="rtsp://demo:demo@192.168.1.100:554/stream1",
                description="Luồng Camera IP trực tiếp qua giao thức RTSP độ trễ thấp"
            ))

        # Dọn dẹp link rác nếu có
        bad_link = db.query(VideoSourceModel).filter(VideoSourceModel.url == "https://abc.con").first()
        if bad_link:
            db.delete(bad_link)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Videos] Lỗi init default videos: {e}")
    finally:
        db.close()


@router.get("", response_model=List[VideoSourceResponse])
def list_video_sources(db: Session = Depends(get_db)):
    """Lấy danh sách các nguồn video trực tiếp từ CSDL (tự động đồng bộ video local)"""
    try:
        sync_local_videos(db)
    except Exception as e:
        print(f"[Videos] Lỗi sync video local: {e}")
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
