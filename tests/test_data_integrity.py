"""Veri butunlugu: Turkce sayi girisi ve yanlis kayitlarin duzeltilmesi.

9. asamadaki gercek kullanim testinde bulunan problemlerin regresyon testleri.
"""

from datetime import date

import pytest

from app import calc, dashboard
from app.db import SessionLocal
from app.models import MeterReading, Production, Target
from app.web import parse_number
from tests.factories import energy_type, meter, readings

OCAK = (date(2026, 1, 1), date(2026, 1, 31))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def sayac(logged_in_client):
    """Bir enerji turu ve bir ana sayac (carpan 40)."""
    logged_in_client.post(
        "/tanimlar/enerji-turleri",
        data={"name": "Elektrik", "unit": "kWh", "unit_price": "2"},
    )
    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Ana Trafo", "energy_type_id": "1", "multiplier": "40",
              "is_main": "on"},
    )
    return logged_in_client


def _add_reading(client, on_date, value):
    return client.post(
        "/okumalar",
        data={"meter_id": "1", "reading_date": on_date, "index_value": value},
    )


# --------------------------------------------------------------------------- #
# 1. Turkce sayi girisi
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "yazim, beklenen",
    [
        ("1.000", 1000),
        ("1.250,50", 1250.50),
        ("1250,5", 1250.5),
        ("1250.5", 1250.5),
        ("1000", 1000),
        ("0,5", 0.5),
        ("0.5", 0.5),
        ("12.500", 12_500),
        ("1.234.567", 1_234_567),
        ("12 500", 12_500),
    ],
)
def test_sayi_yazimlari_dogru_cozumlenir(yazim, beklenen):
    assert parse_number(yazim, "Değer") == pytest.approx(beklenen)


@pytest.mark.parametrize("yazim", ["abc", "1.000.5", "1,2,3", "1,5e3", "--5", ""])
def test_gecersiz_sayi_yazimlari_reddedilir(yazim):
    with pytest.raises(ValueError):
        parse_number(yazim, "Değer")


def test_binlik_ayracli_endeks_bin_kat_kucuk_kaydedilmez(sayac):
    """En kritik regresyon: '1.000' kesinlikle 1,0 olarak kaydedilmemeli."""
    assert _add_reading(sayac, "2025-12-31", "1.000").status_code == 200
    with SessionLocal() as db:
        assert db.get(MeterReading, 1).index_value == pytest.approx(1000)


def test_ekranda_gosterilen_bicim_tekrar_girilebilir(sayac):
    """Ekran '1.250,50' gosteriyor; ayni yazim giriste de kabul edilmeli."""
    _add_reading(sayac, "2025-12-31", "1.000")
    assert _add_reading(sayac, "2026-01-31", "1.250,50").status_code == 200

    with SessionLocal() as db:
        assert db.get(MeterReading, 2).index_value == pytest.approx(1250.50)
        assert calc.total(
            calc.factory_consumptions(db, start=OCAK[0], end=OCAK[1], energy_type_id=1)
        ) == pytest.approx(10_020)  # (1250,50 - 1000) x 40


def test_binlik_ayrac_diger_ekranlarda_da_calisir(sayac):
    assert sayac.post(
        "/uretim",
        data={"production_date": "2026-01-31", "quantity": "1.250", "unit": "ton"},
    ).status_code == 200
    assert sayac.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "17.000"},
    ).status_code == 200

    with SessionLocal() as db:
        assert db.get(Production, 1).quantity == pytest.approx(1250)
        assert db.get(Target, 1).target_value == pytest.approx(17_000)


# --------------------------------------------------------------------------- #
# 2. Sayac okumasi silme
# --------------------------------------------------------------------------- #


def test_yanlis_yuksek_endeks_silinip_dogrusu_girilebilir(sayac):
    """9. asamadaki kilitlenme senaryosu."""
    _add_reading(sayac, "2026-01-31", "25000")
    assert _add_reading(sayac, "2026-03-31", "180000").status_code == 200

    # Duzeltme denemesi engelleniyor (kural korunuyor).
    engel = _add_reading(sayac, "2026-04-30", "26000")
    assert engel.status_code == 400
    assert "küçük olamaz" in engel.text

    # Yanlis kayit siliniyor.
    silme = sayac.post("/okumalar/2/sil")
    assert silme.status_code == 200
    with SessionLocal() as db:
        assert db.get(MeterReading, 2) is None

    # Dogru deger artik girilebiliyor.
    assert _add_reading(sayac, "2026-03-31", "26000").status_code == 200
    with SessionLocal() as db:
        mart = calc.total(
            calc.factory_consumptions(
                db, start=date(2026, 3, 1), end=date(2026, 3, 31), energy_type_id=1
            )
        )
        assert mart == pytest.approx(40_000)  # (26.000 - 25.000) x 40


def test_silme_sonrasi_ayni_tarihe_yeniden_girilebilir(sayac):
    _add_reading(sayac, "2026-01-31", "1000")
    ikinci = _add_reading(sayac, "2026-01-31", "1100")
    assert ikinci.status_code == 400  # duplicate kurali korunuyor

    sayac.post("/okumalar/1/sil")
    assert _add_reading(sayac, "2026-01-31", "1100").status_code == 200
    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 1


def test_aradaki_okuma_silinince_eslesme_yeniden_kurulur(sayac):
    _add_reading(sayac, "2026-01-01", "1000")
    _add_reading(sayac, "2026-02-01", "1100")
    _add_reading(sayac, "2026-03-01", "1300")

    with SessionLocal() as db:
        assert len(calc.meter_consumptions(db, 1)) == 2

    sayac.post("/okumalar/2/sil")  # ortadaki kayit

    with SessionLocal() as db:
        entries = calc.meter_consumptions(db, 1)
        assert len(entries) == 1
        assert entries[0].previous_date == date(2026, 1, 1)
        assert entries[0].consumption == pytest.approx(12_000)  # (1300-1000) x 40


def test_silme_sonrasi_artan_endeks_kontrolu_yeni_duruma_gore_calisir(sayac):
    _add_reading(sayac, "2026-01-01", "1000")
    _add_reading(sayac, "2026-02-01", "5000")
    sayac.post("/okumalar/2/sil")

    # 5.000 kaydi silindigi icin 1.200 artik kabul edilebilir.
    assert _add_reading(sayac, "2026-02-01", "1200").status_code == 200
    # 900 hala reddedilir (1.000'den kucuk).
    assert _add_reading(sayac, "2026-03-01", "900").status_code == 400


def test_olmayan_okuma_silinemez(sayac):
    assert sayac.post("/okumalar/99/sil").status_code == 404


def test_silme_ekranda_onay_ister(sayac):
    _add_reading(sayac, "2026-01-31", "1000")
    page = sayac.get("/okumalar")
    assert "/okumalar/1/sil" in page.text
    assert "Onaylıyor musunuz?" in page.text


# --------------------------------------------------------------------------- #
# 3. Uretim kaydi silme
# --------------------------------------------------------------------------- #


@pytest.fixture
def uretimli(sayac):
    _add_reading(sayac, "2025-12-31", "1000")
    _add_reading(sayac, "2026-01-31", "1250")  # 10.000 kWh
    return sayac


def test_yanlis_uretim_silinip_dogrusu_girilebilir(uretimli):
    uretimli.post(
        "/uretim",
        data={"production_date": "2026-01-31", "quantity": "1000", "unit": "ton"},
    )
    with SessionLocal() as db:
        assert dashboard.production_summary(db, "ton", "2026-01", 10_000)["enpi"] == (
            pytest.approx(10)
        )

    # Ayni gune duzeltme girilemez (kural korunuyor).
    assert uretimli.post(
        "/uretim",
        data={"production_date": "2026-01-31", "quantity": "100", "unit": "ton"},
    ).status_code == 400

    # Silip dogrusunu girince EnPI duzeliyor.
    assert uretimli.post("/uretim/1/sil").status_code == 200
    assert uretimli.post(
        "/uretim",
        data={"production_date": "2026-01-31", "quantity": "100", "unit": "ton"},
    ).status_code == 200

    with SessionLocal() as db:
        assert db.query(Production).count() == 1
        assert calc.production_total(db, "ton", *OCAK) == pytest.approx(100)
        assert dashboard.production_summary(db, "ton", "2026-01", 10_000)["enpi"] == (
            pytest.approx(100)
        )


def test_olmayan_uretim_kaydi_silinemez(uretimli):
    assert uretimli.post("/uretim/99/sil").status_code == 404


def test_uretim_silme_ekranda_onay_ister(uretimli):
    uretimli.post(
        "/uretim",
        data={"production_date": "2026-01-31", "quantity": "100", "unit": "ton"},
    )
    page = uretimli.get("/uretim")
    assert "/uretim/1/sil" in page.text
    assert "Onaylıyor musunuz?" in page.text


# --------------------------------------------------------------------------- #
# 4. Hedef duzeltme / silme
# --------------------------------------------------------------------------- #


def test_yanlis_hedef_duzeltilebilir(uretimli):
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "90.000"},
    )
    with SessionLocal() as db:
        assert db.get(Target, 1).target_value == pytest.approx(90_000)

    duzeltme = uretimli.post(
        "/hedefler/1",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9.000"},
    )
    assert duzeltme.status_code == 200
    assert "9.000,00" in duzeltme.text

    with SessionLocal() as db:
        assert db.query(Target).count() == 1
        assert db.get(Target, 1).target_value == pytest.approx(9_000)


def test_duzeltilen_hedef_panelde_gorunur(uretimli):
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "90000"},
    )
    uretimli.post(
        "/hedefler/1",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9000"},
    )
    page = uretimli.get("/?donem=2026-01")
    assert "9.000,00" in page.text
    assert "hedef aşıldı" in page.text  # 10.000 > 9.000


def test_hedef_silinebilir(uretimli):
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9000"},
    )
    assert uretimli.post("/hedefler/1/sil").status_code == 200
    with SessionLocal() as db:
        assert db.query(Target).count() == 0
    assert "Aylık hedef" not in uretimli.get("/?donem=2026-01").text


def test_hedef_duzeltmede_duplicate_kurali_korunur(uretimli):
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9000"},
    )
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-02", "energy_type_id": "1", "target_value": "8000"},
    )
    çakışma = uretimli.post(
        "/hedefler/2",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "8000"},
    )
    assert çakışma.status_code == 400
    assert "zaten tanımlı" in çakışma.text


def test_hedef_kendi_ayinda_duzeltilebilir(uretimli):
    """Kendi kaydi duplicate sayilmamali."""
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9000"},
    )
    assert uretimli.post(
        "/hedefler/1",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9500"},
    ).status_code == 200


def test_hedef_duzeltmede_sifir_reddedilir(uretimli):
    uretimli.post(
        "/hedefler",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "9000"},
    )
    response = uretimli.post(
        "/hedefler/1",
        data={"year_month": "2026-01", "energy_type_id": "1", "target_value": "0"},
    )
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text
    with SessionLocal() as db:
        assert db.get(Target, 1).target_value == pytest.approx(9_000)


def test_olmayan_hedef_acilamaz_ve_silinemez(uretimli):
    assert uretimli.get("/hedefler/99").status_code == 404
    assert uretimli.post("/hedefler/99/sil").status_code == 404


# --------------------------------------------------------------------------- #
# 5. Rapor: olcum uyumsuzlugu
# --------------------------------------------------------------------------- #


@pytest.fixture
def uyumsuz(logged_in_client, db):
    """Alt sayaclar (12.000) ana sayactan (10.000) fazla olcuyor."""
    electricity = energy_type(db, price=2.0)
    from tests.factories import department

    production_dept = department(db, "Üretim")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Üretim Panosu", electricity, production_dept)
    readings(db, main, {"2025-12-31": 0, "2026-01-31": 10_000})
    readings(db, sub, {"2025-12-31": 0, "2026-01-31": 12_000})
    return logged_in_client


def test_uyumsuzlukta_scope_warning_korunur(uyumsuz, db):
    from app.models import EnergyType

    breakdown = dashboard.department_breakdown(
        db, db.get(EnergyType, 1), *OCAK, 10_000
    )
    assert breakdown["scope_warning"] is True
    assert breakdown["unmeasured"] == pytest.approx(-2_000)
    assert all(row["measured"] for row in breakdown["rows"])


def test_uyumsuz_raporda_celiskili_yuzde_gosterilmez(uyumsuz):
    page = uyumsuz.get("/rapor?baslangic=2026-01-01&bitis=2026-01-31&kirilim=bolum")
    assert page.status_code == 200
    assert "120,0%" in page.text  # bölüm payı olduğu gibi gösterilir
    assert "Fabrika toplamı (ana sayaç)" in page.text
    assert "100,0%" not in page.text  # yanıltıcı toplam yüzdesi yok
    assert "kapsamı sorunudur" in page.text


def test_uyumsuzluk_yokken_toplam_yuzdesi_gosterilir(logged_in_client, db):
    from tests.factories import department

    electricity = energy_type(db, price=2.0)
    production_dept = department(db, "Üretim")
    main = meter(db, "Ana Trafo", electricity, is_main=True)
    sub = meter(db, "Üretim Panosu", electricity, production_dept)
    readings(db, main, {"2025-12-31": 0, "2026-01-31": 10_000})
    readings(db, sub, {"2025-12-31": 0, "2026-01-31": 6_000})

    page = logged_in_client.get(
        "/rapor?baslangic=2026-01-01&bitis=2026-01-31&kirilim=bolum"
    )
    assert "Fabrika toplamı (ana sayaç)" in page.text
    assert "100,0%" in page.text
    assert "Ölçülmeyen / dağıtılmamış" in page.text
