# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
from typing import Optional
from video_manager import video_manager
from ai.dataset_generator import (
    label_and_save_frame, extract_batch_from_video,
    get_dataset_summary, ensure_dataset_metadata
)
from config import DATASET_IMAGES_DIR
from database.database import SessionLocal
from database.models import DatasetSampleModel

router = APIRouter(prefix="/api/dataset", tags=["Dataset"])


@router.post("/capture-live/{session_id}")
def capture_live_frame(session_id: int):
    """
    Chụp khung hình gốc hiện tại từ luồng video đang chạy (Realtime),
    tự động chạy YOLOv8 để gán nhãn bounding box (Auto-labeling),
    lưu file ảnh vào images/ và file nhãn vào labels/, đồng thời lưu CSDL.
    """
    runner = video_manager.get_runner(session_id)
    if not runner or not runner.is_running:
        raise HTTPException(
            status_code=400,
            detail="Session chưa được kích hoạt hoặc chưa chạy video. Vui lòng bấm 'Bắt Đầu Giám Sát' trước."
        )

    raw_frame = runner.get_latest_raw_frame()
    if raw_frame is None:
        raise HTTPException(
            status_code=404,
            detail="Chưa nhận được khung hình nào từ camera. Vui lòng thử lại sau 1-2 giây."
        )

    # Chạy auto-labeling bằng model của pipeline
    model = runner.pipeline.detector.model
    result = label_and_save_frame(raw_frame, model, session_id=session_id, prefix="live")

    # Lấy tổng số lượng trong dataset
    summary = get_dataset_summary()

    return {
        "success": True,
        "message": f"Đã chụp và tự động gán nhãn {result['vehicles_count']} xe vào Dataset!",
        "sample": result,
        "summary": summary
    }


@router.post("/auto-extract/{session_id}")
def auto_extract_batch(session_id: int, count: int = Query(50, ge=5, le=100)):
    """
    Tự động trích xuất `count` khung hình từ video của session
    và gán nhãn tự động hàng loạt để tạo ngay bộ dữ liệu hoàn chỉnh.
    """
    runner = video_manager.get_runner(session_id)
    if not runner:
        raise HTTPException(
            status_code=400,
            detail="Session chưa tồn tại hoặc chưa sẵn sàng."
        )

    model = runner.pipeline.detector.model
    try:
        batch_result = extract_batch_from_video(
            video_source=runner.video_source,
            model=model,
            session_id=session_id,
            count=count
        )
        summary = get_dataset_summary()
        return {
            "success": True,
            "message": f"Đã trích xuất và tự động gán nhãn {batch_result['extracted_count']} khung hình!",
            "result": batch_result,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi trích xuất video: {str(e)}")


@router.post("/batch-extract-all")
def api_batch_extract_all(count_per_video: int = Query(80, ge=20, le=120)):
    """
    Tự động quét toàn bộ video trong data/videos,
    trích xuất count_per_video ảnh cho mỗi video và lưu trực tiếp tại local.
    """
    from ai.batch_extract_dataset import run_batch_extraction
    import threading
    t = threading.Thread(target=run_batch_extraction, kwargs={"count_per_video": count_per_video}, daemon=True)
    t.start()
    return {
        "success": True,
        "message": f"Đã khởi động tiến trình trích xuất tự động ~{count_per_video} ảnh/video chạy ngầm!",
        "count_per_video": count_per_video
    }


@router.get("/summary")
def get_summary():
    """Lấy số liệu thống kê tổng quan của Bộ dữ liệu"""
    ensure_dataset_metadata()
    return get_dataset_summary()


@router.get("/samples")
def get_recent_samples(limit: int = 30):
    """Lấy danh sách các mẫu đã chụp gần đây từ CSDL"""
    db = SessionLocal()
    try:
        samples = (
            db.query(DatasetSampleModel)
            .order_by(DatasetSampleModel.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": s.id,
                "session_id": s.session_id,
                "image_filename": s.image_filename,
                "vehicles_count": s.vehicles_count,
                "car_count": s.car_count,
                "moto_count": s.moto_count,
                "bus_count": s.bus_count,
                "truck_count": s.truck_count,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
                "cloud_url": s.cloud_url,
                "image_url": s.cloud_url if s.cloud_url else f"/api/dataset/image/{s.image_filename}"
            }
            for s in samples
        ]
    finally:
        db.close()


@router.get("/image/{filename}")
def get_sample_image(filename: str):
    """Xem trực tiếp file ảnh trong dataset (nếu lưu local)"""
    img_path = DATASET_IMAGES_DIR / filename
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy file ảnh")
    return FileResponse(img_path, media_type="image/jpeg")


# pyrefly: ignore [missing-import]
from pydantic import BaseModel
import config
from ai.cloudinary_service import is_cloudinary_configured


class CloudinaryConfigRequest(BaseModel):
    cloud_name: str
    api_key: str
    api_secret: str


@router.get("/cloudinary-status")
def get_cloudinary_status():
    """Kiểm tra trạng thái kết nối Cloudinary"""
    return {
        "is_configured": is_cloudinary_configured(),
        "cloud_name": config.CLOUDINARY_CLOUD_NAME or None
    }


@router.post("/configure-cloudinary")
def configure_cloudinary(req: CloudinaryConfigRequest):
    """Lưu và kích hoạt cấu hình Cloudinary trực tiếp từ Web"""
    c_name = req.cloud_name.strip()
    k = req.api_key.strip()
    s = req.api_secret.strip()

    config.CLOUDINARY_CLOUD_NAME = c_name
    config.CLOUDINARY_API_KEY = k
    config.CLOUDINARY_API_SECRET = s

    env_path = config.BASE_DIR / "backend" / ".env"
    content = (
        f"CLOUDINARY_CLOUD_NAME={c_name}\n"
        f"CLOUDINARY_API_KEY={k}\n"
        f"CLOUDINARY_API_SECRET={s}\n"
    )
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "success": True,
        "message": "Đã lưu và kích hoạt cấu hình Cloudinary thành công!",
        "cloud_name": c_name
    }

