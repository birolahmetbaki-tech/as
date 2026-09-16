# Enerji İzleme

Tek bir fabrika için sade, tek kullanıcılı enerji izleme ve enerji performans
takip sistemi. Bütün enerji ve üretim verileri elle girilir; otomatik veri
toplama (sayaç, PLC, SCADA, ERP) bulunmaz.

## Temel ilkeler

- **Ham veri ile hesap ayrıdır.** Veritabanında sayaç endeksi saklanır;
  tüketim, maliyet ve EnPI gibi türetilmiş değerler saklanmaz, merkezi
  hesaplama modülünde üretilir.
- **Tüketim = (endeks₂ − endeks₁) × sayaç çarpanı** ve ikinci okumanın
  tarihine yazılır.
- Bugün ihtiyaç duyulmayan özellik sisteme eklenmez.

## Teknoloji

Python 3.11 · FastAPI · SQLAlchemy · Alembic · SQLite · Jinja2 · pytest

## Kurulum

```bash
uv venv
uv pip install -e ".[dev]"

cp .env.example .env
.venv/bin/python scripts/generate_secret.py   # çıktıyı .env içine yapıştırın
.venv/bin/python scripts/set_password.py      # çıktıyı .env içine yapıştırın

.venv/bin/alembic upgrade head                # veritabanını oluşturur
.venv/bin/uvicorn app.main:app --reload
```

Uygulama <http://127.0.0.1:8000> adresinde çalışır.

İnternete açık bir sunucuda çalıştırıyorsanız uygulamayı mutlaka HTTPS
arkasına alın ve `.env` içinde `SECURE_COOKIE=1` yapın.

## Testler

```bash
.venv/bin/python -m pytest
```

## Veritabanı ve yedekleme

Bütün veriler `data/enerji.db` dosyasındadır (`DATA_DIR` ile değiştirilebilir).
Yedek almak için uygulama çalışırken de güvenli olan şu komut kullanılır:

```bash
sqlite3 data/enerji.db ".backup 'backups/enerji-$(date +%F).db'"
```

Şema değişiklikleri Alembic ile yönetilir; güncelleme sonrası
`alembic upgrade head` çalıştırılır.

## Ekranlar

- **Bölümler** — ekleme, düzenleme, pasife alma
- **Enerji türleri** — ad, birim, birim fiyat, aktiflik
- **Sayaçlar** — ad, enerji türü, bölüm, seri no, çarpan, ana/alt sayaç, aktiflik

Tanım kayıtları silinmez; kullanılmayan tanımlar pasife alınır. Böylece geçmiş
veriler her zaman anlamlı kalır.

## Veri modeli

| Tablo | İçerik |
|---|---|
| `settings` | Fabrika adı, para birimi (tek satır) |
| `energy_type` | Enerji türü, birimi, birim fiyatı, aktiflik |
| `department` | Fabrika bölümleri |
| `meter` | Sayaç: enerji türü, bölüm, çarpan, ana/alt sayaç ayrımı |
| `meter_reading` | Tarih bazlı sayaç endeksi (ham veri) |
| `production` | Üretim miktarı ve birimi |
| `target` | Aylık tüketim hedefi |

## Proje yapısı

```
app/
  config.py     ayarlar ve .env okuma
  security.py   parola özetleme (scrypt)
  db.py         veritabanı bağlantısı
  models.py     veri modeli
  main.py       giriş/çıkış ve panel rotaları
  definitions.py  tanım ekranları (bölüm, enerji türü, sayaç)
  web.py        şablon, bildirim ve sayı biçimi yardımcıları
  templates/  static/
migrations/     Alembic şema geçişleri
scripts/        parola ve anahtar üretme yardımcıları
tests/
```
