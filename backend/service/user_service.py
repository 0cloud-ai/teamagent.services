"""
User Service — registration, login, token management.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import uuid

from model.dto import AuthResponseDTO, UserDTO, UserWithMembershipsDTO
from repository import user_repo


# ── helpers ──────────────────────────────────────────────────────────

_TOKEN_SECRET = "agent-service-secret"
_TOKEN_EXPIRY_HOURS = 24


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": (dt.datetime.utcnow() + dt.timedelta(hours=_TOKEN_EXPIRY_HOURS)).isoformat(),
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _user_dto(row: dict) -> UserDTO:
    return UserDTO(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        created_at=row["created_at"],
    )


# ── public API ───────────────────────────────────────────────────────

def register(email: str, name: str, password: str) -> AuthResponseDTO:
    user_id = str(uuid.uuid4())
    hashed = _hash_password(password)
    now = dt.datetime.utcnow()

    row = user_repo.create_user(
        id=user_id,
        email=email,
        name=name,
        password=hashed,
        created_at=now,
    )

    token = _generate_token(user_id)
    return AuthResponseDTO(token=token, user=_user_dto(row))


def login(email: str, password: str) -> AuthResponseDTO | None:
    row = user_repo.get_by_email(email)
    if row is None:
        return None

    if row["password"] != _hash_password(password):
        return None

    token = _generate_token(row["id"])
    return AuthResponseDTO(token=token, user=_user_dto(row))


def get_me(user_id: str) -> UserWithMembershipsDTO | None:
    row = user_repo.get_by_id(user_id)
    if row is None:
        return None

    return UserWithMembershipsDTO(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        created_at=row["created_at"],
        memberships=[],
    )


def update_me(user_id: str, name: str) -> UserDTO | None:
    row = user_repo.update_user(user_id, name=name)
    if row is None:
        return None
    return _user_dto(row)


def change_password(user_id: str, old_password: str, new_password: str) -> bool:
    row = user_repo.get_by_id(user_id)
    if row is None:
        return False

    if row["password"] != _hash_password(old_password):
        return False

    user_repo.update_password(user_id, _hash_password(new_password))
    return True


def verify_token(token: str) -> str | None:
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()))
        exp = dt.datetime.fromisoformat(payload["exp"])
        if dt.datetime.utcnow() > exp:
            return None
        return payload["user_id"]
    except Exception:
        return None
