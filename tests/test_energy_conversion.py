"""Enerji icerigi katsayilari ve ortak birimde toplam enerji.

Kural hatirlatmasi:
  * Matematiksel birim donusumu (kWh -> GJ) units modulunde, sabittir.
  * Enerji icerigi katsayisi (Sm3 -> GJ) energy_conversion tablosunda,
    kullanici tarafindan girilir.
  * Katsayi yoksa donusum YAPILMAZ; deger sessizce 0 kabul edilmez.
"""

from datetime import date

import pytest

from app import calc, dashboard, reports, units
from app.db import SessionLocal
from tests.factories import (
    conversion,
    direct_consumption,
    energy_type,
    meter,
    production,
    readings,
)

OCAK = (date(2026, 1, 1), date(2026, 1, 31))
TEMMUZ = (date(2026, 7, 1), date(2026, 7, 31))
HAZIRAN = (date(2026, 6, 1), date(2026, 6, 30))
YIL_2026 = (date(2026, 1, 1), date(2026, 12, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _ana_sayac(db, energy, values, name="Ana Sayaç"):
    main = meter(db, name, energy, is_main=True)
    readings(db, main, values)
    return main


# --------------------------------------------------------------------------- #
# 7. Kullanici katsayisi standart degerin onune gecer
# --------------------------------------------------------------------------- #


def test_07_kullanici_katsayisi_standardin_onune_gecer(db):
    """Elektrik kWh: standart 1 kWh = 0,0036 GJ. Kullanici katsayisi kazanir."""
    electricity = energy_type(db)

    standart = calc.convert_energy(db, electricity, 1_000, "GJ", date(2026, 1, 1))
    assert standart.convertible is True
    assert standart.value == pytest.approx(3.6)
    assert standart.coefficient == pytest.approx(0.0036)
    assert standart.source == calc.FACTOR_SOURCE_STANDARD

    # Kullanici, kendi kaybini da iceren bir katsayi tanimlar.
    conversion(db, electricity, 0.0040, "2026-01-01", source="Tedarikçi")
    kullanici = calc.convert_energy(db, electricity, 1_000, "GJ", date(2026, 1, 1))
    assert kullanici.value == pytest.approx(4.0)
    assert kullanici.coefficient == pytest.approx(0.0040)
    assert kullanici.source == "Tedarikçi"


def test_07b_standart_katsayi_yalnizca_enerji_birimlerinde_vardir(db):
    """Sm3 matematiksel olarak GJ'e cevrilemez; katsayi girilene kadar yok."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")

    once = calc.convert_energy(db, gas, 10_000, "GJ", date(2026, 1, 1))
    assert once.convertible is False
    assert once.value is None

    conversion(db, gas, 0.0385, "2026-01-01")
    sonra = calc.convert_energy(db, gas, 10_000, "GJ", date(2026, 1, 1))
    assert sonra.convertible is True
    assert sonra.value == pytest.approx(385.0)
    assert sonra.source == "Kullanıcı"


# --------------------------------------------------------------------------- #
# 8. valid_from ile tarihsel katsayi secimi
# --------------------------------------------------------------------------- #


def test_08_donemine_uyan_en_yeni_katsayi_kullanilir(db):
    """01.01.2026 -> A, 01.07.2026 -> B. Haziran A, Temmuz B kullanir."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0380, "2026-01-01", source="A")
    conversion(db, gas, 0.0390, "2026-07-01", source="B")

    haziran = calc.convert_energy(db, gas, 1_000, "GJ", date(2026, 6, 1))
    temmuz = calc.convert_energy(db, gas, 1_000, "GJ", date(2026, 7, 1))

    assert haziran.coefficient == pytest.approx(0.0380)
    assert haziran.source == "A"
    assert temmuz.coefficient == pytest.approx(0.0390)
    assert temmuz.source == "B"


def test_08b_katsayidan_onceki_donemde_katsayi_uygulanmaz(db):
    """Ileri tarihli bir katsayi gecmise uygulanmaz."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-07-01")

    onceki = calc.convert_energy(db, gas, 1_000, "GJ", date(2026, 6, 1))
    assert onceki.convertible is False
    assert "geçerli dönüşüm katsayısı bulunamadı" in onceki.reason


def test_08c_donem_icinde_degisen_katsayi_her_aya_ayri_uygulanir(db):
    """Yillik toplamda Haziran A, Temmuz B katsayisiyla cevrilir."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0380, "2026-01-01", source="A")
    conversion(db, gas, 0.0390, "2026-07-01", source="B")
    direct_consumption(db, gas, "2026-06", 1_000)
    direct_consumption(db, gas, "2026-07", 1_000)

    totals = calc.energy_totals(db, *YIL_2026)
    row = totals["rows"][0]
    assert totals["value"] == pytest.approx(38.0 + 39.0)
    # Iki farkli katsayi kullanildiginda tek bir katsayi yazilmaz.
    assert row["coefficient"] is None
    assert row["source"] == "A / B"


# --------------------------------------------------------------------------- #
# 9. Katsayi yoksa convertible=False
# --------------------------------------------------------------------------- #


def test_09_katsayi_bulunamazsa_convertible_false(db):
    coal = energy_type(db, name="Kömür", unit="ton")
    result = calc.convert_energy(db, coal, 50, "GJ", date(2026, 1, 1))

    assert result.convertible is False
    assert result.value is None
    assert result.coefficient is None
    assert result.source is None
    assert result.reason == (
        "Kömür için geçerli dönüşüm katsayısı bulunamadı (ton → GJ)."
    )


# --------------------------------------------------------------------------- #
# 10. Farkli enerji turleri GJ'de toplanir
# --------------------------------------------------------------------------- #


def test_10_farkli_enerji_turleri_gj_uzerinden_toplanir(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    lpg = energy_type(db, name="LPG", unit="kg")
    conversion(db, gas, 0.0385, "2026-01-01")
    conversion(db, lpg, 0.0460, "2026-01-01")

    direct_consumption(db, electricity, "2026-01", 100_000)  # 360 GJ
    direct_consumption(db, gas, "2026-01", 10_000)  # 385 GJ
    direct_consumption(db, lpg, "2026-01", 1_000)  # 46 GJ

    totals = calc.energy_totals(db, *OCAK)
    assert totals["complete"] is True
    assert totals["unit"] == "GJ"
    assert totals["value"] == pytest.approx(360 + 385 + 46)
    assert len(totals["rows"]) == 3


def test_10b_hicbir_tuketimi_olmayan_enerji_turu_satir_uretmez(db):
    electricity = energy_type(db)
    energy_type(db, name="Doğal Gaz", unit="Sm³")  # veri yok, katsayi da yok
    direct_consumption(db, electricity, "2026-01", 1_000)

    totals = calc.energy_totals(db, *OCAK)
    # Katsayisi olmayan tur veri tasimadigi icin toplami bozmaz.
    assert totals["complete"] is True
    assert [row["energy_type"].name for row in totals["rows"]] == ["Elektrik"]


# --------------------------------------------------------------------------- #
# 11. Eksik katsayi sessizce 0 sayilmaz
# --------------------------------------------------------------------------- #


def test_11_eksik_katsayi_sessizce_sifir_yapilmaz(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, electricity, "2026-01", 100_000)
    direct_consumption(db, gas, "2026-01", 10_000)

    totals = calc.energy_totals(db, *OCAK)

    assert totals["complete"] is False
    assert totals["value"] is None  # kismi toplam URETILMEZ
    assert totals["missing"] == ["Doğal Gaz"]
    assert totals["message"] == (
        "Toplam enerji GJ olarak hesaplanamadı: Doğal Gaz için geçerli "
        "dönüşüm katsayısı bulunamadı."
    )

    # Ham tuketim silinmez, satir kaybolmaz: kullanici neyin eksik oldugunu gorur.
    gas_row = next(row for row in totals["rows"] if row["energy_type"].id == gas.id)
    assert gas_row["raw_total"] == pytest.approx(10_000)
    assert gas_row["raw_unit"] == "Sm³"
    assert gas_row["value"] is None
    assert gas_row["convertible"] is False


def test_11b_katsayi_eklenince_toplam_tamamlanir(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, electricity, "2026-01", 100_000)
    direct_consumption(db, gas, "2026-01", 10_000)
    assert calc.energy_totals(db, *OCAK)["complete"] is False

    conversion(db, gas, 0.0385, "2026-01-01")
    totals = calc.energy_totals(db, *OCAK)
    assert totals["complete"] is True
    assert totals["value"] == pytest.approx(360 + 385)
    assert totals["message"] is None


# --------------------------------------------------------------------------- #
# 12. Panel toplami = rapor toplami
# --------------------------------------------------------------------------- #


def test_12_panel_ve_rapor_toplam_enerjisi_ayni(db):
    electricity = energy_type(db, price=2.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    conversion(db, gas, 0.0385, "2026-01-01")
    _ana_sayac(db, electricity, {"2026-01-01": 0, "2026-02-01": 100_000})
    direct_consumption(db, gas, "2026-01", 10_000)

    for unit in calc.DISPLAY_ENERGY_UNITS:
        panel = dashboard.combined_energy(db, "2026-01", unit)
        rapor = calc.energy_totals(db, *OCAK, to_unit=unit)
        assert panel["value"] == pytest.approx(rapor["value"])
        assert panel["unit"] == rapor["unit"] == unit


def test_12b_rapor_satirlari_panel_satirlariyla_ayni(db):
    electricity = energy_type(db, price=2.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    conversion(db, gas, 0.0385, "2026-01-01")
    direct_consumption(db, electricity, "2026-01", 100_000)
    direct_consumption(db, gas, "2026-01", 10_000)

    panel = dashboard.combined_energy(db, "2026-01", "GJ")
    rapor_satirlari = reports.rows_by_energy_type(db, *OCAK)
    panel_degerleri = {
        row["energy_type"].id: row["value"] for row in panel["rows"]
    }
    for row in rapor_satirlari:
        conversion_row = row["conversion"]
        assert conversion_row is not None
        assert conversion_row["value"] == pytest.approx(
            panel_degerleri[row["energy_type"].id]
        )


def test_12c_panel_ve_rapor_ekranlari_ayni_sayiyi_yazar(db, logged_in_client):
    electricity = energy_type(db, price=2.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    conversion(db, gas, 0.0385, "2026-01-01")
    direct_consumption(db, electricity, "2026-01", 100_000)  # 360 GJ
    direct_consumption(db, gas, "2026-01", 10_000)  # 385 GJ

    panel = logged_in_client.get("/?donem=2026-01&enerji_birimi=GJ").text
    rapor = logged_in_client.get(
        "/rapor?baslangic=2026-01-01&bitis=2026-01-31&enerji_birimi=GJ"
    ).text
    assert "745,00" in panel  # 360 + 385
    assert "745,00" in rapor


# --------------------------------------------------------------------------- #
# 13. EnPI GJ bazinda
# --------------------------------------------------------------------------- #


def test_13_birlesik_enpi_gj_bazinda_hesaplanir(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-01-01")
    direct_consumption(db, electricity, "2026-01", 100_000)  # 360 GJ
    direct_consumption(db, gas, "2026-01", 10_000)  # 385 GJ
    production(db, {"2026-01-31": (100, "ton")})

    result = calc.combined_enpi(db, "ton", *OCAK, to_unit="GJ")
    assert result["value"] == pytest.approx(7.45)  # 745 GJ / 100 ton
    assert result["unit"] == "GJ"
    assert result["production"] == pytest.approx(100)


def test_13b_eksik_katsayi_varken_birlesik_enpi_uretilmez(db):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")  # katsayi yok
    direct_consumption(db, electricity, "2026-01", 100_000)
    direct_consumption(db, gas, "2026-01", 10_000)
    production(db, {"2026-01-31": (100, "ton")})

    result = calc.combined_enpi(db, "ton", *OCAK, to_unit="GJ")
    assert result["value"] is None
    assert result["energy"]["missing"] == ["Doğal Gaz"]

    # Tek enerji turunun kendi birimindeki EnPI'si etkilenmez.
    summary = dashboard.energy_summary(db, electricity, "2026-01")
    tekil = dashboard.production_summary(db, "ton", "2026-01", summary["total"])
    assert tekil["enpi"] == pytest.approx(1_000)


def test_13c_uretim_yoksa_birlesik_enpi_none(db):
    electricity = energy_type(db)
    direct_consumption(db, electricity, "2026-01", 100_000)

    result = calc.combined_enpi(db, "ton", *OCAK, to_unit="GJ")
    assert result["value"] is None
    assert result["energy"]["complete"] is True


# --------------------------------------------------------------------------- #
# 14. TEP hesabi GJ uzerinden
# --------------------------------------------------------------------------- #


def test_14_tep_gj_uzerinden_turetilir(db):
    electricity = energy_type(db)
    direct_consumption(db, electricity, "2026-01", 11_630)  # tam 1 TEP

    gj = calc.energy_totals(db, *OCAK, to_unit="GJ")
    tep = calc.energy_totals(db, *OCAK, to_unit="TEP")

    assert gj["value"] == pytest.approx(41.868)
    assert tep["value"] == pytest.approx(1.0)
    assert tep["value"] == pytest.approx(units.convert(gj["value"], "GJ", "TEP"))


def test_14b_tep_icin_ayri_enerji_turu_katsayisi_tanimlanmaz(db):
    """TEP katsayisi her enerji turu icin ayri girilmez; GJ'den turetilir."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-01-01")  # yalnizca GJ katsayisi
    direct_consumption(db, gas, "2026-01", 10_000)

    tep = calc.energy_totals(db, *OCAK, to_unit="TEP")
    assert tep["value"] == pytest.approx(385 / 41.868)
    # Ayni katsayi, hedef birime gore kendiliginden olceklenir.
    row = tep["rows"][0]
    assert row["coefficient"] == pytest.approx(0.0385 / 41.868)


def test_14c_butun_gosterim_birimleri_ayni_enerjiyi_gosterir(db):
    electricity = energy_type(db)
    direct_consumption(db, electricity, "2026-01", 100_000)

    gj = calc.energy_totals(db, *OCAK, to_unit="GJ")["value"]
    for unit in calc.DISPLAY_ENERGY_UNITS:
        value = calc.energy_totals(db, *OCAK, to_unit=unit)["value"]
        assert value == pytest.approx(units.convert(gj, "GJ", unit))


# --------------------------------------------------------------------------- #
# 15. Internetsiz calisma
# --------------------------------------------------------------------------- #


def test_15_donusum_internet_olmadan_calisir(db, monkeypatch):
    import socket

    def _engelle(*args, **kwargs):
        raise AssertionError("Dönüşüm sırasında ağ bağlantısı denendi.")

    monkeypatch.setattr(socket, "socket", _engelle)
    monkeypatch.setattr(socket, "create_connection", _engelle)

    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-01-01")
    direct_consumption(db, gas, "2026-01", 10_000)

    assert calc.energy_totals(db, *OCAK)["value"] == pytest.approx(385.0)


# --------------------------------------------------------------------------- #
# 16-19. Mevcut davranis korunuyor
# --------------------------------------------------------------------------- #


def test_16_dogrudan_tuketim_onceligi_bozulmadi(db):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-01-01")
    _ana_sayac(db, gas, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 12_500)

    # Ham tuketim: dogrudan deger kazanir, toplanmaz.
    assert calc.total(calc.factory_consumptions(db, *OCAK)) == pytest.approx(12_500)
    # Donusum de ayni ham degerden hesaplanir.
    assert calc.energy_totals(db, *OCAK)["value"] == pytest.approx(12_500 * 0.0385)


def test_17_sayac_tuketimi_ve_donem_kurali_bozulmadi(db):
    electricity = energy_type(db)
    _ana_sayac(db, electricity, {"2026-01-01": 0, "2026-02-01": 1_000})

    # Donem kurali: tuketim ilk okumanin ayina yazilir.
    assert calc.total(calc.factory_consumptions(db, *OCAK)) == pytest.approx(1_000)
    assert calc.energy_totals(db, *OCAK)["value"] == pytest.approx(3.6)
    subat = (date(2026, 2, 1), date(2026, 2, 28))
    assert calc.energy_totals(db, *subat)["rows"] == []


def test_18_maliyet_donusumden_etkilenmez(db):
    """Maliyet her zaman enerji turunun kendi birim fiyatindan hesaplanir."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    direct_consumption(db, gas, "2026-01", 10_000)

    once = dashboard.energy_summary(db, gas, "2026-01")["cost"]
    conversion(db, gas, 0.0385, "2026-01-01")
    sonra = dashboard.energy_summary(db, gas, "2026-01")["cost"]

    assert once == pytest.approx(85_000)
    assert sonra == pytest.approx(85_000)  # katsayi maliyeti degistirmez
    assert reports.rows_by_energy_type(db, *OCAK)[0]["cost"] == pytest.approx(85_000)


def test_19_hedef_hesabi_donusumden_etkilenmez(db):
    from app.models import Target

    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 12_500)
    db.add(Target(year_month="2026-01", energy_type_id=gas.id, target_value=12_000))
    db.commit()

    once = dashboard.energy_summary(db, gas, "2026-01")["target"]
    conversion(db, gas, 0.0385, "2026-01-01")
    sonra = dashboard.energy_summary(db, gas, "2026-01")["target"]

    # Hedef, enerji turunun kendi biriminde kalir (Sm3), GJ'e tasinmaz.
    assert once["actual"] == pytest.approx(12_500)
    assert once == sonra
    assert sonra["exceeded"] is True


# --------------------------------------------------------------------------- #
# Katsayi tanimlama ekrani
# --------------------------------------------------------------------------- #


def test_katsayi_ekranda_tanimlanabilir(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 10_000)

    response = logged_in_client.post(
        "/tanimlar/donusum-katsayilari",
        data={
            "energy_type_id": str(gas.id),
            "factor": "0,0385",
            "valid_from": "2026-01-01",
            "source": "Tedarikçi",
            "note": "Fatura değeri, üst ısıl değer",
        },
    )
    assert response.status_code == 200
    assert calc.energy_totals(db, *OCAK)["value"] == pytest.approx(385.0)

    page = logged_in_client.get("/tanimlar/donusum-katsayilari").text
    assert "0,038500" in page
    assert "Tedarikçi" in page
    assert "üst ısıl değer" in page


def test_ayni_tarih_icin_ikinci_katsayi_engellenir(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    conversion(db, gas, 0.0385, "2026-01-01")

    response = logged_in_client.post(
        "/tanimlar/donusum-katsayilari",
        data={
            "energy_type_id": str(gas.id),
            "factor": "0,0390",
            "valid_from": "2026-01-01",
            "source": "Kullanıcı",
        },
    )
    assert response.status_code == 400
    assert "zaten tanımlı" in response.text
    assert len(calc.energy_conversion_records(db)) == 1


def test_sifir_veya_negatif_katsayi_kabul_edilmez(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    for deger in ("0", "-0,5"):
        response = logged_in_client.post(
            "/tanimlar/donusum-katsayilari",
            data={
                "energy_type_id": str(gas.id),
                "factor": deger,
                "valid_from": "2026-01-01",
                "source": "Kullanıcı",
            },
        )
        assert response.status_code == 400
        assert "sıfırdan büyük" in response.text
    assert calc.energy_conversion_records(db) == []


def test_katsayi_silininince_toplam_yeniden_eksik_olur(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    record = conversion(db, gas, 0.0385, "2026-01-01")
    direct_consumption(db, gas, "2026-01", 10_000)
    assert calc.energy_totals(db, *OCAK)["complete"] is True

    response = logged_in_client.post(
        f"/tanimlar/donusum-katsayilari/{record.id}/sil"
    )
    assert response.status_code == 200

    totals = calc.energy_totals(db, *OCAK)
    assert totals["complete"] is False
    assert totals["missing"] == ["Doğal Gaz"]
    # Ham tuketim silinmez.
    assert totals["rows"][0]["raw_total"] == pytest.approx(10_000)
