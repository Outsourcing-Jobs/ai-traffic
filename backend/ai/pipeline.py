from typing import Dict, Any, List, Tuple, Optional
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import supervision as sv
from ai.detector import VehicleDetector
from ai.tracker import VehicleTracker
from ai.counter import VehicleCounter
from ai.speed import SpeedEstimator
from config import DEFAULT_SPEED_LIMIT


class TrafficPipeline:
    """Điều phối toàn bộ quá trình phát hiện, theo vết, đếm, đo tốc độ và giám sát vi phạm ITS"""

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.18,
        fps: float = 30.0,
        frame_wh: Tuple[int, int] = (1280, 720),
        speed_limit: float = DEFAULT_SPEED_LIMIT
    ):
        self.frame_wh = frame_wh
        self.fps = fps
        self.speed_limit = float(speed_limit)

        # Các module AI cốt lõi
        self.detector = VehicleDetector(model_name_or_path=model_path, conf_threshold=conf_threshold)
        self.tracker = VehicleTracker()
        self.counter = VehicleCounter(frame_resolution_wh=frame_wh)
        self.speed_estimator = SpeedEstimator(fps=fps)

        # Các bộ vẽ nhãn (Supervision Annotators)
        self.box_annotator = sv.BoxAnnotator(thickness=2)
        self.label_annotator = sv.LabelAnnotator(
            text_scale=0.5,
            text_thickness=1,
            text_padding=5,
            text_position=sv.Position.TOP_LEFT
        )
        self.trace_annotator = sv.TraceAnnotator(
            thickness=2,
            trace_length=20,
            position=sv.Position.BOTTOM_CENTER
        )

        # Cấu hình vạch đếm mặc định (ngang 60% chiều cao màn hình)
        line_y = int(frame_wh[1] * 0.6)
        self.counter.set_counting_line(
            (int(frame_wh[0] * 0.05), line_y),
            (int(frame_wh[0] * 0.95), line_y)
        )

        self.frame_count = 0

    def configure(self, config_dict: Dict[str, Any]):
        """Cập nhật cấu hình động (ROI polygon, counting line, homography, speed_limit)"""
        if not config_dict:
            return

        # 1. Cấu hình tốc độ giới hạn
        if "speed_limit" in config_dict:
            try:
                self.speed_limit = float(config_dict["speed_limit"])
            except (ValueError, TypeError):
                pass

        # 2. Cấu hình vạch đếm
        counting_lines = config_dict.get("counting_lines", [])
        if counting_lines and len(counting_lines) > 0:
            primary_line = counting_lines[0]
            p1 = primary_line.get("p1")
            p2 = primary_line.get("p2")
            if p1 and p2:
                self.counter.set_counting_line((p1[0], p1[1]), (p2[0], p2[1]))

        # 3. Cấu hình vùng ROI
        roi_polygon = config_dict.get("roi_polygon", [])
        if roi_polygon and len(roi_polygon) >= 3:
            self.counter.set_roi_polygon(roi_polygon)

        # 4. Cấu hình Homography 4 điểm cân chỉnh phối cảnh
        homography = config_dict.get("homography", {})
        if homography:
            pts = homography.get("points") or homography.get("source_pixels", [])
            width_m = homography.get("road_width_m", 10.0)
            length_m = homography.get("road_length_m", 25.0)
            if len(pts) == 4:
                self.speed_estimator.set_homography_quad(
                    source_pixels=pts,
                    road_width_m=width_m,
                    road_length_m=length_m
                )

    def process_frame(
        self, frame: np.ndarray
    ) -> Tuple[np.ndarray, sv.Detections, List[Dict[str, Any]]]:
        """
        Xử lý 1 frame video hoàn chỉnh:
        - Detect xe & theo vết (Tracking)
        - Đo tốc độ & bắt sự kiện cắt vạch
        - Vẽ annotations lên frame
        """
        self.frame_count += 1

        # 1. Phát hiện
        raw_detections = self.detector.detect(frame)

        # 2. Theo dõi (Tracking)
        tracked_detections = self.tracker.update(raw_detections)

        # 3. Đếm & Lọc ROI
        filtered_detections, crossing_events = self.counter.process(tracked_detections)

        # 4. Ước lượng tốc độ
        speeds = self.speed_estimator.update(filtered_detections, self.frame_count)

        # Bổ sung tốc độ và tên loại xe vào các sự kiện vượt vạch
        for event in crossing_events:
            tid = event.get("track_id")
            event["speed_kmh"] = float(speeds.get(tid, 0.0))
            cid = event.get("class_id")
            event["vehicle_type"] = self.detector.get_class_name(cid) if cid is not None else "vehicle"

        # 5. Gán nhãn hiển thị cho xe
        labels = []
        if len(filtered_detections) > 0 and filtered_detections.tracker_id is not None:
            for i, tid in enumerate(filtered_detections.tracker_id):
                tid = int(tid)
                class_id = int(filtered_detections.class_id[i]) if filtered_detections.class_id is not None else 2
                class_name = self.detector.get_class_name(class_id)
                speed = speeds.get(tid, 0.0)
                if speed > 0:
                    labels.append(f"#{tid} {class_name} {speed:.0f}km/h")
                else:
                    labels.append(f"#{tid} {class_name}")

        # 6. Vẽ chú thích (Annotation) lên frame
        annotated_frame = frame.copy()
        annotated_frame = self.counter.annotate(annotated_frame)

        if len(filtered_detections) > 0 and filtered_detections.tracker_id is not None:
            # Vẽ quỹ đạo
            annotated_frame = self.trace_annotator.annotate(
                scene=annotated_frame,
                detections=filtered_detections
            )

            # Vẽ bounding boxes
            annotated_frame = self.box_annotator.annotate(
                scene=annotated_frame,
                detections=filtered_detections
            )

            # Vẽ nhãn
            annotated_frame = self.label_annotator.annotate(
                scene=annotated_frame,
                detections=filtered_detections,
                labels=labels
            )

        return annotated_frame, filtered_detections, crossing_events

    def get_counts(self) -> Dict[str, int]:
        """Lấy số lượng xe vào / ra hiện tại"""
        return self.counter.get_counts()

    def on_video_loop(self):
        """Khi video lặp lại từ đầu trong chế độ demo liên tục:
        Reset tracker và lịch sử vết của các đối tượng cũ để các lượt xe mới được đếm tiếp,
        vẫn giữ nguyên tổng số đếm in / out tích luỹ.
        """
        self.tracker.reset()
        self.counter.reset()
        self.speed_estimator.position_history.clear()

    def reset(self):
        """Khởi động lại toàn bộ pipeline"""
        self.tracker.reset()
        self.counter.reset()
        self.counter.in_count = 0
        self.counter.out_count = 0
        self.speed_estimator.position_history.clear()
        self.speed_estimator.current_speeds.clear()
        self.speed_estimator.speed_samples.clear()
        self.frame_count = 0
