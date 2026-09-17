"""Sunucu hazir olunca tarayiciyi acar.

Sabit sure beklemek yerine uygulamanin /saglik ucunu yoklar: yavas bir
bilgisayarda sunucu gec acilirsa tarayici da o kadar gec acilir, erken
acilip "baglanti kurulamadi" sayfasi gostermez.

Arka planda calistirilmak uzere tasarlanmistir:
    start "" /b .venv\\Scripts\\python.exe scripts\\tarayici_ac.py
"""

import sys
import time
import urllib.error
import urllib.request
import webbrowser

ADRES = "http://127.0.0.1:8000"
ZAMAN_ASIMI = 60.0  # saniye


def hazir_mi(adres: str) -> bool:
    try:
        with urllib.request.urlopen(f"{adres}/saglik", timeout=1) as yanit:
            return yanit.status == 200
    except (urllib.error.URLError, OSError):
        return False


if __name__ == "__main__":
    adres = sys.argv[1] if len(sys.argv) > 1 else ADRES
    baslangic = time.monotonic()
    while time.monotonic() - baslangic < ZAMAN_ASIMI:
        if hazir_mi(adres):
            webbrowser.open(adres)
            raise SystemExit(0)
        time.sleep(0.25)
    print(
        f"Sunucu {ZAMAN_ASIMI:.0f} saniye icinde hazir olmadi. "
        f"Tarayicidan {adres} adresini elle acmayi deneyin."
    )
    raise SystemExit(1)
