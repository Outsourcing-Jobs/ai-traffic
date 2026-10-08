import os
# pyrefly: ignore [missing-import]
import cv2
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from config import (
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CLOUDINARY_FOLDER
)
from database.database import SessionLocal
from database.models import DatasetSampleModel

# ThreadPool chạy ngầm tối đa 2 workers để không chiếm dụng CPU, RAM hay làm nghẽn băng thông
_upload_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cloudinary_worker")


def is_cloudinary_configured() -> bool:
    """Kiểm tra xem thông tin tài khoản Cloudinary đã được cấu hình chưa"""
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)



def compress_frame_for_upload(image_bgr) -> Optional[bytes]:
    """
    Tối ưu hóa hình ảnh trước khi upload:
    - Giới hạn độ phân giải tối đa 1280px (vừa đủ độ sắc nét chi tiết xe)
    - Nén JPEG mức chất lượng 78-80% (giảm dung lượng từ 500KB xuống ~70KB, tiết kiệm 85% mạng và RAM)
    """
    try:
        h, w = image_bgr.shape[:2]
        target_w = min(1280, w)
        if w > target_w:
            target_h = int(h * (target_w / w))
            resized = cv2.resize(image_bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)
        else:
            resized = image_bgr

        success, buffer = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
        if success:
            return buffer.tobytes()
    except Exception as e:
        print(f"[Cloudinary] Lỗi nén ảnh: {e}")
    return None


def upload_image_to_cloudinary(
    image_bgr,
    public_id: str,
    folder: Optional[str] = None,
    timeout: int = 8
) -> Optional[str]:
    """
    Upload ảnh lên Cloudinary với cơ chế Timeout an toàn (8 giây).
    Nếu mạng chập chờn hoặc Cloudinary quá tải, hàm trả về None mà KHÔNG BAO GIỜ làm crash server.
    """
    if not is_cloudinary_configured():
        return None

    jpeg_bytes = compress_frame_for_upload(image_bgr)
    if not jpeg_bytes:
        return None

    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"
    files = {"file": (f"{public_id}.jpg", jpeg_bytes, "image/jpeg")}
    data = {"public_id": public_id, "folder": folder or CLOUDINARY_FOLDER}


    try:
        res = requests.post(
            url,
            auth=HTTPBasicAuth(CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET),
            files=files,
            data=data,
            timeout=timeout
        )
        if res.status_code == 200:
            secure_url = res.json().get("secure_url")
            print(f"[Cloudinary] Tải lên thành công: {secure_url}")
            return secure_url
        else:
            print(f"[Cloudinary] Lỗi phản hồi ({res.status_code}): {res.text[:120]}")
    except requests.exceptions.Timeout:
        print(f"[Cloudinary Warning] Upload bị timeout sau {timeout}s (bỏ qua để không nghẽn hệ thống)")
    except Exception as e:
        print(f"[Cloudinary Warning] Ngoại lệ kết nối: {e}")

    return None


def upload_in_background(image_bgr_copy, public_id: str, sample_id: Optional[int] = None):
    """
    CƠ CHẾ CHẠY NGẦM HOÀN TOÀN (Non-blocking Background Thread):
    Đẩy ảnh vào hàng đợi nền để upload từ từ.
    Sau khi upload xong tự động cập nhật cột `cloud_url` trong SQLite.
    Hệ thống phát video và AI nhận diện thời gian thực vẫn chạy 30 FPS mượt mà 100%.
    """
    if not is_cloudinary_configured():
        return

    def _worker():
        try:
            url = upload_image_to_cloudinary(image_bgr_copy, public_id=public_id, timeout=10)
            if url and sample_id:
                db = SessionLocal()
                try:
                    record = db.query(DatasetSampleModel).filter(DatasetSampleModel.id == sample_id).first()
                    if record:
                        record.cloud_url = url
                        db.commit()
                        print(f"[Cloudinary Background] Đã cập nhật cloud_url cho mẫu #{sample_id}")
                except Exception as db_err:
                    print(f"[Cloudinary Background] Lỗi cập nhật DB: {db_err}")
                finally:
                    db.close()
        except Exception as worker_err:
            print(f"[Cloudinary Worker] Lỗi xử lý ngầm: {worker_err}")

    _upload_executor.submit(_worker)
