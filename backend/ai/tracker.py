import warnings
from collections import Counter
from typing import Dict, List
# pyrefly: ignore [missing-import]
import supervision as sv

# Bỏ qua warning thông báo cập nhật phiên bản của ByteTrack
warnings.filterwarnings("ignore", category=FutureWarning)


class VehicleTracker:
    """Wrapper cho ByteTrack để định danh, theo vết và ổn định nhãn phân loại qua các frame"""

    def __init__(self, track_activation_threshold: float = 0.20, lost_track_buffer: int = 35):
        try:
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer,
                minimum_matching_threshold=0.80,
                minimum_consecutive_frames=1
            )
        except TypeError:
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer
            )
        # Lưu lịch sử class_id của từng xe qua các frame để chống chớp nháy nhãn (Majority Voting)
        self.track_class_history: Dict[int, List[int]] = {}

    def update(self, detections: sv.Detections) -> sv.Detections:
        """
        Cập nhật vị trí các phương tiện với tracker.
        Áp dụng thuật toán lọc mượt nhãn (Temporal Majority Voting) để loại bỏ hiện tượng nhảy nhãn ngẫu nhiên.
        """
        if len(detections) == 0:
            return detections

        tracked = self.tracker.update_with_detections(detections)

        if len(tracked) > 0 and tracked.tracker_id is not None and tracked.class_id is not None:
            stabilized_class_ids = tracked.class_id.copy()

            for i, tid in enumerate(tracked.tracker_id):
                tid = int(tid)
                raw_cid = int(tracked.class_id[i])

                if tid not in self.track_class_history:
                    self.track_class_history[tid] = []

                # Giữ tối đa 15 frames gần nhất
                self.track_class_history[tid].append(raw_cid)
                if len(self.track_class_history[tid]) > 15:
                    self.track_class_history[tid].pop(0)

                # Chọn nhãn xuất hiện nhiều nhất (Majority Vote)
                most_common_cid, _ = Counter(self.track_class_history[tid]).most_common(1)[0]
                stabilized_class_ids[i] = most_common_cid

            tracked.class_id = stabilized_class_ids

        return tracked

    def reset(self):
        """Khởi động lại tracker khi bắt đầu session mới"""
        self.tracker.reset()
        self.track_class_history.clear()

