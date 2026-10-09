import hashlib
import hmac
import json
import base64
import time
from datetime import datetime
from typing import Optional, Dict, Any
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Header
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.database import get_db, SessionLocal
from database.models import UserModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = "ai-traffic-monitoring-secret-key-graduation-project-2026"
TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 ngày


def hash_password(password: str, username: str) -> str:
    """Băm mật khẩu kết hợp Salt theo username bằng PBKDF2 HMAC-SHA256"""
    salt = hashlib.sha256(username.lower().strip().encode("utf-8")).hexdigest()[:16]
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()


def verify_password(password: str, username: str, hashed: str) -> bool:
    """Xác thực mật khẩu người dùng"""
    return hash_password(password, username) == hashed


def create_access_token(user_data: Dict[str, Any]) -> str:
    """Tạo Token xác thực HMAC-SHA256 chuẩn JSON Token"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        **user_data,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
        "iat": int(time.time())
    }

    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    msg = f"{h_b64}.{p_b64}".encode()
    sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
    return f"{h_b64}.{p_b64}.{sig}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Giải mã và xác thực chữ ký của Token"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_b64, p_b64, sig = parts

        # Kiểm tra chữ ký
        msg = f"{h_b64}.{p_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        # Padding base64
        padded_p = p_b64 + "=" * (-len(p_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_p).decode())

        if payload.get("exp", 0) < time.time():
            return None  # Token hết hạn

        return payload
    except Exception:
        return None


def init_default_users():
    """Tự động khởi tạo tài khoản quản trị mặc định (admin / admin123) nếu chưa có"""
    db = SessionLocal()
    try:
        admin = db.query(UserModel).filter(UserModel.username == "admin").first()
        if not admin:
            admin_user = UserModel(
                username="admin",
                hashed_password=hash_password("admin123", "admin"),
                full_name="Quản Trị Viên (ITS Admin)",
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("[Auth] Đã khởi tạo tài khoản mặc định: admin / admin123")
    except Exception as e:
        print(f"[Auth] Lỗi khởi tạo user: {e}")
    finally:
        db.close()


# Gọi khởi tạo tài khoản admin
init_default_users()


# ==========================================
# Schemas
# ==========================================
class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")


class RegisterRequest(BaseModel):
    username: str = Field(..., example="operator01")
    password: str = Field(..., example="123456")
    full_name: str = Field(..., example="Cán bộ điều hành ITS")
    role: Optional[str] = "operator"


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    created_at: datetime


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
    message: str


# ==========================================
# Endpoints
# ==========================================
@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập hệ thống giám sát AI Traffic"""
    u = req.username.strip().lower()
    user = db.query(UserModel).filter(UserModel.username == u).first()
    if not user or not verify_password(req.password, u, user.hashed_password):
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác")

    user_info = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role
    }
    token = create_access_token(user_info)

    return {
        "token": token,
        "user": user,
        "message": f"Chào mừng {user.full_name} đã đăng nhập thành công!"
    }


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký tài khoản điều hành mới"""
    u = req.username.strip().lower()
    existing = db.query(UserModel).filter(UserModel.username == u).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại trong hệ thống")

    new_user = UserModel(
        username=u,
        hashed_password=hash_password(req.password, u),
        full_name=req.full_name.strip(),
        role=req.role or "operator"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Lấy thông tin tài khoản đang đăng nhập từ Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    user = db.query(UserModel).filter(UserModel.id == payload["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    return user
