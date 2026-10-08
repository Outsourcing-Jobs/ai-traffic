# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from database.database import engine, Base
from api import sessions, stats, stream, videos, dataset

# Tự động tạo bảng SQLite nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traffic Monitoring & Speed Estimation API",
    description="Hệ thống xác định lưu lượng và ước lượng tốc độ trung bình phương tiện giao thông sử dụng camera giám sát",
    version="1.0.0"
)

# Cấu hình CORS cho phép Frontend truy cập tự do
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Router API
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(stream.router)
app.include_router(videos.router)
app.include_router(dataset.router)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Traffic Monitoring Backend API",
        "docs_url": "/docs",
        "endpoints": {
            "sessions": "/api/sessions",
            "stream": "/api/stream/{session_id}",
            "stats": "/api/sessions/{session_id}/stats"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
