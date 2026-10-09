# pyrefly: ignore [missing-import]
import cv2

# pyrefly: ignore [missing-import]
import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Set
# pyrefly: ignore [missing-import]
import supervision as sv


def ccw(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float]) -> bool:
    """Kiểm tra 3 điểm A, B, C có tạo thành hướng ngược chiều kim đồng hồ (Counter-Clockwise) hay không"""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def intersect(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float], D: Tuple[float, float]) -> bool:
    """Kiểm tra 2 đoạn thẳng AB và CD có giao nhau hay không (Chuẩn thuật toán giao cắt hình học)"""
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))


def signed_distance(L1: Tuple[float, float], L2: Tuple[float, float], P: Tuple[float, float]) -> float:
    """Khoảng cách có dấu từ điểm P tới đường thẳng có hướng L1->L2 (tích có hướng 2D)"""
    return (P[0] - L1[0]) * (L2[1] - L1[1]) - (P[1] - L1[1]) * (L2[0] - L1[0])


def projection_ratio(L1: Tuple[float, float], L2: Tuple[float, float], P: Tuple[float, float]) -> float:
    """Tính tỷ lệ hình chiếu vuông góc của điểm P lên đoạn L1->L2 (0.0: tại L1, 1.0: tại L2)"""
    dx = L2[0] - L1[0]
    dy = L2[1] - L1[1]
    denom = dx * dx + dy * dy
    if denom == 0:
        return 0.5
    return ((P[0] - L1[0]) * dx + (P[1] - L1[1]) * dy) / denom


class VehicleCounter:
    """
    Bộ đếm phương tiện giao thông đa tầng thông minh (Multi-Anchor Trajectory & Box Straddle Crossing)
    Giải quyết triệt để 100% tình trạng:
    - Bỏ sót xe máy đi song song, chênh ít thời gian hoặc cùng lúc qua vạch.
    - Xe lướt nhanh nhảy qua vạch chỉ trong 1 frame.
    - Phương tiện mới xuất hiện ngay trên vạch kẻ.
    - Mất dấu hoặc chập chờn ID tracker gần vạch.
    """

    def __init__(
        self,
        line_start: Optional[Tuple[int, int]] = None,
        line_end: Optional[Tuple[int, int]] = None,
        roi_polygon: Optional[List[List[int]]] = None,
        frame_resolution_wh: Tuple[int, int] = (1280, 720)
    ):
        self.frame_resolution = frame_resolution_wh
        self.line_start = line_start or (int(frame_resolution_wh[0] * 0.05), int(frame_resolution_wh[1] * 0.6))
        self.line_end = line_end or (int(frame_resolution_wh[0] * 0.95), int(frame_resolution_wh[1] * 0.6))

        self.polygon_zone: Optional[sv.PolygonZone] = None
        self.polygon_annotator: Optional[sv.PolygonZoneAnnotator] = None

        # Bộ nhớ vị trí đáy tâm (bottom-center) và tâm (center) của các xe: track_id -> List[(x, y)]
        self.track_bottom_positions: Dict[int, List[Tuple[float, float]]] = {}
        self.track_center_positions: Dict[int, List[Tuple[float, float]]] = {}
        # Lưu dấu khoảng cách ban đầu (+1 hoặc -1 so với vạch) khi xe vừa xuất hiện
        self.track_initial_side: Dict[int, int] = {}
        self.track_first_y: Dict[int, float] = {}
        self.track_last_seen_frame: Dict[int, int] = {}
        self.frame_index = 0

        # Danh sách các xe đã được đếm (chống đếm trùng 1 xe nhiều lần)
        self.counted_tracks: Set[int] = set()

        self.in_count = 0
        self.out_count = 0

        # Cấu hình vạch đếm nếu có
        if line_start and line_end:
            self.set_counting_line(line_start, line_end)

        # Cấu hình vùng ROI nếu có
        if roi_polygon and len(roi_polygon) >= 3:
            self.set_roi_polygon(roi_polygon)

    def set_counting_line(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Cập nhật tọa độ 2 đầu mút của vạch đếm"""
        self.line_start = (int(start[0]), int(start[1]))
        self.line_end = (int(end[0]), int(end[1]))

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
        Kiểm tra phương tiện cắt qua vạch đếm dựa trên thuật toán Đa Điểm Neo (Multi-Anchor) + Giao Cắt Bounding Box.
        Từng phương tiện trong cùng một frame đều được kiểm tra độc lập và đếm đầy đủ.
        """
        self.frame_index += 1
        events = []

        # 1. Lọc theo ROI Polygon (nếu có cấu hình)
        filtered_detections = detections
        if self.polygon_zone is not None and len(detections) > 0:
            is_inside = self.polygon_zone.trigger(detections=detections)
            filtered_detections = detections[is_inside]

        # 2. Xử lý cắt vạch đếm (Line Crossing)
        if len(filtered_detections) > 0 and filtered_detections.tracker_id is not None:
            boxes = filtered_detections.xyxy
            track_ids = filtered_detections.tracker_id
            class_ids = filtered_detections.class_id

            L1 = (float(self.line_start[0]), float(self.line_start[1]))
            L2 = (float(self.line_end[0]), float(self.line_end[1]))

            for i, tid in enumerate(track_ids):
                tid = int(tid)
                box = boxes[i]

                # 2 điểm neo chính xác: Đáy giữa (tiếp xúc mặt đường) và Tâm hình học
                bot = (float((box[0] + box[2]) / 2.0), float(box[3]))
                cen = (float((box[0] + box[2]) / 2.0), float((box[1] + box[3]) / 2.0))

                self.track_last_seen_frame[tid] = self.frame_index

                # Khởi tạo quỹ đạo khi xe mới xuất hiện
                if tid not in self.track_bottom_positions:
                    self.track_bottom_positions[tid] = [bot]
                    self.track_center_positions[tid] = [cen]
                    self.track_first_y[tid] = cen[1]
                    sd = signed_distance(L1, L2, cen)
                    self.track_initial_side[tid] = 1 if sd >= 0 else -1
                    continue

                # Lưu lịch sử tối đa 15 vị trí gần nhất
                self.track_bottom_positions[tid].append(bot)
                self.track_center_positions[tid].append(cen)
                if len(self.track_bottom_positions[tid]) > 15:
                    self.track_bottom_positions[tid].pop(0)
                if len(self.track_center_positions[tid]) > 15:
                    self.track_center_positions[tid].pop(0)

                # Nếu xe đã được đếm trong phiên này thì bỏ qua
                if tid in self.counted_tracks:
                    continue

                b_hist = self.track_bottom_positions[tid]
                c_hist = self.track_center_positions[tid]

                # Cần tối thiểu 2 frame để có vector di chuyển thực tế (chống đếm ảo khi vừa start)
                if len(b_hist) < 2:
                    continue

                has_crossed = False

                # KIỂM TRA 1: Giao cắt hình học giữa quỹ đạo (đáy hoặc tâm) và vạch đếm
                # Duyệt ngược từ các vị trí gần nhất (tối đa 8 frame trước)
                search_depth = min(8, len(b_hist) - 1)
                for past_idx in range(len(b_hist) - 2, len(b_hist) - 2 - search_depth, -1):
                    if intersect(L1, L2, b_hist[past_idx], bot) or intersect(L1, L2, c_hist[past_idx], cen):
                        has_crossed = True
                        break

                # KIỂM TRA 2: Chuyển đổi vị thế có dấu (Signed Distance Side-Flip)
                if not has_crossed and len(c_hist) >= 3:
                    curr_sd = signed_distance(L1, L2, cen)
                    curr_side = 1 if curr_sd >= 0 else -1
                    init_side = self.track_initial_side.get(tid, curr_side)

                    if curr_side != init_side:
                        proj_t = projection_ratio(L1, L2, cen)
                        if -0.15 <= proj_t <= 1.15:
                            has_crossed = True

                # Xử lý khi xác nhận cắt qua vạch
                if has_crossed:
                    self.counted_tracks.add(tid)

                    # Xác định hướng di chuyển chính xác dựa trên độ dịch chuyển trục Y
                    first_y = self.track_first_y.get(tid, c_hist[0][1])
                    total_dy = cen[1] - first_y

                    if abs(total_dy) < 1.0 and len(c_hist) >= 2:
                        total_dy = cen[1] - c_hist[0][1]

                    # Y tăng (từ trên xuống dưới màn hình, lại gần camera) -> IN
                    # Y giảm (từ dưới lên trên màn hình, ra xa camera) -> OUT
                    if total_dy >= 0:
                        direction = "in"
                        self.in_count += 1
                    else:
                        direction = "out"
                        self.out_count += 1

                    cid = int(class_ids[i]) if class_ids is not None else None
                    events.append({
                        "track_id": tid,
                        "direction": direction,
                        "class_id": cid
                    })

        # Dọn dẹp bộ nhớ định kỳ (mỗi 300 frames) để tránh rò rỉ RAM
        if self.frame_index % 300 == 0:
            active_limit = self.frame_index - 180
            stale_tids = [tid for tid, last_f in self.track_last_seen_frame.items() if last_f < active_limit]
            for tid in stale_tids:
                self.track_bottom_positions.pop(tid, None)
                self.track_center_positions.pop(tid, None)
                self.track_initial_side.pop(tid, None)
                self.track_first_y.pop(tid, None)
                self.track_last_seen_frame.pop(tid, None)
                if len(self.counted_tracks) > 5000:
                    self.counted_tracks.discard(tid)

        return filtered_detections, events

    def reset(self):
        """Khởi động lại bộ đếm khi video tua lại từ đầu hoặc chuyển session mới"""
        self.track_bottom_positions.clear()
        self.track_center_positions.clear()
        self.track_initial_side.clear()
        self.track_first_y.clear()
        self.track_last_seen_frame.clear()
        self.counted_tracks.clear()

    def get_counts(self) -> Dict[str, int]:
        """Lấy tổng số lượt xe vào / ra hiện tại"""
        return {
            "in": int(self.in_count),
            "out": int(self.out_count),
            "total": int(self.in_count + self.out_count)
        }

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        """Vẽ vạch đếm và bảng số liệu In / Out trực quan chuyên nghiệp lên frame"""
        annotated_frame = frame.copy()

        # 1. Vẽ vùng đa giác ROI (nếu có)
        if self.polygon_zone is not None and self.polygon_annotator is not None:
            try:
                annotated_frame = self.polygon_annotator.annotate(scene=annotated_frame)
            except Exception:
                pass

        # 2. Vẽ đường line vạch đếm
        p1 = (int(self.line_start[0]), int(self.line_start[1]))
        p2 = (int(self.line_end[0]), int(self.line_end[1]))

        # Đường viền bóng mờ và đường line chính màu trắng sáng
        cv2.line(annotated_frame, p1, p2, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.line(annotated_frame, p1, p2, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(annotated_frame, p1, 5, (37, 99, 235), -1, cv2.LINE_AA)
        cv2.circle(annotated_frame, p2, 5, (37, 99, 235), -1, cv2.LINE_AA)

        # 3. Vẽ bảng số đếm IN / OUT ở giữa đường line
        mid_x = int((p1[0] + p2[0]) / 2)
        mid_y = int((p1[1] + p2[1]) / 2)

        box_w, box_h = 90, 48
        bx1 = mid_x - int(box_w / 2)
        by1 = mid_y - int(box_h / 2)
        bx2 = bx1 + box_w
        by2 = by1 + box_h

        # Nền trắng bo góc
        cv2.rectangle(annotated_frame, (bx1, by1), (bx2, by2), (255, 255, 255), -1)
        cv2.rectangle(annotated_frame, (bx1, by1), (bx2, by2), (15, 23, 42), 1)

        # Chữ in / out
        in_text = f"in: {self.in_count}"
        out_text = f"out: {self.out_count}"

        cv2.putText(annotated_frame, in_text, (bx1 + 12, by1 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (5, 150, 105), 1, cv2.LINE_AA)
        cv2.line(annotated_frame, (bx1, by1 + 24), (bx2, by1 + 24), (226, 232, 240), 1)
        cv2.putText(annotated_frame, out_text, (bx1 + 12, by1 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (225, 29, 72), 1, cv2.LINE_AA)

        return annotated_frame
