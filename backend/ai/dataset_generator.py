import os
# pyrefly: ignore [missing-import]
import cv2
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from database.database import SessionLocal
from database.models import DatasetSampleModel
from ai.cloudinary_service import (
    upload_image_to_cloudinary, upload_in_background, is_cloudinary_configured
)
from config import (
    DATASET_DIR, DATASET_IMAGES_DIR, DATASET_LABELS_DIR,
    DATASET_CLASS_MAP, DATASET_CLASS_NAMES, TARGET_CLASSES,
    STREAM_FRAME_WIDTH, STREAM_FRAME_HEIGHT, VIDEOS_DIR, BASE_DIR, BACKEND_DIR
)



def ensure_dataset_metadata():
    """Tự động khởi tạo file data.yaml và README.md nếu chưa có"""
    DATASET_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_LABELS_DIR.mkdir(parents=True, exist_ok=True)

    yaml_path = DATASET_DIR / "data.yaml"
    if not yaml_path.exists():
        data_yaml = {
            "path": str(DATASET_DIR.resolve()),
            "train": "images",
            "val": "images",
            "nc": len(DATASET_CLASS_NAMES),
            "names": {i: name for i, name in enumerate(DATASET_CLASS_NAMES)}
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    readme_path = DATASET_DIR / "README.md"
    if not readme_path.exists():
        readme_content = f"""# 🚗 Traffic Vehicle Dataset (Đồ án tốt nghiệp ĐHCN Việt - Hung)

## 1. Giới thiệu bộ dữ liệu
Bộ dữ liệu hình ảnh phương tiện giao thông thực nghiệm được trích xuất trực tiếp từ camera giám sát giao thông thực tế phục vụ đồ án:
**"Xây dựng CSDL và giao diện người dùng cho ứng dụng xác định lưu lượng và ước lượng tốc độ trung bình của phương tiện giao thông sử dụng camera giám sát"**.

## 2. Danh mục phân loại phương tiện (Classes)
- **Class 0 (`car`)**: Ô tô con, xe bán tải, SUV
- **Class 1 (`motorcycle`)**: Xe máy, xe gắn máy, xe tay ga
- **Class 2 (`bus`)**: Xe buýt công cộng, xe khách
- **Class 3 (`truck`)**: Xe tải, container, xe ben

## 3. Định dạng nhãn (Annotation Format)
Chuẩn format YOLOv8: Mỗi file `.txt` tương ứng với một file `.jpg` cùng tên trong thư mục `images/`.
Cấu trúc mỗi dòng:
`<class_id> <x_center> <y_center> <width> <height>` (được chuẩn hóa trong đoạn [0, 1]).
"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)


def label_and_save_frame(
    frame, model, session_id: Optional[int] = None,
    prefix: str = "sample", upload_async: bool = False
) -> Dict[str, Any]:
    """
    Nhận 1 khung hình (BGR), chạy YOLOv8 tự động phát hiện xe (Auto-labeling),
    lưu ảnh vào images/ và file nhãn vào labels/.
    Tối ưu hóa: Hỗ trợ upload ngầm (upload_async) để không block luồng xử lý.
    """
    ensure_dataset_metadata()

    # Sinh tên file dựa trên timestamp
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:21]
    filename_base = f"{prefix}_{timestamp_str}"
    img_filename = f"{filename_base}.jpg"
    lbl_filename = f"{filename_base}.txt"

    img_path = DATASET_IMAGES_DIR / img_filename
    lbl_path = DATASET_LABELS_DIR / lbl_filename

    # 1. Lưu ảnh JPEG cục bộ (chất lượng 85 để file nhẹ)
    cv2.imwrite(str(img_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

    # 2. Chạy Auto-labeling bằng YOLOv8
    results = model(frame, classes=TARGET_CLASSES, conf=0.30, verbose=False)

    label_lines = []
    class_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

    if results and len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes
        for i in range(len(boxes)):
            coco_cls = int(boxes.cls[i].item())
            if coco_cls not in DATASET_CLASS_MAP:
                continue

            dataset_cls = DATASET_CLASS_MAP[coco_cls]
            cls_name = DATASET_CLASS_NAMES[dataset_cls]
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            xywhn = boxes.xywhn[i].tolist()
            label_lines.append(
                f"{dataset_cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}"
            )

    # 3. Ghi file nhãn .txt chuẩn YOLO
    with open(lbl_path, "w", encoding="utf-8") as f:
        f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

    vehicles_count = len(label_lines)

    # 4. Lưu thông tin vào CSDL SQLite trước
    cloud_url = None
    sample_id = None
    db = SessionLocal()
    try:
        sample_record = DatasetSampleModel(
            session_id=session_id,
            image_filename=img_filename,
            image_path=f"data/dataset/images/{img_filename}",
            cloud_url=None,
            label_path=f"data/dataset/labels/{lbl_filename}",
            vehicles_count=vehicles_count,
            car_count=class_counts.get("car", 0),
            moto_count=class_counts.get("motorcycle", 0),
            bus_count=class_counts.get("bus", 0),
            truck_count=class_counts.get("truck", 0),
            created_at=datetime.now()
        )
        db.add(sample_record)
        db.commit()
        sample_id = sample_record.id
    except Exception as e:
        print(f"[Dataset] Lỗi lưu DB record: {e}")
        db.rollback()
    finally:
        db.close()

    # 5. Xử lý Upload Cloudinary (Tối ưu chống lag/sập)
    if is_cloudinary_configured():
        if upload_async:
            # Chạy nền hoàn toàn, trả kết quả tức thì
            upload_in_background(frame.copy(), public_id=filename_base, sample_id=sample_id)
        else:
            # Thử upload nhanh với timeout 6s
            cloud_url = upload_image_to_cloudinary(frame, public_id=filename_base, timeout=6)
            if cloud_url and sample_id:
                db = SessionLocal()
                try:
                    rec = db.query(DatasetSampleModel).filter(DatasetSampleModel.id == sample_id).first()
                    if rec:
                        rec.cloud_url = cloud_url
                        db.commit()
                finally:
                    db.close()

    return {
        "id": sample_id,
        "image_filename": img_filename,
        "label_filename": lbl_filename,
        "cloud_url": cloud_url,
        "vehicles_count": vehicles_count,
        "class_counts": class_counts
    }




def extract_batch_from_video(video_source: str, model, session_id: Optional[int] = None, count: int = 50) -> Dict[str, Any]:
    """
    Trích xuất tự động `count` khung hình từ video (phân bố đều theo thời gian)
    và gán nhãn tự động hàng loạt.
    """
    ensure_dataset_metadata()

    # Resolve đường dẫn video
    video_path = video_source
    if not video_path.startswith(("http://", "https://", "rtsp://")) and not os.path.exists(video_path):
        candidate_backend = BACKEND_DIR / video_path
        if candidate_backend.exists():
            video_path = str(candidate_backend)
        else:
            candidate_videos = VIDEOS_DIR / os.path.basename(video_path)
            if candidate_videos.exists():
                video_path = str(candidate_videos)
            else:
                candidate_base = BASE_DIR / video_path
                if candidate_base.exists():
                    video_path = str(candidate_base)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Không thể mở video để trích xuất: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 1500  # Fallback ước lượng ~50s

    step = max(1, total_frames // count)
    saved_samples = []
    total_vehicles = 0

    frame_idx = 0
    extracted_so_far = 0

    while extracted_so_far < count:
        target_pos = extracted_so_far * step
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_pos)
        ret, frame = cap.read()
        if not ret:
            break

        # Resize chuẩn
        frame = cv2.resize(frame, (STREAM_FRAME_WIDTH, STREAM_FRAME_HEIGHT))
        res = label_and_save_frame(
            frame, model, session_id=session_id,
            prefix=f"batch_{extracted_so_far+1:03d}", upload_async=True
        )
        saved_samples.append(res)

        total_vehicles += res["vehicles_count"]
        extracted_so_far += 1

    cap.release()

    return {
        "extracted_count": extracted_so_far,
        "total_vehicles": total_vehicles,
        "samples": saved_samples
    }


def get_dataset_summary() -> Dict[str, Any]:
    """Thống kê tổng quan số lượng ảnh, nhãn và phương tiện trong dataset"""
    ensure_dataset_metadata()

    image_files = list(DATASET_IMAGES_DIR.glob("*.jpg"))
    label_files = list(DATASET_LABELS_DIR.glob("*.txt"))

    class_totals = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}
    total_boxes = 0

    for lbl_file in label_files:
        try:
            with open(lbl_file, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        cls_id = int(parts[0])
                        if 0 <= cls_id < len(DATASET_CLASS_NAMES):
                            name = DATASET_CLASS_NAMES[cls_id]
                            class_totals[name] = class_totals.get(name, 0) + 1
                            total_boxes += 1
        except Exception:
            continue

    return {
        "total_images": len(image_files),
        "total_labels": len(label_files),
        "total_boxes": total_boxes,
        "class_totals": class_totals
    }
