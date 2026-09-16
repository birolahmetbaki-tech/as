"""Maliyet hesabi ve aylik hedefler."""

import pytest

from app import calc, dashboard
from app.db import SessionLocal
from app.models import Target
from tests.factories import energy_type, meter, readings


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _add_target(client, year_month="2026-01", energy_type_id="1", value="17000"):
    return client.post(
        "/hedefler",
        data={
            "year_month": year_month,
            "energy_type_id": energy_type_id,
            "target_value": value,
        },
    )


# --------------------------------------------------------------------------- #
# Maliyet
# --------------------------------------------------------------------------- #


def test_maliyet_hesabi():
    """18.400 kWh x 2,85 TL/kWh = 52.440 TL"""
    assert calc.cost(18_400, 2.85) == pytest.approx(52_440)


def test_tuketim_yokken_maliyet_sifirdir():
    assert calc.cost(0, 2.85) == pytest.approx(0)


def test_farkli_enerji_turlerinde_maliyetler_karismaz(db):
    electricity = energy_type(db, price=2.85)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=12.0)
    electric_meter = meter(db, "Elektrik Ana", electricity, is_main=True)
    gas_meter = meter(db, "Gaz Sayacı", gas)
    readings(db, electric_meter, {"2025-12-31": 0, "2026-01-31": 10_000})
    readings(db, gas_meter, {"2025-12-31": 0, "2026-01-31": 1_000})

    electric = dashboard.energy_summary(db, electricity, "2026-01")
    gas_summary = dashboard.energy_summary(db, gas, "2026-01")

    assert electric["cost"] == pytest.approx(10_000 * 2.85)
    assert gas_summary["cost"] == pytest.approx(1_000 * 12.0)


def test_birim_fiyat_degisince_gecmis_maliyet_de_degisir(db):
    """Bilinen tasarim sinirlamasi: gecmis fiyat takibi yoktur.

    Birim fiyat guncel fiyattir; degistirildiginde gecmis donemlerin maliyeti
    de yeni fiyatla hesaplanir.
    """
    electricity = energy_type(db, price=2.85)
    electric_meter = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, electric_meter, {"2025-12-31": 0, "2026-01-31": 10_000})

    assert dashboard.energy_summary(db, electricity, "2026-01")["cost"] == pytest.approx(
        28_500
    )

    electricity.unit_price = 3.20
    db.commit()

    assert dashboard.energy_summary(db, electricity, "2026-01")["cost"] == pytest.approx(
        32_000
    )


# --------------------------------------------------------------------------- #
# Hedef durumu (calc)
# --------------------------------------------------------------------------- #


def test_hedef_asildiginda_isaretlenir():
    status = calc.target_status(18_400, 17_000)
    assert status["exceeded"] is True
    assert status["percent"] == pytest.approx(108.2, abs=0.05)
    assert status["difference"] == pytest.approx(1_400)


def test_hedefin_altinda_kalinca_asilmis_sayilmaz():
    status = calc.target_status(16_000, 17_000)
    assert status["exceeded"] is False
    assert status["percent"] == pytest.approx(94.1, abs=0.05)
    assert status["difference"] == pytest.approx(-1_000)


def test_hedefe_tam_esitlik_asim_sayilmaz():
    status = calc.target_status(17_000, 17_000)
    assert status["exceeded"] is False
    assert status["percent"] == pytest.approx(100)


def test_gecersiz_hedef_gosterge_uretmez():
    assert calc.target_status(1_000, 0) is None
    assert calc.target_status(1_000, -5) is None


# --------------------------------------------------------------------------- #
# Hedef ekrani
# --------------------------------------------------------------------------- #


def test_hedef_ekrani_giris_gerektirir(client):
    response = client.get("/hedefler", follow_redirects=False)
    assert response.status_code == 303


def test_enerji_turu_yoksa_uyari_gosterilir(logged_in_client):
    response = logged_in_client.get("/hedefler")
    assert "önce bir" in response.text


def test_hedef_eklenir(logged_in_client, db):
    energy_type(db, price=2.85)
    response = _add_target(logged_in_client, value="17000")
    assert response.status_code == 200
    assert "Ocak 2026" in response.text
    assert "17.000,00" in response.text

    with SessionLocal() as session:
        target = session.get(Target, 1)
        assert target.year_month == "2026-01"
        assert target.target_value == pytest.approx(17_000)


def test_virgullu_hedef_kabul_edilir(logged_in_client, db):
    energy_type(db)
    _add_target(logged_in_client, value="17500,5")
    with SessionLocal() as session:
        assert session.get(Target, 1).target_value == pytest.approx(17_500.5)


def test_gelecek_ay_icin_hedef_girilebilir(logged_in_client, db):
    """Hedefler ileriye donuktur; gelecek ay engellenmez."""
    energy_type(db)
    response = _add_target(logged_in_client, year_month="2030-06")
    assert response.status_code == 200
    assert "Haziran 2030" in response.text


def test_ayni_ay_ve_enerji_turune_ikinci_hedef_engellenir(logged_in_client, db):
    energy_type(db)
    _add_target(logged_in_client, value="17000")
    response = _add_target(logged_in_client, value="18000")
    assert response.status_code == 400
    assert "zaten tanımlı" in response.text

    with SessionLocal() as session:
        assert session.query(Target).count() == 1


def test_ayni_ayda_farkli_enerji_turune_hedef_girilebilir(logged_in_client, db):
    energy_type(db)
    energy_type(db, name="Doğal Gaz", unit="Sm³")
    _add_target(logged_in_client, energy_type_id="1")
    response = _add_target(logged_in_client, energy_type_id="2", value="5000")
    assert response.status_code == 200

    with SessionLocal() as session:
        assert session.query(Target).count() == 2


def test_sifir_hedef_reddedilir(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, value="0")
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text


def test_negatif_hedef_reddedilir(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, value="-100")
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text


def test_ay_zorunludur(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, year_month="")
    assert response.status_code == 400
    assert "Ay alanı boş bırakılamaz" in response.text


def test_gecersiz_ay_reddedilir(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, year_month="2026-13")
    assert response.status_code == 400
    assert "geçerli bir ay olmalıdır" in response.text


def test_enerji_turu_secilmeden_hedef_girilemez(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, energy_type_id="")
    assert response.status_code == 400
    assert "Enerji türü seçilmelidir" in response.text


def test_hata_durumunda_girilen_degerler_korunur(logged_in_client, db):
    energy_type(db)
    response = _add_target(logged_in_client, year_month="2026-03", value="-5")
    assert response.status_code == 400
    assert 'value="2026-03"' in response.text
    assert 'value="-5"' in response.text


# --------------------------------------------------------------------------- #
# Panel
# --------------------------------------------------------------------------- #


@pytest.fixture
def fabrika(db):
    electricity = energy_type(db, price=2.85)
    main = meter(db, "Ana Trafo", electricity, multiplier=40, is_main=True)
    readings(db, main, {"2025-12-31": 1000, "2026-01-31": 1460})
    return electricity


def test_panelde_maliyet_gosterilir(logged_in_client, db, fabrika):
    response = logged_in_client.get("/?donem=2026-01")
    assert "Enerji maliyeti" in response.text
    assert "52.440,00" in response.text  # 18.400 x 2,85


def test_panelde_hedef_karti_asimda_uyarir(logged_in_client, db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=17_000))
    db.commit()

    response = logged_in_client.get("/?donem=2026-01")
    assert "Aylık hedef" in response.text
    assert "17.000,00" in response.text
    assert "108,2%" in response.text
    assert "hedef aşıldı" in response.text


def test_panelde_hedef_icindeyse_boyle_yazilir(logged_in_client, db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=20_000))
    db.commit()

    response = logged_in_client.get("/?donem=2026-01")
    assert "hedef içinde" in response.text
    assert "hedef aşıldı" not in response.text


def test_hedefi_olmayan_ayda_kart_gosterilmez(logged_in_client, db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=17_000))
    db.commit()

    response = logged_in_client.get("/?donem=2025-12")
    assert "Aylık hedef" not in response.text
