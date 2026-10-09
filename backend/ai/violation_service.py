import os
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from config import VIOLATIONS_DIR
from database.database import SessionLocal
from database.models import ViolationModel
from ai.cloudinary_service import upload_in_background, is_cloudinary_configured


def generate_evidence_image(
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int],
    track_id: int,
    vehicle_type: str,
    speed_kmh: float,
    speed_limit: float,
    timestamp: datetime,
    session_id: int
) -> Tuple[str, str]:
    """
    Tạo ảnh bằng chứng vi phạm tốc độ sắc nét kèm dấu mờ (Watermark banner)
    chứa đầy đủ thông tin: ID xe, loại xe, tốc độ đo được, tốc độ quy định và thời gian.
    """
    evidence = frame.copy()
    h, w = evidence.shape[:2]

    # 1. Vẽ banner thông tin ở góc trên ảnh
    banner_h = 70
    overlay = evidence.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_h), (15, 23, 42), -1)  # Nền tối
    cv2.addWeighted(overlay, 0.85, evidence, 0.15, 0, evidence)

    # Viền đỏ cảnh báo dưới banner
    cv2.line(evidence, (0, banner_h), (w, banner_h), (0, 0, 230), 3)

    # Tiêu đề biên bản
    title_text = "BIEN BAN HINH ANH VI PHAM TOC DO - CAMERA GIAM SAT (ITS)"
    cv2.putText(
        evidence, title_text, (20, 28),
        cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 215, 255), 2, cv2.LINE_AA
    )

    # Thông số chi tiết
    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    excess_kmh = speed_kmh - speed_limit
    details_text = (
        f"XE: {vehicle_type.upper()} | TRACK: #{track_id} | "
        f"TOC DO: {speed_kmh:.1f} km/h (QUY DINH: {speed_limit:.1f} km/h - VUOT: +{excess_kmh:.1f} km/h) | "
        f"THOI GIAN: {time_str}"
    )
    cv2.putText(
        evidence, details_text, (20, 56),
        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA
    )

    # 2. Vẽ khung đỏ nổi bật quanh phương tiện vi phạm
    if bbox:
        x1, y1, x2, y2 = [int(v) for v in bbox]
        # Bounding box đỏ
        cv2.rectangle(evidence, (x1, y1), (x2, y2), (0, 0, 235), 3)

        # Nhãn nổi trên đầu xe
        tag_text = f"VI PHAM: {speed_kmh:.0f} km/h"
        (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_DUPLEX, 0.6, 2)
        tag_y = max(banner_h + 20, y1 - 10)
        cv2.rectangle(evidence, (x1, tag_y - th - 6), (x1 + tw + 10, tag_y + 4), (0, 0, 220), -1)
        cv2.putText(evidence, tag_text, (x1 + 5, tag_y - 2), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    # 3. Lưu file ảnh
    time_tag = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:21]
    filename = f"violation_s{session_id}_t{track_id}_{time_tag}.jpg"
    filepath = str(VIOLATIONS_DIR / filename)

    cv2.imwrite(filepath, evidence, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    return filename, filepath


def record_speed_violation(
    session_id: int,
    track_id: int,
    vehicle_type: str,
    speed_kmh: float,
    speed_limit: float,
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int]
) -> Optional[Dict[str, Any]]:
    """
    Xử lý lưu trữ vi phạm: tạo ảnh bằng chứng, ghi CSDL SQLite và upload Cloudinary ngầm.
    """
    now = datetime.now()
    try:
        filename, filepath = generate_evidence_image(
            frame=frame,
            bbox=bbox,
            track_id=track_id,
            vehicle_type=vehicle_type,
            speed_kmh=speed_kmh,
            speed_limit=speed_limit,
            timestamp=now,
            session_id=session_id
        )
    except Exception as e:
        print(f"[ViolationService] Lỗi tạo ảnh bằng chứng: {e}")
        return None

    db = SessionLocal()
    violation_id = None
    try:
        record = ViolationModel(
            session_id=session_id,
            track_id=track_id,
            vehicle_type=vehicle_type,
            speed_kmh=round(float(speed_kmh), 1),
            speed_limit=round(float(speed_limit), 1),
            evidence_image_path=filename,
            cloud_url=None,
            violated_at=now,
            status="pending"
        )
        db.add(record)
        db.commit()
        violation_id = record.id
    except Exception as e:
        print(f"[ViolationService] Lỗi lưu CSDL vi phạm: {e}")
        db.rollback()
    finally:
        db.close()

    # Upload ảnh bằng chứng lên Cloudinary ở chế độ ngầm nếu đã kết nối
    if is_cloudinary_configured() and violation_id:
        upload_in_background(
            image_bgr_copy=cv2.imread(filepath),
            public_id=filename.replace(".jpg", ""),
            sample_id=None
        )

    return {
        "id": violation_id,
        "session_id": session_id,
        "track_id": track_id,
        "vehicle_type": vehicle_type,
        "speed_kmh": round(float(speed_kmh), 1),
        "speed_limit": round(float(speed_limit), 1),
        "evidence_image_path": filename,
        "filename": filename,
        "violated_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }
