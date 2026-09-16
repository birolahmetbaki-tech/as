"""Uygulama parolasinin ozetini uretir.

Kullanim:
    python scripts/set_password.py
Cikan satiri .env dosyasina yapistirin. Parolanin kendisi hicbir yerde saklanmaz.
"""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security import hash_password  # noqa: E402

if __name__ == "__main__":
    password = getpass.getpass("Yeni parola: ")
    if len(password) < 8:
        raise SystemExit("Parola en az 8 karakter olmalidir.")
    if password != getpass.getpass("Parola (tekrar): "):
        raise SystemExit("Parolalar eslesmedi.")
    print(f"APP_PASSWORD_HASH={hash_password(password)}")
