"""
User API — /api/v1/user
注册、登录、个人信息管理。
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from model.dto import AuthResponseDTO, UserDTO, UserWithMembershipsDTO
from service import user_service

router = APIRouter(prefix="/api/v1/user", tags=["user"])


# ── Request Bodies ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateMeRequest(BaseModel):
    name: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ── Auth Helper ─────────────────────────────────────────────────────

def _get_current_user_id(request: Request) -> str:
    """Extract Bearer token from Authorization header and verify it."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ")
    user_id = user_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


# ── Routes ──────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponseDTO)
def register(body: RegisterRequest) -> AuthResponseDTO:
    return user_service.register(email=body.email, name=body.name, password=body.password)


@router.post("/login", response_model=AuthResponseDTO)
def login(body: LoginRequest) -> AuthResponseDTO:
    result = user_service.login(email=body.email, password=body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return result


@router.post("/logout")
def logout() -> dict:
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserWithMembershipsDTO)
def get_me(request: Request) -> UserWithMembershipsDTO:
    user_id = _get_current_user_id(request)
    user = user_service.get_me(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.put("/me", response_model=UserDTO)
def update_me(request: Request, body: UpdateMeRequest) -> UserDTO:
    user_id = _get_current_user_id(request)
    result = user_service.update_me(user_id, name=body.name)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.put("/me/password")
def change_password(request: Request, body: ChangePasswordRequest) -> dict:
    user_id = _get_current_user_id(request)
    success = user_service.change_password(
        user_id, old_password=body.old_password, new_password=body.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    return {"message": "Password updated"}
