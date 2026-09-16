"""Uretim verisi girisi."""

from datetime import date, timedelta

import pytest

from app.db import SessionLocal
from app.models import Production


def _add(client, on_date="2026-01-31", quantity="120", unit="ton"):
    return client.post(
        "/uretim",
        data={"production_date": on_date, "quantity": quantity, "unit": unit},
    )


def test_uretim_ekrani_giris_gerektirir(client):
    response = client.get("/uretim", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/giris"


def test_uretim_kaydedilir(logged_in_client):
    response = _add(logged_in_client)
    assert response.status_code == 200
    assert "31.01.2026" in response.text
    assert "ton" in response.text

    with SessionLocal() as db:
        record = db.get(Production, 1)
        assert record.quantity == pytest.approx(120)
        assert record.unit == "ton"


def test_virgullu_miktar_kabul_edilir(logged_in_client):
    _add(logged_in_client, quantity="135,75")
    with SessionLocal() as db:
        assert db.get(Production, 1).quantity == pytest.approx(135.75)


def test_tarih_zorunludur(logged_in_client):
    response = _add(logged_in_client, on_date="")
    assert response.status_code == 400
    assert "Tarih alanı boş bırakılamaz" in response.text


def test_miktar_zorunludur(logged_in_client):
    response = _add(logged_in_client, quantity="")
    assert response.status_code == 400
    assert "boş bırakılamaz" in response.text


def test_birim_zorunludur(logged_in_client):
    response = _add(logged_in_client, unit="  ")
    assert response.status_code == 400
    assert "Birim alanı boş bırakılamaz" in response.text


def test_sifir_uretim_reddedilir(logged_in_client):
    response = _add(logged_in_client, quantity="0")
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text


def test_negatif_uretim_reddedilir(logged_in_client):
    response = _add(logged_in_client, quantity="-10")
    assert response.status_code == 400
    assert "sıfırdan büyük olmalıdır" in response.text


def test_gelecek_tarihli_uretim_reddedilir(logged_in_client):
    yarin = (date.today() + timedelta(days=1)).isoformat()
    response = _add(logged_in_client, on_date=yarin)
    assert response.status_code == 400
    assert "bugünden ileri olamaz" in response.text

    with SessionLocal() as db:
        assert db.query(Production).count() == 0


def test_ayni_tarih_ve_birime_ikinci_kayit_engellenir(logged_in_client):
    _add(logged_in_client, on_date="2026-01-31", quantity="120")
    response = _add(logged_in_client, on_date="2026-01-31", quantity="130")
    assert response.status_code == 400
    assert "zaten bir üretim kaydı var" in response.text

    with SessionLocal() as db:
        assert db.query(Production).count() == 1


def test_ayni_tarihte_farkli_birim_girilebilir(logged_in_client):
    _add(logged_in_client, on_date="2026-01-31", quantity="120", unit="ton")
    response = _add(logged_in_client, on_date="2026-01-31", quantity="2000", unit="adet")
    assert response.status_code == 200

    with SessionLocal() as db:
        assert db.query(Production).count() == 2


def test_birimin_farkli_yazimi_ayni_birim_sayilir(logged_in_client):
    """'Ton' ve 'ton' ayri seri olusturmamalidir."""
    _add(logged_in_client, on_date="2026-01-30", quantity="120", unit="ton")
    _add(logged_in_client, on_date="2026-01-31", quantity="130", unit="Ton")

    with SessionLocal() as db:
        assert {record.unit for record in db.query(Production)} == {"ton"}


def test_farkli_yazimla_duplicate_de_engellenir(logged_in_client):
    _add(logged_in_client, on_date="2026-01-31", unit="ton")
    response = _add(logged_in_client, on_date="2026-01-31", unit="TON")
    assert response.status_code == 400
    assert "zaten bir üretim kaydı var" in response.text


def test_hata_durumunda_girilen_degerler_korunur(logged_in_client):
    response = _add(logged_in_client, on_date="2026-01-31", quantity="-5", unit="adet")
    assert response.status_code == 400
    assert 'value="-5"' in response.text
    assert 'value="2026-01-31"' in response.text
    assert 'value="adet"' in response.text


def test_kayitlar_yeniden_eskiye_siralanir(logged_in_client):
    _add(logged_in_client, on_date="2026-01-10")
    _add(logged_in_client, on_date="2026-03-10")
    _add(logged_in_client, on_date="2026-02-10")

    page = logged_in_client.get("/uretim").text
    assert page.index("10.03.2026") < page.index("10.02.2026") < page.index("10.01.2026")
