# 🚗 Hệ Thống Giám Sát Lưu Lượng & Ước Lượng Tốc Độ Phương Tiện Giao Thông (AI Traffic Monitoring)

> **Đồ án tốt nghiệp CNTT - Trường ĐHCN Việt - Hung**  
> **GVHD:** TS. Nguyễn Hồng Quân  
> **Công nghệ:** YOLOv8 + ByteTrack + Homography Transformation + FastAPI + React (Vite) + SQLite + Docker

---

## 🌟 Tính Năng Chính
1. **Thị giác máy tính AI:** Tự động phát hiện 4 nhóm phương tiện (Ô tô con, Xe máy, Xe buýt, Xe tải) với độ trễ thấp theo thời gian thực.
2. **Theo dõi đa đối tượng (MOT):** Gán Track ID duy nhất và vẽ vệt quỹ đạo di chuyển qua các khung hình liên tiếp.
3. **Đếm xe 2 chiều & Vùng ROI:** Thiết lập Vạch đếm (LineZone IN/OUT) và Vùng quan sát (PolygonZone) trực tiếp trên Web.
4. **Ước lượng vận tốc Homography:** Biến đổi 4 điểm phối cảnh từ Pixel sang hệ Mét thực tế, ước lượng vận tốc tức thời và vận tốc trung bình (km/h) kèm bộ lọc làm mượt chống rung lắc camera.
5. **Giao diện Web Giám Sát (Light Theme):** Trực quan hóa luồng video MJPEG, đồ thị Chart.js và bảng sự kiện thời gian thực (GMT+7).
6. **Thu thập & Tự động gán nhãn Dataset:** Tự động nén ảnh và đẩy lên Cloudinary CDN, sinh nhãn chuẩn YOLO format lưu vào CSDL.

---

## 🚀 Hướng Dẫn Chạy Bằng Docker (Khuyến nghị trên mọi máy)

Hệ thống đã được đóng gói Docker hoàn chỉnh, độc lập 100% với môi trường máy chủ (không lo thiếu thư viện, không dính cache).

### 1. Yêu cầu tiên quyết
* Cài đặt **Docker Desktop** (trên Windows / macOS) hoặc **Docker Engine & Docker Compose** (trên Linux).

### 2. Khởi chạy 1 lệnh duy nhất
Tại thư mục gốc của dự án:
```bash
docker compose up -d --build
```

### 3. Truy cập ứng dụng
* **Giao diện người dùng Web:** [http://localhost:5173](http://localhost:5173)
* **Tài liệu API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Kiểm tra trạng thái (Health Check):** [http://localhost:8000/health](http://localhost:8000/health)

### 4. Dừng hệ thống
```bash
docker compose down
```

---

## 🛠️ Hướng Dẫn Chạy Thủ Công (Không dùng Docker)

### 1. Chạy Backend (FastAPI)
```bash
# Di chuyển vào thư mục backend
cd backend

# Tạo và kích hoạt môi trường ảo Python
python -m venv .venv
source .venv/bin/activate  # Trên Linux/macOS
# hoặc: .venv\Scripts\activate  # Trên Windows

# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy server
python main.py
```
Backend sẽ chạy tại: `http://localhost:8000`

### 2. Chạy Frontend (React Vite)
```bash
# Mở một terminal mới và vào thư mục frontend
cd frontend

# Cài đặt gói npm
npm install

# Khởi chạy server phát triển
npm run dev
```
Frontend sẽ chạy tại: `http://localhost:5173`

---

## 📁 Cấu Trúc Thư Mục Dự Án
```text
ai-traffic/
├── backend/
│   ├── ai/                  # Module AI: detector, tracker, counter, speed, pipeline, cloudinary
│   ├── api/                 # REST Endpoints: sessions, stats, stream, videos, dataset
│   ├── database/            # SQLite models, schemas, database engine
│   ├── config.py            # Cấu hình tham số hệ thống
│   ├── main.py              # Entrypoint FastAPI
│   └── Dockerfile           # Docker image cho Backend
├── frontend/
│   ├── src/                 # Giao diện React: pages, components, services
│   ├── nginx.conf           # Cấu hình reverse proxy Nginx cho Docker
│   └── Dockerfile           # Dockerfile multi-stage cho Frontend
├── data/                    # Thư mục dữ liệu: dataset, models, videos
├── docker-compose.yml       # File điều phối Docker 2 container
├── .dockerignore            # Loại bỏ file thừa khi build Docker
├── .gitignore               # Loại bỏ file nặng/bí mật khỏi Git
└── README.md                # Tài liệu hướng dẫn
```
