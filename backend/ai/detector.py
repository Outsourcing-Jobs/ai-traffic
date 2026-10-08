from typing import Optional, List
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
# pyrefly: ignore [missing-import]  
import supervision as sv
from config import MODEL_PATH, DEFAULT_MODEL_NAME, TARGET_CLASSES, CLASS_NAMES_MAP


class VehicleDetector:
    """Wrapper cho mô hình YOLOv8 phát hiện phương tiện giao thông"""

    def __init__(self, model_name_or_path: Optional[str] = None, conf_threshold: float = 0.35):
        # Nếu không truyền path, thử dùng MODEL_PATH hoặc mặc định yolov8n.pt
        path = model_name_or_path or (str(MODEL_PATH) if MODEL_PATH.exists() else DEFAULT_MODEL_NAME)
        self.model = YOLO(path)
        self.conf_threshold = conf_threshold
        self.target_classes = set(TARGET_CLASSES)

    def detect(self, frame: np.ndarray) -> sv.Detections:
        """
        Dự đoán phương tiện trên 1 frame ảnh.
        Trả về sv.Detections chỉ chứa 4 lớp xe mục tiêu: car, motorcycle, bus, truck.
        """
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            verbose=False
        )[0]

        # Chuyển kết quả sang định dạng supervision
        detections = sv.Detections.from_ultralytics(results)

        # Lọc chỉ giữ các class mục tiêu giao thông
        if len(detections) > 0 and detections.class_id is not None:
            mask = np.isin(detections.class_id, list(self.target_classes))
            detections = detections[mask]

        return detections

    def get_class_name(self, class_id: int) -> str:
        """Lấy tên tiếng Anh của loại xe dựa theo class_id"""
        return CLASS_NAMES_MAP.get(int(class_id), "vehicle")
