"""Gercek kullanimda ortaya cikan sinir durumlari (Faz 10).

Bu asamada hesaplama mantigi DEGISMEDI. Eklenen tek sey, kullanicinin
sonucu yanlis yorumlamasina yol acabilecek durumlarda acik uyari ve
dogrulamadir. Her testin ikinci yarisi, hesap sonuclarinin ayni kaldigini
dogrular.
"""

from datetime import date

import pytest

from app import calc, dashboard, reports
from app.db import SessionLocal
from app.models import EnergyType, Meter, MeterReading, Target
from tests.factories import (
    conversion,
    department,
    direct_consumption,
    energy_type,
    meter,
    production,
    readings,
)

OCAK = (date(2026, 1, 1), date(2026, 1, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def _meter_form(record, **degisiklik):
    """Sayac duzenleme formunun mevcut degerleri; degistirilenler uzerine yazilir."""
    form = {
        "name": record.name,
        "energy_type_id": str(record.energy_type_id),
        "department_id": str(record.department_id or ""),
        "serial_no": record.serial_no or "",
        "multiplier": str(record.multiplier),
        "is_active": "on" if record.is_active else "",
    }
    if record.is_main:
        form["is_main"] = "on"
    form.update(degisiklik)
    return {key: value for key, value in form.items() if value != ""}


# --------------------------------------------------------------------------- #
# 1. Enerji turu degistirme
# --------------------------------------------------------------------------- #


def test_01_okumasi_olan_sayacin_enerji_turu_onaysiz_degismez(db, logged_in_client):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000})

    response = logged_in_client.post(
        f"/tanimlar/sayaclar/{main.id}", data=_meter_form(main, energy_type_id=str(gas.id))
    )

    assert response.status_code == 400
    assert "GEÇMİŞ tüketimler" in response.text
    assert "onay kutusunu işaretleyin" in response.text
    db.expire_all()
    assert db.get(Meter, main.id).energy_type_id == electricity.id
    # Hesap degismedi.
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 1_000


def test_01b_onay_isaretlenince_enerji_turu_degisir(db, logged_in_client):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000})

    response = logged_in_client.post(
        f"/tanimlar/sayaclar/{main.id}",
        data=_meter_form(main, energy_type_id=str(gas.id), onay="on"),
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.get(Meter, main.id).energy_type_id == gas.id
    # Gecmis tuketim artik yeni enerji turune sayilir: uyarinin soyledigi sey.
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 0
    assert calc.total(calc.factory_consumptions(db, *OCAK, gas.id)) == 1_000


def test_01c_okumasi_olmayan_sayacta_onay_istenmez(db, logged_in_client):
    electricity = energy_type(db)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    yeni = meter(db, "Yeni Sayaç", electricity)

    response = logged_in_client.post(
        f"/tanimlar/sayaclar/{yeni.id}", data=_meter_form(yeni, energy_type_id=str(gas.id))
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.get(Meter, yeni.id).energy_type_id == gas.id


def test_01d_enerji_turu_disindaki_alanlar_onaysiz_degisir(db, logged_in_client):
    electricity = energy_type(db)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000})

    response = logged_in_client.post(
        f"/tanimlar/sayaclar/{main.id}", data=_meter_form(main, name="Ana Trafo 1")
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.get(Meter, main.id).name == "Ana Trafo 1"


# --------------------------------------------------------------------------- #
# 2. Ana sayac + departman
# --------------------------------------------------------------------------- #


def test_02_bolume_bagli_ana_sayac_bolum_dagilimina_girmez(db):
    """Davranis DEGISMEDI: ana sayac fabrika toplamindadir, dagilimda degil."""
    electricity = energy_type(db)
    press = department(db, name="Pres")
    main = meter(db, "Ana Trafo", electricity, dept=press, is_main=True)
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 10_000})
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    breakdown = dashboard.department_breakdown(db, electricity, *OCAK, 10_000)
    rows = {row["label"]: row["value"] for row in breakdown["rows"]}

    assert rows["Pres"] == pytest.approx(4_000)  # ana sayacin 10.000'i eklenmez
    assert rows["Ölçülmeyen / dağıtılmamış"] == pytest.approx(6_000)
    assert breakdown["measured"] == pytest.approx(4_000)


def test_02b_sayac_ekranlarinda_ana_sayac_hatirlatmasi_var(db, logged_in_client):
    energy_type(db)
    record = meter(db, "Ana Trafo", db.get(EnergyType, 1), is_main=True)

    for url in ("/tanimlar/sayaclar", f"/tanimlar/sayaclar/{record.id}"):
        page = logged_in_client.get(url).text
        assert "Ana sayaçlar fabrika toplamında kullanılır" in page
        assert "bölüm dağılımına" in page


# --------------------------------------------------------------------------- #
# 3. Ana sayac okumasi yok
# --------------------------------------------------------------------------- #


def test_03_ana_sayac_okumasi_yokken_uyari_verilir(db):
    electricity = energy_type(db)
    press = department(db, name="Pres")
    meter(db, "Ana Trafo", electricity, is_main=True)  # okumasi yok
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    # Oncelik kurali DEGISMEDI: alt sayac ana sayacin yerine gecmez.
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 0

    gaps = calc.main_meter_gaps(db, *OCAK)
    assert len(gaps) == 1
    assert gaps[0]["enerji_turu"] == "Elektrik"
    assert gaps[0]["ana_sayaclar"] == ["Ana Trafo"]
    assert gaps[0]["alt_toplam"] == pytest.approx(4_000)
    assert dashboard.energy_summary(db, electricity, "2026-01")["main_meter_gap"]


def test_03b_uyari_panelde_ve_raporda_gorunur(db, logged_in_client):
    electricity = energy_type(db)
    press = department(db, name="Pres")
    meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    panel = logged_in_client.get("/?donem=2026-01").text
    rapor = logged_in_client.get("/rapor?baslangic=2026-01-01&bitis=2026-01-31").text

    for page in (panel, rapor):
        assert "Ana Trafo" in page
        assert "alt sayaçlarda" in page.lower()
        assert "ana sayaç yerine geçmez" in page.lower()


def test_03c_ana_sayac_okumasi_varken_uyari_yok(db):
    electricity = energy_type(db)
    press = department(db, name="Pres")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 10_000})
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    assert calc.main_meter_gaps(db, *OCAK) == []


def test_03d_dogrudan_tuketim_varken_uyari_verilmez(db):
    """Dogrudan tuketim girilen ayda fabrika toplami eksik degildir."""
    electricity = energy_type(db)
    press = department(db, name="Pres")
    meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})
    direct_consumption(db, electricity, "2026-01", 10_000)

    assert calc.main_meter_gaps(db, *OCAK) == []
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 10_000


def test_03e_ana_sayaci_olmayan_turde_uyari_yok(db):
    """Ana sayac tanimli degilse tum sayaclar kullanilir; eksiklik yoktur."""
    electricity = energy_type(db)
    press = department(db, name="Pres")
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    assert calc.main_meter_gaps(db, *OCAK) == []
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 4_000


# --------------------------------------------------------------------------- #
# 4. Pasif enerji turu
# --------------------------------------------------------------------------- #


def _pasiflestir(db, record):
    record.is_active = False
    db.commit()


def test_04_pasif_ture_yeni_sayac_baglanamaz(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _pasiflestir(db, gas)

    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Gaz Sayacı", "energy_type_id": str(gas.id), "multiplier": "1"},
    )

    assert response.status_code == 400
    assert "Pasif türlere yeni sayaç bağlanamaz" in response.text
    assert db.query(Meter).count() == 0


def test_04b_pasif_ture_yeni_hedef_girilemez(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _pasiflestir(db, gas)

    response = logged_in_client.post(
        "/hedefler",
        data={
            "year_month": "2026-01",
            "energy_type_id": str(gas.id),
            "target_value": "1.000",
        },
    )

    assert response.status_code == 400
    assert "Pasif türlere yeni hedef girilemez" in response.text
    assert db.query(Target).count() == 0


def test_04c_pasif_ture_dogrudan_tuketim_girilemez(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    _pasiflestir(db, gas)

    response = logged_in_client.post(
        "/dogrudan-tuketim",
        data={
            "year_month": "2026-01",
            "energy_type_id": str(gas.id),
            "quantity": "1.000",
        },
    )

    assert response.status_code == 400
    assert "Pasif türlere yeni tüketim girilemez" in response.text


def test_04d_mevcut_sayac_pasif_turde_kalabilir(db, logged_in_client):
    """Pasiflestirme gecmisi kilitlemez: mevcut sayacin adi yine duzeltilebilir."""
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    record = meter(db, "Gaz Sayacı", gas)
    _pasiflestir(db, gas)

    response = logged_in_client.post(
        f"/tanimlar/sayaclar/{record.id}", data=_meter_form(record, name="Gaz Sayacı 1")
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.get(Meter, record.id).name == "Gaz Sayacı 1"


def test_04e_pasif_tur_panel_ve_raporda_isaretlenir(db, logged_in_client):
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³")
    direct_consumption(db, gas, "2026-01", 10_000)
    _pasiflestir(db, gas)

    panel = logged_in_client.get(f"/?donem=2026-01&enerji={gas.id}").text
    rapor = logged_in_client.get("/rapor?baslangic=2026-01-01&bitis=2026-01-31").text

    assert "pasif bir enerji türüdür" in panel
    assert "(pasif)" in rapor
    # Gecmis hesaplar korunur.
    assert calc.total(calc.factory_consumptions(db, *OCAK, gas.id)) == 10_000


# --------------------------------------------------------------------------- #
# 5. Sayac okumasi silme
# --------------------------------------------------------------------------- #


def test_05_okuma_silme_onayi_donem_tuketimini_soyluyor(db, logged_in_client):
    electricity = energy_type(db)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000})

    page = logged_in_client.get("/okumalar").text
    assert "ilgili dönem tüketimleri değişir" in page
    assert "maliyet ve EnPI" in page


def test_05b_okuma_silinince_tuketim_gercekten_degisir(db, logged_in_client):
    """Uyarinin dogru oldugunu dogrular: silme sonrasi donem tuketimi degisir."""
    electricity = energy_type(db)
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 1_000, "2026-03-01": 2_200})
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 1_000

    orta = (
        db.query(MeterReading)
        .filter(MeterReading.reading_date == date(2026, 2, 1))
        .one()
    )
    response = logged_in_client.post(f"/okumalar/{orta.id}/sil")
    assert response.status_code == 200

    db.expire_all()
    # 01.01 -> 01.03 esleserek Ocak'a 2.200 yazilir.
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 2_200


# --------------------------------------------------------------------------- #
# 6. Tanim degisiklikleri gecmis raporlari etkiler
# --------------------------------------------------------------------------- #


def test_06_sayac_duzenleme_ekraninda_gecmis_rapor_uyarisi_var(db, logged_in_client):
    electricity = energy_type(db)
    record = meter(db, "Ana Trafo", electricity, is_main=True)

    page = logged_in_client.get(f"/tanimlar/sayaclar/{record.id}").text
    assert "geçmiş raporları da etkiler" in page
    for konu in ("bölüm değiştirilirse", "ana/alt durumu", "çarpan"):
        assert konu in page


def test_06b_enerji_turu_duzenleme_ekraninda_gecmis_rapor_uyarisi_var(
    db, logged_in_client
):
    electricity = energy_type(db)

    page = logged_in_client.get(f"/tanimlar/enerji-turleri/{electricity.id}").text
    assert "geçmiş raporları da etkiler" in page
    assert "birim fiyat" in page.lower()


def test_06c_bolum_degisikligi_gecmis_dagilimi_gercekten_degistirir(db, logged_in_client):
    """Uyarinin dogru oldugunu dogrular."""
    electricity = energy_type(db)
    press = department(db, name="Pres")
    packing = department(db, name="Paketleme")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Pano", electricity, dept=press)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 10_000})
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 4_000})

    once = dashboard.department_breakdown(db, electricity, *OCAK, 10_000)
    assert {row["label"] for row in once["rows"]} >= {"Pres"}

    logged_in_client.post(
        f"/tanimlar/sayaclar/{sub.id}", data=_meter_form(sub, department_id=str(packing.id))
    )
    db.expire_all()

    sonra = dashboard.department_breakdown(db, electricity, *OCAK, 10_000)
    labels = {row["label"]: row["value"] for row in sonra["rows"]}
    assert "Pres" not in labels
    assert labels["Paketleme"] == pytest.approx(4_000)


# --------------------------------------------------------------------------- #
# Hesaplarin degismedigi: fabrika toplami, dagilim, oncelik, maliyet,
# EnPI ve GJ/TEP donusumu
# --------------------------------------------------------------------------- #


def test_hesaplar_degismedi(db):
    electricity = energy_type(db, price=2.0)
    gas = energy_type(db, name="Doğal Gaz", unit="Sm³", price=8.5)
    press = department(db, name="Pres")
    conversion(db, gas, 0.0385, "2026-01-01")

    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Pres Panosu", electricity, dept=press)
    readings(db, main, {"2026-01-01": 0, "2026-02-01": 100_000})
    readings(db, sub, {"2026-01-01": 0, "2026-02-01": 40_000})
    gas_main = meter(db, "Gaz Ana", gas, is_main=True)
    readings(db, gas_main, {"2026-01-01": 0, "2026-02-01": 12_180})
    direct_consumption(db, gas, "2026-01", 10_000)
    production(db, {"2026-01-31": (100, "ton")})

    # Fabrika toplami
    assert calc.total(calc.factory_consumptions(db, *OCAK, electricity.id)) == 100_000
    # Dogrudan tuketim onceligi (toplanmaz)
    assert calc.total(calc.factory_consumptions(db, *OCAK, gas.id)) == 10_000

    # Bolum dagilimi
    breakdown = dashboard.department_breakdown(db, electricity, *OCAK, 100_000)
    rows = {row["label"]: row["value"] for row in breakdown["rows"]}
    assert rows["Pres"] == pytest.approx(40_000)
    assert rows["Ölçülmeyen / dağıtılmamış"] == pytest.approx(60_000)

    # Maliyet
    summary = dashboard.energy_summary(db, electricity, "2026-01")
    assert summary["cost"] == pytest.approx(200_000)
    assert dashboard.energy_summary(db, gas, "2026-01")["cost"] == pytest.approx(85_000)

    # EnPI (tekil)
    assert dashboard.production_summary(db, "ton", "2026-01", 100_000)["enpi"] == 1_000

    # GJ / TEP donusumu
    gj = calc.energy_totals(db, *OCAK, to_unit="GJ")
    assert gj["complete"] is True
    assert gj["value"] == pytest.approx(360 + 385)
    assert calc.energy_totals(db, *OCAK, to_unit="TEP")["value"] == pytest.approx(
        745 / 41.868
    )

    # Panel = rapor
    rapor = reports.rows_by_energy_type(db, *OCAK)
    assert rapor[0]["total"] == pytest.approx(summary["total"])
