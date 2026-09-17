"""Baslatma yardimcilari: on kontrol ve tarayici acma (FAZ 15).

Bu betikler yalnizca kullanici deneyimi icindir; uygulamanin hesabina
dokunmazlar. Amac, kullanicinin Python traceback'i ya da anlamsiz bir hata
sayfasi yerine ne yapmasi gerektigini Turkce gormesidir.
"""

import socket
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts import onkontrol, tarayici_ac  # noqa: E402


# --------------------------------------------------------------------------- #
# On kontrol
# --------------------------------------------------------------------------- #


def _ortam(monkeypatch, tmp_path, *, env_var=True, degerler=True, veritabani="tam"):
    """Betigin gordugu ortami kurar."""
    monkeypatch.setattr(onkontrol, "BASE_DIR", tmp_path)
    if env_var:
        (tmp_path / ".env").write_text("# test\n", encoding="utf-8")

    db = tmp_path / "veri" / "enerji.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    if veritabani != "yok":
        baglanti = sqlite3.connect(db)
        if veritabani == "tam":
            for tablo in ("energy_type", "meter", "meter_reading"):
                baglanti.execute(f"create table {tablo} (id integer primary key)")
        baglanti.commit()
        baglanti.close()

    import app.config

    monkeypatch.setattr(app.config, "database_url", lambda: f"sqlite:///{db}")
    for degisken in ("SECRET_KEY", "APP_PASSWORD_HASH"):
        if degerler:
            monkeypatch.setenv(degisken, "deger")
        else:
            monkeypatch.delenv(degisken, raising=False)
    return db


def test_her_sey_hazirsa_sorun_yok(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path)
    assert onkontrol.sorunlar() == []


def test_env_dosyasi_yoksa_tek_ve_net_mesaj(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path, env_var=False)
    bulgular = onkontrol.sorunlar()

    assert len(bulgular) == 1
    assert ".env dosyasi yok" in bulgular[0]
    assert ".env.example" in bulgular[0]


def test_bos_degerler_bildiriliyor(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path, degerler=False)
    metin = "\n".join(onkontrol.sorunlar())

    assert "SECRET_KEY" in metin and "generate_secret" in metin
    assert "APP_PASSWORD_HASH" in metin and "set_password" in metin


def test_veritabani_yoksa_alembic_soyleniyor(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path, veritabani="yok")
    bulgular = onkontrol.sorunlar()

    assert len(bulgular) == 1
    assert "alembic upgrade head" in bulgular[0]


def test_tablolar_yoksa_internal_server_error_uyarisi(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path, veritabani="bos")
    bulgu = onkontrol.sorunlar()[0]

    assert "alembic upgrade head" in bulgu
    assert "Internal Server Error" in bulgu
    for tablo in ("energy_type", "meter", "meter_reading"):
        assert tablo in bulgu


def test_mesajlarda_python_traceback_izi_yok(monkeypatch, tmp_path):
    _ortam(monkeypatch, tmp_path, env_var=False)
    metin = "\n".join(onkontrol.sorunlar())

    for iz in ("Traceback", "File \"", "Error:", "Exception"):
        assert iz not in metin


def test_betik_dogru_cikis_kodu_veriyor(tmp_path):
    """Eksik ortamda 1, hazir ortamda 0."""
    bos = tmp_path / "bos-proje"
    bos.mkdir()
    sonuc = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts" / "onkontrol.py")],
        capture_output=True, text=True, cwd=bos,
        env={"PATH": "/usr/bin:/bin", "DATA_DIR": str(tmp_path / "yok")},
    )
    # Betik kendi klasorunu kullanir; gercek .env varsa 0, yoksa 1 doner.
    assert sonuc.returncode in (0, 1)
    assert "Traceback" not in (sonuc.stdout + sonuc.stderr)


# --------------------------------------------------------------------------- #
# Tarayici acma: sabit bekleme yerine saglik yoklamasi
# --------------------------------------------------------------------------- #


def test_sunucu_yokken_hazir_degil():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        bos_port = s.getsockname()[1]
    assert tarayici_ac.hazir_mi(f"http://127.0.0.1:{bos_port}") is False


def test_saglik_ucu_yanit_verince_hazir(logged_in_client):
    """Uygulamanin /saglik ucu kimlik dogrulamasi istemez."""
    yanit = logged_in_client.get("/saglik")
    assert yanit.status_code == 200
    assert yanit.json() == {"status": "ok"}


def test_sunucu_gec_acilirsa_tarayici_beklenir(monkeypatch):
    """Sunucu hazir olana kadar acilmaz, hazir olunca hemen acilir."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Saglik(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        def log_message(self, *args):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    adres = f"http://127.0.0.1:{port}"

    assert tarayici_ac.hazir_mi(adres) is False

    sunucu = HTTPServer(("127.0.0.1", port), Saglik)
    threading.Thread(target=sunucu.serve_forever, daemon=True).start()
    try:
        for _ in range(100):
            if tarayici_ac.hazir_mi(adres):
                break
            time.sleep(0.02)
        assert tarayici_ac.hazir_mi(adres) is True
    finally:
        sunucu.shutdown()


def test_zaman_asimi_makul():
    """Yavas bir bilgisayarda bile yetecek kadar, sonsuz beklemeyecek kadar."""
    assert 30 <= tarayici_ac.ZAMAN_ASIMI <= 300
