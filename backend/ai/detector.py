# pyrefly: ignore [missing-import]
import cv2
from typing import Optional, List
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
# pyrefly: ignore [missing-import]  
import supervision as sv
from config import MODEL_PATH, DEFAULT_MODEL_NAME, TARGET_CLASSES, CLASS_NAMES_MAP


class VehicleDetector:
    """Wrapper cho mô hình YOLOv8 phát hiện phương tiện giao thông (Tối ưu hóa xe máy & phân loại chuẩn xác Bus/Car/Truck)"""

    def __init__(self, model_name_or_path: Optional[str] = None, conf_threshold: float = 0.18):
        path = model_name_or_path or (str(MODEL_PATH) if MODEL_PATH.exists() else DEFAULT_MODEL_NAME)
        self.model = YOLO(path)
        self.conf_threshold = conf_threshold
        self.target_classes = set(TARGET_CLASSES)
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    def _enhance_low_light(self, frame: np.ndarray) -> np.ndarray:
        """Tăng cường độ tương phản thích ứng khi trời tối hoặc video bị mờ/ngược sáng"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_lum = np.mean(gray)

        # Nếu độ sáng trung bình thấp (trời tối/ban đêm < 85) hoặc quá tối
        if mean_lum < 85:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_enhanced = self.clahe.apply(l)
            enhanced_lab = cv2.merge((l_enhanced, a, b))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return frame

    def detect(self, frame: np.ndarray) -> sv.Detections:
        """
        Dự đoán phương tiện trên 1 frame ảnh:
        - Tự động tăng cường chi tiết nếu trời tối/mờ
        - Tối ưu hóa phân định kích thước hình học giữa Bus và Car
        """
        proc_frame = self._enhance_low_light(frame)

        results = self.model.predict(
            source=proc_frame,
            conf=self.conf_threshold,
            imgsz=1280,
            verbose=False
        )[0]

        # Chuyển kết quả sang định dạng supervision
        detections = sv.Detections.from_ultralytics(results)

        # Lọc chỉ giữ các class mục tiêu giao thông
        if len(detections) > 0 and detections.class_id is not None:
            mask = np.isin(detections.class_id, list(self.target_classes))
            detections = detections[mask]

            if len(detections) > 0 and detections.class_id is not None:
                new_class_ids = detections.class_id.copy()
                boxes = detections.xyxy

                for idx in range(len(new_class_ids)):
                    cid = int(new_class_ids[idx])
                    box = boxes[idx]
                    w = abs(box[2] - box[0])
                    h = abs(box[3] - box[1])
                    area = w * h

                    # 1. Gộp class 1 (bicycle) về 3 (motorcycle)
                    if cid == 1:
                        new_class_ids[idx] = 3
                        continue

                    # 2. Xử lý nhầm lẫn Bus (5) / Truck (7) thành Car (2) và ngược lại khi trời tối
                    # Nếu model đoán là Bus (5) hoặc Truck (7) nhưng kích thước quá nhỏ -> Ô tô con (2)
                    if cid in (5, 7):
                        if area < 12000 or (w < 90 and h < 90):
                            new_class_ids[idx] = 2  # Chỉnh lại thành ô tô con (car)

                    # Nếu model đoán là Car (2) nhưng kích thước cực lớn (chiều dài hoặc chiều cao vượt trội) -> Bus (5)
                    elif cid == 2:
                        if area > 48000 and (w > 200 or h > 180):
                            new_class_ids[idx] = 5  # Chỉnh lại thành xe buýt/xe khách (bus)

                detections.class_id = new_class_ids

        return detections

    def get_class_name(self, class_id: int) -> str:
        """Lấy tên tiếng Anh của loại xe dựa theo class_id"""
        return CLASS_NAMES_MAP.get(int(class_id), "vehicle")

