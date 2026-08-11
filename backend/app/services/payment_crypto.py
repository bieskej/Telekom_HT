import hashlib

from app.config import settings


def _pepper() -> bytes:
    return settings.jwt_secret.encode("utf-8")


def hash_sensitive(value: str) -> str:
    payload = f"{value.strip()}:{settings.jwt_secret}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
