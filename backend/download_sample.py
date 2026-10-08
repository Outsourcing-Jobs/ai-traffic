"""
Script tự động tải video giao thông mẫu về thư mục data/videos/traffic.mp4
Sử dụng thư viện supervision assets hoặc tải trực tiếp từ CDN chuẩn.
"""

import sys
import shutil
from pathlib import Path

# Đường dẫn thư mục
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
VIDEOS_DIR = PROJECT_DIR / "data" / "videos"
TARGET_FILE = VIDEOS_DIR / "traffic.mp4"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def download_via_supervision():
    print("[*] Đang tải video giao thông mẫu từ Roboflow Supervision Assets...")
    try:
        # pyrefly: ignore [missing-import]
        from supervision.assets import download_assets, VideoAssets
        downloaded_path = download_assets(VideoAssets.VEHICLES)
        print(f"[*] Đã tải thành công về: {downloaded_path}")
        shutil.copy(downloaded_path, TARGET_FILE)
        print(f"[SUCCESS] Video mẫu đã sẵn sàng tại: {TARGET_FILE}")
        return True
    except Exception as e:
        print(f"[!] Lỗi khi tải qua supervision: {e}")
        return False


def download_via_urllib():
    print("[*] Đang thử tải từ URL dự phòng...")
    import urllib.request
    # Link video mẫu xe cộ trực tiếp từ kho asset mở của Roboflow
    url = "https://media.roboflow.com/supervision/video/vehicles.mp4"
    try:
        urllib.request.urlretrieve(url, TARGET_FILE)
        print(f"[SUCCESS] Video mẫu đã tải thành công tại: {TARGET_FILE}")
        return True
    except Exception as e:
        print(f"[!] Lỗi khi tải từ URL: {e}")
        return False


if __name__ == "__main__":
    if TARGET_FILE.exists():
        print(f"[*] File {TARGET_FILE} đã tồn tại sẵn!")
        sys.exit(0)

    if not download_via_supervision():
        download_via_urllib()
