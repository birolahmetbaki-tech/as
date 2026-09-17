"""Donem atama kurali: tuketim, BIRINCI okumanin ait oldugu takvim ayina yazilir.

Sahada endeksler her ayin ertesi ayin 1. gunu okunuyor:

    01.01.2026 -> 0
    01.02.2026 -> 1.000      => Ocak 2026 = 1.000
    01.03.2026 -> 2.200      => Şubat 2026 = 1.200
"""

from datetime import date

import pytest

from app import calc, dashboard, reports
from app.db import SessionLocal
from app.models import EnergyType
from tests.factories import energy_type, meter, readings

OCAK = (date(2026, 1, 1), date(2026, 1, 31))
SUBAT = (date(2026, 2, 1), date(2026, 2, 28))
MART = (date(2026, 3, 1), date(2026, 3, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def sayac(db):
    """Sartnamedeki ornek: 01.01=0, 01.02=1.000, 01.03=2.200"""
    electricity = energy_type(db, price=2.0)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1000, "2026-03-01": 2200})
    return main


def _fabrika(db, start, end, energy_type_id=1):
    return calc.total(
        calc.factory_consumptions(db, start=start, end=end, energy_type_id=energy_type_id)
    )


# --------------------------------------------------------------------------- #
# 1-2. Tuketim dogru aya yaziliyor
# --------------------------------------------------------------------------- #


def test_01_01_ile_01_02_arasi_ocak_ayina_yazilir(db, sayac):
    assert _fabrika(db, *OCAK) == pytest.approx(1_000)


def test_01_02_ile_01_03_arasi_subat_ayina_yazilir(db, sayac):
    assert _fabrika(db, *SUBAT) == pytest.approx(1_200)


def test_son_okumadan_sonraki_ay_bos_kalir(db, sayac):
    """01.03 son okuma; Mart tuketimi ancak 01.04 okumasiyla olusur."""
    assert _fabrika(db, *MART) == pytest.approx(0)


def test_donem_tarihi_ilk_okumanin_tarihidir(db, sayac):
    entries = calc.meter_consumptions(db, sayac.id)
    assert [entry.period_date for entry in entries] == [
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]
    # Kaynak okuma tarihi izlenebilirlik icin korunur.
    assert [entry.reading_date for entry in entries] == [
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


# --------------------------------------------------------------------------- #
# 3-4. Rapor, donem disindaki okumayi kullanabiliyor
# --------------------------------------------------------------------------- #


def test_ocak_raporu_1_subat_okumasini_kullanir(db, sayac):
    rows = reports.rows_by_energy_type(db, *OCAK)
    assert rows[0]["total"] == pytest.approx(1_000)
    assert rows[0]["cost"] == pytest.approx(2_000)  # 1.000 x 2,00


def test_subat_raporu_1_mart_okumasini_kullanir(db, sayac):
    rows = reports.rows_by_energy_type(db, *SUBAT)
    assert rows[0]["total"] == pytest.approx(1_200)


# --------------------------------------------------------------------------- #
# 5. Dashboard = rapor
# --------------------------------------------------------------------------- #


def test_dashboard_ve_rapor_ayni_degeri_gosterir(db, sayac):
    electricity = db.get(EnergyType, 1)
    for year_month, (start, end) in [("2026-01", OCAK), ("2026-02", SUBAT), ("2026-03", MART)]:
        panel = dashboard.energy_summary(db, electricity, year_month)
        rapor = reports.rows_by_energy_type(db, start, end)[0]
        assert panel["total"] == pytest.approx(rapor["total"])
        assert panel["cost"] == pytest.approx(rapor["cost"])


def test_panelde_onceki_donem_dogru(db, sayac):
    """Şubat panelinde önceki dönem Ocak'ın 1.000 kWh'i olmalı."""
    summary = dashboard.energy_summary(db, db.get(EnergyType, 1), "2026-02")
    assert summary["total"] == pytest.approx(1_200)
    assert summary["change"]["previous"] == pytest.approx(1_000)
    assert summary["change"]["difference"] == pytest.approx(200)


def test_aylik_trend_dogru_aylara_dagilir(db, sayac):
    trend = {
        point["month"]: point["value"]
        for point in dashboard.monthly_trend(db, db.get(EnergyType, 1), "2026-03")
    }
    assert trend["2026-01"] == pytest.approx(1_000)
    assert trend["2026-02"] == pytest.approx(1_200)
    assert trend["2026-03"] == pytest.approx(0)


# --------------------------------------------------------------------------- #
# 6. Yil gecisi
# --------------------------------------------------------------------------- #


def test_yil_gecisi_aralik_2025_e_yazilir(db):
    """01.12.2025 -> 01.01.2026 arasindaki tuketim Aralik 2025'e aittir."""
    electricity = energy_type(db, price=1.0)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2025-12-01": 0, "2026-01-01": 500, "2026-02-01": 900})

    aralik = _fabrika(db, date(2025, 12, 1), date(2025, 12, 31))
    ocak = _fabrika(db, *OCAK)
    assert aralik == pytest.approx(500)
    assert ocak == pytest.approx(400)

    yillik = calc.group_by_period(
        calc.factory_consumptions(db, energy_type_id=electricity.id), calc.PERIOD_YEAR
    )
    assert yillik == {"2025": pytest.approx(500), "2026": pytest.approx(400)}


# --------------------------------------------------------------------------- #
# 7. Cok ayli rapor
# --------------------------------------------------------------------------- #


def test_cok_ayli_raporda_aylik_toplamlar_dogru(db, sayac):
    aylik = calc.group_by_period(
        calc.factory_consumptions(db, start=OCAK[0], end=MART[1], energy_type_id=1)
    )
    assert aylik == {"2026-01": pytest.approx(1_000), "2026-02": pytest.approx(1_200)}

    # Aralik raporu, aylarin toplamina esit olmali.
    aralik_raporu = reports.rows_by_energy_type(db, OCAK[0], MART[1])[0]["total"]
    assert aralik_raporu == pytest.approx(2_200)
    assert aralik_raporu == pytest.approx(sum(aylik.values()))


def test_aylik_panel_toplamlari_aralik_raporuna_esit(db, sayac):
    electricity = db.get(EnergyType, 1)
    panel_toplami = sum(
        dashboard.energy_summary(db, electricity, ay)["total"]
        for ay in ["2026-01", "2026-02", "2026-03"]
    )
    rapor = reports.rows_by_energy_type(db, OCAK[0], MART[1])[0]["total"]
    assert panel_toplami == pytest.approx(rapor)


# --------------------------------------------------------------------------- #
# 8. Yil sinirinin sartnamedeki ornegi: 01.12.2026 -> 01.01.2027 = Aralik 2026
# --------------------------------------------------------------------------- #


def test_01_12_ile_01_01_arasi_onceki_yilin_aralik_ayina_yazilir(db):
    electricity = energy_type(db, price=1.0)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-12-01": 10_000, "2027-01-01": 11_500})

    aralik_2026 = _fabrika(db, date(2026, 12, 1), date(2026, 12, 31))
    ocak_2027 = _fabrika(db, date(2027, 1, 1), date(2027, 1, 31))

    assert aralik_2026 == pytest.approx(1_500)
    assert ocak_2027 == pytest.approx(0)

    # Panel de ayni sonucu verir: tuketim ikinci okumanin ayina kaymaz.
    panel = dashboard.energy_summary(db, electricity, "2026-12")
    assert panel["total"] == pytest.approx(1_500)
    assert dashboard.energy_summary(db, electricity, "2027-01")["total"] == 0


def test_yil_sinirinda_panel_ve_rapor_ayni_degeri_verir(db):
    electricity = energy_type(db, price=1.0)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-12-01": 10_000, "2027-01-01": 11_500})

    for year_month, bounds in (
        ("2026-12", (date(2026, 12, 1), date(2026, 12, 31))),
        ("2027-01", (date(2027, 1, 1), date(2027, 1, 31))),
    ):
        panel = dashboard.energy_summary(db, electricity, year_month)
        rapor = reports.rows_by_energy_type(db, *bounds)[0]
        assert panel["total"] == pytest.approx(rapor["total"])
        assert panel["cost"] == pytest.approx(rapor["cost"])


# --------------------------------------------------------------------------- #
# 9. Suzme sirasi eslesmeyi bozmuyor
# --------------------------------------------------------------------------- #


def test_dar_aralik_sorgusu_eslesmeyi_bozmaz(db, sayac):
    """Eslestirme her zaman TUM okumalar uzerinden yapilir, suzme sonradan.

    Subat sorgulandiginda 01.02 okumasi aralik icinde, 01.03 okumasi disinda
    kalir; buna ragmen Subat tuketimi (1.200) dogru uretilir.
    """
    assert _fabrika(db, *SUBAT) == pytest.approx(1_200)

    # Yalnizca tek gunluk aralik: 01.02 donem tarihini tasiyan kayit gelir.
    entries = calc.factory_consumptions(
        db, start=date(2026, 2, 1), end=date(2026, 2, 1), energy_type_id=1
    )
    assert [entry.consumption for entry in entries] == [pytest.approx(1_200)]


def test_suzme_donem_tarihine_gore_yapilir(db, sayac):
    """Ay ortasindan ay ortasina aralik: donem tarihi (ilk okuma) belirleyicidir."""
    entries = calc.factory_consumptions(
        db, start=date(2026, 1, 15), end=date(2026, 2, 15), energy_type_id=1
    )
    # 01.01 donem tarihi araligin disinda, 01.02 icinde kalir.
    assert [entry.period_date for entry in entries] == [date(2026, 2, 1)]
    assert calc.total(entries) == pytest.approx(1_200)


def test_aylik_toplamlar_tek_seferde_de_ay_ay_da_ayni(db, sayac):
    """Aralik sorgusu ile ay ay sorgu ayni sonucu verir: kayma veya tekrar yok."""
    topluca = calc.group_by_period(
        calc.factory_consumptions(db, start=OCAK[0], end=MART[1], energy_type_id=1)
    )
    ay_ay = {
        "2026-01": _fabrika(db, *OCAK),
        "2026-02": _fabrika(db, *SUBAT),
    }
    assert topluca == {key: pytest.approx(value) for key, value in ay_ay.items()}


# --------------------------------------------------------------------------- #
# 10. Dogrudan tuketim ayni kurala uyar
# --------------------------------------------------------------------------- #


def test_dogrudan_tuketim_ayni_donem_kuralina_uyar(db):
    """Ocak dogrudan kaydi ile 01.01 -> 01.02 sayac tuketimi ayni aya duser."""
    from tests.factories import direct_consumption

    electricity = energy_type(db, price=1.0)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000})

    # Once yalnizca sayac: Ocak.
    assert _fabrika(db, *OCAK) == pytest.approx(1_000)

    # Ocak dogrudan kaydi ayni aya denk gelir, cakisma olarak bildirilir.
    direct_consumption(db, electricity, "2026-01", 1_100)
    assert _fabrika(db, *OCAK) == pytest.approx(1_100)
    assert _fabrika(db, *SUBAT) == pytest.approx(0)

    conflicts = calc.consumption_conflicts(db, start=OCAK[0], end=OCAK[1])
    assert [conflict["donem"] for conflict in conflicts] == ["2026-01"]
