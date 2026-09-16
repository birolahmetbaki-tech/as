"""Gosterge paneli: donem ozeti, bolum dagilimi, olculmeyen pay, trend."""

import pytest

from app import dashboard
from app.db import SessionLocal
from app.models import Target
from tests.factories import department, energy_type, meter, production, readings


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def fabrika(db):
    """Sartnamedeki ornek: fabrika 18.400, Üretim 12.000, Paketleme 3.500.

    Ana Trafo carpani 40. Aralik 2025 tuketimi 4.000 (karsilastirma icin).
    """
    electricity = energy_type(db, price=2.85)
    production = department(db, "Üretim")
    packaging = department(db, "Paketleme")

    main = meter(db, "Ana Trafo", electricity, multiplier=40, is_main=True)
    production_meter = meter(db, "Üretim Sayacı", electricity, production)
    packaging_meter = meter(db, "Paketleme Sayacı", electricity, packaging)

    readings(db, main, {"2025-11-30": 900, "2025-12-31": 1000, "2026-01-31": 1460})
    readings(db, production_meter, {"2025-12-31": 0, "2026-01-31": 12000})
    readings(db, packaging_meter, {"2025-12-31": 0, "2026-01-31": 3500})
    return electricity


# --------------------------------------------------------------------------- #
# Donem yardimcilari
# --------------------------------------------------------------------------- #


def test_ay_sinirlari():
    assert dashboard.month_bounds("2026-02")[1].isoformat() == "2026-02-28"
    assert dashboard.month_bounds("2024-02")[1].isoformat() == "2024-02-29"


def test_ay_kaydirma():
    assert dashboard.shift_month("2026-01", -1) == "2025-12"
    assert dashboard.shift_month("2026-12", 1) == "2027-01"
    assert dashboard.shift_month("2026-06", -11) == "2025-07"


def test_ay_etiketi():
    assert dashboard.month_label("2026-01") == "Ocak 2026"


# --------------------------------------------------------------------------- #
# Donem toplami ve karsilastirma
# --------------------------------------------------------------------------- #


def test_donem_toplami_ana_sayactan_gelir(db, fabrika):
    summary = dashboard.energy_summary(db, fabrika, "2026-01")
    assert summary["total"] == pytest.approx(18_400)


def test_onceki_donem_karsilastirmasi(db, fabrika):
    change = dashboard.energy_summary(db, fabrika, "2026-01")["change"]
    assert change["previous"] == pytest.approx(4_000)
    assert change["difference"] == pytest.approx(14_400)
    assert change["percent"] == pytest.approx(360)


def test_onceki_donemde_veri_yoksa_yuzde_hesaplanmaz(db, fabrika):
    change = dashboard.energy_summary(db, fabrika, "2025-12")["change"]
    assert change["previous"] == pytest.approx(0)
    assert change["percent"] is None


def test_maliyet_birim_fiyatla_hesaplanir(db, fabrika):
    summary = dashboard.energy_summary(db, fabrika, "2026-01")
    assert summary["cost"] == pytest.approx(18_400 * 2.85)


# --------------------------------------------------------------------------- #
# Bolum dagilimi ve olculmeyen pay
# --------------------------------------------------------------------------- #


def test_bolum_dagilimi_ana_sayaci_ikinci_kez_saymaz(db, fabrika):
    breakdown = dashboard.department_breakdown(db, fabrika, *dashboard.month_bounds("2026-01"), 18_400)
    measured = {row["label"]: row["value"] for row in breakdown["rows"] if row["measured"]}

    assert measured == {
        "Üretim": pytest.approx(12_000),
        "Paketleme": pytest.approx(3_500),
    }
    assert breakdown["measured"] == pytest.approx(15_500)
    assert "Ana Trafo" not in measured


def test_olculmeyen_pay_dogru_hesaplanir(db, fabrika):
    breakdown = dashboard.department_breakdown(db, fabrika, *dashboard.month_bounds("2026-01"), 18_400)
    assert breakdown["unmeasured"] == pytest.approx(2_900)

    unmeasured_rows = [row for row in breakdown["rows"] if not row["measured"]]
    assert len(unmeasured_rows) == 1
    assert unmeasured_rows[0]["label"] == "Ölçülmeyen / dağıtılmamış"
    assert unmeasured_rows[0]["value"] == pytest.approx(2_900)
    assert breakdown["scope_warning"] is False


def test_bolum_toplami_fabrika_toplamini_asarsa_uyari_verilir(db):
    """Negatif fark normal tuketim gibi gosterilmez."""
    electricity = energy_type(db)
    production = department(db, "Üretim")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Üretim Sayacı", electricity, production)
    readings(db, main, {"2026-01-01": 0, "2026-01-31": 1000})
    readings(db, sub, {"2026-01-01": 0, "2026-01-31": 1500})

    breakdown = dashboard.department_breakdown(db, electricity, *dashboard.month_bounds("2026-01"), 1000)
    assert breakdown["unmeasured"] == pytest.approx(-500)
    assert breakdown["scope_warning"] is True
    assert all(row["measured"] for row in breakdown["rows"])


def test_bolumu_olmayan_alt_sayac_dagilima_girmez(db):
    """Bolume bagli olmayan alt sayac olculmeyen payin icinde kalir."""
    electricity = energy_type(db)
    production = department(db, "Üretim")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Üretim Sayacı", electricity, production)
    loose = meter(db, "Bölümsüz Sayaç", electricity)
    readings(db, main, {"2026-01-01": 0, "2026-01-31": 1000})
    readings(db, sub, {"2026-01-01": 0, "2026-01-31": 600})
    readings(db, loose, {"2026-01-01": 0, "2026-01-31": 200})

    breakdown = dashboard.department_breakdown(db, electricity, *dashboard.month_bounds("2026-01"), 1000)
    assert [row["label"] for row in breakdown["rows"]] == [
        "Üretim",
        "Ölçülmeyen / dağıtılmamış",
    ]
    assert breakdown["unmeasured"] == pytest.approx(400)


# --------------------------------------------------------------------------- #
# Enerji turleri
# --------------------------------------------------------------------------- #


def test_enerji_turu_toplamlari_karismaz(db, fabrika):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=12.0)
    gas_meter = meter(db, "Kazan Gaz Sayacı", gas)
    readings(db, gas_meter, {"2025-12-31": 8000, "2026-01-31": 9200})

    electricity_summary = dashboard.energy_summary(db, fabrika, "2026-01")
    gas_summary = dashboard.energy_summary(db, gas, "2026-01")

    assert electricity_summary["total"] == pytest.approx(18_400)
    assert gas_summary["total"] == pytest.approx(1_200)
    assert gas_summary["cost"] == pytest.approx(1_200 * 12)


# --------------------------------------------------------------------------- #
# Hedef
# --------------------------------------------------------------------------- #


def test_hedef_yoksa_kart_gosterilmez(db, fabrika):
    assert dashboard.energy_summary(db, fabrika, "2026-01")["target"] is None


def test_hedef_asildiginda_isaretlenir(db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=16_000))
    db.commit()

    target = dashboard.energy_summary(db, fabrika, "2026-01")["target"]
    assert target["target"] == pytest.approx(16_000)
    assert target["percent"] == pytest.approx(115, abs=0.1)
    assert target["exceeded"] is True


def test_hedefin_altinda_kalindiginda_asilmis_sayilmaz(db, fabrika):
    db.add(Target(year_month="2026-01", energy_type_id=fabrika.id, target_value=20_000))
    db.commit()

    target = dashboard.energy_summary(db, fabrika, "2026-01")["target"]
    assert target["exceeded"] is False
    assert target["percent"] == pytest.approx(92, abs=0.1)


# --------------------------------------------------------------------------- #
# Trend
# --------------------------------------------------------------------------- #


def test_trend_son_12_ayi_kapsar(db, fabrika):
    trend = dashboard.monthly_trend(db, fabrika, "2026-01")
    assert len(trend) == 12
    assert trend[0]["month"] == "2025-02"
    assert trend[-1]["month"] == "2026-01"
    assert trend[-1]["selected"] is True


def test_trend_degerleri_aylik_tuketimi_verir(db, fabrika):
    values = {
        point["month"]: point["value"]
        for point in dashboard.monthly_trend(db, fabrika, "2026-01")
    }
    assert values["2026-01"] == pytest.approx(18_400)
    assert values["2025-12"] == pytest.approx(4_000)
    assert values["2025-10"] == pytest.approx(0)


# --------------------------------------------------------------------------- #
# Ekran
# --------------------------------------------------------------------------- #


def test_panel_giris_gerektirir(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303


def test_veri_yokken_yonlendirme_mesaji_gosterilir(logged_in_client):
    response = logged_in_client.get("/")
    assert response.status_code == 200
    assert "Başlamak için önce bir" in response.text


def test_tanim_var_okuma_yokken_panel_cokmez(logged_in_client):
    logged_in_client.post(
        "/tanimlar/enerji-turleri",
        data={"name": "Elektrik", "unit": "kWh", "unit_price": "2,5"},
    )
    response = logged_in_client.get("/")
    assert response.status_code == 200
    assert "0,00" in response.text
    assert "tüketim verisi yok" in response.text


def test_panelde_donem_rakamlari_gosterilir(logged_in_client, db, fabrika):
    response = logged_in_client.get("/?donem=2026-01")
    assert response.status_code == 200
    assert "18.400,00" in response.text  # fabrika toplami
    assert "12.000,00" in response.text  # Üretim
    assert "2.900,00" in response.text  # olculmeyen
    assert "Ocak 2026" in response.text


def test_gecersiz_donem_bugune_doner(logged_in_client, db, fabrika):
    response = logged_in_client.get("/?donem=abc")
    assert response.status_code == 200
    assert dashboard.month_label(dashboard._valid_month("abc")) in response.text


def test_enerji_turu_secilebilir(logged_in_client, db, fabrika):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=12.0)
    gas_meter = meter(db, "Kazan Gaz Sayacı", gas)
    readings(db, gas_meter, {"2025-12-31": 8000, "2026-01-31": 9200})

    response = logged_in_client.get(f"/?donem=2026-01&enerji={gas.id}")
    assert "Ocak 2026 · Doğal Gaz" in response.text
    assert "1.200,00" in response.text


# --------------------------------------------------------------------------- #
# Uretim ve EnPI
# --------------------------------------------------------------------------- #


def test_donem_uretimi_ve_enpi(db, fabrika):
    production(db, {"2026-01-15": (100, "ton"), "2026-01-31": (84, "ton")})

    summary = dashboard.production_summary(db, "ton", "2026-01", 18_400)
    assert summary["total"] == pytest.approx(184)
    assert summary["enpi"] == pytest.approx(100)  # 18.400 / 184


def test_uretim_yokken_enpi_tanimsiz(db, fabrika):
    summary = dashboard.production_summary(db, "ton", "2026-01", 18_400)
    assert summary["total"] == pytest.approx(0)
    assert summary["enpi"] is None


def test_enpi_trendi_son_12_ayi_kapsar(db, fabrika):
    production(db, {"2025-12-31": (50, "ton"), "2026-01-31": (184, "ton")})

    trend = dashboard.enpi_trend(db, fabrika, "ton", "2026-01")
    points = trend["points"]
    values = {point["month"]: point["value"] for point in points}
    assert len(points) == 12
    assert trend["low"] == pytest.approx(80)
    assert trend["high"] == pytest.approx(100)
    assert values["2026-01"] == pytest.approx(100)  # 18.400 / 184
    assert values["2025-12"] == pytest.approx(80)  # 4.000 / 50
    assert values["2025-11"] is None  # üretim yok
    assert points[-1]["selected"] is True


def test_panelde_uretim_ve_enpi_gosterilir(logged_in_client, db, fabrika):
    production(db, {"2026-01-31": (184, "ton")})

    response = logged_in_client.get("/?donem=2026-01")
    assert response.status_code == 200
    assert "Enerji performansı" in response.text
    assert "kWh/ton" in response.text
    assert "184,00 ton" in response.text
    assert "100,00" in response.text


def test_uretim_verisi_yokken_panel_bozulmaz(logged_in_client, db, fabrika):
    response = logged_in_client.get("/?donem=2026-01")
    assert response.status_code == 200
    assert "Enerji performansı" not in response.text
    assert "18.400,00" in response.text  # tüketim tarafı çalışmaya devam eder


def test_panelde_uretim_birimi_secilebilir(logged_in_client, db, fabrika):
    production(db, {"2026-01-31": (184, "ton"), "2026-01-30": (2000, "adet")})

    ton_page = logged_in_client.get("/?donem=2026-01&birim=ton")
    assert "kWh/ton" in ton_page.text
    assert "184,00 ton" in ton_page.text

    adet_page = logged_in_client.get("/?donem=2026-01&birim=adet")
    assert "kWh/adet" in adet_page.text
    assert "2.000,00 adet" in adet_page.text
    # 18.400 / 2.000 = 9,20
    assert "9,20" in adet_page.text


def test_varsayilan_birim_en_cok_uretim_yapilan_birimdir(logged_in_client, db, fabrika):
    production(db, {"2026-01-31": (184, "ton"), "2026-01-30": (2000, "adet")})

    response = logged_in_client.get("/?donem=2026-01")
    assert "kWh/adet" in response.text  # 2.000 > 184


def test_bilinmeyen_birim_istenirse_varsayilana_donulur(logged_in_client, db, fabrika):
    production(db, {"2026-01-31": (184, "ton")})

    response = logged_in_client.get("/?donem=2026-01&birim=fıçı")
    assert response.status_code == 200
    assert "kWh/ton" in response.text
