"""Ucdan uca gercek kullanim senaryosu.

Kullanici gibi HTTP uzerinden ilerler: tanimlar -> okumalar -> uretim ->
hedef -> panel -> rapor. Amac tek tek fonksiyonlari degil, ekranlarin birlikte
tutarli calistigini korumaktir.
"""

from datetime import date

import pytest

from app import calc, dashboard, reports
from app.db import SessionLocal
from app.models import EnergyType

OCAK = (date(2026, 1, 1), date(2026, 1, 31))
SUBAT = (date(2026, 2, 1), date(2026, 2, 28))


@pytest.fixture
def fabrika(logged_in_client):
    """Iki enerji turu, uc bolum, bir ana ve dort alt sayac, iki aylik veri."""
    client = logged_in_client
    for name, unit, price in [("Elektrik", "kWh", "2,85"), ("Doğal Gaz", "Sm³", "12,40")]:
        assert client.post(
            "/tanimlar/enerji-turleri",
            data={"name": name, "unit": unit, "unit_price": price},
        ).status_code == 200

    for name in ["Üretim", "Paketleme", "Kazan Dairesi"]:
        assert client.post("/tanimlar/bolumler", data={"name": name}).status_code == 200

    meters = [
        {"name": "Ana Trafo", "energy_type_id": "1", "department_id": "",
         "multiplier": "40", "is_main": "on"},
        {"name": "Üretim Panosu", "energy_type_id": "1", "department_id": "1",
         "multiplier": "1"},
        {"name": "Paketleme Panosu", "energy_type_id": "1", "department_id": "2",
         "multiplier": "1"},
        {"name": "Kazan Panosu", "energy_type_id": "1", "department_id": "3",
         "multiplier": "1"},
        {"name": "Kazan Gaz Sayacı", "energy_type_id": "2", "department_id": "3",
         "multiplier": "1"},
    ]
    for meter in meters:
        assert client.post("/tanimlar/sayaclar", data=meter).status_code == 200

    readings = {
        "1": [("31.12.2025", "1000"), ("2026-01-31", "1250"), ("2026-02-28", "1460")],
        "2": [("2025-12-31", "50000"), ("2026-01-31", "56000"), ("2026-02-28", "61000")],
        "3": [("2025-12-31", "12000"), ("2026-01-31", "13800"), ("2026-02-28", "15200")],
        "4": [("2025-12-31", "8000"), ("2026-01-31", "8900"), ("2026-02-28", "9900")],
        "5": [("2025-12-31", "62000"), ("2026-01-31", "63200"), ("2026-02-28", "64150")],
    }
    for meter_id, rows in readings.items():
        for reading_date, value in rows:
            assert client.post(
                "/okumalar",
                data={
                    "meter_id": meter_id,
                    "reading_date": reading_date,
                    "index_value": value,
                },
            ).status_code == 200

    for production_date, quantity, unit in [
        ("2026-01-31", "100", "ton"),
        ("2026-02-28", "84", "ton"),
        ("2026-01-30", "2000", "adet"),
    ]:
        assert client.post(
            "/uretim",
            data={
                "production_date": production_date,
                "quantity": quantity,
                "unit": unit,
            },
        ).status_code == 200

    for year_month, energy_type_id, value in [("2026-01", "1", "9000"), ("2026-02", "1", "8000")]:
        assert client.post(
            "/hedefler",
            data={
                "year_month": year_month,
                "energy_type_id": energy_type_id,
                "target_value": value,
            },
        ).status_code == 200

    return client


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _electricity(db):
    return db.get(EnergyType, 1)


# --------------------------------------------------------------------------- #
# Temel tutarlilik
# --------------------------------------------------------------------------- #


def test_ocak_tuketimi_elle_hesapla_ayni(fabrika, db):
    """Ana trafo: (1250 - 1000) x 40 = 10.000 kWh"""
    total = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    assert total == pytest.approx(10_000)


def test_donemin_ilk_tuketimi_kaybolmaz(fabrika, db):
    """Şubat aralığı, 31 Ocak okumasıyla eşleşmeye devam eder."""
    subat = calc.total(
        calc.factory_consumptions(db, start=SUBAT[0], end=SUBAT[1], energy_type_id=1)
    )
    assert subat == pytest.approx(8_400)  # (1460 - 1250) x 40

    iki_ay = reports.rows_by_energy_type(db, OCAK[0], SUBAT[1])[0]["total"]
    assert iki_ay == pytest.approx(18_400)


def test_panel_ve_rapor_ayni_sonucu_verir(fabrika, db):
    for year_month, (start, end) in [("2026-01", OCAK), ("2026-02", SUBAT)]:
        report_rows = {
            row["energy_type"].id: row
            for row in reports.rows_by_energy_type(db, start, end)
        }
        for energy_type in db.query(EnergyType):
            panel = dashboard.energy_summary(db, energy_type, year_month)
            report = report_rows[energy_type.id]
            assert panel["total"] == pytest.approx(report["total"])
            assert panel["cost"] == pytest.approx(report["cost"])


def test_enerji_turleri_karismaz(fabrika, db):
    rows = {
        row["energy_type"].name: row["total"]
        for row in reports.rows_by_energy_type(db, *OCAK)
    }
    assert rows == {
        "Elektrik": pytest.approx(10_000),
        "Doğal Gaz": pytest.approx(1_200),
    }


# --------------------------------------------------------------------------- #
# Cift sayim
# --------------------------------------------------------------------------- #


def test_bolum_satirlari_fabrika_toplamina_esittir(fabrika, db):
    electricity = _electricity(db)
    factory_total = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    breakdown = dashboard.department_breakdown(db, electricity, *OCAK, factory_total)

    assert breakdown["scope_warning"] is False
    assert sum(row["value"] for row in breakdown["rows"]) == pytest.approx(factory_total)
    assert not any("Ana Trafo" in row["label"] for row in breakdown["rows"])


def test_panel_ve_rapor_bolum_dagiliminda_ayni(fabrika, db):
    electricity = _electricity(db)
    factory_total = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    panel = dashboard.department_breakdown(db, electricity, *OCAK, factory_total)
    report = next(
        section
        for section in reports.rows_by_department(db, *OCAK)
        if section["energy_type"].id == 1
    )
    assert report["factory_total"] == pytest.approx(factory_total)
    assert [row["value"] for row in report["breakdown"]["rows"]] == [
        pytest.approx(row["value"]) for row in panel["rows"]
    ]


# --------------------------------------------------------------------------- #
# Uretim, EnPI, hedef, maliyet
# --------------------------------------------------------------------------- #


def test_enpi_uretim_birimlerini_karistirmaz(fabrika, db):
    ton = dashboard.production_summary(db, "ton", "2026-01", 10_000)
    adet = dashboard.production_summary(db, "adet", "2026-01", 10_000)
    assert ton["enpi"] == pytest.approx(100)  # 10.000 / 100 ton
    assert adet["enpi"] == pytest.approx(5)  # 10.000 / 2.000 adet


def test_hedef_ve_maliyet(fabrika, db):
    summary = dashboard.energy_summary(db, _electricity(db), "2026-01")
    assert summary["cost"] == pytest.approx(10_000 * 2.85)
    assert summary["target"]["percent"] == pytest.approx(111.1, abs=0.1)
    assert summary["target"]["exceeded"] is True


# --------------------------------------------------------------------------- #
# Pasif sayac
# --------------------------------------------------------------------------- #


def test_pasif_sayac_gecmisi_degistirmez(fabrika, db):
    before_total = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    before_measured = dashboard.department_breakdown(
        db, _electricity(db), *OCAK, before_total
    )["measured"]

    # "Üretim Panosu" pasife alinir (aktif kutusu isaretlenmez).
    assert fabrika.post(
        "/tanimlar/sayaclar/2",
        data={
            "name": "Üretim Panosu",
            "energy_type_id": "1",
            "department_id": "1",
            "multiplier": "1",
        },
    ).status_code == 200

    db.expire_all()
    after_total = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    after_measured = dashboard.department_breakdown(
        db, _electricity(db), *OCAK, after_total
    )["measured"]

    assert after_total == pytest.approx(before_total)
    assert after_measured == pytest.approx(before_measured)


# --------------------------------------------------------------------------- #
# Ekranlar acilir
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "path",
    [
        "/?donem=2026-01",
        "/?donem=2026-02&birim=adet",
        "/okumalar",
        "/okumalar?sayac=1",
        "/uretim",
        "/hedefler",
        "/rapor?baslangic=2026-01-01&bitis=2026-02-28",
        "/rapor?baslangic=2026-01-01&bitis=2026-02-28&kirilim=sayac",
        "/rapor?baslangic=2026-01-01&bitis=2026-02-28&kirilim=bolum",
    ],
)
def test_tum_ekranlar_gercek_veriyle_acilir(fabrika, path):
    assert fabrika.get(path).status_code == 200
