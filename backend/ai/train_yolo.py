import os
import shutil
from pathlib import Path
# pyrefly: ignore [missing-import]
from ultralytics import YOLO

# Thiết lập đường dẫn
AI_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AI_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
METRICS_DIR = MODELS_DIR / "metrics"
DATASET_DIR = DATA_DIR / "dataset"
DATA_YAML = DATASET_DIR / "data.yaml"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)


def train_traffic_model():
    """
    Huấn luyện chuyển giao (Transfer Learning / Fine-Tuning) mô hình YOLOv8n
    trên tập dữ liệu phương tiện giao thông thực tế Việt Nam:
    Class 0: car (Ô tô con, taxi, SUV)
    Class 1: motorcycle (Xe máy, xe 2 bánh)
    Class 2: bus (Xe buýt, xe khách)
    Class 3: truck (Xe tải, xe ben, container)
    """
    print("=" * 60)
    print("🚦 BẮT ĐẦU FINE-TUNING YOLOV8N TRÊN DỮ LIỆU GIAO THÔNG VIỆT NAM")
    print("=" * 60)

    # 1. Khởi tạo mô hình nền tảng YOLOv8n pretrained
    base_model_path = BACKEND_DIR / "yolov8n.pt"
    model = YOLO(str(base_model_path) if base_model_path.exists() else "yolov8n.pt")

    # 2. Thiết lập tham số huấn luyện tối ưu
    runs_dir = MODELS_DIR / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset config: {DATA_YAML}")
    print(f"Output runs: {runs_dir}")

    # Chạy training
    results = model.train(
        data=str(DATA_YAML).replace("\\", "/"),
        epochs=12,              # 12 epochs tối ưu cho CPU, học nhanh hội tụ các class xe
        imgsz=416,              # Kích thước 416 vừa chuẩn vừa nhanh
        batch=8,                # Batch size 8
        device="cpu",           # Huấn luyện trên CPU máy tính
        project=str(runs_dir).replace("\\", "/"),
        name="traffic_vn",
        exist_ok=True,
        plots=True,             # Tự động xuất biểu đồ huấn luyện Loss, mAP, Confusion Matrix
        verbose=True,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        patience=5
    )

    print("\n" + "=" * 60)
    print("✅ HUẤN LUYỆN HOÀN TẤT! ĐANG XUẤT MODEL VÀ BIỂU ĐỒ METRICS...")
    print("=" * 60)

    train_output_dir = runs_dir / "traffic_vn"
    best_weights_src = train_output_dir / "weights" / "best.pt"
    target_model_file = MODELS_DIR / "yolov8_traffic_vn.pt"

    # Sao chép file trọng số tốt nhất vào models/
    if best_weights_src.exists():
        shutil.copy2(best_weights_src, target_model_file)
        print(f"🎯 Đã lưu trọng số Fine-tuned: {target_model_file}")
    else:
        # Fallback lấy last.pt nếu không có best.pt
        last_weights = train_output_dir / "weights" / "last.pt"
        if last_weights.exists():
            shutil.copy2(last_weights, target_model_file)
            print(f"🎯 Đã lưu trọng số (last): {target_model_file}")

    # Sao chép các biểu đồ đánh giá vào thư mục metrics/ phục vụ Báo cáo & Nghiệm thu
    chart_names = [
        "results.png",
        "confusion_matrix.png",
        "confusion_matrix_normalized.png",
        "F1_curve.png",
        "PR_curve.png",
        "val_batch0_pred.jpg",
        "val_batch0_labels.jpg"
    ]

    copied_charts = []
    for c_name in chart_names:
        c_src = train_output_dir / c_name
        if c_src.exists():
            c_dest = METRICS_DIR / c_name
            shutil.copy2(c_src, c_dest)
            copied_charts.append(c_name)

    print(f"📊 Đã sao chép {len(copied_charts)} biểu đồ đánh giá vào: {METRICS_DIR}")
    for c in copied_charts:
        print(f"   + {c}")

    # Đánh giá lại trên tập val
    try:
        val_metrics = model.val()
        print("\n📈 THỐNG KÊ HIỆU NĂNG TRÊN TẬP KIỂM CHỨNG (VAL):")
        print(f"   - mAP@0.5      : {val_metrics.box.map50 * 100:.2f}%")
        print(f"   - mAP@0.5:0.95 : {val_metrics.box.map * 100:.2f}%")
        print(f"   - Precision    : {val_metrics.box.mp * 100:.2f}%")
        print(f"   - Recall       : {val_metrics.box.mr * 100:.2f}%")
    except Exception as e:
        print(f"Lưu ý khi validate: {e}")

    return target_model_file


if __name__ == "__main__":
    train_traffic_model()
