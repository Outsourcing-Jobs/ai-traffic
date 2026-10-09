# ========================================================
# Dockerfile cho Backend AI Traffic Monitoring
# ========================================================
FROM python:3.10-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Cài đặt các thư viện hệ thống cho OpenCV, video codecs và network
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt PyTorch CPU-only trước để tối ưu dung lượng (chỉ ~180MB thay vì 4GB CUDA)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Cài đặt các dependencies từ requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Tạo sẵn cấu trúc thư mục dữ liệu
RUN mkdir -p /app/data/models /app/data/videos /app/data/dataset/images /app/data/dataset/labels

# Tải trước mô hình YOLOv8n để container khởi động chạy ngay mà không cần internet tải lại
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && \
    cp yolov8n.pt /app/data/models/yolov8n.pt 2>/dev/null || true

# Copy mã nguồn backend và data
COPY backend/ /app/backend/
COPY data/ /app/data/

WORKDIR /app/backend

# Expose cổng FastAPI
EXPOSE 8000

# Chạy server FastAPI qua uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
