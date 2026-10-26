# TÀI LIỆU CHI TIẾT VỀ DỮ LIỆU & LOGIC HUẤN LUYỆN YOLOv8 (AI TRAFFIC)

> **Dự án:** Hệ thống xác định lưu lượng & ước lượng tốc độ phương tiện giao thông thông minh.  
> **Thư mục làm việc:** `d:\Jobs\ai-trafic`

---

## MỤC LỤC
1. [Nguồn Gốc Kho Dữ Liệu (Dataset Lấy Từ Đâu?)](#1-nguồn-gốc-kho-dữ-liệu-dataset-lấy-từ-đâu)
2. [Cấu Trúc Kho Ảnh & File Nhãn Trong Dự Án](#2-cấu-trúc-kho-ảnh--file-nhãn-trong-dự-án)
3. [Cách Thêm Kho Ảnh Mới Của Bạn Vào Hệ Thống](#3-cách-thêm-kho-ảnh-mới-của-bạn-vào-hệ-thống)
4. [Mô Tả Luồng Huấn Luyện Bằng Tiếng Việt (Không Kèm Code - Dành Cho Báo Cáo/Thuyết Minh)](#4-mô-tả-luồng-huấn-luyện-bằng-tiếng-việt-không-kèm-code---dành-cho-báo-cáothuyết-minh)
5. [Giải Thích Toàn Bộ Logic Huấn Luyện (Kèm Vị Trí Code Cụ Thể)](#5-giải-thích-toàn-bộ-logic-huấn-luyện-kèm-vị-trí-code-cụ-thể)
   - [Đoạn 1: Logic gom kho ảnh & tự động chia Train/Val (82/18)](#đoạn-1-logic-gom-kho-ảnh--tự-động-chia-trainval-8218)
   - [Đoạn 2: Logic sinh file cấu hình data.yaml](#đoạn-2-logic-sinh-file-cấu-hình-datayaml)
   - [Đoạn 3: Logic nạp weights nền tảng yolov8n.pt](#đoạn-3-logic-nạp-weights-nền-tảng-yolov8npt)
   - [Đoạn 4: Logic thực thi huấn luyện (Hyperparameters & Hàm mất mát)](#đoạn-4-logic-thực-thi-huấn-luyện-hyperparameters--hàm-mất-mát)
   - [Đoạn 5: Logic trích xuất Best Weights & Biểu đồ Nghiệm thu](#đoạn-5-logic-trích-xuất-best-weights--biểu-đồ-nghiệm-thu)
   - [Đoạn 6: Logic kiểm định mô hình (Validation mAP)](#đoạn-6-logic-kiểm-định-mô-hình-validation-map)
   - [Đoạn 7: Logic tự động nhận diện mô hình khi chạy Backend](#đoạn-7-logic-tự-động-nhận-diện-mô-hình-khi-chạy-backend)
6. [Hướng Dẫn Các Lệnh Thực Thi Hands-On](#6-hướng-dẫn-các-lệnh-thực-thi-hands-on)

---

## 1. Nguồn Gốc Kho Dữ Liệu (Dataset Lấy Từ Đâu?)

Bạn thắc mắc: **"Mô hình đọc dataset từ đâu để huấn luyện? Có kho ảnh sẵn không?"**

👉 **Câu trả lời là: ĐÚNG! Dự án đã có sẵn một kho ảnh hơn 900 ảnh thực tế.**

Cụ thể, dữ liệu huấn luyện được hình thành từ 3 nguồn:
1. **Kho ảnh thực nghiệm có sẵn:** Nằm trực tiếp trong thư mục:
   `d:\Jobs\ai-trafic\backend\data\dataset\images\` (hiện chứa hơn **906 file ảnh `.jpg`**)
   kèm nhãn tương ứng trong `d:\Jobs\ai-trafic\backend\data\dataset\labels\` (hơn **908 file nhãn `.txt`**).
2. **Trích xuất từ các video giao thông thực tế:** Được cắt tự động từ các video camera giao thông đặt tại Hà Nội (`hanoi_ngatu_v1.mp4`, `hanoi_vcc.mp4`, `vehicles.mp4` trong `backend/data/videos/`).
3. **Chụp trực tiếp từ camera / video stream:** Thông qua chức năng **"Chụp & Gán nhãn mẫu"** trên giao diện Web (API `POST /api/dataset/capture-live/{session_id}`).

---

## 2. Cấu Trúc Kho Ảnh & File Nhãn Trong Dự Án

Kho dữ liệu được lưu trữ chuẩn hóa theo định dạng của **Ultralytics YOLO**:

```
d:\Jobs\ai-trafic\backend\data\dataset\
│
├── data.yaml                         # File cầu nối: Chỉ đường cho YOLO biết tập train/val ở đâu
│
├── images/                           # KHO ẢNH (Gồm hơn 900 ảnh .jpg)
│   ├── batch_001_....jpg
│   ├── hanoi_ngatu_001.jpg
│   ├── traffic_001.jpg ... traffic_090.jpg
│   ├── traffic_2_001.jpg ... traffic_2_090.jpg
│   ├── traffic_3_001.jpg ... traffic_3_090.jpg
│   ├── traffic_4_001.jpg ... traffic_4_090.jpg
│   ├── traffic_5_001.jpg ... traffic_5_090.jpg
│   ├── traffic_6_001.jpg ... traffic_6_090.jpg
│   ├── traffic_7_001.jpg ... traffic_7_090.jpg
│   │
│   ├── train/                        # Tập huấn luyện (YOLO sẽ đọc ảnh từ đây khi train)
│   └── val/                          # Tập kiểm chứng (YOLO sẽ đọc ảnh từ đây để test)
│
└── labels/                           # KHO NHÃN TƯƠNG ỨNG (Mỗi file .jpg có 1 file .txt cùng tên)
    ├── batch_001_....txt
    ├── hanoi_ngatu_001.txt
    ├── traffic_001.txt ...
    │
    ├── train/                        # Nhãn cho tập huấn luyện
    └── val/                          # Nhãn cho tập kiểm chứng
```

### Định dạng bên trong mỗi file nhãn `.txt`:
Mỗi dòng đại diện cho 1 xe trong ảnh theo cú pháp chuẩn YOLO:
```text
<class_id> <x_center> <y_center> <width> <height>
```
*Các tọa độ được chuẩn hóa tỉ lệ từ `0.0` đến `1.0` so với chiều rộng và chiều cao ảnh.*  
- `0`: Xe ô tô con (`car`)
- `1`: Xe máy (`motorcycle`)
- `2`: Xe buýt, xe khách (`bus`)
- `3`: Xe tải (`truck`)

---

## 3. Cách Thêm Kho Ảnh Mới Của Bạn Vào Hệ Thống

Nếu bạn có thêm ảnh xe cộ mới tự chụp hoặc tải về:
1. **Bước 1:** Copy toàn bộ file ảnh (`.jpg` hoặc `.png`) ném vào thư mục:
   `d:\Jobs\ai-trafic\backend\data\dataset\images\`
2. **Bước 2:** Copy các file nhãn `.txt` tương ứng vào:
   `d:\Jobs\ai-trafic\backend\data\dataset\labels\`  
   *(Nếu chưa có nhãn, hệ thống có script tự động gán nhãn `batch_extract_dataset.py` bằng AI)*
3. **Bước 3:** Chạy lệnh phân chia lại tập train/val:
   ```powershell
   python backend/ai/prepare_vietnam_dataset.py
   ```
   *Script sẽ tự động quét toàn bộ kho ảnh (cũ + mới), trộn ngẫu nhiên và phân bổ lại 82% Train - 18% Val.*

---

## 4. Mô Tả Luồng Huấn Luyện Bằng Tiếng Việt (Không Kèm Code - Dành Cho Báo Cáo/Thuyết Minh)

Dưới đây là đoạn văn mô tả tự nhiên toàn bộ cách thức và luồng huấn luyện của hệ thống, phù hợp sử dụng cho các bài báo cáo, thuyết trình hoặc tài liệu nghiệm thu:

### 4.1. Mục tiêu và Bản chất
Trong đề tài này, hệ thống không huấn luyện mô hình AI từ con số 0 (vì phương pháp này đòi hỏi hàng triệu bức ảnh và siêu máy tính với chi phí rất lớn), mà áp dụng kỹ thuật **Học chuyển giao (Transfer Learning)**. 

Bản chất của kỹ thuật này là: Chúng ta kế thừa một mô hình YOLOv8 tiêu chuẩn đã được học sẵn các tri thức thị giác nền tảng (như khả năng nhận biết các đường nét cơ bản, hình khối tròn/vuông, góc cạnh, bánh xe, mặt đường). Sau đó, mô hình được "dạy chuyên sâu" và tinh chỉnh lại trên bộ dữ liệu ảnh giao thông thực tế tại Việt Nam để tối ưu hóa việc phân loại chính xác **4 nhóm phương tiện giao thông trọng tâm**: *Ô tô con, Xe máy, Xe buýt/khách và Xe tải*.

### 4.2. Luồng hoạt động (Workflow) từ đầu đến cuối:

1. **Chuẩn bị và số hóa kho dữ liệu hình ảnh:**  
   Các đoạn video thực tế thu thập từ camera giám sát giao thông (tại các tuyến đường, nút giao cắt có mật độ xe dày đặc) được đưa vào hệ thống. Thuật toán sẽ tự động trích xuất các khung hình cách đều nhau để thu được một kho ảnh đa dạng về góc nhìn và thời điểm. Trên mỗi khung hình, từng phương tiện giao thông được bao quanh bởi một khung định vị và gán nhãn đúng với loại xe thực tế.

2. **Phân chia dữ liệu khách quan (Train và Validation):**  
   Toàn bộ kho ảnh được xáo trộn ngẫu nhiên và phân thành hai phần tách biệt:
   - **Tập huấn luyện (khoảng 82%):** Đóng vai trò là "sách giáo khoa" cung cấp mẫu để mô hình quan sát, so sánh và học hỏi các đặc điểm nhận dạng của từng dòng xe.
   - **Tập kiểm chứng (khoảng 18%):** Đóng vai trò như "đề thi thử". Tập này được giữ bí mật, mô hình không được tiếp cận trong lúc học mà chỉ được đưa ra ở cuối mỗi vòng để chấm điểm xem mô hình hiểu bài chuẩn xác đến đâu.

3. **Quá trình mô hình tự học và tự điều chỉnh qua các vòng lặp (Epochs):**  
   Quá trình huấn luyện diễn ra qua 12 vòng lặp liên tục:
   - Ở mỗi lượt, một nhóm nhỏ các bức ảnh được đưa qua mạng nơ-ron để mô hình phán đoán vị trí và loại xe.
   - Hệ thống ngay lập tức so sánh phán đoán đó với nhãn thực tế để tính ra mức độ sai lệch (sai lệch về vị trí khung bao và sai lệch về phân loại tên xe).
   - Dựa trên mức độ sai lệch này, thuật toán tối ưu sẽ tự động tính toán ngược và điều chỉnh lại các kết nối nơ-ron bên trong mô hình để giảm thiểu sai số cho các lượt ảnh tiếp theo.
   - Hết mỗi vòng lặp, hệ thống lại mang "bộ đề thi thử" ra chấm điểm. Bản mô hình nào đạt độ chính xác cao nhất từ đầu tới giờ sẽ được tự động ghi đè và lưu lại thành "phiên bản tốt nhất".

4. **Đóng gói sản phẩm và xuất kết quả nghiệm thu:**  
   Sau khi hoàn thành các vòng lặp, hệ thống tự động trích xuất tệp trọng số tối ưu nhất đưa vào thư mục mô hình chính thức. Đồng thời, hệ thống tự động vẽ và xuất ra một bộ biểu đồ đánh giá khoa học (như biểu đồ suy giảm sai số, biểu đồ độ chính xác theo độ phủ, ma trận nhầm lẫn đo tỉ lệ nhận diện đúng của từng loại xe). Các biểu đồ này đóng vai trò là bằng chứng thực nghiệm rõ ràng nhất để đưa vào báo cáo nghiệm thu.

5. **Đưa vào giám sát thực tế:**  
   Khi máy chủ Backend được khởi động, hệ thống sẽ tự động phát hiện mô hình tinh chỉnh này và nạp ngay vào bộ xử lý video. Tại đây, mô hình kết hợp cùng thuật toán lọc sáng ban đêm và thuật toán bám vết phương tiện để thực hiện đồng thời các nhiệm vụ: nhận diện từng loại xe, đếm lưu lượng xe chạy qua vạch ảo và ước lượng tốc độ trung bình theo thời gian thực.

---

## 5. Giải Thích Toàn Bộ Logic Huấn Luyện (Kèm Vị Trí Code Cụ Thể)

Dưới đây là chi tiết mã nguồn xử lý từng bước của quá trình huấn luyện:

---

### Đoạn 1: Logic gom kho ảnh & tự động chia Train/Val (82/18)
- **Vị trí file:** [backend/ai/prepare_vietnam_dataset.py](file:///d:/Jobs/ai-trafic/backend/ai/prepare_vietnam_dataset.py#L107-L146)
- **Đoạn code thực thi:**
  ```python
  def organize_train_val_split(val_ratio: float = 0.18):
      # Tạo sẵn các thư mục train và val
      train_img_dir = IMAGES_DIR / "train"
      val_img_dir = IMAGES_DIR / "val"
      train_lbl_dir = LABELS_DIR / "train"
      val_lbl_dir = LABELS_DIR / "val"

      # 1. Quét TOÀN BỘ file ảnh trong kho images/
      all_imgs = [p for p in IMAGES_DIR.glob("*.jpg") if p.is_file()]
      
      # 2. Cố định seed 42 để mỗi lần chia tập đều cho kết quả nhất quán
      random.seed(42)
      random.shuffle(all_imgs)

      # 3. Tính toán số lượng: 18% làm tập Val, 82% còn lại làm tập Train
      val_count = max(1, int(len(all_imgs) * val_ratio))
      val_imgs = set(all_imgs[:val_count])
      train_imgs = set(all_imgs[val_count:])

      # 4. Sao chép từng cặp (ảnh .jpg + nhãn .txt) vào đúng thư mục con
      for p in train_imgs:
          copy_pair(p, train_img_dir, train_lbl_dir)
      for p in val_imgs:
          copy_pair(p, val_img_dir, val_lbl_dir)
  ```
- **Ý nghĩa logic:**
  Thuật toán tự động tìm thấy toàn bộ 906 ảnh trong kho `images/`. Sau đó trích **163 ảnh làm tập kiểm chứng (Val)** và **743 ảnh làm tập huấn luyện (Train)**, đảm bảo file nhãn `.txt` luôn đi kèm với ảnh.

---

### Đoạn 2: Logic sinh file cấu hình `data.yaml`
- **Vị trí file:** [backend/ai/prepare_vietnam_dataset.py](file:///d:/Jobs/ai-trafic/backend/ai/prepare_vietnam_dataset.py#L148-L161)
- **Đoạn code thực thi:**
  ```python
  data_yaml = {
      "path": str(DATASET_DIR.resolve()).replace("\\", "/"),
      "train": "images/train",
      "val": "images/val",
      "nc": 4,
      "names": {0: "car", 1: "motorcycle", 2: "bus", 3: "truck"}
  }
  with open(yaml_path, "w", encoding="utf-8") as f:
      yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)
  ```
- **Ý nghĩa logic:**
  YOLOv8 bắt buộc phải có 1 file manifest định dạng YAML để biết:
  - Thư mục gốc dataset nằm ở đâu (`path`).
  - Thư mục ảnh huấn luyện nằm ở đâu (`images/train`).
  - Thư mục ảnh kiểm chứng nằm ở đâu (`images/val`).
  - Có bao nhiêu lớp xe (`nc: 4`) và tên từng lớp (`car`, `motorcycle`, `bus`, `truck`).

---

### Đoạn 3: Logic nạp weights nền tảng `yolov8n.pt`
- **Vị trí file:** [backend/ai/train_yolo.py](file:///d:/Jobs/ai-trafic/backend/ai/train_yolo.py#L33-L36)
- **Đoạn code thực thi:**
  ```python
  # 1. Khởi tạo mô hình nền tảng YOLOv8n pretrained
  base_model_path = BACKEND_DIR / "yolov8n.pt"
  model = YOLO(str(base_model_path) if base_model_path.exists() else "yolov8n.pt")
  ```
- **Ý nghĩa logic:**
  Thay vì huấn luyện từ số 0 (train from scratch) mất hàng tuần và cần hàng triệu ảnh, chương trình nạp mô hình `yolov8n.pt` đã được học sẵn khả năng nhận biết hình khối cơ bản (bánh xe, kính xe, đèn xe, mặt đường...). Việc này gọi là **Transfer Learning**.

---

### Đoạn 4: Logic thực thi huấn luyện (Hyperparameters & Hàm mất mát)
- **Vị trí file:** [backend/ai/train_yolo.py](file:///d:/Jobs/ai-trafic/backend/ai/train_yolo.py#L44-L60)
- **Đoạn code thực thi:**
  ```python
  results = model.train(
      data=str(DATA_YAML).replace("\\", "/"),
      epochs=12,              # 12 epochs tối ưu cho CPU, học nhanh hội tụ các class xe
      imgsz=416,              # Kích thước 416 vừa chuẩn vừa nhanh
      batch=8,                # Batch size 8 ảnh mỗi bước cập nhật trọng số
      device="cpu",           # Huấn luyện trên CPU (hoặc đổi '0' nếu có card rời NVIDIA)
      project=str(runs_dir).replace("\\", "/"),
      name="traffic_vn",
      plots=True,             # Tự động xuất biểu đồ huấn luyện Loss, mAP, Confusion Matrix
      verbose=True,
      workers=2,
      optimizer="AdamW",      # Thuật toán tối ưu trọng số AdamW
      lr0=0.001,              # Tốc độ học ban đầu
      patience=5              # Nếu sau 5 epoch liên tiếp mà loss không giảm thì dừng sớm
  )
  ```
- **Ý nghĩa logic sâu bên trong:**
  1. **Batching:** Cứ mỗi lượt, 8 bức ảnh kèm nhãn từ thư mục `images/train/` được đưa qua mạng nơ-ron.
  2. **Feed Forward & Loss Calculation:** Mô hình đưa ra dự đoán và so sánh với nhãn thật thông qua 3 hàm mất mát:
     - `box_loss` (CIoU): Đo mức độ trùng khớp của khung bao quanh xe.
     - `cls_loss` (BCE): Đo mức độ đoán đúng loại xe (Car, Bus, Motorcycle, Truck).
     - `dfl_loss`: Tinh chỉnh ranh giới biên khi xe máy đi san sát nhau.
  3. **Backpropagation:** Thuật toán tối ưu `AdamW` tính đạo hàm gradient và cập nhật trọng số mạng nơ-ron theo tốc độ học `lr0 = 0.001`.
  4. **Validation Check:** Hết 1 epoch, mô hình tự động chấm điểm trên 163 ảnh của tập `images/val/`. Nếu điểm số cao nhất từ trước đến nay, Ultralytics sẽ ghi đè file `weights/best.pt`.

---

### Đoạn 5: Logic trích xuất Best Weights & Biểu đồ Nghiệm thu
- **Vị trí file:** [backend/ai/train_yolo.py](file:///d:/Jobs/ai-trafic/backend/ai/train_yolo.py#L66-L103)
- **Đoạn code thực thi:**
  ```python
  train_output_dir = runs_dir / "traffic_vn"
  best_weights_src = train_output_dir / "weights" / "best.pt"
  target_model_file = MODELS_DIR / "yolov8_traffic_vn.pt"

  # Sao chép file trọng số tốt nhất vào models/
  if best_weights_src.exists():
      shutil.copy2(best_weights_src, target_model_file)
      print(f"🎯 Đã lưu trọng số Fine-tuned: {target_model_file}")

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
  for c_name in chart_names:
      c_src = train_output_dir / c_name
      if c_src.exists():
          shutil.copy2(c_src, METRICS_DIR / c_name)
  ```
- **Ý nghĩa logic:**
  Sau khi hoàn tất 12 epochs:
  - File weights tốt nhất được tự động sao chép ra `backend/data/models/yolov8_traffic_vn.pt` để sẵn sàng cho Backend dùng.
  - 7 biểu đồ minh chứng khoa học (`confusion_matrix`, `PR_curve`, `results.png`...) được gom về thư mục `backend/data/models/metrics/` để bạn chỉ việc copy vào Word/Slide báo cáo đề tài.

---

### Đoạn 6: Logic kiểm định mô hình (Validation mAP)
- **Vị trí file:** [backend/ai/train_yolo.py](file:///d:/Jobs/ai-trafic/backend/ai/train_yolo.py#L105-L113)
- **Đoạn code thực thi:**
  ```python
  val_metrics = model.val()
  print(f"   - mAP@0.5      : {val_metrics.box.map50 * 100:.2f}%")
  print(f"   - mAP@0.5:0.95 : {val_metrics.box.map * 100:.2f}%")
  print(f"   - Precision    : {val_metrics.box.mp * 100:.2f}%")
  print(f"   - Recall       : {val_metrics.box.mr * 100:.2f}%")
  ```
- **Ý nghĩa logic:**
  Mô hình chạy lại 1 lần trên toàn bộ tập ảnh kiểm chứng để xuất ra các con số phần trăm định lượng chính xác:
  - `mAP@0.5`: Độ chính xác phát hiện xe ở ngưỡng chồng lấn 50%.
  - `Precision`: Tỉ lệ xe nhận diện được là đúng thực tế.
  - `Recall`: Tỉ lệ không bỏ sót xe đi qua đường.

---

### Đoạn 7: Logic tự động nhận diện mô hình khi chạy Backend
- **Vị trí file:** [backend/config.py](file:///d:/Jobs/ai-trafic/backend/config.py#L45-L60) và [backend/ai/detector.py](file:///d:/Jobs/ai-trafic/backend/ai/detector.py#L17-L21)
- **Đoạn code trong `config.py`:**
  ```python
  VN_MODEL_NAME = "yolov8_traffic_vn.pt"
  VN_MODEL_PATH = MODELS_DIR / VN_MODEL_NAME

  if VN_MODEL_PATH.exists():
      MODEL_PATH = VN_MODEL_PATH
      ACTIVE_MODEL_NAME = VN_MODEL_NAME
      IS_FINE_TUNED = True
      TARGET_CLASSES = [0, 1, 2, 3] # Car, Motorcycle, Bus, Truck
      CLASS_NAMES_MAP = {0: "car", 1: "motorcycle", 2: "bus", 3: "truck"}
  else:
      # Nếu chưa train, fallback về mô hình COCO 80 lớp
      MODEL_PATH = BACKEND_DIR / "yolov8n.pt"
      TARGET_CLASSES = [1, 2, 3, 5, 7]
  ```
- **Ý nghĩa logic:**
  Khi bạn gõ lệnh chạy server `python backend/main.py`:
  - Hệ thống tự động kiểm tra xem file `yolov8_traffic_vn.pt` đã được tạo ra ở Bước 5 hay chưa.
  - Nếu đã có, hệ thống lập tức chuyển sang chế độ **Fine-tuned 4 class xe Việt Nam** mà bạn **không cần phải sửa thủ công bất kỳ dòng code nào**!

---

## 6. Hướng Dẫn Các Lệnh Thực Thi Hands-On

Tất cả chỉ gói gọn trong 3 lệnh terminal:

```powershell
# 1. Kích hoạt môi trường Python
cd d:\Jobs\ai-trafic
.venv\Scripts\activate

# 2. Quét kho ảnh, chia tập 82% Train / 18% Val và sinh data.yaml
python backend/ai/prepare_vietnam_dataset.py

# 3. Tiến hành huấn luyện mô hình YOLOv8 trên kho dữ liệu đó
python backend/ai/train_yolo.py
```

Sau khi train xong, bạn khởi động backend:
```powershell
python backend/main.py
```
Backend sẽ tự động in dòng thông báo:
```text
🎯 Sử dụng mô hình AI: yolov8_traffic_vn.pt (Fine-tuned trên xe Việt Nam - 4 Classes)
```
Toàn bộ luồng phát hiện lưu lượng và ước lượng tốc độ phương tiện sẽ hoạt động với độ chính xác tối ưu nhất trên dữ liệu giao thông thực tế.
