"""
Script kiểm thử độc lập cho AI Pipeline (YOLOv8 + ByteTrack + LineZone + Speed)
Chạy trực tiếp: python test_pipeline.py --video ../data/videos/traffic.mp4
"""

import sys
import argparse
from pathlib import Path
# pyrefly: ignore [missing-import]
import cv2

# Bổ sung đường dẫn import
sys.path.append(str(Path(__file__).resolve().parent))

from ai.pipeline import TrafficPipeline


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử độc lập AI Traffic Pipeline")
    parser.add_argument("--video", type=str, default="data/videos/traffic.mp4", help="Đường dẫn file video .mp4")
    parser.add_argument("--display", action="store_true", default=True, help="Hiển thị cửa sổ OpenCV")
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parent
    video_p = Path(args.video)
    if not video_p.exists():
        if (backend_dir / args.video).exists():
            video_p = backend_dir / args.video
        elif (backend_dir / "data" / "videos" / video_p.name).exists():
            video_p = backend_dir / "data" / "videos" / video_p.name

    if not video_p.exists():
        print(f"[!] Không tìm thấy file video: {args.video}")
        print("    Vui lòng đặt một video mẫu vào backend/data/videos/traffic.mp4 hoặc chỉ định qua --video")
        return

    video_path = str(video_p)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[!] Không thể mở video: {video_path}")
        return

    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Chuẩn hoá về 1280px để xử lý nhanh và mượt mà (video gốc 4K rất nặng)
    target_w = 1280
    target_h = int(1280 * orig_h / orig_w) if orig_w > 0 else 720

    print(f"[*] Khởi tạo Pipeline...")
    print(f"    - Độ phân giải gốc: {orig_w}x{orig_h} -> Tối ưu xử lý: {target_w}x{target_h}")
    print(f"    - FPS gốc: {fps:.1f}")

    pipeline = TrafficPipeline(fps=fps, frame_wh=(target_w, target_h))

    # Cấu hình vạch đếm thử nghiệm (kẻ ngang giữa màn hình)
    line_y = int(target_h * 0.6)
    pipeline.counter.set_counting_line((int(target_w * 0.05), line_y), (int(target_w * 0.95), line_y))

    print("[*] Đang bắt đầu xử lý video... (Nhấn phím 'q' trên cửa sổ để dừng)")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[*] Video đã kết thúc.")
            break

        # Resize về kích thước chuẩn
        frame = cv2.resize(frame, (target_w, target_h))

        annotated_frame, detections, events = pipeline.process_frame(frame)

        # In log nếu có xe vừa qua vạch
        if events:
            for ev in events:
                print(f"[CROSSING] Track #{ev['track_id']} | Loại: {ev['vehicle_type']} | Hướng: {ev['direction']} | Tốc độ: {ev.get('speed_kmh', 0):.1f} km/h")

        counts = pipeline.get_counts()
        cv2.putText(
            annotated_frame,
            f"IN: {counts['in']} | OUT: {counts['out']} | TOTAL: {counts['total']}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        if args.display:
            cv2.imshow("AI Traffic Monitor - Test Pipeline", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("[*] Đã hoàn thành kiểm thử.")


if __name__ == "__main__":
    main()
