"""Uygulama ayarlari.

Hassas degerler (SECRET_KEY, parola ozeti) yalnizca ortam degiskeninden okunur,
hicbir zaman kod icinde tutulmaz.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path: Path | None = None) -> None:
    """.env dosyasini okur. Zaten tanimli ortam degiskenleri ezilmez."""
    env_path = path or BASE_DIR / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DATA_DIR / 'enerji.db'}"


def secret_key() -> str:
    """Oturum cerezini imzalamak icin kullanilir."""
    key = os.environ.get("SECRET_KEY")
    if not key:
        raise RuntimeError(
            "SECRET_KEY tanimli degil. .env.example dosyasina bakin ve "
            "'python scripts/generate_secret.py' ile bir anahtar uretin."
        )
    return key


def password_hash() -> str:
    """Tek kullanicinin parola ozeti (scrypt)."""
    value = os.environ.get("APP_PASSWORD_HASH")
    if not value:
        raise RuntimeError(
            "APP_PASSWORD_HASH tanimli degil. "
            "'python scripts/set_password.py' ile olusturun."
        )
    return value


def secure_cookie() -> bool:
    """HTTPS arkasinda calisirken 1 yapilmalidir."""
    return os.environ.get("SECURE_COOKIE", "0") == "1"
