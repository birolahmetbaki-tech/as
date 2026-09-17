"""Hesaplama cekirdegi: okumalardan tuketim uretimi.

Testler veritabanina dogrudan yazar; boylece calc modulu web katmanindan
bagimsiz olarak dogrulanir.
"""

from datetime import date

import pytest

from app import calc
from app.db import SessionLocal
from tests.factories import department as _department
from tests.factories import energy_type as _energy_type
from tests.factories import meter as _meter
from tests.factories import production as _production
from tests.factories import readings as _readings


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


# --------------------------------------------------------------------------- #
# Temel tuketim hesabi
# --------------------------------------------------------------------------- #


def test_iki_okuma_arasindaki_tuketim(db):
    """Sartnamedeki ornek: (1.250 - 1.000) x 40 = 10.000"""
    meter = _meter(db, "Ana Trafo", _energy_type(db), multiplier=40)
    _readings(db, meter, {"2026-01-01": 1000, "2026-02-01": 1250})

    entries = calc.meter_consumptions(db, meter.id)
    assert len(entries) == 1
    assert entries[0].consumption == pytest.approx(10_000)
    assert entries[0].multiplier == pytest.approx(40)


def test_carpani_olmayan_sayacta_endeks_farki_kullanilir(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 1000, "2026-02-01": 1250})

    assert calc.meter_consumptions(db, meter.id)[0].consumption == pytest.approx(250)


def test_ilk_okuma_icin_tuketim_uretilmez(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 1000})

    assert calc.meter_consumptions(db, meter.id) == []


def test_okumasi_olmayan_sayac_bos_doner(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    assert calc.meter_consumptions(db, meter.id) == []


def test_olmayan_sayac_bos_doner(db):
    assert calc.meter_consumptions(db, 999) == []


def test_birden_fazla_okuma_zincirlenir(db):
    meter = _meter(db, "Sayaç", _energy_type(db), multiplier=2)
    _readings(
        db,
        meter,
        {"2026-01-01": 100, "2026-01-11": 150, "2026-01-21": 220, "2026-02-01": 300},
    )

    entries = calc.meter_consumptions(db, meter.id)
    assert [entry.consumption for entry in entries] == [
        pytest.approx(100),  # (150-100) x 2
        pytest.approx(140),  # (220-150) x 2
        pytest.approx(160),  # (300-220) x 2
    ]
    assert calc.total(entries) == pytest.approx(400)


def test_tuketim_ikinci_okumanin_tarihine_yazilir(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 100, "2026-02-15": 300})

    entry = calc.meter_consumptions(db, meter.id)[0]
    assert entry.reading_date == date(2026, 2, 15)
    assert entry.previous_date == date(2026, 1, 1)


def test_okumalar_giris_sirasindan_bagimsiz_kronolojik_eslesir(db):
    """Araya sonradan girilen okuma da dogru esleseme girmelidir."""
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-03-01": 300, "2026-01-01": 100})
    _readings(db, meter, {"2026-02-01": 180})

    entries = calc.meter_consumptions(db, meter.id)
    assert [entry.reading_date for entry in entries] == [
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]
    assert [entry.consumption for entry in entries] == [
        pytest.approx(80),
        pytest.approx(120),
    ]


def test_ayni_endeks_sifir_tuketim_uretir(db):
    meter = _meter(db, "Sayaç", _energy_type(db), multiplier=10)
    _readings(db, meter, {"2026-01-01": 500, "2026-01-02": 500})

    assert calc.meter_consumptions(db, meter.id)[0].consumption == pytest.approx(0)


def test_dusuk_endeks_negatif_uretir_bu_yuzden_giriste_engellenir(db):
    """Sayac sifirlama icin ozel mekanizma yoktur.

    Azalan endeks gecersiz veridir ve okuma ekraninda engellenir; calc buna
    ozel bir kural uygulamaz.
    """
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 1000, "2026-01-02": 900})

    assert calc.meter_consumptions(db, meter.id)[0].consumption == pytest.approx(-100)


def test_ondalikli_endeksler_yuvarlanmadan_hesaplanir(db):
    meter = _meter(db, "Sayaç", _energy_type(db), multiplier=1.5)
    _readings(db, meter, {"2026-01-01": 1000.25, "2026-01-02": 1250.5})

    entry = calc.meter_consumptions(db, meter.id)[0]
    assert entry.consumption == pytest.approx(375.375)


# --------------------------------------------------------------------------- #
# Tarih araligi
# --------------------------------------------------------------------------- #


def test_tarih_araligi_filtrelenir(db):
    """Suzme, tuketimin ait oldugu tarihe (ilk okuma) gore yapilir."""
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(
        db, meter, {"2026-01-01": 100, "2026-02-01": 200, "2026-03-01": 350}
    )

    # 01.02 -> 01.03 arasindaki tuketim Şubat ayina aittir.
    entries = calc.meter_consumptions(
        db, meter.id, start=date(2026, 2, 1), end=date(2026, 2, 28)
    )
    assert len(entries) == 1
    assert entries[0].consumption == pytest.approx(150)
    assert entries[0].period_date == date(2026, 2, 1)


def test_donem_sonrasi_okuma_donem_tuketimini_verir(db):
    """Subat tuketimi, 1 Mart'ta alinan okumayla hesaplanir.

    Okuma araligin disinda kalsa bile donem tuketimi dogru cikar.
    """
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-02-01": 1000, "2026-03-01": 1400})

    entries = calc.meter_consumptions(
        db, meter.id, start=date(2026, 2, 1), end=date(2026, 2, 28)
    )
    assert len(entries) == 1
    assert entries[0].consumption == pytest.approx(400)
    assert entries[0].period_date == date(2026, 2, 1)  # donem: Şubat
    assert entries[0].reading_date == date(2026, 3, 1)  # kaynak okuma: 1 Mart


def test_aralik_disinda_kayit_yoksa_bos_doner(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 100, "2026-02-01": 200})

    assert (
        calc.meter_consumptions(
            db, meter.id, start=date(2026, 5, 1), end=date(2026, 5, 31)
        )
        == []
    )


# --------------------------------------------------------------------------- #
# Ana sayac / alt sayac kurali
# --------------------------------------------------------------------------- #


def test_ana_sayac_varsa_yalnizca_ana_sayaclar_kullanilir(db):
    electricity = _energy_type(db)
    main_one = _meter(db, "Ana Sayaç 1", electricity, is_main=True)
    main_two = _meter(db, "Ana Sayaç 2", electricity, is_main=True)
    sub = _meter(db, "Alt Sayaç 1", electricity)
    for meter, values in (
        (main_one, {"2026-01-01": 0, "2026-01-31": 1000}),
        (main_two, {"2026-01-01": 0, "2026-01-31": 500}),
        (sub, {"2026-01-01": 0, "2026-01-31": 300}),
    ):
        _readings(db, meter, values)

    assert calc.factory_meter_ids(db, electricity.id) == sorted(
        [main_one.id, main_two.id]
    )
    assert calc.total(calc.factory_consumptions(db)) == pytest.approx(1500)


def test_ana_sayac_yoksa_tum_sayaclar_kullanilir(db):
    electricity = _energy_type(db)
    first = _meter(db, "Sayaç 1", electricity)
    second = _meter(db, "Sayaç 2", electricity)
    _readings(db, first, {"2026-01-01": 0, "2026-02-01": 1000})
    _readings(db, second, {"2026-01-01": 0, "2026-02-01": 300})

    assert calc.factory_meter_ids(db, electricity.id) == sorted([first.id, second.id])
    assert calc.total(calc.factory_consumptions(db)) == pytest.approx(1300)


def test_ana_sayac_kurali_her_enerji_turu_icin_ayri_uygulanir(db):
    electricity = _energy_type(db)
    gas = _energy_type(db, name="Doğal Gaz", unit="Sm³")

    main_electric = _meter(db, "Elektrik Ana", electricity, is_main=True)
    sub_electric = _meter(db, "Elektrik Alt", electricity)
    gas_one = _meter(db, "Gaz 1", gas)
    gas_two = _meter(db, "Gaz 2", gas)

    _readings(db, main_electric, {"2026-01-01": 0, "2026-02-01": 1000})
    _readings(db, sub_electric, {"2026-01-01": 0, "2026-02-01": 400})
    _readings(db, gas_one, {"2026-01-01": 0, "2026-02-01": 200})
    _readings(db, gas_two, {"2026-01-01": 0, "2026-02-01": 100})

    # Elektrikte ana sayac var -> yalnizca ana sayac; gazda yok -> ikisi de.
    assert calc.total(
        calc.factory_consumptions(db, energy_type_id=electricity.id)
    ) == pytest.approx(1000)
    assert calc.total(
        calc.factory_consumptions(db, energy_type_id=gas.id)
    ) == pytest.approx(300)
    assert calc.total(calc.factory_consumptions(db)) == pytest.approx(1300)


# --------------------------------------------------------------------------- #
# Bolum kirilimi
# --------------------------------------------------------------------------- #


def test_bolum_kirilimi(db):
    electricity = _energy_type(db)
    production = _department(db, "Üretim")
    packaging = _department(db, "Paketleme")

    production_meter = _meter(db, "Üretim Sayacı", electricity, production)
    packaging_meter = _meter(db, "Paketleme Sayacı", electricity, packaging)
    _readings(db, production_meter, {"2026-01-01": 0, "2026-02-01": 800})
    _readings(db, packaging_meter, {"2026-01-01": 0, "2026-02-01": 200})

    totals = calc.group_by_department(calc.consumptions(db))
    assert totals == {"Üretim": pytest.approx(800), "Paketleme": pytest.approx(200)}


def test_bolumsuz_sayac_ayri_gosterilir(db):
    electricity = _energy_type(db)
    production = _department(db, "Üretim")
    with_department = _meter(db, "Üretim Sayacı", electricity, production)
    without_department = _meter(db, "Şebeke Sayacı", electricity)
    _readings(db, with_department, {"2026-01-01": 0, "2026-02-01": 600})
    _readings(db, without_department, {"2026-01-01": 0, "2026-02-01": 400})

    entries = calc.consumptions(db)
    assert calc.group_by_department(entries) == {
        "Üretim": pytest.approx(600),
        calc.UNASSIGNED_DEPARTMENT: pytest.approx(400),
    }
    assert {entry.department_label for entry in entries} == {
        "Üretim",
        calc.UNASSIGNED_DEPARTMENT,
    }


# --------------------------------------------------------------------------- #
# Enerji turu ayrimi
# --------------------------------------------------------------------------- #


def test_farkli_enerji_turleri_birbirine_karismaz(db):
    electricity = _energy_type(db)
    water = _energy_type(db, name="Su", unit="m³")
    electric_meter = _meter(db, "Elektrik Sayacı", electricity)
    water_meter = _meter(db, "Su Sayacı", water)
    _readings(db, electric_meter, {"2026-01-01": 0, "2026-02-01": 1000})
    _readings(db, water_meter, {"2026-01-01": 0, "2026-02-01": 50})

    electric_entries = calc.consumptions(db, energy_type_id=electricity.id)
    assert calc.total(electric_entries) == pytest.approx(1000)
    assert {entry.energy_type_name for entry in electric_entries} == {"Elektrik"}
    assert electric_entries[0].unit == "kWh"

    water_entries = calc.consumptions(db, energy_type_id=water.id)
    assert calc.total(water_entries) == pytest.approx(50)
    assert water_entries[0].unit == "m³"


# --------------------------------------------------------------------------- #
# Aktif / pasif sayac
# --------------------------------------------------------------------------- #


def test_pasif_sayacin_gecmis_tuketimi_hesaba_dahildir(db):
    """Pasiflik yeni veri girisini kapatir; gecmisi silmez."""
    electricity = _energy_type(db)
    active = _meter(db, "Aktif Sayaç", electricity)
    retired = _meter(db, "Emekli Sayaç", electricity, is_active=False)
    _readings(db, active, {"2026-01-01": 0, "2026-02-01": 700})
    _readings(db, retired, {"2026-01-01": 0, "2026-02-01": 300})

    assert calc.total(calc.consumptions(db)) == pytest.approx(1000)
    assert calc.total(calc.factory_consumptions(db)) == pytest.approx(1000)


def test_pasif_ana_sayac_kurali_bozmaz(db):
    electricity = _energy_type(db)
    main = _meter(db, "Ana Sayaç", electricity, is_main=True, is_active=False)
    sub = _meter(db, "Alt Sayaç", electricity)
    _readings(db, main, {"2026-01-01": 0, "2026-02-01": 900})
    _readings(db, sub, {"2026-01-01": 0, "2026-02-01": 400})

    assert calc.factory_meter_ids(db, electricity.id) == [main.id]
    assert calc.total(calc.factory_consumptions(db)) == pytest.approx(900)


# --------------------------------------------------------------------------- #
# Donem gruplamasi
# --------------------------------------------------------------------------- #


def test_gunluk_gruplama(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 0, "2026-01-02": 100, "2026-01-03": 250})

    assert calc.group_by_period(calc.consumptions(db), calc.PERIOD_DAY) == {
        "2026-01-01": pytest.approx(100),
        "2026-01-02": pytest.approx(150),
    }


def test_aylik_gruplama(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(
        db,
        meter,
        {
            "2026-01-01": 0,
            "2026-01-15": 100,
            "2026-02-01": 250,
            "2026-03-01": 400,
        },
    )

    assert calc.group_by_period(calc.consumptions(db)) == {
        "2026-01": pytest.approx(250),
        "2026-02": pytest.approx(150),
    }


def test_yillik_gruplama(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-01-01": 0, "2026-07-01": 500, "2027-01-01": 900})

    assert calc.group_by_period(calc.consumptions(db), calc.PERIOD_YEAR) == {
        "2026": pytest.approx(900)
    }


def test_gruplama_anahtarlari_kronolojik_siralanir(db):
    meter = _meter(db, "Sayaç", _energy_type(db))
    _readings(db, meter, {"2026-03-01": 300, "2026-01-01": 0, "2026-02-01": 100})

    assert list(calc.group_by_period(calc.consumptions(db))) == ["2026-01", "2026-02"]


def test_bilinmeyen_donem_hata_verir(db):
    with pytest.raises(ValueError, match="Bilinmeyen dönem"):
        calc.period_key(date(2026, 1, 1), "hafta")


# --------------------------------------------------------------------------- #
# Bos veri
# --------------------------------------------------------------------------- #


def test_veri_yokken_bos_sonuc_doner(db):
    assert calc.consumptions(db) == []
    assert calc.factory_consumptions(db) == []
    assert calc.factory_meter_ids(db) == []
    assert calc.total([]) == 0
    assert calc.group_by_period([]) == {}
    assert calc.group_by_department([]) == {}


# --------------------------------------------------------------------------- #
# Uretim ve EnPI
# --------------------------------------------------------------------------- #


def test_donem_uretim_toplami(db):
    _production(
        db,
        {
            "2026-01-10": (120, "ton"),
            "2026-01-20": (135, "ton"),
            "2026-02-05": (100, "ton"),
        },
    )

    assert calc.production_total(
        db, "ton", start=date(2026, 1, 1), end=date(2026, 1, 31)
    ) == pytest.approx(255)
    assert calc.production_total(db, "ton") == pytest.approx(355)


def test_uretim_birimleri_karismaz(db):
    _production(db, {"2026-01-10": (100, "ton"), "2026-01-11": (2000, "adet")})

    assert calc.production_total(db, "ton") == pytest.approx(100)
    assert calc.production_total(db, "adet") == pytest.approx(2000)
    # Toplam 2.100 gibi anlamsiz bir deger uretilmez.
    assert calc.production_units(db) == ["adet", "ton"]


def test_bilinmeyen_birimde_uretim_sifirdir(db):
    _production(db, {"2026-01-10": (100, "ton")})
    assert calc.production_total(db, "m³") == pytest.approx(0)


def test_enpi_hesabi(db):
    """10.000 kWh / 100 ton = 100 kWh/ton"""
    assert calc.enpi(10_000, 100) == pytest.approx(100)


def test_uretim_yokken_enpi_tanimsizdir(db):
    assert calc.enpi(10_000, 0) is None
    assert calc.enpi(0, 0) is None


def test_enpi_serisi_aylik_uretilir(db):
    electricity = _energy_type(db)
    meter = _meter(db, "Ana Trafo", electricity, is_main=True)
    _readings(
        db,
        meter,
        {"2026-01-01": 0, "2026-02-01": 10_000, "2026-03-01": 18_000},
    )
    _production(db, {"2026-01-31": (100, "ton"), "2026-02-28": (80, "ton")})

    series = calc.enpi_series(db, "ton", electricity.id)
    assert series["2026-01"] == pytest.approx(100)  # 10.000 / 100
    assert series["2026-02"] == pytest.approx(100)  # 8.000 / 80


def test_uretimi_olmayan_ay_enpi_uretmez(db):
    electricity = _energy_type(db)
    meter = _meter(db, "Ana Trafo", electricity, is_main=True)
    _readings(db, meter, {"2026-01-01": 0, "2026-02-01": 10_000, "2026-03-01": 16_000})
    _production(db, {"2026-01-31": (100, "ton")})

    series = calc.enpi_series(db, "ton", electricity.id)
    assert series["2026-01"] == pytest.approx(100)
    assert series["2026-02"] is None


def test_enpi_farkli_enerji_turlerini_karistirmaz(db):
    electricity = _energy_type(db)
    gas = _energy_type(db, name="Doğal Gaz", unit="Sm³")
    electric_meter = _meter(db, "Elektrik Ana", electricity, is_main=True)
    gas_meter = _meter(db, "Gaz Sayacı", gas)
    _readings(db, electric_meter, {"2026-01-01": 0, "2026-02-01": 10_000})
    _readings(db, gas_meter, {"2026-01-01": 0, "2026-02-01": 500})
    _production(db, {"2026-01-31": (100, "ton")})

    assert calc.enpi_series(db, "ton", electricity.id)["2026-01"] == pytest.approx(100)
    assert calc.enpi_series(db, "ton", gas.id)["2026-01"] == pytest.approx(5)


def test_enpi_farkli_uretim_birimlerini_karistirmaz(db):
    electricity = _energy_type(db)
    meter = _meter(db, "Ana Trafo", electricity, is_main=True)
    _readings(db, meter, {"2026-01-01": 0, "2026-02-01": 10_000})
    _production(db, {"2026-01-31": (100, "ton"), "2026-01-30": (2000, "adet")})

    assert calc.enpi_series(db, "ton", electricity.id)["2026-01"] == pytest.approx(100)
    assert calc.enpi_series(db, "adet", electricity.id)["2026-01"] == pytest.approx(5)


def test_uretim_donem_gruplamasi(db):
    _production(
        db,
        {"2026-01-10": (120, "ton"), "2026-01-20": (135, "ton"), "2026-02-05": (100, "ton")},
    )

    assert calc.production_by_period(db, "ton") == {
        "2026-01": pytest.approx(255),
        "2026-02": pytest.approx(100),
    }
