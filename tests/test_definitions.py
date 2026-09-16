"""Tanim ekranlari: bolum, enerji turu ve sayac."""

import pytest


def _add_energy_type(client, name="Elektrik", unit="kWh", price="2,5"):
    return client.post(
        "/tanimlar/enerji-turleri",
        data={"name": name, "unit": unit, "unit_price": price},
    )


def _add_department(client, name="Üretim"):
    return client.post("/tanimlar/bolumler", data={"name": name})


# --------------------------------------------------------------------------- #
# Erisim
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "path",
    ["/tanimlar/bolumler", "/tanimlar/enerji-turleri", "/tanimlar/sayaclar"],
)
def test_tanim_ekranlari_giris_gerektirir(client, path):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/giris"


# --------------------------------------------------------------------------- #
# Bolum
# --------------------------------------------------------------------------- #


def test_bolum_eklenir_ve_listelenir(logged_in_client):
    response = _add_department(logged_in_client, "Kazan Dairesi")
    assert response.status_code == 200
    assert "Kazan Dairesi" in response.text
    assert "Aktif" in response.text


def test_bos_bolum_adi_reddedilir(logged_in_client):
    response = _add_department(logged_in_client, "   ")
    assert response.status_code == 400
    assert "boş bırakılamaz" in response.text


def test_ayni_isimli_bolum_reddedilir(logged_in_client):
    _add_department(logged_in_client, "Üretim")
    response = _add_department(logged_in_client, "üretim")
    assert response.status_code == 400
    assert "zaten var" in response.text


def test_bolum_duzenlenir_ve_pasife_alinir(logged_in_client):
    _add_department(logged_in_client, "Eski Bölüm")
    response = logged_in_client.post(
        "/tanimlar/bolumler/1", data={"name": "Yeni Bölüm"}
    )
    assert response.status_code == 200
    assert "Yeni Bölüm" in response.text
    assert "Pasif" in response.text


def test_olmayan_bolum_404_doner(logged_in_client):
    assert logged_in_client.get("/tanimlar/bolumler/99").status_code == 404


# --------------------------------------------------------------------------- #
# Enerji turu
# --------------------------------------------------------------------------- #


def test_enerji_turu_eklenir(logged_in_client):
    response = _add_energy_type(logged_in_client)
    assert response.status_code == 200
    assert "Elektrik" in response.text
    assert "kWh" in response.text


def test_virgullu_birim_fiyat_kabul_edilir(logged_in_client):
    from app.db import SessionLocal
    from app.models import EnergyType

    _add_energy_type(logged_in_client, price="3,45")
    with SessionLocal() as db:
        assert db.get(EnergyType, 1).unit_price == pytest.approx(3.45)


def test_negatif_birim_fiyat_reddedilir(logged_in_client):
    response = _add_energy_type(logged_in_client, price="-1")
    assert response.status_code == 400
    assert "negatif olamaz" in response.text


def test_sayi_olmayan_birim_fiyat_reddedilir(logged_in_client):
    response = _add_energy_type(logged_in_client, price="abc")
    assert response.status_code == 400
    assert "sayı olmalıdır" in response.text


def test_birimsiz_enerji_turu_reddedilir(logged_in_client):
    response = _add_energy_type(logged_in_client, unit="")
    assert response.status_code == 400
    assert "Birim" in response.text


def test_enerji_turu_pasife_alinir(logged_in_client):
    _add_energy_type(logged_in_client)
    response = logged_in_client.post(
        "/tanimlar/enerji-turleri/1",
        data={"name": "Elektrik", "unit": "kWh", "unit_price": "2,5"},
    )
    assert response.status_code == 200
    assert "Pasif" in response.text


# --------------------------------------------------------------------------- #
# Sayac
# --------------------------------------------------------------------------- #


def test_enerji_turu_yoksa_sayac_formu_yerine_uyari_cikar(logged_in_client):
    response = logged_in_client.get("/tanimlar/sayaclar")
    assert response.status_code == 200
    assert "önce en az bir" in response.text


def test_sayac_eklenir(logged_in_client):
    from app.db import SessionLocal
    from app.models import Meter

    _add_energy_type(logged_in_client)
    _add_department(logged_in_client, "Üretim")
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={
            "name": "Ana Trafo",
            "energy_type_id": "1",
            "department_id": "1",
            "serial_no": "TR-001",
            "multiplier": "40",
            "is_main": "on",
        },
    )
    assert response.status_code == 200
    assert "Ana Trafo" in response.text

    with SessionLocal() as db:
        meter = db.get(Meter, 1)
        assert meter.multiplier == pytest.approx(40)
        assert meter.is_main is True
        assert meter.department_id == 1
        assert meter.is_active is True


def test_sayac_bolumsuz_eklenebilir(logged_in_client):
    from app.db import SessionLocal
    from app.models import Meter

    _add_energy_type(logged_in_client)
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={
            "name": "Şebeke Sayacı",
            "energy_type_id": "1",
            "department_id": "",
            "serial_no": "",
            "multiplier": "1",
        },
    )
    assert response.status_code == 200
    with SessionLocal() as db:
        meter = db.get(Meter, 1)
        assert meter.department_id is None
        assert meter.serial_no is None
        assert meter.is_main is False


def test_enerji_turu_secilmeden_sayac_eklenemez(logged_in_client):
    _add_energy_type(logged_in_client)
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Sayaç", "energy_type_id": "", "multiplier": "1"},
    )
    assert response.status_code == 400
    assert "Enerji türü seçilmelidir" in response.text


def test_sifir_carpan_reddedilir(logged_in_client):
    _add_energy_type(logged_in_client)
    response = logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Sayaç", "energy_type_id": "1", "multiplier": "0"},
    )
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text


def test_ayni_isimli_sayac_reddedilir(logged_in_client):
    _add_energy_type(logged_in_client)
    data = {"name": "Kompresör", "energy_type_id": "1", "multiplier": "1"}
    logged_in_client.post("/tanimlar/sayaclar", data=data)
    response = logged_in_client.post("/tanimlar/sayaclar", data=data)
    assert response.status_code == 400
    assert "zaten var" in response.text


def test_pasif_enerji_turu_sayac_formunda_listelenmez(logged_in_client):
    _add_energy_type(logged_in_client, name="Doğal Gaz", unit="Sm³")
    logged_in_client.post(
        "/tanimlar/enerji-turleri/1",
        data={"name": "Doğal Gaz", "unit": "Sm³", "unit_price": "0"},
    )
    response = logged_in_client.get("/tanimlar/sayaclar")
    assert "önce en az bir" in response.text


def test_sayac_duzenlenir(logged_in_client):
    from app.db import SessionLocal
    from app.models import Meter

    _add_energy_type(logged_in_client)
    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Sayaç 1", "energy_type_id": "1", "multiplier": "1"},
    )
    response = logged_in_client.post(
        "/tanimlar/sayaclar/1",
        data={
            "name": "Sayaç 1",
            "energy_type_id": "1",
            "department_id": "",
            "serial_no": "S-9",
            "multiplier": "2,5",
            "is_active": "on",
        },
    )
    assert response.status_code == 200
    with SessionLocal() as db:
        meter = db.get(Meter, 1)
        assert meter.multiplier == pytest.approx(2.5)
        assert meter.serial_no == "S-9"
        assert meter.is_active is True


# --------------------------------------------------------------------------- #
# Duzenleme ekranlarinin acilmasi
# --------------------------------------------------------------------------- #


def test_duzenleme_ekranlari_acilir(logged_in_client):
    _add_energy_type(logged_in_client)
    _add_department(logged_in_client, "Üretim")
    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={
            "name": "Sayaç 1",
            "energy_type_id": "1",
            "department_id": "1",
            "multiplier": "1",
        },
    )

    assert "Üretim" in logged_in_client.get("/tanimlar/bolumler/1").text
    assert "Elektrik" in logged_in_client.get("/tanimlar/enerji-turleri/1").text

    meter_page = logged_in_client.get("/tanimlar/sayaclar/1")
    assert meter_page.status_code == 200
    assert "Sayaç 1" in meter_page.text
    assert "Ana sayaç" in meter_page.text


def test_pasif_bolum_sayacin_duzenleme_ekraninda_korunur(logged_in_client):
    """Sayacin bagli oldugu bolum pasife alinsa bile secim kaybolmaz."""
    _add_energy_type(logged_in_client)
    _add_department(logged_in_client, "Eski Bölüm")
    logged_in_client.post(
        "/tanimlar/sayaclar",
        data={"name": "Sayaç 1", "energy_type_id": "1", "department_id": "1", "multiplier": "1"},
    )
    logged_in_client.post("/tanimlar/bolumler/1", data={"name": "Eski Bölüm"})

    page = logged_in_client.get("/tanimlar/sayaclar/1")
    assert page.status_code == 200
    assert "Eski Bölüm (pasif)" in page.text
