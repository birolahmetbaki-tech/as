"""Kullaniciya gosterilen hata ve yardim metinleri (FAZ 13 / B, C).

Bu ekranlarda hesaplama yoktur; amac kullanicinin ham Python/FastAPI
ciktisiyla karsilasmamasi ve alanlarin ne istedigini anlamasidir.
"""

import pytest

from app.db import SessionLocal
from app.models import DirectConsumption, Meter, MeterReading, Target
from tests.factories import department, energy_type, meter
from tests.conftest import TEST_PASSWORD  # noqa: F401  (ortam kurulumu icin)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


# --------------------------------------------------------------------------- #
# B1 — bozuk kayit numarasi ham Python hatasi gostermiyor
# --------------------------------------------------------------------------- #

BOZUK_DEGERLER = ("abc", "1; DROP TABLE meter", "١٢٣", "1.5", " ", "-1", "99999")

# Bozuk deger hangi asamada yakalanirsa yakalansin, kullanici bu Turkce
# mesajlardan birini gorur; ham Python/FastAPI ciktisi asla gorunmez.
# ("١٢٣" gibi rakamlari Python int() cozer; o zaman kayit bulunamaz.)
KABUL_EDILEN = (
    "Enerji türü seçilmelidir.",
    "Geçersiz enerji türü seçimi.",
    "Seçilen enerji türü bulunamadı.",
)


@pytest.mark.parametrize("bozuk", BOZUK_DEGERLER)
def test_sayac_formunda_bozuk_enerji_turu(db, logged_in_client, bozuk):
    energy_type(db)
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Deneme", "energy_type_id": bozuk, "multiplier": "1"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert any(mesaj in response.text for mesaj in KABUL_EDILEN), bozuk
    assert db.query(Meter).count() == 0


def test_sayac_formunda_bozuk_bolum(db, logged_in_client):
    energy_type(db)
    department(db)
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Deneme", "energy_type_id": "1", "department_id": "abc",
              "multiplier": "1"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert "Geçersiz bölüm seçimi." in response.text


def test_hedef_formunda_bozuk_enerji_turu(db, logged_in_client):
    energy_type(db)
    response = logged_in_client.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "abc", "target_value": "1.000"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert "Geçersiz enerji türü seçimi." in response.text
    assert db.query(Target).count() == 0


def test_dogrudan_tuketimde_bozuk_enerji_turu(db, logged_in_client):
    energy_type(db)
    response = logged_in_client.post(
        "/dogrudan-tuketim",
        data={"year_month": "2026-01", "energy_type_id": "abc", "quantity": "1.000"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert "Geçersiz enerji türü seçimi." in response.text
    assert db.query(DirectConsumption).count() == 0


def test_okuma_formunda_bozuk_sayac(db, logged_in_client):
    electricity = energy_type(db)
    meter(db, "Ana", electricity, is_main=True)
    response = logged_in_client.post(
        "/okumalar",
        data={"meter_id": "abc", "reading_date": "2026-01-01", "index_value": "100"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert "Geçersiz sayaç seçimi." in response.text
    assert db.query(MeterReading).count() == 0


def test_katsayi_formunda_bozuk_enerji_turu(db, logged_in_client):
    energy_type(db)
    response = logged_in_client.post(
        "/tanimlar/donusum-katsayilari",
        data={"energy_type_id": "abc", "factor": "0,0385", "valid_from": "2026-01-01"},
    )
    assert response.status_code == 400
    assert "invalid literal" not in response.text
    assert "Geçersiz enerji türü seçimi." in response.text


def test_normal_select_kullanimi_bozulmadi(db, logged_in_client):
    """Dogru id ile kayit her zamanki gibi olusur."""
    electricity = energy_type(db)
    press = department(db, name="Pres")
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Pres Panosu", "energy_type_id": str(electricity.id),
              "department_id": str(press.id), "multiplier": "1"},
    )
    assert response.status_code == 200
    db.expire_all()
    kayit = db.query(Meter).one()
    assert kayit.energy_type_id == electricity.id
    assert kayit.department_id == press.id


# --------------------------------------------------------------------------- #
# B2 — adres cubugundaki bozuk deger ham 422 JSON gostermiyor
# --------------------------------------------------------------------------- #


def test_panelde_bozuk_enerji_parametresi_varsayilana_duser(db, logged_in_client):
    electricity = energy_type(db)
    energy_type(db, name="Doğal Gaz", unit="Sm³")

    response = logged_in_client.get("/?enerji=abc")

    assert response.status_code == 200
    assert "int_parsing" not in response.text
    assert "detail" not in response.text[:200]
    # Varsayilan: ilk tanimlanan enerji turu.
    assert electricity.name in response.text


def test_panelde_gecerli_enerji_parametresi_calisiyor(db, logged_in_client):
    energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")

    response = logged_in_client.get(f"/?enerji={gas.id}")

    assert response.status_code == 200
    assert f"Doğal Gaz" in response.text


def test_bozuk_adres_turkce_sayfa_gosteriyor(db, logged_in_client):
    energy_type(db)
    response = logged_in_client.get("/tanimlar/sayaclar/abc")

    assert response.status_code == 400
    assert "int_parsing" not in response.text
    assert "Geçersiz adres" in response.text


# --------------------------------------------------------------------------- #
# C — enerji turu "Birim" alani yardim metni
# --------------------------------------------------------------------------- #


def test_birim_yardim_metni_tanim_ekraninda(db, logged_in_client):
    sayfa = logged_in_client.get("/tanimlar/enerji-turleri").text

    assert "temel tüketim birimidir" in sayfa
    assert "Sm³" in sayfa and "kWh" in sayfa
    assert "dönüşüm katsayısı" in sayfa


def test_birim_yardim_metni_duzenleme_ekraninda(db, logged_in_client):
    electricity = energy_type(db)
    sayfa = logged_in_client.get(f"/tanimlar/enerji-turleri/{electricity.id}").text

    assert "temel tüketim birimidir" in sayfa
    assert "dönüşüm katsayısı" in sayfa
