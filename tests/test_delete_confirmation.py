"""Silme onayi, kullanici metninden bagimsiz olmali (FAZ 11 / K-1).

Eski yontemde onay metni satir ici JavaScript dizesine gomuluyordu:

    onsubmit="return confirm('{{ sayac.adi }} ... ')"

Jinja `'` karakterini `&#39;` yapiyor, tarayici ozniteligi JS'e vermeden once
decode ediyor ve dize kiriliyordu; sonucta onay penceresi HIC ACILMADAN kayit
siliniyordu. Artik metin data-onay ozniteliginde durur ve DOM uzerinden
okunur; kullanici metni hicbir zaman bir JS dizesinin icine girmez.
"""

from datetime import date

import pytest

from app import calc
from app.db import SessionLocal
from app.models import DirectConsumption, EnergyConversion, MeterReading, Production
from tests.factories import (
    conversion,
    direct_consumption,
    energy_type,
    meter,
    readings,
)

# Onay metnini kirabilecek karakterler ve gercek kullanimdaki ornekler.
ZOR_ADLAR = [
    "Kazan'ın Sayacı",
    "B Blok'un Sayacı",
    'Pompa & Kompresör',
    "<Test> Sayacı",
    'Kazan "A" Sayacı',
    "Çğıöşü ÇĞİÖŞÜ Sayacı",
]

SILME_EKRANLARI = ("readings.html", "conversions.html", "direct.html",
                   "production.html", "target_edit.html")


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _sablon(ad: str) -> str:
    from pathlib import Path

    return Path("app/templates", ad).read_text(encoding="utf-8")


def _script_govdeleri(sayfa: str) -> str:
    """Sayfadaki butun <script> bloklarinin icerigi."""
    import re

    return "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", sayfa, re.S))


def _js_dizesine_metin_gomulmus_mu(sayfa: str) -> bool:
    """confirm()/alert() cagrilarina dize sabiti gecirilmis mi?"""
    return "confirm('" in sayfa or 'confirm("' in sayfa


# --------------------------------------------------------------------------- #
# Mekanizma: kullanici metni artik JS dizesine gomulmuyor
# --------------------------------------------------------------------------- #


def test_silme_formlari_satir_ici_confirm_kullanmiyor():
    for ad in SILME_EKRANLARI:
        icerik = _sablon(ad)
        assert "onsubmit" not in icerik, f"{ad} hâlâ satır içi onsubmit kullanıyor"
        assert "confirm(" not in icerik, f"{ad} hâlâ JS dizesine metin gömüyor"


def test_silme_formlari_data_onay_tasiyor():
    for ad in SILME_EKRANLARI:
        assert "data-onay=" in _sablon(ad), f"{ad} içinde data-onay yok"


def test_hicbir_sablonun_script_blogunda_sunucu_verisi_yok():
    """JS'e veri yalnizca DOM (data-*) uzerinden gecer, sablon icinden degil.

    Bu kural K-1'in kok nedenini kapatir: sunucudan gelen metin hicbir zaman
    bir JavaScript kaynak dosyasinin parcasi haline gelmez.
    """
    from pathlib import Path

    for yol in sorted(Path("app/templates").glob("*.html")):
        govde = _script_govdeleri(yol.read_text(encoding="utf-8"))
        assert "{{" not in govde and "{%" not in govde, f"{yol.name}: script içinde şablon ifadesi var"


def test_ortak_onay_kodu_metni_dom_uzerinden_okuyor():
    temel = _sablon("base.html")
    assert "dataset.onay" in temel
    assert "preventDefault" in temel
    # Onay metni sunucudan JS'e dize sabiti olarak gecirilmiyor.
    assert not _js_dizesine_metin_gomulmus_mu(temel)
    # Sablon degiskeni de script blogunun icine girmiyor.
    assert "{{" not in _script_govdeleri(temel)


# --------------------------------------------------------------------------- #
# Zor karakterli adlarda onay metni bozulmuyor
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("ad", ZOR_ADLAR)
def test_okuma_silme_onayi_zor_adlarda_bozulmuyor(db, logged_in_client, ad):
    electricity = energy_type(db)
    record = meter(db, ad, electricity, is_main=True)
    readings(db, record, {"2026-01-01": 0, "2026-02-01": 1_000})

    sayfa = logged_in_client.get("/okumalar").text

    assert "data-onay=" in sayfa
    assert "okuması silinecek" in sayfa
    # Onay metni JS'e dize sabiti olarak gecirilmiyor...
    assert not _js_dizesine_metin_gomulmus_mu(sayfa)
    # ...ve sayacin adi hicbir <script> blogunun icinde gecmiyor.
    assert ad not in _script_govdeleri(sayfa)
    # Ham < > karakteri de sayfaya sizmiyor.
    assert "<Test>" not in sayfa


def test_dogrudan_tuketim_ve_katsayi_onaylari_da_guvenli(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz & <Kazan>'ın Hattı", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 10_000)
    conversion(db, gas, 0.0385, "2026-01-01")

    for yol, beklenen in (
        ("/dogrudan-tuketim", "doğrudan tüketim kaydı silinecek"),
        ("/tanimlar/donusum-katsayilari", "tarihli katsayı silinecek"),
    ):
        sayfa = logged_in_client.get(yol).text
        assert "data-onay=" in sayfa
        assert beklenen in sayfa
        assert not _js_dizesine_metin_gomulmus_mu(sayfa)
        assert gas.name not in _script_govdeleri(sayfa)


# --------------------------------------------------------------------------- #
# HTML kacisi bozulmadi
# --------------------------------------------------------------------------- #


def test_html_kacisi_korunuyor(db, logged_in_client):
    electricity = energy_type(db)
    record = meter(db, "<script>alert(1)</script> Sayacı", electricity)
    readings(db, record, {"2026-01-01": 0, "2026-02-01": 100})

    sayfa = logged_in_client.get("/okumalar").text

    assert "<script>alert(1)</script>" not in sayfa
    assert "&lt;script&gt;" in sayfa


def test_tirnak_ozniteligi_kirmiyor(db, logged_in_client):
    """Cift tirnakli ad, data-onay ozniteligini erken kapatmamali."""
    electricity = energy_type(db)
    record = meter(db, 'Kazan "A" Sayacı', electricity)
    readings(db, record, {"2026-01-01": 0, "2026-02-01": 100})

    sayfa = logged_in_client.get("/okumalar").text
    satir = next(s for s in sayfa.splitlines() if "data-onay=" in s)

    # Ham cift tirnak ozniteligin icine sizmamali (Jinja &#34; yapar).
    assert 'Kazan "A"' not in satir
    assert "&#34;" in satir or "&quot;" in satir


# --------------------------------------------------------------------------- #
# Silme davranisi ve sonrasinda hesabin yeniden uretilmesi
# --------------------------------------------------------------------------- #


def test_zor_adli_sayacin_okumasi_silinince_tuketim_yeniden_hesaplanir(
    db, logged_in_client
):
    electricity = energy_type(db)
    record = meter(db, "Kazan'ın Sayacı", electricity, is_main=True)
    readings(db, record, {"2026-01-01": 0, "2026-02-01": 1_000, "2026-03-01": 2_200})

    ocak = (date(2026, 1, 1), date(2026, 1, 31))
    assert calc.total(calc.factory_consumptions(db, *ocak)) == 1_000

    orta = db.query(MeterReading).filter_by(reading_date=date(2026, 2, 1)).one()
    response = logged_in_client.post(f"/okumalar/{orta.id}/sil")
    assert response.status_code == 200

    db.expire_all()
    # 01.01 -> 01.03 eslesir; Ocak tuketimi yeniden hesaplanir.
    assert calc.total(calc.factory_consumptions(db, *ocak)) == 2_200


def test_diger_silme_uclari_calismaya_devam_ediyor(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    kayit = direct_consumption(db, gas, "2026-01", 10_000)
    katsayi = conversion(db, gas, 0.0385, "2026-01-01")
    db.add(Production(production_date=date(2026, 1, 31), quantity=100, unit="ton"))
    db.commit()
    uretim = db.query(Production).one()

    assert logged_in_client.post(f"/dogrudan-tuketim/{kayit.id}/sil").status_code == 200
    assert logged_in_client.post(
        f"/tanimlar/donusum-katsayilari/{katsayi.id}/sil"
    ).status_code == 200
    assert logged_in_client.post(f"/uretim/{uretim.id}/sil").status_code == 200

    db.expire_all()
    assert db.query(DirectConsumption).count() == 0
    assert db.query(EnergyConversion).count() == 0
    assert db.query(Production).count() == 0


# --------------------------------------------------------------------------- #
# Ö-1: Carpan alaninin yardim metni
# --------------------------------------------------------------------------- #


def test_carpan_yardim_metni_olusturma_ekraninda_var(db, logged_in_client):
    energy_type(db)
    sayfa = logged_in_client.get("/tanimlar/sayaclar").text

    assert "endeks farkı bu katsayıyla" in sayfa
    assert "ölçü" in sayfa and "trafosu" in sayfa
    assert "sessizce yanlış hesaplar" in sayfa


def test_carpan_yardim_metni_duzenleme_ekraninda_var(db, logged_in_client):
    electricity = energy_type(db)
    record = meter(db, "Ana Trafo", electricity, is_main=True)

    sayfa = logged_in_client.get(f"/tanimlar/sayaclar/{record.id}").text

    assert "endeks farkı bu katsayıyla" in sayfa
    assert "ölçü" in sayfa and "trafosu" in sayfa


def test_carpan_yardim_metni_kesin_ifade_kullanmiyor(db, logged_in_client):
    """Kullaniciyi 'her zaman 1' diye yanlis yonlendirmemeli."""
    energy_type(db)
    sayfa = logged_in_client.get("/tanimlar/sayaclar").text

    assert "her zaman 1" not in sayfa
    assert "çoğunlukla 1" in sayfa


def test_carpan_davranisi_degismedi(db, logged_in_client):
    """Varsayilan 1, multiplier > 0 kurali ve hesap aynen duruyor."""
    electricity = energy_type(db)

    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Varsayılan", "energy_type_id": str(electricity.id),
              "multiplier": "1"},
    )
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Sıfır Çarpan", "energy_type_id": str(electricity.id),
              "multiplier": "0"},
    )
    assert response.status_code == 400
    assert "sıfırdan büyük" in response.text

    carpanli = meter(db, "Trafolu", electricity, multiplier=200.0, is_main=True)
    readings(db, carpanli, {"2026-01-01": 0, "2026-02-01": 50})
    ocak = (date(2026, 1, 1), date(2026, 1, 31))
    assert calc.total(calc.factory_consumptions(db, *ocak)) == 10_000
