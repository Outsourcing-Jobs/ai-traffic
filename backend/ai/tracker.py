import warnings
# pyrefly: ignore [missing-import]
import supervision as sv

# Bỏ qua warning thông báo cập nhật phiên bản của ByteTrack
warnings.filterwarnings("ignore", category=FutureWarning)


class VehicleTracker:
    """Wrapper cho ByteTrack để định danh và theo vết phương tiện qua các frame"""

    def __init__(self, track_activation_threshold: float = 0.25, lost_track_buffer: int = 30):
        self.tracker = sv.ByteTrack(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer
        )

    def update(self, detections: sv.Detections) -> sv.Detections:
        """
        Cập nhật vị trí các phương tiện với tracker.
        Trả về detections có gán tracker_id duy nhất.
        """
        if len(detections) == 0:
            return detections
        return self.tracker.update_with_detections(detections)

    def reset(self):
        """Khởi động lại tracker khi bắt đầu session mới"""
        self.tracker.reset()
