import os
from pathlib import Path

# Thư mục gốc dự án (d:/Jobs/ai-trafic)
BASE_DIR = Path(__file__).resolve().parent.parent

# Đường dẫn dữ liệu
DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
MODELS_DIR = DATA_DIR / "models"
VIOLATIONS_DIR = DATA_DIR / "violations"
DB_PATH = BASE_DIR / "backend" / "traffic.db"

# Đảm bảo các thư mục tồn tại
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
VIOLATIONS_DIR.mkdir(parents=True, exist_ok=True)

# Tốc độ giới hạn mặc định (km/h)
DEFAULT_SPEED_LIMIT = 50.0


# Cấu hình CSDL SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")


# Cấu hình Model AI
DEFAULT_MODEL_NAME = "yolov8n.pt"
BACKEND_MODEL = BASE_DIR / "backend" / DEFAULT_MODEL_NAME
MODEL_PATH = BACKEND_MODEL if BACKEND_MODEL.exists() else (MODELS_DIR / DEFAULT_MODEL_NAME)

# Lớp COCO đối tượng giao thông cần theo dõi
# 1: bicycle (xe 2 bánh/xe đạp), 2: car, 3: motorcycle, 5: bus, 7: truck
TARGET_CLASSES = [1, 2, 3, 5, 7]
CLASS_NAMES_MAP = {
    1: "motorcycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Cấu hình Stream Video
STREAM_FRAME_WIDTH = 1280
STREAM_FRAME_HEIGHT = 720
JPEG_QUALITY = 65  # Tối ưu hóa kích thước frame khi stream qua mạng

# Cấu hình Dataset (Ảnh & Nhãn phục vụ Nghiệm thu & Fine-tuning)
DATASET_DIR = DATA_DIR / "dataset"
DATASET_IMAGES_DIR = DATASET_DIR / "images"
DATASET_LABELS_DIR = DATASET_DIR / "labels"

DATASET_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATASET_LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Ánh xạ từ COCO ID (2: car, 3: motor, 5: bus, 7: truck) sang Dataset ID (0, 1, 2, 3)
DATASET_CLASS_MAP = {
    2: 0,  # car
    3: 1,  # motorcycle
    5: 2,  # bus
    7: 3   # truck
}
DATASET_CLASS_NAMES = ["car", "motorcycle", "bus", "truck"]

# Tự động nạp file .env nếu có
ENV_PATH = BASE_DIR / "backend" / ".env"
if ENV_PATH.exists():
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ[_k.strip()] = _v.strip().strip("'\"")
    except Exception:
        pass

# Cấu hình Cloudinary (Tải ảnh lên Cloud lưu trữ)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "ai_traffic_dataset")

