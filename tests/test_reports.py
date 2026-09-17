"""Rapor ekrani: mevcut hesaplama cekirdeginin kullaniciya sunulmasi."""

from datetime import date

import pytest

from app import reports
from app.db import SessionLocal
from app.models import Target
from tests.factories import department, energy_type, meter, production, readings

START = "2026-01-01"
END = "2026-01-31"


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def fabrika(db):
    """Ocak 2026: fabrika 18.400 kWh, Üretim 12.000, Paketleme 3.500."""
    electricity = energy_type(db, price=2.85)
    production_dept = department(db, "Üretim")
    packaging = department(db, "Paketleme")

    main = meter(db, "Ana Trafo", electricity, multiplier=40, is_main=True)
    production_meter = meter(db, "Üretim Panosu", electricity, production_dept)
    packaging_meter = meter(db, "Paketleme Panosu", electricity, packaging)

    readings(db, main, {"2026-01-01": 1000, "2026-02-01": 1460})
    readings(db, production_meter, {"2026-01-01": 0, "2026-02-01": 12000})
    readings(db, packaging_meter, {"2026-01-01": 0, "2026-02-01": 3500})
    return electricity


def _report(client, start=START, end=END, breakdown="enerji"):
    return client.get(f"/rapor?baslangic={start}&bitis={end}&kirilim={breakdown}")


# --------------------------------------------------------------------------- #
# Erisim ve varsayilanlar
# --------------------------------------------------------------------------- #


def test_rapor_giris_gerektirir(client):
    response = client.get("/rapor", follow_redirects=False)
    assert response.status_code == 303


def test_varsayilan_aralik_ayin_basindan_bugune(logged_in_client):
    start, end = reports.default_range()
    assert start.day == 1
    assert end == date.today()
    assert start.month == date.today().month


def test_gecersiz_aralik_uyari_verir(logged_in_client, db, fabrika):
    response = logged_in_client.get("/rapor?baslangic=2026-03-01&bitis=2026-01-01")
    assert response.status_code == 200
    assert "bitiş tarihinden sonra olamaz" in response.text


def test_bilinmeyen_kirilim_enerji_turune_doner(logged_in_client, db, fabrika):
    response = _report(logged_in_client, breakdown="uzay")
    assert "Kırılım: Enerji türü" in response.text


# --------------------------------------------------------------------------- #
# Enerji turu kirilimi
# --------------------------------------------------------------------------- #


def test_enerji_turu_kirilimi(db, fabrika):
    rows = reports.rows_by_energy_type(db, date(2026, 1, 1), date(2026, 1, 31))
    assert len(rows) == 1
    assert rows[0]["total"] == pytest.approx(18_400)
    assert rows[0]["cost"] == pytest.approx(18_400 * 2.85)


def test_coklu_enerji_turu_kirilimi(db, fabrika):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=12.0)
    gas_meter = meter(db, "Kazan Gaz Sayacı", gas)
    readings(db, gas_meter, {"2026-01-01": 8000, "2026-02-01": 9200})

    rows = reports.rows_by_energy_type(db, date(2026, 1, 1), date(2026, 1, 31))
    totals = {row["energy_type"].name: row["total"] for row in rows}
    assert totals == {"Elektrik": pytest.approx(18_400), "Doğal Gaz": pytest.approx(1_200)}


def test_tarih_araligi_disindaki_tuketim_rapora_girmez(db, fabrika):
    rows = reports.rows_by_energy_type(db, date(2026, 2, 1), date(2026, 2, 28))
    assert rows[0]["total"] == pytest.approx(0)


def test_ocak_tuketimi_1_subat_okumasiyla_hesaplanir(db, fabrika):
    """Donem kurali: 01.01 -> 01.02 arasindaki tuketim Ocak ayina aittir."""
    rows = reports.rows_by_energy_type(db, date(2026, 1, 1), date(2026, 1, 31))
    assert rows[0]["total"] == pytest.approx(18_400)


# --------------------------------------------------------------------------- #
# Sayac kirilimi
# --------------------------------------------------------------------------- #


def test_sayac_kirilimi(db, fabrika):
    rows = reports.rows_by_meter(db, date(2026, 1, 1), date(2026, 1, 31))
    totals = {row["meter"].name: row["total"] for row in rows}
    assert totals == {
        "Ana Trafo": pytest.approx(18_400),
        "Üretim Panosu": pytest.approx(12_000),
        "Paketleme Panosu": pytest.approx(3_500),
    }


def test_tuketimi_olmayan_sayac_listelenmez(db, fabrika):
    meter(db, "Yeni Sayaç", fabrika)
    rows = reports.rows_by_meter(db, date(2026, 1, 1), date(2026, 1, 31))
    assert "Yeni Sayaç" not in {row["meter"].name for row in rows}


def test_sayac_raporunda_maliyet_kendi_enerji_turunden_gelir(db, fabrika):
    rows = reports.rows_by_meter(db, date(2026, 1, 1), date(2026, 1, 31))
    ana = next(row for row in rows if row["meter"].name == "Ana Trafo")
    assert ana["cost"] == pytest.approx(18_400 * 2.85)


def test_sayac_raporunda_genel_toplam_gosterilmez(logged_in_client, db, fabrika):
    response = _report(logged_in_client, breakdown="sayac")
    assert "genel toplam gösterilmez" in response.text


# --------------------------------------------------------------------------- #
# Bolum kirilimi
# --------------------------------------------------------------------------- #


def test_bolum_kirilimi_ana_sayaci_ikinci_kez_saymaz(db, fabrika):
    sections = reports.rows_by_department(db, date(2026, 1, 1), date(2026, 1, 31))
    assert len(sections) == 1

    section = sections[0]
    rows = {row["label"]: row["value"] for row in section["breakdown"]["rows"]}
    assert section["factory_total"] == pytest.approx(18_400)
    assert rows["Üretim"] == pytest.approx(12_000)
    assert rows["Paketleme"] == pytest.approx(3_500)
    assert "Ana Trafo" not in rows


def test_bolum_satirlarinin_toplami_fabrika_toplamina_esittir(db, fabrika):
    section = reports.rows_by_department(db, date(2026, 1, 1), date(2026, 1, 31))[0]
    toplam = sum(row["value"] for row in section["breakdown"]["rows"])
    assert toplam == pytest.approx(section["factory_total"])
    assert section["breakdown"]["unmeasured"] == pytest.approx(2_900)


def test_veri_olmayan_enerji_turu_bolum_raporuna_girmez(db, fabrika):
    energy_type(db, name="Su", unit="m³")
    sections = reports.rows_by_department(db, date(2026, 1, 1), date(2026, 1, 31))
    assert [section["energy_type"].name for section in sections] == ["Elektrik"]


# --------------------------------------------------------------------------- #
# Uretim ve EnPI
# --------------------------------------------------------------------------- #


def test_uretim_ve_enpi_satirlari(db, fabrika):
    production(db, {"2026-01-31": (184, "ton")})

    rows = reports.production_rows(db, date(2026, 1, 1), date(2026, 1, 31))
    assert len(rows) == 1
    assert rows[0]["unit"] == "ton"
    assert rows[0]["production"] == pytest.approx(184)
    assert rows[0]["enpi"] == pytest.approx(100)  # 18.400 / 184


def test_uretim_birimleri_ayri_satirlarda_kalir(db, fabrika):
    production(db, {"2026-01-31": (184, "ton"), "2026-01-30": (2000, "adet")})

    rows = reports.production_rows(db, date(2026, 1, 1), date(2026, 1, 31))
    enpi_by_unit = {row["unit"]: row["enpi"] for row in rows}
    assert enpi_by_unit["ton"] == pytest.approx(100)
    assert enpi_by_unit["adet"] == pytest.approx(9.2)


def test_uretim_yoksa_uretim_bolumu_bos_kalir(db, fabrika):
    assert reports.production_rows(db, date(2026, 1, 1), date(2026, 1, 31)) == []


# --------------------------------------------------------------------------- #
# Hedef
# --------------------------------------------------------------------------- #


def test_hedef_satirlari(db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=17_000))
    db.commit()

    rows = reports.target_rows(db, date(2026, 1, 1), date(2026, 1, 31))
    assert len(rows) == 1
    assert rows[0]["label"] == "Ocak 2026"
    assert rows[0]["status"]["actual"] == pytest.approx(18_400)
    assert rows[0]["status"]["percent"] == pytest.approx(108.2, abs=0.05)
    assert rows[0]["status"]["exceeded"] is True


def test_yarim_kalan_ay_hedefi_raporlanmaz(db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=17_000))
    db.commit()

    rows = reports.target_rows(db, date(2026, 1, 10), date(2026, 1, 31))
    assert rows == []


def test_hedefi_olmayan_aralik_bos_doner(db, fabrika):
    assert reports.target_rows(db, date(2026, 1, 1), date(2026, 1, 31)) == []


# --------------------------------------------------------------------------- #
# Ekran
# --------------------------------------------------------------------------- #


def test_bos_veride_rapor_cokmez(logged_in_client):
    response = _report(logged_in_client)
    assert response.status_code == 200
    assert "tüketim verisi yok" in response.text


def test_raporda_tuketim_ve_maliyet_gosterilir(logged_in_client, db, fabrika):
    response = _report(logged_in_client)
    assert "18.400,00" in response.text
    assert "52.440,00" in response.text


def test_bolum_raporu_ekranda(logged_in_client, db, fabrika):
    response = _report(logged_in_client, breakdown="bolum")
    assert "Ölçülmeyen / dağıtılmamış" in response.text
    assert "2.900,00" in response.text
    assert "Fabrika toplamı" in response.text


def test_sayac_raporu_ekranda(logged_in_client, db, fabrika):
    response = _report(logged_in_client, breakdown="sayac")
    assert "Ana Trafo" in response.text
    assert "Üretim Panosu" in response.text
