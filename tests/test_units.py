"""Matematiksel birim donusumleri (app/units.py).

Bu testler veritabanina ve aga dokunmaz: modul saf hesaptir.
"""

import pytest

from app import units


# --------------------------------------------------------------------------- #
# 1-5. Temel enerji donusumleri
# --------------------------------------------------------------------------- #


def test_kwh_mj_donusumu():
    assert units.convert(1, "kWh", "MJ") == pytest.approx(3.6)
    assert units.convert(1_000, "kWh", "MJ") == pytest.approx(3_600)


def test_kwh_gj_donusumu():
    assert units.convert(1, "kWh", "GJ") == pytest.approx(0.0036)
    assert units.convert(1_000, "kWh", "GJ") == pytest.approx(3.6)


def test_gj_tep_donusumu():
    assert units.convert(41.868, "GJ", "TEP") == pytest.approx(1.0)
    assert units.convert(100, "GJ", "TEP") == pytest.approx(100 / 41.868)


def test_tep_gj_donusumu():
    assert units.convert(1, "TEP", "GJ") == pytest.approx(41.868)
    assert units.convert(2.5, "TEP", "GJ") == pytest.approx(104.67)


def test_gj_kwh_donusumu():
    assert units.convert(1, "GJ", "kWh") == pytest.approx(1 / 0.0036)
    assert units.convert(3.6, "GJ", "kWh") == pytest.approx(1_000)


# --------------------------------------------------------------------------- #
# 6. Standart katsayilarin dogrulugu
# --------------------------------------------------------------------------- #


def test_tep_tanimi_gj_uzerinden_turetilir():
    """1 TEP = 41,868 GJ = 10 Gcal = 11.630 kWh"""
    assert units.convert(1, "TEP", "GJ") == pytest.approx(41.868)
    assert units.convert(1, "TEP", "kWh") == pytest.approx(11_630)
    assert units.convert(1, "TEP", "Gcal") == pytest.approx(10.0)
    assert units.convert(1, "TEP", "kgep") == pytest.approx(1_000)


def test_jul_ailesi_ondalik_katlar():
    assert units.convert(1, "MJ", "GJ") == pytest.approx(0.001)
    assert units.convert(1, "GJ", "MJ") == pytest.approx(1_000)
    assert units.convert(1, "kJ", "MJ") == pytest.approx(0.001)
    assert units.convert(1, "TJ", "GJ") == pytest.approx(1_000)
    assert units.convert(1, "GJ", "J") == pytest.approx(1e9)


def test_vatsaat_ailesi():
    assert units.convert(1, "MWh", "kWh") == pytest.approx(1_000)
    assert units.convert(1, "GWh", "MWh") == pytest.approx(1_000)
    assert units.convert(1, "kWh", "Wh") == pytest.approx(1_000)
    assert units.convert(1, "Wh", "J") == pytest.approx(3_600)


def test_kalori_ve_britanya_birimleri():
    assert units.convert(1, "kcal", "kJ") == pytest.approx(4.1868)
    assert units.convert(1, "Gcal", "Mcal") == pytest.approx(1_000)
    assert units.convert(1, "BTU", "J") == pytest.approx(1_055.05585262)
    assert units.convert(1, "MMBTU", "BTU") == pytest.approx(1e6)
    assert units.convert(1, "therm", "BTU") == pytest.approx(100_000)


def test_ileri_geri_donusum_degeri_korur():
    for code in ("kWh", "MJ", "TEP", "Gcal", "MMBTU"):
        ara = units.convert(1_234.5, code, "GJ")
        assert units.convert(ara, "GJ", code) == pytest.approx(1_234.5)


def test_ayni_birime_donusum_degeri_degistirmez():
    assert units.convert(987.65, "kWh", "kWh") == pytest.approx(987.65)


# --------------------------------------------------------------------------- #
# Boyut altyapisi
# --------------------------------------------------------------------------- #


def test_enerji_boyutunun_referansi_gj():
    assert units.reference_unit(units.DIMENSION_ENERGY) == "GJ"
    assert units.get("GJ").factor == 1.0


def test_birim_kodu_buyuk_kucuk_harf_farkini_gozetmez():
    assert units.get("kwh").code == "kWh"
    assert units.get("GJ") is units.get("gj")


def test_tanimsiz_birim_hata_verir():
    with pytest.raises(units.UnknownUnit):
        units.get("Sm³")
    assert units.find("Sm³") is None
    assert units.is_known("Sm³") is False
    assert units.dimension_of("Sm³") is None


def test_yakit_birimleri_bilerek_tanimli_degildir():
    """Sm3, kg komur, litre LPG gibi birimler matematiksel olarak GJ'e cevrilemez.

    Bunlarin enerji icerigi yakita gore degisir; units modulunde varsayilan
    bir katsayi bulunmasi yanlis sonucu dogru gibi gosterirdi.
    """
    for code in ("Sm³", "Nm³", "kg", "lt", "ton"):
        assert units.is_known(code) is False


def test_farkli_boyut_donusumu_engellenir():
    """Bugun yalnizca enerji boyutu kayitli; kural yine de zorunludur."""
    uzunluk = "test-uzunluk"
    units.register("__m", "metre", uzunluk, 1.0)
    units.register("__km", "kilometre", uzunluk, 1000.0)
    try:
        assert units.convert(1, "__km", "__m") == pytest.approx(1_000)
        with pytest.raises(units.DimensionMismatch):
            units.convert(1, "kWh", "__m")
    finally:
        units._UNITS.pop("__m"), units._UNITS.pop("__km")
        units._REFERENCE.pop(uzunluk)


def test_enerji_birimleri_listelenebilir():
    kodlar = [unit.code for unit in units.units_of(units.DIMENSION_ENERGY)]
    for beklenen in ("kWh", "MJ", "GJ", "TEP"):
        assert beklenen in kodlar


# --------------------------------------------------------------------------- #
# 15. Internet bagimliligi yok
# --------------------------------------------------------------------------- #


def test_donusumler_internetsiz_calisir(monkeypatch):
    """Modul ag cagrisi yapmaz: soket acilmasi denenirse test kirilir."""
    import socket

    def _engelle(*args, **kwargs):
        raise AssertionError("Dönüşüm sırasında ağ bağlantısı denendi.")

    monkeypatch.setattr(socket, "socket", _engelle)
    monkeypatch.setattr(socket, "create_connection", _engelle)

    assert units.convert(1_000, "kWh", "GJ") == pytest.approx(3.6)
    assert units.convert(1, "TEP", "kWh") == pytest.approx(11_630)


def test_units_modulu_ag_kutuphanesi_kullanmaz():
    from pathlib import Path

    kaynak = Path("app/units.py").read_text(encoding="utf-8")
    for yasak in ("requests", "urllib", "httpx", "socket", "aiohttp"):
        assert yasak not in kaynak
