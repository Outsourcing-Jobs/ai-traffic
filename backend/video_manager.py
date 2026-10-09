from typing import Any
import os
import json
import time
from datetime import datetime
import threading
from typing import Dict, Optional, Generator
# pyrefly: ignore [missing-import]
import cv2
from database.database import SessionLocal
from database.models import SessionModel, CrossingEventModel, TrafficStatModel
from ai.pipeline import TrafficPipeline
from ai.violation_service import record_speed_violation
from config import JPEG_QUALITY, STREAM_FRAME_WIDTH, STREAM_FRAME_HEIGHT, BASE_DIR, VIDEOS_DIR


class SessionRunner:
    """Quản lý luồng đọc video và xử lý AI cho 1 session giám sát"""

    def __init__(self, session_id: int, video_source: str, config_json: Optional[str] = None):
        self.session_id = session_id
        self.video_source = video_source
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

        self.pipeline = TrafficPipeline(frame_wh=(STREAM_FRAME_WIDTH, STREAM_FRAME_HEIGHT))
        if config_json:
            try:
                cfg = json.loads(config_json)
                self.pipeline.configure(cfg)
            except Exception as e:
                print(f"[Runner {session_id}] Lỗi nạp config: {e}")

        self.latest_jpeg: Optional[bytes] = None
        self.latest_raw_frame = None
        self.logged_violation_tracks = set()
        self.latest_congestion = {
            "level": "FLUID",
            "text": "Lưu thông thông thoáng",
            "active_count": 0,
            "current_avg_speed": 0.0,
            "speed_limit": self.pipeline.speed_limit
        }
        self.lock = threading.Lock()


    def start(self):
        """Bắt đầu chạy luồng xử lý video"""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Dừng luồng xử lý video"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _run_loop(self):
        """Vòng lặp đọc frame, chạy AI pipeline và ghi nhận CSDL"""
        # Resolve đường dẫn video linh hoạt (tương đối từ gốc dự án, thư mục data/videos, hoặc URL Cloud)
        video_path = self.video_source
        if not video_path.startswith(("http://", "https://", "rtsp://")) and not os.path.exists(video_path):
            candidate1 = BASE_DIR / video_path
            if candidate1.exists():
                video_path = str(candidate1)
            else:
                candidate2 = VIDEOS_DIR / os.path.basename(video_path)
                if candidate2.exists():
                    video_path = str(candidate2)

        print(f"[Runner {self.session_id}] Bắt đầu xử lý video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[Runner {self.session_id}] Không thể mở video: {video_path}")
            self.is_running = False
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_delay = 1.0 / fps

        db = SessionLocal()
        last_stat_time = time.time()
        minute_events = []

        try:
            while self.is_running:
                start_t = time.time()
                ret, frame = cap.read()
                if not ret:
                    # Video kết thúc -> Tua lại từ đầu để tiếp tục demo liên tục
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.pipeline.on_video_loop()
                    self.logged_violation_tracks.clear()
                    time.sleep(0.1)
                    continue

                # Resize frame về kích thước chuẩn stream
                frame = cv2.resize(frame, (STREAM_FRAME_WIDTH, STREAM_FRAME_HEIGHT))

                # Chạy AI Pipeline
                annotated_frame, detections, events, violations, congestion_info = self.pipeline.process_frame(frame)

                # Nén ảnh thành JPEG cho stream
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                _, buffer = cv2.imencode(".jpg", annotated_frame, encode_param)
                with self.lock:
                    self.latest_jpeg = buffer.tobytes()
                    self.latest_raw_frame = frame.copy()
                    self.latest_congestion = congestion_info

                # Lưu các xe vi phạm tốc độ (chụp ảnh bằng chứng & ghi CSDL)
                if violations:
                    for v in violations:
                        tid = v["track_id"]
                        if tid not in self.logged_violation_tracks:
                            self.logged_violation_tracks.add(tid)
                            record_speed_violation(
                                session_id=self.session_id,
                                track_id=tid,
                                vehicle_type=v["vehicle_type"],
                                speed_kmh=v["speed_kmh"],
                                speed_limit=v["speed_limit"],
                                frame=frame,
                                bbox=v["bbox"]
                            )

                # Lưu các sự kiện xe cắt qua vạch vào CSDL
                if events:
                    for ev in events:
                        crossing_record = CrossingEventModel(
                            session_id=self.session_id,
                            track_id=ev["track_id"],
                            vehicle_type=ev.get("vehicle_type", "vehicle"),
                            speed_kmh=ev.get("speed_kmh", 0.0),
                            direction=ev.get("direction", "in"),
                            line_id=1,
                            crossed_at=datetime.now()
                        )
                        db.add(crossing_record)
                        minute_events.append(ev)
                    db.commit()


                # Tổng hợp thống kê mỗi 60 giây vào bảng traffic_stats
                if time.time() - last_stat_time >= 60.0:
                    counts_by_type = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}
                    speeds = []
                    for me in minute_events:
                        vtype = me.get("vehicle_type", "car")
                        if vtype in counts_by_type:
                            counts_by_type[vtype] += 1
                        sp = me.get("speed_kmh", 0.0)
                        if sp and sp > 0:
                            speeds.append(sp)

                    stat_record = TrafficStatModel(
                        session_id=self.session_id,
                        timestamp=datetime.now(),
                        period_min=1,
                        car_count=counts_by_type["car"],
                        moto_count=counts_by_type["motorcycle"],
                        bus_count=counts_by_type["bus"],
                        truck_count=counts_by_type["truck"],
                        total_count=len(minute_events),
                        avg_speed=round(float(sum(speeds) / len(speeds)), 1) if speeds else 0.0,
                        max_speed=round(float(max(speeds)), 1) if speeds else 0.0,
                        min_speed=round(float(min(speeds)), 1) if speeds else 0.0
                    )
                    db.add(stat_record)
                    db.commit()

                    last_stat_time = time.time()
                    minute_events = []

                # Điều chỉnh tốc độ xử lý khớp FPS video
                elapsed = time.time() - start_t
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            print(f"[Runner {self.session_id}] Lỗi runtime: {e}")
        finally:
            cap.release()
            db.close()
            self.is_running = False
            print(f"[Runner {self.session_id}] Đã dừng xử lý.")

    def get_latest_frame(self) -> Optional[bytes]:
        """Lấy JPEG frame mới nhất cho video streaming"""
        with self.lock:
            return self.latest_jpeg

    def get_latest_raw_frame(self):
        """Lấy frame gốc dạng BGR numpy array trước khi vẽ bbox để gán nhãn dataset"""
        with self.lock:
            if self.latest_raw_frame is not None:
                return self.latest_raw_frame.copy()
            return None

    def get_congestion_info(self) -> Dict[str, Any]:
        """Lấy thông tin đánh giá mức độ ùn tắc giao thông thời gian thực"""
        with self.lock:
            return self.latest_congestion.copy()

    def set_speed_limit(self, limit: float):
        """Cập nhật tốc độ giới hạn động cho pipeline"""
        with self.lock:
            self.pipeline.speed_limit = float(limit)
            self.latest_congestion["speed_limit"] = float(limit)



class VideoManager:
    """Singleton quản lý tập trung tất cả các session đang chạy"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VideoManager, cls).__new__(cls)
            cls._instance.runners: Dict[int, SessionRunner] = {}
        return cls._instance

    def start_session(self, session_id: int, video_source: str, config_json: Optional[str] = None) -> SessionRunner:
        """Bắt đầu chạy hoặc tái khởi động một session"""
        self.stop_session(session_id)
        runner = SessionRunner(session_id, video_source, config_json)
        self.runners[session_id] = runner
        runner.start()
        return runner

    def stop_session(self, session_id: int):
        """Dừng 1 session"""
        if session_id in self.runners:
            self.runners[session_id].stop()
            del self.runners[session_id]

    def get_runner(self, session_id: int) -> Optional[SessionRunner]:
        """Lấy runner của session"""
        return self.runners.get(session_id)


# Instance toàn cục dùng chung cho toàn bộ app
video_manager = VideoManager()
