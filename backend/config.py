import os
from pathlib import Path

# Thư mục backend và thư mục gốc
BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent

# Đường dẫn dữ liệu (Tất cả data được đóng gói trong backend/data để độc lập khi deploy)
DATA_DIR = BACKEND_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
MODELS_DIR = DATA_DIR / "models"
VIOLATIONS_DIR = DATA_DIR / "violations"
DB_PATH = BACKEND_DIR / "traffic.db"

# Đảm bảo các thư mục tồn tại
DATA_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
VIOLATIONS_DIR.mkdir(parents=True, exist_ok=True)

# Tốc độ giới hạn mặc định (km/h)
DEFAULT_SPEED_LIMIT = 50.0


# Tự động nạp file .env nếu có (nạp trước để các biến môi trường có hiệu lực)
ENV_PATH = BACKEND_DIR / ".env"
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

# Cấu hình CSDL (Mặc định SQLite nếu không khai báo DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


# Cấu hình Model AI (Ưu tiên mô hình đã qua Fine-tuning trên xe Việt Nam)
VN_MODEL_NAME = "yolov8_traffic_vn.pt"
VN_MODEL_PATH = MODELS_DIR / VN_MODEL_NAME
DEFAULT_MODEL_NAME = "yolov8n.pt"
BACKEND_MODEL = BACKEND_DIR / DEFAULT_MODEL_NAME

if VN_MODEL_PATH.exists():
    MODEL_PATH = VN_MODEL_PATH
    ACTIVE_MODEL_NAME = VN_MODEL_NAME
    IS_FINE_TUNED = True
    TARGET_CLASSES = [0, 1, 2, 3]
    CLASS_NAMES_MAP = {
        0: "car",
        1: "motorcycle",
        2: "bus",
        3: "truck"
    }
else:
    MODEL_PATH = BACKEND_MODEL if BACKEND_MODEL.exists() else (MODELS_DIR / DEFAULT_MODEL_NAME)
    ACTIVE_MODEL_NAME = DEFAULT_MODEL_NAME
    IS_FINE_TUNED = False
    # Lớp COCO đối tượng giao thông cần theo dõi
    # 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
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

# Cấu hình Cloudinary (Tải ảnh lên Cloud lưu trữ)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "ai_traffic_dataset")

