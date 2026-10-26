import os
import sys
import argparse
import random
import shutil
from pathlib import Path
from datetime import datetime
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import yaml
# pyrefly: ignore [missing-import]
from ultralytics import YOLO

# Cấu hình đường dẫn
AI_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AI_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
DATASET_DIR = DATA_DIR / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

# Import CSDL để lưu thông tin mẫu (tùy chọn)
try:
    sys.path.insert(0, str(BACKEND_DIR))
    from database.database import SessionLocal
    from database.models import DatasetSampleModel
    HAS_DB = True
except Exception:
    HAS_DB = False

# Ánh xạ từ COCO ID sang Dataset ID (0: car, 1: motorcycle, 2: bus, 3: truck)
COCO_TO_TRAFFIC = {
    1: 1,  # bicycle -> motorcycle (2 bánh)
    2: 0,  # car
    3: 1,  # motorcycle
    5: 2,  # bus
    7: 3   # truck
}
CLASS_NAMES = ["car", "motorcycle", "bus", "truck"]


def ensure_dirs():
    """Khởi tạo các thư mục dataset nếu chưa có"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)


def extract_from_single_video(
    video_path: Path,
    model: YOLO,
    count_per_video: int = 80,
    video_index: int = 1,
    total_videos: int = 1
):
    """
    Trích xuất count_per_video khung hình từ 1 video cụ thể,
    chạy auto-labeling và lưu trực tiếp xuống ổ cứng (không upload cloud).
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[{video_index}/{total_videos}] ❌ Không thể mở video: {video_path.name}")
        return 0, 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration_sec = total_frames / max(fps, 1.0)

    if total_frames <= 0:
        total_frames = 900  # Fallback nếu video stream không đọc được tổng frame

    # Lấy phân bổ đều từ đầu đến cuối video
    count = min(count_per_video, total_frames)
    step = max(1, total_frames // count)

    video_prefix = video_path.stem.replace(" ", "_")
    print(f"\n[{video_index}/{total_videos}] 🎬 Đang xử lý: {video_path.name}")
    print(f"   + Tổng số frame: {total_frames} (~{duration_sec:.1f}s) | Trích xuất: {count} ảnh (mỗi {step} frames)")

    saved_images = 0
    total_boxes = 0
    db = SessionLocal() if HAS_DB else None

    try:
        for idx in range(count):
            target_pos = min(idx * step, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_pos)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            frame_resized = cv2.resize(frame, (1280, 720))
            filename_base = f"{video_prefix}_{idx+1:03d}"
            img_filename = f"{filename_base}.jpg"
            lbl_filename = f"{filename_base}.txt"

            img_path = IMAGES_DIR / img_filename
            lbl_path = LABELS_DIR / lbl_filename

            # 1. Lưu file ảnh JPEG chất lượng cao trực tiếp tại local (không upload cloud)
            cv2.imwrite(str(img_path), frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

            # 2. Chạy Auto-labeling phát hiện phương tiện bằng YOLOv8
            results = model.predict(frame_resized, conf=0.18, imgsz=1280, verbose=False)[0]
            boxes = results.boxes

            label_lines = []
            class_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

            if boxes is not None and len(boxes) > 0:
                is_coco = len(model.names) > 10

                for b_idx in range(len(boxes)):
                    raw_cls = int(boxes.cls[b_idx].item())
                    xywhn = boxes.xywhn[b_idx].tolist()

                    if is_coco:
                        if raw_cls not in COCO_TO_TRAFFIC:
                            continue
                        target_cls = COCO_TO_TRAFFIC[raw_cls]
                    else:
                        target_cls = raw_cls if 0 <= raw_cls < len(CLASS_NAMES) else 0

                    w_px = xywhn[2] * 1280
                    h_px = xywhn[3] * 720
                    area_px = w_px * h_px

                    # Tinh chỉnh logic kích thước xe buýt / xe tải
                    if target_cls in (2, 3) and area_px < 10000:
                        target_cls = 0
                    elif target_cls == 0 and area_px > 45000 and (w_px > 180 or h_px > 160):
                        target_cls = 2

                    cls_name = CLASS_NAMES[target_cls]
                    class_counts[cls_name] += 1
                    label_lines.append(f"{target_cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}")

            # 3. Ghi file nhãn .txt chuẩn YOLO
            with open(lbl_path, "w", encoding="utf-8") as f:
                f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

            # 4. Ghi nhận vào CSDL 
            if db:
                try:
                    sample = DatasetSampleModel(
                        session_id=None,
                        image_filename=img_filename,
                        image_path=f"data/dataset/images/{img_filename}",
                        cloud_url=None,  # Không đẩy lên cloud
                        label_path=f"data/dataset/labels/{lbl_filename}",
                        vehicles_count=len(label_lines),
                        car_count=class_counts["car"],
                        moto_count=class_counts["motorcycle"],
                        bus_count=class_counts["bus"],
                        truck_count=class_counts["truck"],
                        created_at=datetime.now()
                    )
                    db.add(sample)
                    db.commit()
                except Exception:
                    db.rollback()

            saved_images += 1
            total_boxes += len(label_lines)

            # In tiến độ dạng ngắn gọn
            if (idx + 1) % 20 == 0 or (idx + 1) == count:
                print(f"      -> Tiến độ: {idx+1}/{count} ảnh ({saved_images} đã lưu, {total_boxes} bboxes)")

    finally:
        cap.release()
        if db:
            db.close()

    print(f"   ✅ Đã xong {video_path.name}: {saved_images} ảnh, {total_boxes} nhãn xe.")
    return saved_images, total_boxes


def auto_split_train_val(val_ratio: float = 0.18):
    """Tự động phân bổ lại toàn bộ tập ảnh và nhãn thành train/val và cập nhật data.yaml"""
    train_img_dir = IMAGES_DIR / "train"
    val_img_dir = IMAGES_DIR / "val"
    train_lbl_dir = LABELS_DIR / "train"
    val_lbl_dir = LABELS_DIR / "val"

    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.*"):
            f.unlink()

    all_imgs = [p for p in IMAGES_DIR.glob("*.jpg") if p.is_file()]
    random.seed(42)
    random.shuffle(all_imgs)

    val_count = max(1, int(len(all_imgs) * val_ratio))
    val_imgs = set(all_imgs[:val_count])
    train_imgs = set(all_imgs[val_count:])

    def copy_pair(img_p: Path, dest_img: Path, dest_lbl: Path):
        lbl_p = LABELS_DIR / f"{img_p.stem}.txt"
        shutil.copy2(img_p, dest_img / img_p.name)
        if lbl_p.exists():
            shutil.copy2(lbl_p, dest_lbl / lbl_p.name)
        else:
            (dest_lbl / lbl_p.name).write_text("")

    for p in train_imgs:
        copy_pair(p, train_img_dir, train_lbl_dir)

    for p in val_imgs:
        copy_pair(p, val_img_dir, val_lbl_dir)

    # Cập nhật data.yaml
    yaml_path = DATASET_DIR / "data.yaml"
    data_yaml = {
        "path": str(DATASET_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "nc": len(CLASS_NAMES),
        "names": {i: name for i, name in enumerate(CLASS_NAMES)}
    }
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    return len(train_imgs), len(val_imgs)


def run_batch_extraction(count_per_video: int = 80):
    """
    Quét toàn bộ video trong backend/data/videos,
    tự động chạy từng video để trích xuất và gán nhãn dataset.
    """
    ensure_dirs()

    # Tìm tất cả video hợp lệ
    video_extensions = (".mp4", ".avi", ".mkv", ".mov")
    video_files = sorted([
        f for f in VIDEOS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ])

    if not video_files:
        print(f"❌ Không tìm thấy video nào trong thư mục: {VIDEOS_DIR}")
        return

    print("=" * 70)
    print("🚦 TỰ ĐỘNG TRÍCH XUẤT DATASET HÀNG LOẠT TỪ TẤT CẢ VIDEO GIAO THÔNG")
    print(f"   + Thư mục video : {VIDEOS_DIR}")
    print(f"   + Số lượng video: {len(video_files)} video")
    print(f"   + Số ảnh / video: {count_per_video} ảnh (lấy đều theo thời gian)")
    print(f"   + Thư mục lưu   : {DATASET_DIR} (Chỉ lưu local, KHÔNG upload cloud)")
    print("=" * 70)

    # Khởi tạo model AI phục vụ auto-labeling
    vn_model = DATA_DIR / "models" / "yolov8_traffic_vn.pt"
    base_model = BACKEND_DIR / "yolov8n.pt"

    if vn_model.exists():
        print(f"🧠 Sử dụng mô hình: {vn_model.name} (Fine-tuned)")
        model = YOLO(str(vn_model))
    elif base_model.exists():
        print(f"🧠 Sử dụng mô hình: {base_model.name} (Base pretrained)")
        model = YOLO(str(base_model))
    else:
        print("🧠 Tải mô hình YOLOv8n mặc định...")
        model = YOLO("yolov8n.pt")

    grand_total_images = 0
    grand_total_boxes = 0

    for i, v_path in enumerate(video_files, 1):
        n_img, n_box = extract_from_single_video(
            video_path=v_path,
            model=model,
            count_per_video=count_per_video,
            video_index=i,
            total_videos=len(video_files)
        )
        grand_total_images += n_img
        grand_total_boxes += n_box

    # Phân bổ train / val
    print("\n" + "=" * 70)
    print("🔄 Đang phân bổ tập Train (82%) và Val (18%) chuẩn YOLOv8...")
    n_train, n_val = auto_split_train_val(val_ratio=0.18)

    print("\n" + "=" * 70)
    print("🎉 HOÀN THÀNH TOÀN BỘ QUÁ TRÌNH TRÍCH XUẤT DATASET!")
    print(f"   + Đã quét qua       : {len(video_files)} video")
    print(f"   + Tổng số ảnh đã tạo : {grand_total_images} ảnh")
    print(f"   + Tổng số hộp nhãn   : {grand_total_boxes} bounding boxes")
    print(f"   + Tập Train          : {n_train} ảnh (kèm nhãn .txt tương ứng)")
    print(f"   + Tập Val            : {n_val} ảnh (kèm nhãn .txt tương ứng)")
    print(f"   + File config YOLO   : {DATASET_DIR / 'data.yaml'}")
    print("=" * 70)
    print("💡 Giờ bạn có thể train lại model với tập dữ liệu đa dạng này bất kỳ lúc nào bằng:")
    print("   python backend/ai/train_yolo.py")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tự động trích xuất dataset từ toàn bộ video giao thông")
    parser.add_argument(
        "--count",
        type=int,
        default=80,
        help="Số lượng khung hình trích xuất cho mỗi video (mặc định: 80, khoảng 70-100)"
    )
    args = parser.parse_args()
    run_batch_extraction(count_per_video=args.count)
