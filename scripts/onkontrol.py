"""Uygulamayi baslatmadan once ortami denetler.

Amac: kullanicinin tarayicida anlamsiz bir hata sayfasiyla ya da terminalde
Python traceback'iyle karsilasmasi yerine, ne yapmasi gerektigini Turkce ve
tek cumleyle gormesi.

Cikis kodu 0 ise her sey hazirdir; 1 ise eksik vardir ve mesaj yazilmistir.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def sorunlar() -> list[str]:
    bulgular: list[str] = []

    if not (BASE_DIR / ".env").is_file():
        return [
            ".env dosyasi yok.\n"
            "  Cozum: .env.example dosyasini .env olarak kopyalayin, sonra\n"
            "         python scripts/generate_secret.py\n"
            "         python scripts/set_password.py\n"
            "         ciktilarini .env icine yapistirin."
        ]

    from app import config  # .env yuklenir

    for degisken, uretici in (
        ("SECRET_KEY", "python scripts/generate_secret.py"),
        ("APP_PASSWORD_HASH", "python scripts/set_password.py"),
    ):
        import os

        if not os.environ.get(degisken):
            bulgular.append(
                f"{degisken} degeri .env dosyasinda bos.\n"
                f"  Cozum: {uretici} ciktisini .env icine yapistirin."
            )

    url = config.database_url()
    if url.startswith("sqlite"):
        veritabani = Path(url.split("///", 1)[1])
        if not veritabani.is_file():
            bulgular.append(
                f"Veritabani dosyasi yok: {veritabani}\n"
                "  Cozum: alembic upgrade head komutunu calistirin."
            )
        else:
            import sqlite3

            baglanti = sqlite3.connect(f"file:{veritabani}?mode=ro", uri=True)
            try:
                tablolar = {
                    satir[0]
                    for satir in baglanti.execute(
                        "select name from sqlite_master where type='table'"
                    )
                }
            finally:
                baglanti.close()
            eksik = {"energy_type", "meter", "meter_reading"} - tablolar
            if eksik:
                bulgular.append(
                    "Veritabani tablolari olusturulmamis "
                    f"(eksik: {', '.join(sorted(eksik))}).\n"
                    "  Cozum: alembic upgrade head komutunu calistirin.\n"
                    "  Bu adim atlanirsa giris sonrasi 'Internal Server Error' gorursunuz."
                )
    return bulgular


if __name__ == "__main__":
    bulgular = sorunlar()
    if not bulgular:
        raise SystemExit(0)
    print("\nUygulama baslatilamaz. Eksikler:\n")
    for numara, bulgu in enumerate(bulgular, 1):
        print(f"  {numara}. {bulgu}\n")
    print("Ayrintili kurulum adimlari: README.md\n")
    raise SystemExit(1)
