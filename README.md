# Enerji İzleme

Tek bir fabrika için sade, tek kullanıcılı enerji izleme ve enerji performans
takip sistemi. Bütün enerji ve üretim verileri elle girilir; otomatik veri
toplama (sayaç, PLC, SCADA, ERP) bulunmaz.

## Temel ilkeler

- **Ham veri ile hesap ayrıdır.** Veritabanında sayaç endeksi saklanır;
  tüketim, maliyet ve EnPI gibi türetilmiş değerler saklanmaz, merkezi
  hesaplama modülünde üretilir.
- **Tüketim = (endeks₂ − endeks₁) × sayaç çarpanı** ve **birinci okumanın
  bulunduğu takvim ayına** yazılır. Sahada endeksler bir sonraki ayın 1. günü
  okunduğu için dönem, ikinci okumanın değil ilk okumanın tarihine göre
  belirlenir:
  `01.01 → 01.02 = Ocak`, `01.02 → 01.03 = Şubat`,
  `01.12.2026 → 01.01.2027 = Aralık 2026`.
  Tüketim gün bazında orantılı olarak bölünmez. Bu hesap yalnızca
  `app/calc.py` içinde yapılır; hiçbir ekran kendi tüketim hesabını yapmaz.
- Fabrika toplamında, bir enerji türünde **ana sayaç tanımlıysa yalnızca ana
  sayaçlar** kullanılır; tanımlı değilse o türdeki tüm sayaçlar kullanılır.
- **Maliyet = tüketim × enerji türünün güncel birim fiyatı.** Geçmiş fiyat
  takibi yoktur: birim fiyat değiştirilirse geçmiş dönemlerin maliyeti de yeni
  fiyata göre hesaplanır. Vergi, ek bedel ve tarife dilimi kapsam dışıdır.
- **EnPI = enerji tüketimi ÷ üretim miktarı**, yalnızca tek bir üretim birimi
  için hesaplanır. Farklı üretim birimleri (ton, adet) asla birbirine toplanmaz.
- **Enerji dönüşümünde iki mekanizma ayrıdır ve karıştırılmaz.**
  *Matematiksel birim dönüşümü* (kWh → MJ → GJ → TEP) sabittir ve
  `app/units.py` içindedir; referans birim GJ'dir (1 TEP = 41,868 GJ =
  11.630 kWh). *Enerji içeriği katsayısı* (1 Sm³ doğal gaz = ? GJ) yakıta ve
  ölçüm bazına göre değiştiği için sistem tarafından varsayılmaz; kullanıcı
  `energy_conversion` tablosunda tanımlar. Bir dönem için
  `valid_from ≤ dönem` koşulunu sağlayan en yeni katsayı kullanılır.
- **Dönüştürülemeyen değer sıfır sayılmaz.** Bir enerji türünün geçerli
  katsayısı yoksa ortak birimdeki toplam üretilmez; eksikliğin hangi enerji
  türünden kaynaklandığı ekranda yazılır. Ham tüketim kayıtları hiçbir zaman
  dönüştürülerek saklanmaz; dönüşüm yalnızca gösterim sırasında yapılır.
- **Maliyet dönüşümden etkilenmez:** her zaman enerji türünün kendi biriminden
  ve kendi birim fiyatından hesaplanır. Aylık hedefler de enerji türünün kendi
  birimindedir.
- Gösterge panelinde **bölüm dağılımı** bölüme bağlı alt sayaçlardan gelir;
  fabrika toplamı ile arasındaki fark "ölçülmeyen / dağıtılmamış" olarak
  gösterilir. Bu fark negatifse tüketim gibi değil, ölçüm kapsamı uyarısı
  olarak gösterilir.
- Sayı girişi Türkçe yazımı doğru yorumlar: `1.000` → 1000, `1.250,50` → 1250,5.
  Tanımsız biçimler sessizce dönüştürülmez, hata verilir.
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

- **Gösterge paneli** — seçilen ayın tüketimi, önceki dönemle karşılaştırma,
  maliyet, varsa aylık hedef durumu, bölüm dağılımı, son 12 ayın trendi
- **Bölümler** — ekleme, düzenleme, pasife alma
- **Enerji türleri** — ad, birim, birim fiyat, aktiflik
- **Sayaçlar** — ad, enerji türü, bölüm, seri no, çarpan, ana/alt sayaç, aktiflik
- **Okumalar** — sayaç endeksi girişi; son okumalar ve sayaç bazında geçmiş.
  Yanlış girilen okuma onay alınarak silinip yeniden girilebilir
- **Üretim** — tarih, miktar ve birim; aynı gün ve birim için tek kayıt.
  Yanlış kayıt onay alınarak silinebilir
- **Hedefler** — ay + enerji türü bazında aylık tüketim hedefi; düzeltilebilir
  ve silinebilir
- **Rapor** — tarih aralığı ve kırılım (enerji türü / sayaç / bölüm) seçimiyle
  tek ekranlık, yazdırılabilir rapor

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
| `production` | Üretim miktarı ve birimi (tarih + birim benzersiz) |
| `target` | Aylık tüketim hedefi (ay + enerji türü benzersiz) |

## Proje yapısı

```
app/
  config.py     ayarlar ve .env okuma
  security.py   parola özetleme (scrypt)
  db.py         veritabanı bağlantısı
  models.py     veri modeli
  main.py       giriş/çıkış ve panel rotaları
  definitions.py  tanım ekranları (bölüm, enerji türü, sayaç, dönüşüm katsayısı)
  readings.py   sayaç okuma girişi
  direct.py     doğrudan tüketim girişi (fatura/beyan)
  production.py üretim verisi girişi
  targets.py    aylık tüketim hedefleri
  reports.py    rapor ekranı (yalnızca calc sonuçlarını sunar)
  calc.py       hesaplama çekirdeği (tüketim ve dönüşümün tek kaynağı)
  units.py      birim envanteri ve matematiksel birim dönüşümleri
  dashboard.py  gösterge paneli (calc sonuçlarını gösterir)
  web.py        şablon, bildirim, sayı/tarih biçimi ve doğrulama yardımcıları
  templates/  static/
migrations/     Alembic şema geçişleri
scripts/        parola ve anahtar üretme yardımcıları
tests/
```
