from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _secret() -> bytes:
    secret = settings.auth_secret
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured. Set AUTH_SECRET (32+ characters) before starting the service.")
    return secret.encode("utf-8")


def hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    salt = salt or __import__("secrets").token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{_b64(salt)}${_b64(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_text, expected = encoded.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        actual = _b64(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user: dict[str, Any]) -> str:
    now = int(time.time())
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user.get("role", "user"),
        "iat": now,
        "exp": now + settings.auth_token_ttl_seconds,
    }
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Sign in required.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload, signature = credentials.credentials.split(".", 1)
        expected = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid token")
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data["exp"]) < int(time.time()):
            raise ValueError("expired token")
        return {
            "id": str(data["sub"]),
            "username": str(data["username"]),
            "role": str(data.get("role", "user")),
        }
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token.", headers={"WWW-Authenticate": "Bearer"})


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user
