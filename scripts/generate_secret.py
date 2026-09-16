"""Oturum cerezi icin rastgele anahtar uretir."""

import secrets

if __name__ == "__main__":
    print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
