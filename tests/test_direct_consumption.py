"""Dogrudan tuketim girisi.

Fabrika toplaminda oncelik sirasi (enerji turu + ay bazinda):

    dogrudan tuketim  ->  ana sayac  ->  tum sayaclar

Ayni ay ve turde her iki kaynak da varsa DEGERLER TOPLANMAZ; dogrudan
tuketim esas alinir, sayac degeri yalnizca uyari olarak gosterilir.
"""

from datetime import date

import pytest

from app import calc, dashboard, reports
from app.db import SessionLocal
from app.models import DirectConsumption
from tests.factories import (
    department,
    direct_consumption,
    energy_type,
    meter,
    production,
    readings,
)

OCAK = (date(2026, 1, 1), date(2026, 1, 31))
SUBAT = (date(2026, 2, 1), date(2026, 2, 28))
ARALIK_2025 = (date(2025, 12, 1), date(2025, 12, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _fabrika(db, start, end, energy_type_id):
    return calc.total(
        calc.factory_consumptions(
            db, start=start, end=end, energy_type_id=energy_type_id
        )
    )


def _ana_sayac(db, energy, values):
    """Okuma kurali: tuketim BIRINCI okumanin ayina yazilir."""
    main = meter(db, "Ana Sayaç", energy, is_main=True)
    readings(db, main, values)
    return main


# --------------------------------------------------------------------------- #
# 1-2. Tek kaynak
# --------------------------------------------------------------------------- #


def test_01_yalnizca_sayac_verisi_varsa_sayac_kullanilir(db):
    electricity = energy_type(db)
    _ana_sayac(db, electricity, {"2026-01-01": 0, "2026-02-01": 1000})

    assert _fabrika(db, *OCAK, electricity.id) == pytest.approx(1_000)


def test_02_yalnizca_dogrudan_veri_varsa_dogrudan_kullanilir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 12_500)

    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_500)


# --------------------------------------------------------------------------- #
# 3-4. Iki kaynak ayni ayda
# --------------------------------------------------------------------------- #


def test_03_ayni_ayda_iki_kaynak_varsa_dogrudan_kazanir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)

    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_500)


def test_04_iki_kaynak_asla_toplanmaz(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)

    total = _fabrika(db, *OCAK, gas.id)
    assert total != pytest.approx(12_500 + 12_180)
    assert total == pytest.approx(12_500)

    conflicts = calc.consumption_conflicts(db, start=OCAK[0], end=OCAK[1])
    assert len(conflicts) == 1
    assert conflicts[0]["dogrudan"] == pytest.approx(12_500)
    assert conflicts[0]["sayac"] == pytest.approx(12_180)
    assert conflicts[0]["fark_yuzde"] == pytest.approx(320 / 12_180 * 100)


# --------------------------------------------------------------------------- #
# 5. Silme
# --------------------------------------------------------------------------- #


def test_05_dogrudan_kayit_silinince_sayac_degeri_geri_gelir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    record = direct_consumption(db, gas, "2026-01", 12_500)
    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_500)

    db.delete(record)
    db.commit()

    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_180)
    assert calc.consumption_conflicts(db, start=OCAK[0], end=OCAK[1]) == []


# --------------------------------------------------------------------------- #
# 6-7. Ay ve enerji turu yalitimi
# --------------------------------------------------------------------------- #


def test_06_ocak_dogrudan_subat_sayac_birbirini_etkilemez(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, gas, {"2026-02-01": 0, "2026-03-01": 9_000})
    direct_consumption(db, gas, "2026-01", 12_500)

    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_500)
    assert _fabrika(db, *SUBAT, gas.id) == pytest.approx(9_000)
    # Iki ay birlikte sorulunca da toplam bozulmaz.
    assert _fabrika(db, OCAK[0], SUBAT[1], gas.id) == pytest.approx(21_500)


def test_07_dogrudan_giris_diger_enerji_turunu_etkilemez(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, electricity, {"2026-01-01": 0, "2026-02-01": 1_000})
    direct_consumption(db, gas, "2026-01", 12_500)

    assert _fabrika(db, *OCAK, electricity.id) == pytest.approx(1_000)
    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_500)


# --------------------------------------------------------------------------- #
# 8-9. Maliyet ve EnPI
# --------------------------------------------------------------------------- #


def test_08_maliyet_dogrudan_tuketimden_hesaplanir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)

    summary = dashboard.energy_summary(db, gas, "2026-01")
    assert summary["total"] == pytest.approx(12_500)
    assert summary["cost"] == pytest.approx(12_500 * 8.5)


def test_09_enpi_dogrudan_tuketimden_hesaplanir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)
    production(db, {"2026-01-31": (100, "ton")})

    summary = dashboard.energy_summary(db, gas, "2026-01")
    result = dashboard.production_summary(db, "ton", "2026-01", summary["total"])
    assert result["enpi"] == pytest.approx(125.0)


# --------------------------------------------------------------------------- #
# 10-12. Bolum dagilimi ve cift sayim
# --------------------------------------------------------------------------- #


def test_10_bolum_dagilimi_yalnizca_alt_sayaclardan_gelir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    press = department(db, name="Pres")
    sub = meter(db, "Pres Sayacı", gas, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})
    direct_consumption(db, gas, "2026-01", 12_500)

    breakdown = dashboard.department_breakdown(db, gas, *OCAK, 12_500)
    rows = {row["label"]: row["value"] for row in breakdown["rows"]}
    assert rows["Pres"] == pytest.approx(4_000)
    assert rows["Ölçülmeyen / dağıtılmamış"] == pytest.approx(8_500)
    assert breakdown["scope_warning"] is False


def test_11_ana_alt_ve_dogrudan_bir_arada_cift_sayilmaz(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    press = department(db, name="Pres")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    sub = meter(db, "Pres Sayacı", gas, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})
    direct_consumption(db, gas, "2026-01", 12_500)

    total = _fabrika(db, *OCAK, gas.id)
    assert total == pytest.approx(12_500)

    breakdown = dashboard.department_breakdown(db, gas, *OCAK, total)
    assert breakdown["measured"] == pytest.approx(4_000)
    assert breakdown["unmeasured"] == pytest.approx(8_500)
    # Satirlarin toplami fabrika toplamina esittir, uzerine eklenmez.
    assert sum(row["value"] for row in breakdown["rows"]) == pytest.approx(total)


def test_12_hic_sayaci_olmayan_enerji_turu_dogrudan_ile_calisir(db):
    steam = energy_type(db, name="Buhar", unit="ton", price=450.0)
    direct_consumption(db, steam, "2026-01", 320)

    summary = dashboard.energy_summary(db, steam, "2026-01")
    assert summary["total"] == pytest.approx(320)
    assert summary["cost"] == pytest.approx(320 * 450.0)
    assert summary["conflict"] is None
    assert summary["source"] == "Doğrudan"


# --------------------------------------------------------------------------- #
# 13-14. Panel/rapor tutarliligi ve yil siniri
# --------------------------------------------------------------------------- #


def test_13_panel_ve_rapor_ayni_degeri_gosterir(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)

    summary = dashboard.energy_summary(db, gas, "2026-01")
    rows = reports.rows_by_energy_type(db, *OCAK)
    row = next(row for row in rows if row["energy_type"].id == gas.id)

    assert row["total"] == pytest.approx(summary["total"])
    assert row["cost"] == pytest.approx(summary["cost"])
    assert row["source"] == summary["source"] == "Doğrudan"


def test_14_yil_sinirinda_donemler_karismaz(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2025-12", 15_000)
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})

    assert _fabrika(db, *ARALIK_2025, gas.id) == pytest.approx(15_000)
    assert _fabrika(db, *OCAK, gas.id) == pytest.approx(12_180)
    assert _fabrika(db, ARALIK_2025[0], OCAK[1], gas.id) == pytest.approx(27_180)
    # Aralik dogrudan, Ocak sayac: aralik genelinde kaynak "Karışık".
    rows = reports.rows_by_energy_type(db, ARALIK_2025[0], OCAK[1])
    assert rows[0]["source"] == "Karışık"


# --------------------------------------------------------------------------- #
# 15-17. Giris ekrani
# --------------------------------------------------------------------------- #


def test_15_turkce_sayi_bicimleri_dogru_okunur(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    electricity = energy_type(db)

    for year_month, raw, expected in (
        ("2026-01", "12.500", 12_500.0),
        ("2026-02", "1.250,50", 1_250.5),
    ):
        response = logged_in_client.post(
            "/dogrudan-tuketim",
            data={
                "year_month": year_month,
                "energy_type_id": str(gas.id),
                "quantity": raw,
            },
        )
        assert response.status_code == 200

    quantities = [
        record.quantity
        for record in db.query(DirectConsumption).order_by(
            DirectConsumption.period_date
        )
    ]
    assert quantities == pytest.approx([12_500.0, 1_250.5])

    # Tanimsiz bicim sessizce cevrilmez.
    response = logged_in_client.post(
        "/dogrudan-tuketim",
        data={
            "year_month": "2026-01",
            "energy_type_id": str(electricity.id),
            "quantity": "12.5.0",
        },
    )
    assert response.status_code == 400
    assert "sayı olmalıdır" in response.text


def test_16_ayni_ay_ve_tur_icin_ikinci_kayit_engellenir(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 12_500)

    response = logged_in_client.post(
        "/dogrudan-tuketim",
        data={
            "year_month": "2026-01",
            "energy_type_id": str(gas.id),
            "quantity": "9.000",
        },
    )
    assert response.status_code == 400
    assert "zaten girilmiş" in response.text
    assert db.query(DirectConsumption).count() == 1


def test_17_gelecek_ay_icin_giris_engellenir(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    today = date.today()
    future = f"{today.year + 1:04d}-{today.month:02d}"

    response = logged_in_client.post(
        "/dogrudan-tuketim",
        data={
            "year_month": future,
            "energy_type_id": str(gas.id),
            "quantity": "1.000",
        },
    )
    assert response.status_code == 400
    assert "Gelecek ay" in response.text
    assert db.query(DirectConsumption).count() == 0
