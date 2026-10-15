# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from database.database import engine, Base
from api import sessions, stats, stream, videos, dataset, violations, auth

# Tự động tạo bảng SQLite nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

# Tự động khởi tạo tài khoản quản trị mặc định (admin / admin123)
auth.init_default_users()


app = FastAPI(
    title="Traffic Monitoring & Speed Estimation API",
    description="Hệ thống xác định lưu lượng và ước lượng tốc độ trung bình phương tiện giao thông sử dụng camera giám sát",
    version="1.0.0"
)

# Danh sách các domain được phép truy cập
ALLOWED_ORIGINS = [
    "https://smarttraffic-monitoring.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

# Cấu hình CORSMiddleware tiêu chuẩn của FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers_middleware(request, call_next):
    """Đảm bảo mọi response (kể cả lỗi hoặc preflight OPTIONS) luôn có Access-Control-Allow-Origin"""
    origin = request.headers.get("origin")
    
    # Xử lý nhanh preflight OPTIONS
    if request.method == "OPTIONS":
        # pyrefly: ignore [missing-import]
        from fastapi import Response
        res = Response(status_code=204)
        target_origin = origin if origin else "*"
        res.headers["Access-Control-Allow-Origin"] = target_origin
        res.headers["Access-Control-Allow-Credentials"] = "true"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        res.headers["Access-Control-Allow-Headers"] = "*"
        res.headers["Access-Control-Max-Age"] = "86400"
        return res

    try:
        response = await call_next(request)
    except Exception as e:
        # pyrefly: ignore [missing-import]
        from fastapi.responses import JSONResponse
        response = JSONResponse(status_code=500, content={"detail": str(e)})

    # Gắn CORS header vào response
    target_origin = origin if origin else "*"
    response.headers["Access-Control-Allow-Origin"] = target_origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Đăng ký các Router API
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(violations.router)
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
