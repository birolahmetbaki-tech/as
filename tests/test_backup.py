"""Yedekleme ve geri yukleme betikleri (FAZ 14).

Uygulamanin en degerli varligi tek bir SQLite dosyasidir. Uygulama WAL
kipinde calistigi icin bu dosyanin DUZ KOPYASI yedek olarak yeterli degildir:
henuz ana dosyaya islenmemis kayitlar -wal dosyasinda bekler. Betikler
SQLite'in kendi yedekleme arayuzunu kullanir; bu testler farkin gercekten
onemli oldugunu ve betiklerin dogru calistigini dogrular.
"""

import shutil
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app import calc
from app.db import SessionLocal, engine
from app.models import Department, EnergyType
from scripts.backup import backup
from scripts.restore import BEKLENEN_TABLOLAR, restore, tablolar, yedekleri_listele
from tests.factories import (
    conversion,
    direct_consumption,
    energy_type,
    meter,
    production,
    readings,
)

OCAK = (date(2026, 1, 1), date(2026, 1, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def db_yolu() -> Path:
    """Test veritabaninin diskteki yolu."""
    return Path(engine.url.database)


def _gercekci_veri(db):
    """Kucuk ama her ozelligi kullanan bir veri seti."""
    electricity = energy_type(db, price=5.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    db.add(Department(name="Pres", is_active=True))
    db.commit()
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 10_000})
    direct_consumption(db, gas, "2026-01", 10_000)
    conversion(db, gas, 0.0385, "2026-01-01", source="Tedarikçi")
    production(db, {"2026-01-31": (100, "ton")})
    return electricity, gas


def _ozet(db) -> dict:
    """Yedek oncesi/sonrasi karsilastirilacak sonuclar."""
    db.expire_all()
    toplam = calc.energy_totals(db, *OCAK, to_unit="GJ")
    return {
        "elektrik": calc.total(calc.factory_consumptions(db, *OCAK, energy_type_id=1)),
        "gaz": calc.total(calc.factory_consumptions(db, *OCAK, energy_type_id=2)),
        "maliyet": calc.cost(
            calc.total(calc.factory_consumptions(db, *OCAK, energy_type_id=1)), 5.0
        ),
        "gj": toplam["value"],
        "tep": calc.energy_totals(db, *OCAK, to_unit="TEP")["value"],
        "enpi": calc.combined_enpi(db, "ton", *OCAK, to_unit="GJ")["value"],
        "bolumler": sorted(b.name for b in db.query(Department).all()),
    }


# --------------------------------------------------------------------------- #
# WAL: duz dosya kopyasi neden yeterli degil
# --------------------------------------------------------------------------- #


def test_veritabani_wal_kipinde_calisiyor(db_yolu):
    with sqlite3.connect(db_yolu) as baglanti:
        assert baglanti.execute("pragma journal_mode").fetchone()[0].lower() == "wal"


def test_duz_dosya_kopyasi_eksik_kalabilir(db, db_yolu, tmp_path):
    """Acik baglanti varken yalnizca .db kopyalanirsa kayitlar eksik kalir."""
    for numara in range(20):
        db.add(Department(name=f"Bölüm {numara:02d}", is_active=True))
    db.commit()
    gercek = db.query(Department).count()

    duz = tmp_path / "duz.db"
    shutil.copy2(db_yolu, duz)
    try:
        kopyadaki = sqlite3.connect(duz).execute(
            "select count(*) from department"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        # Eksikligin en uc hali: tablo bile kopyaya girmemis.
        kopyadaki = None

    # Bu testin amaci kopyanin her zaman bos cikmasi degil, yedek olarak
    # GUVENILMEZ olmasidir: -wal dosyasindaki kayitlar kopyaya girmez.
    assert kopyadaki is None or kopyadaki < gercek
    assert Path(str(db_yolu) + "-wal").exists()
    # Ayni anda betik yedegi tam veriyi getirir.
    assert sqlite3.connect(backup(db_yolu, tmp_path)).execute(
        "select count(*) from department"
    ).fetchone()[0] == gercek


def test_betik_yedegi_uygulama_acikken_de_tam(db, db_yolu, tmp_path):
    for numara in range(20):
        db.add(Department(name=f"Bölüm {numara:02d}", is_active=True))
    db.commit()
    gercek = db.query(Department).count()

    hedef = backup(db_yolu, tmp_path)
    yedekteki = sqlite3.connect(hedef).execute(
        "select count(*) from department"
    ).fetchone()[0]

    assert yedekteki == gercek == 20


# --------------------------------------------------------------------------- #
# Yedek dosyasi
# --------------------------------------------------------------------------- #


def test_yedek_tek_dosya_olarak_olusuyor(db, db_yolu, tmp_path):
    _gercekci_veri(db)
    hedef = backup(db_yolu, tmp_path)

    assert hedef.is_file()
    assert hedef.name.startswith("enerji-") and hedef.suffix == ".db"
    assert not Path(str(hedef) + "-wal").exists()
    assert not Path(str(hedef) + "-shm").exists()


def test_ayni_dakikada_ikinci_yedek_ustune_yazmiyor(db, db_yolu, tmp_path):
    ilk = backup(db_yolu, tmp_path)
    ikinci = backup(db_yolu, tmp_path)

    assert ilk != ikinci
    assert ilk.is_file() and ikinci.is_file()


def test_yedek_klasoru_yoksa_olusturuluyor(db, db_yolu, tmp_path):
    klasor = tmp_path / "olmayan" / "klasor"
    hedef = backup(db_yolu, klasor)

    assert hedef.is_file()
    assert yedekleri_listele(klasor) == [hedef]


def test_yedek_uygulamanin_butun_tablolarini_iceriyor(db, db_yolu, tmp_path):
    from app.db import Base

    _gercekci_veri(db)
    hedef = backup(db_yolu, tmp_path)

    yedekteki = tablolar(hedef)
    assert set(Base.metadata.tables) <= yedekteki
    # Geri yuklemede kullanilan dogrulama da gecmeli.
    assert BEKLENEN_TABLOLAR <= yedekteki


# --------------------------------------------------------------------------- #
# Geri yukleme
# --------------------------------------------------------------------------- #


def test_geri_yukleme_sonuclari_aynen_getiriyor(db, db_yolu, tmp_path):
    _gercekci_veri(db)
    once = _ozet(db)
    assert once["gj"] == pytest.approx(36 + 385)

    hedef = backup(db_yolu, tmp_path)

    # Kullanici yanlis veri giriyor.
    gas = db.get(EnergyType, 2)
    direct_consumption(db, gas, "2025-11", 999_999)
    db.add(Department(name="Yanlış Bölüm", is_active=True))
    db.commit()
    bozuk = _ozet(db)
    assert bozuk["bolumler"] != once["bolumler"]

    # Yedek geri yuklenir.
    engine.dispose()
    restore(hedef, db_yolu)

    with SessionLocal() as taze:
        sonra = _ozet(taze)
    assert sonra == once


def test_yanlis_dosya_yedek_olarak_taninmiyor(tmp_path):
    sahte = tmp_path / "rastgele.db"
    sqlite3.connect(sahte).execute("create table baska (id integer)")

    assert not BEKLENEN_TABLOLAR <= tablolar(sahte)


def test_sqlite_olmayan_dosya_hata_veriyor(tmp_path):
    metin = tmp_path / "not.txt"
    metin.write_text("bu bir veritabanı değil", encoding="utf-8")

    with pytest.raises(sqlite3.DatabaseError):
        tablolar(metin)


def test_yedekler_en_yeni_ustte_listeleniyor(db, db_yolu, tmp_path):
    import os
    import time

    ilk = backup(db_yolu, tmp_path)
    time.sleep(0.01)
    ikinci = backup(db_yolu, tmp_path)
    os.utime(ikinci, (time.time() + 10, time.time() + 10))

    assert yedekleri_listele(tmp_path)[0] == ikinci
    assert set(yedekleri_listele(tmp_path)) == {ilk, ikinci}


def test_bos_klasorde_yedek_listesi_bos(tmp_path):
    assert yedekleri_listele(tmp_path / "hic-yok") == []
