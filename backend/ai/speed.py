from typing import List, Tuple, Dict, Optional
from collections import defaultdict, deque
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np


class SpeedEstimator:
    """
    Ước lượng vận tốc phương tiện (km/h) sử dụng biến đổi Homography.
    Chuyển đổi phối cảnh từ mặt phẳng ảnh camera (pixel) sang mặt đất thực tế (mét).
    """

    def __init__(
        self,
        source_points: Optional[List[List[float]]] = None,
        target_points_meters: Optional[List[List[float]]] = None,
        fps: float = 30.0,
        history_len: int = 12
    ):
        self.fps = fps
        self.history_len = history_len
        self.homography_matrix: Optional[np.ndarray] = None
        self.source_pixels: Optional[List[List[float]]] = None
        self.road_width_m: float = 10.0
        self.road_length_m: float = 25.0

        # Lịch sử vị trí thực tế của xe: {track_id: [(frame, X_meter, Y_meter)]}
        self.position_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=self.history_len))
        
        # Vận tốc tức thời và vận tốc tích lũy
        self.current_speeds: Dict[int, float] = {}
        self.speed_samples: Dict[int, List[float]] = defaultdict(list)

        if source_points and len(source_points) == 4:
            if target_points_meters and len(target_points_meters) == 4:
                self.set_homography(source_points, target_points_meters)
            else:
                self.set_homography_quad(source_points)

    def set_homography(self, source_pixels: List[List[float]], target_meters: List[List[float]]):
        """Thiết lập ma trận Homography tổng quát từ 4 điểm pixel sang 4 điểm mét"""
        self.source_pixels = source_pixels
        src = np.array(source_pixels, dtype=np.float32)
        dst = np.array(target_meters, dtype=np.float32)
        self.homography_matrix = cv2.getPerspectiveTransform(src, dst)

    def set_homography_quad(
        self,
        source_pixels: List[List[float]],
        road_width_m: float = 10.0,
        road_length_m: float = 25.0
    ):
        """
        Cân chỉnh ma trận Homography từ 4 điểm phối cảnh trên mặt đường:
        P1: Top-Left (Xa - Trái)      -> (0, 0)
        P2: Top-Right (Xa - Phải)     -> (W, 0)
        P3: Bottom-Right (Gần - Phải) -> (W, L)
        P4: Bottom-Left (Gần - Trái)  -> (0, L)
        """
        self.source_pixels = source_pixels
        self.road_width_m = float(road_width_m)
        self.road_length_m = float(road_length_m)

        target_meters = [
            [0.0, 0.0],
            [self.road_width_m, 0.0],
            [self.road_width_m, self.road_length_m],
            [0.0, self.road_length_m]
        ]
        self.set_homography(source_pixels, target_meters)

    def _transform_point(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Chuyển đổi tọa độ 1 điểm pixel sang tọa độ mét thực tế trên mặt đường"""
        if self.homography_matrix is None:
            return None
        px = np.array([[[point[0], point[1]]]], dtype=np.float32)
        dst = cv2.perspectiveTransform(px, self.homography_matrix)
        return float(dst[0][0][0]), float(dst[0][0][1])

    def update(self, detections, frame_number: int) -> Dict[int, float]:
        """
        Cập nhật vị trí và tính toán vận tốc xe (km/h) dựa trên Homography.
        Lọc rung lắc camera và che khuất bằng trung bình di động.
        """
        if len(detections) == 0 or detections.tracker_id is None:
            return self.current_speeds

        for i, track_id in enumerate(detections.tracker_id):
            track_id = int(track_id)
            bbox = detections.xyxy[i]
            
            # Lấy điểm đáy giữa (bottom-center) tiếp xúc mặt đất của xe
            bottom_center = ((bbox[0] + bbox[2]) / 2.0, float(bbox[3]))

            # Chuyển đổi sang hệ mét
            if self.homography_matrix is not None:
                real_pos = self._transform_point(bottom_center)
            else:
                # Ước lượng mặc định nếu chưa cấu hình ma trận
                real_pos = (bottom_center[0] * 0.03, bottom_center[1] * 0.03)

            if real_pos is None:
                continue

            self.position_history[track_id].append((frame_number, real_pos[0], real_pos[1]))

            # Cần tối thiểu 4 frame liên tiếp để đo khoảng cách và triệt tiêu rung lắc
            history = self.position_history[track_id]
            if len(history) >= 4:
                start_frame, x_start, y_start = history[0]
                end_frame, x_end, y_end = history[-1]

                delta_frames = end_frame - start_frame
                if delta_frames > 0:
                    time_sec = delta_frames / self.fps
                    # Khoảng cách Euclide trên mặt đường thực tế (mét)
                    distance_m = np.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)
                    
                    # Vận tốc: v = (d / t) * 3.6 (km/h)
                    speed_kmh = (distance_m / time_sec) * 3.6

                    # Lọc nhiễu: Loại bỏ sai số bất thường ngoài khoảng 5 - 130 km/h
                    if 5.0 <= speed_kmh <= 130.0:
                        self.speed_samples[track_id].append(speed_kmh)
                        # Làm mịn trung bình di động (Moving Average)
                        if track_id in self.current_speeds:
                            self.current_speeds[track_id] = round(0.65 * self.current_speeds[track_id] + 0.35 * speed_kmh, 1)
                        else:
                            self.current_speeds[track_id] = round(speed_kmh, 1)

        return self.current_speeds

    def get_speed(self, track_id: int) -> Optional[float]:
        """Lấy vận tốc tức thời của xe"""
        return self.current_speeds.get(track_id)

    def get_average_speed(self, track_id: int) -> Optional[float]:
        """Lấy vận tốc trung bình của xe trong suốt quãng đường quan sát"""
        samples = self.speed_samples.get(track_id, [])
        if not samples:
            return self.current_speeds.get(track_id)
        return round(float(sum(samples) / len(samples)), 1)
