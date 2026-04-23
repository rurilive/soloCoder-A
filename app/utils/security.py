import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def _preprocess_password(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    hashed = hashlib.sha256(password_bytes).digest()
    return base64.b64encode(hashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = _preprocess_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    password_bytes = _preprocess_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_session_id() -> str:
    return secrets.token_hex(32)


def generate_file_id() -> str:
    return secrets.token_urlsafe(12)


def hash_filename(filename: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    random_str = secrets.token_hex(8)
    hash_input = f"{filename}{timestamp}{random_str}".encode()
    return hashlib.sha256(hash_input).hexdigest()[:32]
