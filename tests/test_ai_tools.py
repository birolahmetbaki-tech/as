"""AI read-only veri katmani.

Bu testler AI modeli veya ag baglantisi kullanmaz. Amac uc sey:
1. Tool ciktisi JSON'a cevrilebiliyor ve ORM nesnesi icermiyor
2. Tool'lar veritabanini degistirmiyor (read-only)
3. Tool ciktisi mevcut calc/dashboard/reports sonuclariyla birebir ayni
"""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app import ai_tools, calc, dashboard, reports
from app.db import SessionLocal
from app.models import (
    Department,
    EnergyType,
    Meter,
    MeterReading,
    Production,
    Settings,
    Target,
)
from tests.factories import department, energy_type, meter, production, readings

OCAK = (date(2026, 1, 1), date(2026, 1, 31))
TABLES = (Settings, EnergyType, Department, Meter, MeterReading, Production, Target)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def fabrika(db):
    """Ocak 2026: fabrika 10.020 kWh, Üretim 6.000, Paketleme 1.800.

    Ana Trafo çarpanı 40, endeksler 1.000 -> 1.250,50 (9.5 aşamasındaki
    Türkçe sayı senaryosunun sonucu).
    """
    electricity = energy_type(db, price=2.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=12.0)
    production_dept = department(db, "Üretim")
    packaging = department(db, "Paketleme")

    main = meter(db, "Ana Trafo", electricity, multiplier=40, is_main=True)
    production_meter = meter(db, "Üretim Panosu", electricity, production_dept)
    packaging_meter = meter(db, "Paketleme Panosu", electricity, packaging)
    gas_meter = meter(db, "Kazan Gaz Sayacı", gas, production_dept)

    readings(db, main, {"2025-12-31": 1000, "2026-01-31": 1250.50})
    readings(db, production_meter, {"2025-12-31": 50_000, "2026-01-31": 56_000})
    readings(db, packaging_meter, {"2025-12-31": 12_000, "2026-01-31": 13_800})
    readings(db, gas_meter, {"2025-12-31": 62_000, "2026-01-31": 63_200})
    production(db, {"2026-01-31": (100, "ton"), "2026-01-30": (2000, "adet")})
    db.add(Target(year_month="2026-01", energy_type_id=electricity.id, target_value=9_000))
    db.commit()
    return electricity


def _table_state(db) -> dict:
    """Her tablonun satir sayisi ve tum satirlarin ozeti."""
    state = {}
    for model in TABLES:
        rows = db.scalars(select(model).order_by(model.id)).all()
        state[model.__tablename__] = [
            {
                column.name: getattr(row, column.name)
                for column in model.__table__.columns
            }
            for row in rows
        ]
    return state


def _assert_json_safe(value, path="kok"):
    """Cikti yalnizca dict / list / str / int / float / bool / None icermeli."""
    if isinstance(value, dict):
        for key, item in value.items():
            assert isinstance(key, str), f"{path}: sözlük anahtarı metin değil ({key!r})"
            _assert_json_safe(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_json_safe(item, f"{path}[{index}]")
    else:
        assert value is None or isinstance(value, (str, int, float, bool)), (
            f"{path}: JSON'a çevrilemeyen değer {type(value).__name__} ({value!r})"
        )


def _all_tool_results(db) -> dict:
    """Her tool'un gercek veriyle bir kez calistirilmis sonucu."""
    return {
        "list_definitions": ai_tools.list_definitions(db),
        "get_data_coverage": ai_tools.get_data_coverage(db),
        "get_dashboard_summary": ai_tools.get_dashboard_summary(db, "2026-01", 1),
        "get_energy_consumption": ai_tools.get_energy_consumption(db, *OCAK),
        "get_department_breakdown": ai_tools.get_department_breakdown(db, 1, *OCAK),
        "get_production_and_enpi": ai_tools.get_production_and_enpi(
            db, "ton", 1, *OCAK
        ),
        "get_trend": ai_tools.get_trend(db, 1, "2026-01"),
        "get_targets": ai_tools.get_targets(db, *OCAK),
    }


# --------------------------------------------------------------------------- #
# Kayit sistemi
# --------------------------------------------------------------------------- #


def test_sekiz_tool_kayitli():
    assert set(ai_tools.TOOLS) == {
        "list_definitions",
        "get_data_coverage",
        "get_dashboard_summary",
        "get_energy_consumption",
        "get_department_breakdown",
        "get_production_and_enpi",
        "get_trend",
        "get_targets",
    }


def test_registry_gercek_fonksiyonlari_gosterir():
    assert ai_tools.TOOLS["get_trend"] is ai_tools.get_trend


# --------------------------------------------------------------------------- #
# JSON serilestirme ve ORM sinirlari
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("tool_name", sorted(ai_tools.TOOLS))
def test_tool_ciktisi_json_serilestirilebilir(db, fabrika, tool_name):
    result = _all_tool_results(db)[tool_name]
    json.dumps(result, ensure_ascii=False)  # hata verirse test düşer
    _assert_json_safe(result, tool_name)


def test_ciktida_orm_nesnesi_yok(db, fabrika):
    """date, EnergyType, Meter, Session gibi nesneler sızmamalı."""
    for name, result in _all_tool_results(db).items():
        _assert_json_safe(result, name)


def test_tarihler_metin_olarak_doner(db, fabrika):
    coverage = ai_tools.get_data_coverage(db)
    assert coverage["ilk_okuma"] == "2025-12-31"
    assert coverage["son_okuma"] == "2026-01-31"

    consumption = ai_tools.get_energy_consumption(db, *OCAK)
    assert consumption["baslangic"] == "2026-01-01"
    assert consumption["bitis"] == "2026-01-31"


def test_tarih_metin_olarak_da_verilebilir(db, fabrika):
    metinle = ai_tools.get_energy_consumption(db, "2026-01-01", "2026-01-31")
    tarihle = ai_tools.get_energy_consumption(db, *OCAK)
    assert metinle == tarihle


# --------------------------------------------------------------------------- #
# Read-only garantisi
# --------------------------------------------------------------------------- #


def test_hicbir_tool_veritabanini_degistirmez(db, fabrika):
    before = _table_state(db)
    _all_tool_results(db)
    db.expire_all()
    after = _table_state(db)
    assert after == before


@pytest.mark.parametrize("tool_name", sorted(ai_tools.TOOLS))
def test_tek_tek_her_tool_read_only(db, fabrika, tool_name):
    counts_before = {
        model.__tablename__: db.scalar(select(func.count()).select_from(model))
        for model in TABLES
    }
    _all_tool_results(db)[tool_name]
    db.expire_all()
    counts_after = {
        model.__tablename__: db.scalar(select(func.count()).select_from(model))
        for model in TABLES
    }
    assert counts_after == counts_before


def test_ai_tools_yazma_islevi_icermiyor():
    """Kaynak kodda yazma cagrisi bulunmamalı."""
    text = Path(ai_tools.__file__).read_text(encoding="utf-8")
    for yasak in (".commit(", ".flush(", ".add(", ".delete(", "text("):
        assert yasak not in text, f"ai_tools.py içinde yazma çağrısı: {yasak}"


# --------------------------------------------------------------------------- #
# Hesaplama eslesmeleri: ai_tools == calc / dashboard / reports
# --------------------------------------------------------------------------- #


def test_tuketim_calc_ile_ayni(db, fabrika):
    beklenen = calc.total(
        calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
    )
    assert beklenen == pytest.approx(10_020)  # (1250,50 - 1000) x 40

    ozet = ai_tools.get_dashboard_summary(db, "2026-01", 1)
    assert ozet["tuketim"] == pytest.approx(beklenen)

    aralik = ai_tools.get_energy_consumption(db, *OCAK, energy_type_id=1)
    assert aralik["satirlar"][0]["tuketim"] == pytest.approx(beklenen)


def test_maliyet_calc_cost_ile_ayni(db, fabrika):
    beklenen = calc.cost(10_020, 2.0)
    assert ai_tools.get_dashboard_summary(db, "2026-01", 1)["maliyet"] == (
        pytest.approx(beklenen)
    )


def test_hedef_calc_target_status_ile_ayni(db, fabrika):
    beklenen = calc.target_status(10_020, 9_000)
    hedef = ai_tools.get_dashboard_summary(db, "2026-01", 1)["hedef"]
    assert hedef["hedef"] == pytest.approx(beklenen["target"])
    assert hedef["gerceklesen"] == pytest.approx(beklenen["actual"])
    assert hedef["yuzde"] == pytest.approx(beklenen["percent"])
    assert hedef["asildi"] is beklenen["exceeded"]


def test_enpi_calc_enpi_ile_ayni(db, fabrika):
    uretim = calc.production_total(db, "ton", *OCAK)
    beklenen = calc.enpi(10_020, uretim)
    sonuc = ai_tools.get_production_and_enpi(db, "ton", 1, *OCAK)
    assert sonuc["uretim"] == pytest.approx(uretim)
    assert sonuc["enpi"] == pytest.approx(beklenen)
    assert sonuc["enpi_birimi"] == "kWh/ton"


def test_bolum_kirilimi_dashboard_ile_ayni(db, fabrika):
    beklenen = dashboard.department_breakdown(
        db, db.get(EnergyType, 1), *OCAK, 10_020
    )
    sonuc = ai_tools.get_department_breakdown(db, 1, *OCAK)

    assert sonuc["fabrika_toplami"] == pytest.approx(10_020)
    assert sonuc["olculmeyen"] == pytest.approx(beklenen["unmeasured"])
    assert sonuc["olcum_uyarisi"] is beklenen["scope_warning"]
    assert [row["tuketim"] for row in sonuc["satirlar"]] == [
        pytest.approx(row["value"]) for row in beklenen["rows"]
    ]


def test_hedefler_reports_ile_ayni(db, fabrika):
    beklenen = reports.target_rows(db, *OCAK)
    sonuc = ai_tools.get_targets(db, *OCAK)["hedefler"]
    assert len(sonuc) == len(beklenen)
    assert sonuc[0]["gerceklesen"] == pytest.approx(beklenen[0]["status"]["actual"])
    assert sonuc[0]["yuzde"] == pytest.approx(beklenen[0]["status"]["percent"])


def test_trend_dashboard_ile_ayni(db, fabrika):
    beklenen = dashboard.monthly_trend(db, db.get(EnergyType, 1), "2026-01")
    sonuc = ai_tools.get_trend(db, 1, "2026-01")
    assert len(sonuc["tuketim"]) == 12
    assert [nokta["deger"] for nokta in sonuc["tuketim"]] == [
        pytest.approx(nokta["value"]) for nokta in beklenen
    ]
    assert sonuc["tuketim"][-1]["donem"] == "2026-01"


# --------------------------------------------------------------------------- #
# Karistirmama kurallari
# --------------------------------------------------------------------------- #


def test_enerji_turleri_ayri_satirlarda_kalir(db, fabrika):
    satirlar = ai_tools.get_energy_consumption(db, *OCAK)["satirlar"]
    degerler = {row["enerji_turu"]: (row["tuketim"], row["birim"]) for row in satirlar}
    assert degerler["Elektrik"] == (pytest.approx(10_020), "kWh")
    assert degerler["Doğal Gaz"] == (pytest.approx(1_200), "Sm³")
    # Farklı birimleri birleştiren tek bir toplam alanı yok.
    assert all("toplam" not in key for row in satirlar for key in row)


def test_uretim_birimleri_karismaz(db, fabrika):
    ton = ai_tools.get_production_and_enpi(db, "ton", 1, *OCAK)
    adet = ai_tools.get_production_and_enpi(db, "adet", 1, *OCAK)
    assert ton["uretim"] == pytest.approx(100)
    assert adet["uretim"] == pytest.approx(2_000)
    assert ton["enpi"] == pytest.approx(100.2)
    assert adet["enpi"] == pytest.approx(5.01)


def test_uretim_yoksa_enpi_null(db, fabrika):
    sonuc = ai_tools.get_production_and_enpi(db, "m³", 1, *OCAK)
    assert sonuc["uretim"] == pytest.approx(0)
    assert sonuc["enpi"] is None


# --------------------------------------------------------------------------- #
# Tanimlar ve kapsam
# --------------------------------------------------------------------------- #


def test_tanimlar_gercek_kayitlari_verir(db, fabrika):
    tanimlar = ai_tools.list_definitions(db)
    assert [item["ad"] for item in tanimlar["enerji_turleri"]] == ["Elektrik", "Doğal Gaz"]
    assert [item["ad"] for item in tanimlar["bolumler"]] == ["Üretim", "Paketleme"]

    ana = next(m for m in tanimlar["sayaclar"] if m["ad"] == "Ana Trafo")
    assert ana["carpan"] == pytest.approx(40)
    assert ana["ana_sayac"] is True
    assert ana["bolum"] is None
    assert ana["aktif"] is True


def test_veri_kapsami_dogru(db, fabrika):
    kapsam = ai_tools.get_data_coverage(db)
    assert kapsam["okuma_sayisi"] == 8
    assert kapsam["uretim_baslangic"] == "2026-01-30"
    assert sorted(kapsam["uretim_birimleri"]) == ["adet", "ton"]


def test_veri_yokken_kapsam_none_doner(db):
    kapsam = ai_tools.get_data_coverage(db)
    assert kapsam["ilk_okuma"] is None
    assert kapsam["son_okuma"] is None
    assert kapsam["okuma_sayisi"] == 0
    assert kapsam["uretim_birimleri"] == []


# --------------------------------------------------------------------------- #
# Hata durumlari
# --------------------------------------------------------------------------- #


def test_olmayan_enerji_turu_acik_hata_verir(db, fabrika):
    with pytest.raises(ValueError, match="Enerji türü bulunamadı"):
        ai_tools.get_dashboard_summary(db, "2026-01", 99)


def test_desteklenmeyen_ay_sayisi_reddedilir(db, fabrika):
    with pytest.raises(ValueError, match="12 ay"):
        ai_tools.get_trend(db, 1, "2026-01", months=6)
