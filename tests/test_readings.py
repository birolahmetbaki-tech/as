"""Sayac okuma girisi."""

import pytest

from app.db import SessionLocal
from app.models import MeterReading


def _setup_meter(client, name="Ana Trafo", multiplier="1"):
    """Bir enerji turu, bir bolum ve bir sayac olusturur."""
    client.post(
        "/tanimlar/enerji-turleri",
        data={"name": "Elektrik", "unit": "kWh", "unit_price": "2,5"},
    )
    client.post("/tanimlar/bolumler", data={"name": "Üretim"})
    client.post(
        "/tanimlar/sayaclar",
        data={
            "name": name,
            "energy_type_id": "1",
            "department_id": "1",
            "multiplier": multiplier,
        },
    )
    return 1  # ilk sayacin id'si


def _add_reading(client, meter_id=1, on_date="2026-01-01", value="1000", note=""):
    return client.post(
        "/okumalar",
        data={
            "meter_id": str(meter_id),
            "reading_date": on_date,
            "index_value": value,
            "note": note,
        },
    )


def _table_rows(html: str) -> list[str]:
    """Okuma tablosundaki satirlari dondurur."""
    body = html.split("<tbody>")[1].split("</tbody>")[0]
    return [row for row in body.split("<tr>") if "<td>" in row]


def test_okuma_ekrani_giris_gerektirir(client):
    response = client.get("/okumalar", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/giris"


def test_sayac_yoksa_uyari_gosterilir(logged_in_client):
    response = logged_in_client.get("/okumalar")
    assert response.status_code == 200
    assert "önce en az bir aktif" in response.text


# --------------------------------------------------------------------------- #
# Basarili kayit
# --------------------------------------------------------------------------- #


def test_okuma_kaydedilir(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(
        logged_in_client, on_date="2026-01-31", value="1250", note="Ay sonu"
    )
    assert response.status_code == 200
    assert "Ay sonu" in response.text
    assert "31.01.2026" in response.text

    with SessionLocal() as db:
        reading = db.get(MeterReading, 1)
        assert reading.index_value == pytest.approx(1250)
        assert reading.note == "Ay sonu"
        assert reading.reading_date.isoformat() == "2026-01-31"


def test_virgullu_endeks_kabul_edilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, value="1250,50")
    with SessionLocal() as db:
        assert db.get(MeterReading, 1).index_value == pytest.approx(1250.50)


def test_nokta_ile_yazilan_tarih_kabul_edilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="15.02.2026")
    with SessionLocal() as db:
        assert db.get(MeterReading, 1).reading_date.isoformat() == "2026-02-15"


def test_aciklama_bos_birakilabilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, note="   ")
    with SessionLocal() as db:
        assert db.get(MeterReading, 1).note is None


# --------------------------------------------------------------------------- #
# Dogrulamalar
# --------------------------------------------------------------------------- #


def test_sayac_secilmeden_kayit_yapilamaz(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, meter_id="")
    assert response.status_code == 400
    assert "Sayaç seçilmelidir" in response.text


def test_tarih_zorunludur(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, on_date="")
    assert response.status_code == 400
    assert "Tarih alanı boş bırakılamaz" in response.text


def test_gecersiz_tarih_reddedilir(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, on_date="2026-13-45")
    assert response.status_code == 400
    assert "geçerli bir tarih olmalıdır" in response.text


def test_endeks_zorunludur(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, value="")
    assert response.status_code == 400
    assert "Endeks alanı boş bırakılamaz" in response.text


def test_sayi_olmayan_endeks_reddedilir(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, value="bin")
    assert response.status_code == 400
    assert "sayı olmalıdır" in response.text


def test_negatif_endeks_reddedilir(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, value="-5")
    assert response.status_code == 400
    assert "negatif olamaz" in response.text


def test_ayni_sayac_ve_tarihe_ikinci_okuma_girilemez(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-31", value="1000")
    response = _add_reading(logged_in_client, on_date="2026-01-31", value="1100")
    assert response.status_code == 400
    assert "zaten bir okuma var" in response.text

    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 1


def test_onceki_okumadan_dusuk_endeks_reddedilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-31", value="1000")
    response = _add_reading(logged_in_client, on_date="2026-02-28", value="900")
    assert response.status_code == 400
    assert "önceki okumadan" in response.text
    assert "küçük olamaz" in response.text


def test_sonraki_okumadan_buyuk_geriye_donuk_endeks_reddedilir(logged_in_client):
    """Araya girilen kayit da endeksin artan sirasini bozmamalidir."""
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-01", value="1000")
    _add_reading(logged_in_client, on_date="2026-03-01", value="1200")
    response = _add_reading(logged_in_client, on_date="2026-02-01", value="1500")
    assert response.status_code == 400
    assert "sonraki okumadan" in response.text


def test_araya_uygun_okuma_girilebilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-01", value="1000")
    _add_reading(logged_in_client, on_date="2026-03-01", value="1200")
    response = _add_reading(logged_in_client, on_date="2026-02-01", value="1100")
    assert response.status_code == 200
    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 3


def test_ayni_endeks_tekrar_girilebilir(logged_in_client):
    """Tuketim olmayan bir donemde endeks degismeyebilir."""
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-01", value="1000")
    response = _add_reading(logged_in_client, on_date="2026-01-02", value="1000")
    assert response.status_code == 200


def test_hata_durumunda_girilen_degerler_korunur(logged_in_client):
    _setup_meter(logged_in_client)
    response = _add_reading(
        logged_in_client, value="-5", on_date="2026-01-31", note="Deneme notu"
    )
    assert response.status_code == 400
    assert 'value="-5"' in response.text
    assert 'value="2026-01-31"' in response.text
    assert "Deneme notu" in response.text


# --------------------------------------------------------------------------- #
# Pasif sayaclar
# --------------------------------------------------------------------------- #


def test_pasif_sayac_okuma_formunda_listelenmez(logged_in_client):
    _setup_meter(logged_in_client)
    logged_in_client.post(
        "/tanimlar/sayaclar/1",
        data={"name": "Ana Trafo", "energy_type_id": "1", "multiplier": "1"},
    )
    response = logged_in_client.get("/okumalar")
    assert "önce en az bir aktif" in response.text


def test_pasif_sayaca_okuma_girilemez(logged_in_client):
    _setup_meter(logged_in_client)
    logged_in_client.post(
        "/tanimlar/sayaclar/1",
        data={"name": "Ana Trafo", "energy_type_id": "1", "multiplier": "1"},
    )
    response = _add_reading(logged_in_client)
    assert response.status_code == 400
    assert "pasif bir sayaç" in response.text

    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 0


def test_pasif_sayacin_gecmisi_goruntulenebilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-01", value="1000")
    logged_in_client.post(
        "/tanimlar/sayaclar/1",
        data={"name": "Ana Trafo", "energy_type_id": "1", "multiplier": "1"},
    )
    response = logged_in_client.get("/okumalar?sayac=1")
    assert response.status_code == 200
    assert "01.01.2026" in response.text


# --------------------------------------------------------------------------- #
# Listeleme
# --------------------------------------------------------------------------- #


def test_okumalar_yeniden_eskiye_siralanir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-01", value="1000")
    _add_reading(logged_in_client, on_date="2026-03-01", value="1200")
    _add_reading(logged_in_client, on_date="2026-02-01", value="1100")

    page = logged_in_client.get("/okumalar").text
    assert page.index("01.03.2026") < page.index("01.02.2026") < page.index("01.01.2026")


def test_sayac_bazinda_filtreleme(logged_in_client):
    _setup_meter(logged_in_client)
    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Kompresör", "energy_type_id": "1", "multiplier": "1"},
    )
    _add_reading(logged_in_client, meter_id=1, on_date="2026-01-01", value="1000")
    _add_reading(logged_in_client, meter_id=2, on_date="2026-01-01", value="500")

    response = logged_in_client.get("/okumalar?sayac=2")
    assert response.status_code == 200
    rows = _table_rows(response.text)
    assert len(rows) == 1
    assert "Kompresör" in rows[0]
    assert "500,00" in rows[0]


def test_son_endeks_secim_listesinde_gosterilir(logged_in_client):
    _setup_meter(logged_in_client)
    _add_reading(logged_in_client, on_date="2026-01-31", value="1250,5")
    response = logged_in_client.get("/okumalar")
    assert 'data-son-endeks="1.250,50"' in response.text
    assert 'data-son-tarih="31.01.2026"' in response.text


# --------------------------------------------------------------------------- #
# Gelecek tarih
# --------------------------------------------------------------------------- #


def test_gelecek_tarihli_okuma_reddedilir(logged_in_client):
    from datetime import date, timedelta

    _setup_meter(logged_in_client)
    yarin = (date.today() + timedelta(days=1)).isoformat()
    response = _add_reading(logged_in_client, on_date=yarin)
    assert response.status_code == 400
    assert "bugünden ileri olamaz" in response.text

    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 0


def test_bugun_tarihli_okuma_kabul_edilir(logged_in_client):
    from datetime import date

    _setup_meter(logged_in_client)
    response = _add_reading(logged_in_client, on_date=date.today().isoformat())
    assert response.status_code == 200
    with SessionLocal() as db:
        assert db.query(MeterReading).count() == 1
