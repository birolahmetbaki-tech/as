from tests.conftest import TEST_PASSWORD


def test_saglik_kontrolu_girissiz_calisir(client):
    response = client.get("/saglik")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_giris_yapmadan_panele_erisilemez(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/giris"


def test_yanlis_parola_reddedilir(client):
    response = client.post("/giris", data={"password": "yanlis"})
    assert response.status_code == 401
    assert "Parola hatalı" in response.text


def test_dogru_parola_ile_panele_erisilir(logged_in_client):
    response = logged_in_client.get("/")
    assert response.status_code == 200
    assert "Gösterge Paneli" in response.text


def test_cikis_sonrasi_erisim_kapanir(logged_in_client):
    logged_in_client.post("/cikis")
    response = logged_in_client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/giris"
