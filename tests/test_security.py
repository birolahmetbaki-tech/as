from app.security import hash_password, verify_password


def test_dogru_parola_dogrulanir():
    stored = hash_password("gizli-parola")
    assert verify_password("gizli-parola", stored)


def test_yanlis_parola_reddedilir():
    stored = hash_password("gizli-parola")
    assert not verify_password("baska-parola", stored)


def test_ozet_her_seferinde_farklidir():
    """Farkli tuz kullanildigi icin ayni parolanin ozeti tekrar etmez."""
    assert hash_password("ayni-parola") != hash_password("ayni-parola")


def test_bozuk_ozet_hata_vermeden_reddedilir():
    assert not verify_password("parola", "bozuk-deger")
