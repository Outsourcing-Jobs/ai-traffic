# HƯỚNG DẪN HUẤN LUYỆN YOLOv8 (AI TRAFFIC)

> Tài liệu đầy đủ và chi tiết đã được lưu tại: [docs/07_huong_dan_huan_luyen_yolo.md](file:///d:/Jobs/ai-trafic/docs/07_huong_dan_huan_luyen_yolo.md)

---

## Tóm tắt nhanh vị trí file & lệnh thực thi

### 1. Vị trí các file cốt lõi:
- **File chạy train:** [backend/ai/train_yolo.py](file:///d:/Jobs/ai-trafic/backend/ai/train_yolo.py)
- **File chuẩn bị dữ liệu train/val:** [backend/ai/prepare_vietnam_dataset.py](file:///d:/Jobs/ai-trafic/backend/ai/prepare_vietnam_dataset.py)
- **Thư mục dataset:** [backend/data/dataset/](file:///d:/Jobs/ai-trafic/backend/data/dataset/)
  - `data.yaml`: Cấu hình 4 class (`car`, `motorcycle`, `bus`, `truck`)
  - `images/`: Chứa folder `train/` và `val/`
  - `labels/`: Chứa folder `train/` và `val/`
- **Model đầu ra sau train:** [backend/data/models/yolov8_traffic_vn.pt](file:///d:/Jobs/ai-trafic/backend/data/models/yolov8_traffic_vn.pt)
- **Biểu đồ đánh giá kết quả (Loss, mAP, Confusion Matrix):** [backend/data/models/metrics/](file:///d:/Jobs/ai-trafic/backend/data/models/metrics/)

---

### 2. Các bước chạy lệnh:

```powershell
# 1. Kích hoạt môi trường ảo
.venv\Scripts\activate

# 2. Chuẩn bị & phân chia dataset thành 82% train / 18% val
python backend/ai/prepare_vietnam_dataset.py

# 3. Tiến hành huấn luyện mô hình YOLOv8
python backend/ai/train_yolo.py
```

Sau khi hoàn tất, hệ thống sẽ tự động sao chép trọng số vào `yolov8_traffic_vn.pt` và biểu đồ vào thư mục `metrics/`. Khi khởi chạy Backend (`python backend/main.py`), hệ thống sẽ tự động ưu tiên nhận diện bằng mô hình này.
