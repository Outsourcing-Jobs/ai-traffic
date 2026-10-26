import os
import random
import shutil
from pathlib import Path
import cv2
import numpy as np
import yaml
from ultralytics import YOLO

# Cấu hình đường dẫn
AI_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AI_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
DATASET_DIR = DATA_DIR / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

# Ánh xạ từ COCO ID sang Dataset ID (0: car, 1: motorcycle, 2: bus, 3: truck)
COCO_TO_TRAFFIC = {
    1: 1,  # bicycle -> motorcycle (2 bánh)
    2: 0,  # car
    3: 1,  # motorcycle
    5: 2,  # bus
    7: 3   # truck
}
CLASS_NAMES = ["car", "motorcycle", "bus", "truck"]


def extract_frames_from_video(video_path: Path, output_prefix: str, count: int = 40):
    """Trích xuất count frames phân bổ đều từ video và lưu vào DATASET"""
    if not video_path.exists():
        print(f"Không tìm thấy video: {video_path}")
        return []

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return []

    step = max(1, total_frames // count)
    saved = []

    model_path = BACKEND_DIR / "yolov8n.pt"
    model = YOLO(str(model_path) if model_path.exists() else "yolov8n.pt")

    for i in range(count):
        pos = min(i * step, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            break

        frame_resized = cv2.resize(frame, (1280, 720))
        filename_base = f"{output_prefix}_{i+1:03d}"
        img_name = f"{filename_base}.jpg"
        lbl_name = f"{filename_base}.txt"

        img_path = IMAGES_DIR / img_name
        lbl_path = LABELS_DIR / lbl_name

        # Nếu đã có file thì bỏ qua
        if img_path.exists() and lbl_path.exists():
            saved.append((img_path, lbl_path))
            continue

        # Lưu ảnh JPEG
        cv2.imwrite(str(img_path), frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

        # Dự đoán nhãn
        results = model.predict(frame_resized, conf=0.18, imgsz=1280, verbose=False)[0]
        boxes = results.boxes

        label_lines = []
        if boxes is not None and len(boxes) > 0:
            for b_idx in range(len(boxes)):
                coco_cls = int(boxes.cls[b_idx].item())
                if coco_cls not in COCO_TO_TRAFFIC:
                    continue

                target_cls = COCO_TO_TRAFFIC[coco_cls]
                xywhn = boxes.xywhn[b_idx].tolist()

                # Tinh chỉnh hình học cho xe buýt / xe tải Việt Nam
                w = xywhn[2] * 1280
                h = xywhn[3] * 720
                area = w * h

                if target_cls in (2, 3) and area < 10000:
                    target_cls = 0  # Quá nhỏ -> car
                elif target_cls == 0 and area > 45000 and (w > 180 or h > 160):
                    target_cls = 2  # Xe khách/xe buýt to

                label_lines.append(f"{target_cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}")

        with open(lbl_path, "w", encoding="utf-8") as f:
            f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

        saved.append((img_path, lbl_path))

    cap.release()
    print(f"-> Đã trích xuất {len(saved)} frames từ {video_path.name}")
    return saved


def organize_train_val_split(val_ratio: float = 0.18):
    """Phân chia ảnh và nhãn thành 2 tập train và val chuẩn YOLOv8"""
    train_img_dir = IMAGES_DIR / "train"
    val_img_dir = IMAGES_DIR / "val"
    train_lbl_dir = LABELS_DIR / "train"
    val_lbl_dir = LABELS_DIR / "val"

    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Lấy tất cả các file ảnh gốc ở tầng images/ (trừ subfolder train/val)
    all_imgs = [p for p in IMAGES_DIR.glob("*.jpg") if p.is_file()]
    random.seed(42)
    random.shuffle(all_imgs)

    val_count = max(1, int(len(all_imgs) * val_ratio))
    val_imgs = set(all_imgs[:val_count])
    train_imgs = set(all_imgs[val_count:])

    def copy_pair(img_path: Path, dest_img_dir: Path, dest_lbl_dir: Path):
        lbl_path = LABELS_DIR / f"{img_path.stem}.txt"
        shutil.copy2(img_path, dest_img_dir / img_path.name)
        if lbl_path.exists():
            shutil.copy2(lbl_path, dest_lbl_dir / lbl_path.name)
        else:
            (dest_lbl_dir / lbl_path.name).write_text("")

    # Dọn dẹp subfolder cũ nếu có
    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        for f in d.glob("*.*"):
            f.unlink()

    for p in train_imgs:
        copy_pair(p, train_img_dir, train_lbl_dir)

    for p in val_imgs:
        copy_pair(p, val_img_dir, val_lbl_dir)

    print(f"-> Đã phân chia: {len(train_imgs)} ảnh train, {len(val_imgs)} ảnh val")

    # Tạo data.yaml chuẩn YOLO
    data_yaml = {
        "path": str(DATASET_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "nc": len(CLASS_NAMES),
        "names": {i: name for i, name in enumerate(CLASS_NAMES)}
    }

    yaml_path = DATASET_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    print(f"-> Đã cập nhật file config: {yaml_path}")
    return len(train_imgs), len(val_imgs)


if __name__ == "__main__":
    print("=== BẮT ĐẦU CHUẨN BỊ BỘ DỮ LIỆU XE GIAO THÔNG VIỆT NAM ===")
    extract_frames_from_video(VIDEOS_DIR / "hanoi_ngatu_v1.mp4", "hanoi_ngatu", count=45)
    extract_frames_from_video(VIDEOS_DIR / "hanoi_vcc.mp4", "hanoi_vcc", count=45)
    n_train, n_val = organize_train_val_split(val_ratio=0.18)
    print(f"=== HOÀN TẤT: Tổng cộng {n_train + n_val} mẫu dữ liệu ({n_train} train, {n_val} val) ===")
