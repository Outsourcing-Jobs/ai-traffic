import time
from typing import Generator
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
from video_manager import video_manager

router = APIRouter(prefix="/api/stream", tags=["Streaming"])


def generate_mjpeg_frames(session_id: int) -> Generator[bytes, None, None]:
    """Generator sinh các multipart JPEG frame cho luồng MJPEG"""
    runner = video_manager.get_runner(session_id)
    if not runner:
        return

    while runner.is_running:
        frame_bytes = runner.get_latest_frame()
        if frame_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.03)  # ~30 FPS


@router.get("/{session_id}")
def stream_video(session_id: int):
    """
    Endpoint phát luồng MJPEG trực tiếp.
    Frontend chỉ cần nhúng vào thẻ <img>:
    <img src="http://localhost:8000/api/stream/1" alt="Live Stream" />
    """
    runner = video_manager.get_runner(session_id)
    if not runner or not runner.is_running:
        raise HTTPException(
            status_code=400,
            detail="Session chưa được kích hoạt. Hãy gọi POST /api/sessions/{id}/start trước."
        )

    return StreamingResponse(
        generate_mjpeg_frames(session_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/{session_id}/snapshot")
def get_snapshot(session_id: int):
    """
    Lấy 1 frame ảnh JPEG tĩnh mới nhất.
    Dùng cho màn hình cấu hình ROI & Vạch đếm (chụp 1 hình để vẽ lên Canvas).
    """
    runner = video_manager.get_runner(session_id)
    if not runner:
        raise HTTPException(status_code=400, detail="Session chưa chạy")

    frame_bytes = runner.get_latest_frame()
    if not frame_bytes:
        raise HTTPException(status_code=404, detail="Chưa có frame nào sẵn sàng")

    return Response(content=frame_bytes, media_type="image/jpeg")
