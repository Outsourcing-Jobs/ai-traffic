from typing import List, Tuple, Dict, Any, Optional
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import supervision as sv


class VehicleCounter:
    """Quản lý vạch đếm (LineZone) và vùng giám sát (PolygonZone)"""

    def __init__(
        self,
        line_start: Optional[Tuple[int, int]] = None,
        line_end: Optional[Tuple[int, int]] = None,
        roi_polygon: Optional[List[List[int]]] = None,
        frame_resolution_wh: Tuple[int, int] = (1280, 720)
    ):
        self.frame_resolution = frame_resolution_wh
        self.line_zone: Optional[sv.LineZone] = None
        self.line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)

        self.polygon_zone: Optional[sv.PolygonZone] = None
        self.polygon_annotator: Optional[sv.PolygonZoneAnnotator] = None

        # Cấu hình vạch đếm nếu có
        if line_start and line_end:
            self.set_counting_line(line_start, line_end)

        # Cấu hình vùng ROI nếu có
        if roi_polygon and len(roi_polygon) >= 3:
            self.set_roi_polygon(roi_polygon)

    def set_counting_line(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Cập nhật tọa độ vạch đếm"""
        self.line_zone = sv.LineZone(
            start=sv.Point(int(start[0]), int(start[1])),
            end=sv.Point(int(end[0]), int(end[1]))
        )

    def set_roi_polygon(self, polygon_points: List[List[int]]):
        """Cập nhật vùng đa giác ROI"""
        if len(polygon_points) >= 3:
            np_poly = np.array(polygon_points, dtype=np.int32)
            self.polygon_zone = sv.PolygonZone(
                polygon=np_poly,
                frame_resolution_wh=self.frame_resolution
            )
            self.polygon_annotator = sv.PolygonZoneAnnotator(
                zone=self.polygon_zone,
                thickness=2,
                text_thickness=1,
                text_scale=0.5
            )

    def process(self, detections: sv.Detections) -> Tuple[sv.Detections, List[Dict[str, Any]]]:
        """
        Kiểm tra phương tiện cắt qua vạch đếm hoặc trong ROI.
        Trả về (detections_in_roi, list các sự kiện qua vạch vừa diễn ra).
        """
        events = []

        # 1. Lọc theo ROI Polygon (nếu có cấu hình)
        filtered_detections = detections
        if self.polygon_zone is not None and len(detections) > 0:
            is_inside = self.polygon_zone.trigger(detections=detections)
            filtered_detections = detections[is_inside]

        # 2. Kiểm tra vạch đếm LineZone
        if self.line_zone is not None and len(filtered_detections) > 0 and filtered_detections.tracker_id is not None:
            crossed_in, crossed_out = self.line_zone.trigger(detections=filtered_detections)

            # Thu thập các xe vừa cắt qua hướng IN
            for i, crossed in enumerate(crossed_in):
                if crossed:
                    events.append({
                        "track_id": int(filtered_detections.tracker_id[i]),
                        "direction": "in",
                        "class_id": int(filtered_detections.class_id[i]) if filtered_detections.class_id is not None else None
                    })

            # Thu thập các xe vừa cắt qua hướng OUT
            for i, crossed in enumerate(crossed_out):
                if crossed:
                    events.append({
                        "track_id": int(filtered_detections.tracker_id[i]),
                        "direction": "out",
                        "class_id": int(filtered_detections.class_id[i]) if filtered_detections.class_id is not None else None
                    })

        return filtered_detections, events

    def get_counts(self) -> Dict[str, int]:
        """Lấy tổng số lượt xe vào / ra hiện tại"""
        if self.line_zone is None:
            return {"in": 0, "out": 0, "total": 0}
        return {
            "in": int(self.line_zone.in_count),
            "out": int(self.line_zone.out_count),
            "total": int(self.line_zone.in_count + self.line_zone.out_count)
        }

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        """Vẽ vạch đếm và vùng ROI lên frame"""
        annotated_frame = frame.copy()
        if self.polygon_zone is not None and self.polygon_annotator is not None:
            try:
                annotated_frame = self.polygon_annotator.annotate(scene=annotated_frame)
            except Exception:
                pass
        if self.line_zone is not None:
            annotated_frame = self.line_annotator.annotate(
                frame=annotated_frame,
                line_counter=self.line_zone
            )
        return annotated_frame
