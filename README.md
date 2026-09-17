# Enerji İzleme

Tek bir fabrika için sade, tek kullanıcılı enerji izleme ve enerji performans
takip sistemi. Bütün enerji ve üretim verileri elle girilir; otomatik veri
toplama (sayaç, PLC, SCADA, ERP) bulunmaz.

## Durum

MVP tamamlandı ve günlük kullanıma hazırdır. Kapsam bilinçli olarak dardır:

- **Tek kullanıcı** — rol, yetki ve kullanıcı yönetimi yoktur.
- **Manuel veri girişi** — bütün okuma, üretim ve fatura verileri elle girilir.
  Otomatik veri toplama (sayaç, PLC, SCADA, Modbus, ERP, IoT) **yoktur**.
- **Yerel web uygulaması** — kendi bilgisayarınızda çalışır, tarayıcıdan
  `http://127.0.0.1:8000` adresiyle kullanılır (Chrome veya Edge).
- **İnternet gerektirmez** — ilk kurulumdaki paket indirme dışında hiçbir
  özellik ağ bağlantısına ihtiyaç duymaz.
- **Veriler tek bir SQLite dosyasındadır** (`data/enerji.db`); yedekleme
  kullanıcının sorumluluğundadır ve elle yapılır.
- **AI asistanı şu an aktif değildir.** `app/ai_tools.py` ve
  `app/ai_snapshot.py` ileride kullanılmak üzere durur, uygulamanın hiçbir
  yerinden çağrılmaz.
- ISO 50001 çalışmasını **destekler**, ancak eksiksiz bir ISO 50001 platformu
  değildir.

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
- **Fabrika toplamında kaynak önceliği**, enerji türü ve AY bazında:
  **doğrudan tüketim → ana sayaç → tüm sayaçlar.** Bir ay için doğrudan tüketim
  (fatura/beyan) girilmişse o ayın fabrika toplamı odur; girilmemişse o türde
  ana sayaç tanımlıysa yalnızca ana sayaçlar, ana sayaç yoksa o türdeki tüm
  sayaçlar kullanılır. Aynı ayda iki kaynak birden bulunursa **değerler
  toplanmaz**: doğrudan tüketim esas alınır ve çakışma ekranda farkıyla
  birlikte bildirilir.
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
- **Bölüm dağılımı** yalnızca bölüme bağlı **alt** sayaçlardan hesaplanır; ana
  sayaçlar bölüm dağılımına dahil edilmez (edilseydi aynı tüketim iki kez
  sayılırdı). Bir ana sayaca bölüm seçilebilir, bu onun dağılımdaki payını
  değiştirmez. Fabrika toplamı ile bölüm satırlarının toplamı arasındaki fark
  **"ölçülmeyen / dağıtılmamış"** olarak ayrı bir satırda gösterilir; satırların
  toplamı fabrika toplamına eşittir, üzerine eklenmez. Bu fark negatifse tüketim
  gibi değil, ölçüm kapsamı uyarısı olarak gösterilir.
- Sayı girişi Türkçe yazımı doğru yorumlar: `1.000` → 1000, `1.250,50` → 1250,5.
  Tanımsız biçimler sessizce dönüştürülmez, hata verilir.
- Bugün ihtiyaç duyulmayan özellik sisteme eklenmez.

## Teknoloji

Python 3.11 · FastAPI · SQLAlchemy · Alembic · SQLite · Jinja2 · pytest

## Kurulum

Gereken her şey: **Python 3.11 veya üstü** ve bir tarayıcı (**Chrome** veya
**Edge**). Docker, Node.js, veritabanı sunucusu, bulut hesabı **gerekmez**.
Projeyi ZIP olarak indirirseniz Git de gerekmez.

İnternet yalnızca ilk kurulumda (Python ve paketleri indirmek için) gerekir;
sonrasında uygulama tamamen çevrimdışı çalışır.

### Windows

**1. Python'u kurun.** <https://www.python.org/downloads/> adresinden Windows
sürümünü indirin. Kurulum ekranındaki **"Add python.exe to PATH"** kutusunu
mutlaka işaretleyin. İşaretlenmezse sonraki adımlarda
`Python was not found` hatası alırsınız.

Kontrol: Başlat → `cmd` → Komut İstemi'nde `python --version` yazın;
`Python 3.11.x` veya üstü görmelisiniz.

**2. Projeyi indirin.** İki yoldan biri:

- GitHub sayfasında **Code → Download ZIP** deyin ve ZIP'i örneğin
  `C:\EnerjiIzleme` klasörüne çıkarın (Git gerekmez), **veya**
- Git kuruluysa: `git clone <depo-adresi> C:\EnerjiIzleme`

Klasör adında Türkçe karakter ve boşluk olabilir, sorun çıkarmaz.

**3. Komut İstemi'ni proje klasöründe açın.** Dosya Gezgini'nde proje
klasörüne girin, adres çubuğuna `cmd` yazıp Enter'a basın. Aşağıdaki komutları
bu pencerede, **sırayla** çalıştırın:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"

copy .env.example .env
.venv\Scripts\python scripts\generate_secret.py   :: çıktıyı .env içine yapıştırın
.venv\Scripts\python scripts\set_password.py      :: çıktıyı .env içine yapıştırın

.venv\Scripts\alembic upgrade head                 :: veritabanını oluşturur
.venv\Scripts\uvicorn app.main:app
```

Son komut uygulamayı başlatır; durdurmak için `Ctrl+C` yapın.

Kurulumdan sonra uygulamayı her seferinde `baslat.bat` dosyasına çift
tıklayarak açabilirsiniz. Bu dosya önce ortamı denetler (`.env`, anahtarlar,
veritabanı tabloları) ve eksik varsa ne yapılacağını yazar; sonra sunucuyu
başlatıp **hazır olduğunu doğrulayınca** tarayıcıyı açar.

### Linux / macOS

```bash
python3 -m venv .venv            # veya: uv venv
.venv/bin/python -m pip install -e ".[dev]"

cp .env.example .env
.venv/bin/python scripts/generate_secret.py   # çıktıyı .env içine yapıştırın
.venv/bin/python scripts/set_password.py      # çıktıyı .env içine yapıştırın

.venv/bin/alembic upgrade head                # veritabanını oluşturur
.venv/bin/uvicorn app.main:app
```

Uygulama <http://127.0.0.1:8000> adresinde çalışır; tarayıcıdan bu adresi açın.
Pencereyi kapatmak uygulamayı durdurur (terminalde `Ctrl+C`).

`alembic upgrade head` adımı atlanırsa tablolar oluşmaz ve giriş sonrası
**Internal Server Error** görürsünüz. Bu durumda uygulamayı durdurup komutu
çalıştırın, sonra yeniden başlatın.

Geliştirme yaparken kod değişince otomatik yeniden başlatma için
`uvicorn app.main:app --reload` kullanılır; günlük kullanımda gerekmez.

İnternete açık bir sunucuda çalıştırıyorsanız uygulamayı mutlaka HTTPS
arkasına alın ve `.env` içinde `SECURE_COOKIE=1` yapın. Tasarım hedefi tek
bilgisayarda, yerel ağda çalışmaktır.

## Testler

```bash
.venv/bin/python -m pytest        # Windows: .venv\Scripts\python -m pytest
```

## Veritabanı ve yedekleme

Bütün veriler tek bir dosyadadır: `data/enerji.db` (`DATA_DIR` ile
değiştirilebilir). Bu dosya kaybolursa bütün geçmiş kaybolur.

**Yedek almak** (uygulama açıkken de güvenlidir):

```bash
.venv/bin/python scripts/backup.py            # Windows: .venv\Scripts\python scripts\backup.py
```

Yedek `backups/enerji-YYYY-AA-GG_SSDD.db` adıyla oluşur. Windows'ta
`yedekle.bat` dosyasına çift tıklamak da aynı işi yapar.

> **`data\enerji.db` dosyasını elle kopyalamayın.** Uygulama SQLite'ı WAL
> kipinde çalıştırır; henüz ana dosyaya işlenmemiş kayıtlar `enerji.db-wal`
> dosyasında bekler. Uygulama açıkken yalnızca `enerji.db` kopyalanırsa bu
> kayıtlar yedeğe girmez ve yedek sessizce eksik olur. Yukarıdaki betik
> SQLite'ın kendi yedekleme arayüzünü kullandığı için her zaman tam ve
> tutarlı bir kopya üretir. Harici bir program (`sqlite3.exe` gibi) gerekmez.

Yedek dosyasını ayrıca bir USB belleğe veya başka bir diske kopyalayın; aynı
bilgisayarda kalırsa disk arızasında veriyle birlikte kaybolur.

**Geri yüklemek** (önce uygulamayı kapatın):

```bash
.venv/bin/python scripts/restore.py                            # yedekleri listeler
.venv/bin/python scripts/restore.py backups/enerji-2026-01-15_0900.db
```

Geri yükleme, üzerine yazmadan önce mevcut veritabanını
`backups/geri-yukleme-oncesi-...db` adıyla kendiliğinden yedekler; yanlış dosya
seçilse bile eski duruma dönülebilir.

Şema değişiklikleri Alembic ile yönetilir; güncelleme sonrası
`alembic upgrade head` çalıştırılır.

Günlük kullanım için adım adım anlatım: **[KULLANIM.md](KULLANIM.md)**.

## Ekranlar

- **Gösterge paneli** — seçilen ayın tüketimi ve kaynağı (sayaç / doğrudan),
  önceki dönemle karşılaştırma, maliyet, varsa aylık hedef durumu, üretim
  birimine göre **EnPI**, bölüm dağılımı ve "ölçülmeyen / dağıtılmamış" payı,
  son 12 ayın tüketim ve EnPI trendi. Ayrıca **bütün enerji türlerinin ortak
  birimde toplamı**: görüntüleme birimi kWh / MJ / GJ / TEP arasından seçilir,
  her tür kendi katsayısıyla çevrilip toplanır ve son 12 ay bu birimde
  gösterilir. Çakışma, eksik ana sayaç okuması ve eksik dönüşüm katsayısı
  durumlarında ekranda açık uyarı çıkar
- **Bölümler** — ekleme, düzenleme, pasife alma
- **Enerji türleri** — ad, birim, birim fiyat, aktiflik
- **Sayaçlar** — ad, enerji türü, bölüm, seri no, çarpan, ana/alt sayaç, aktiflik.
  Okuması olan bir sayacın enerji türü, geçmiş tüketimlerin anlamı değişeceği
  için ancak açık onayla değiştirilebilir
- **Dönüşüm katsayıları** — enerji içeriği katsayısı: `1 <enerji türü birimi> =
  katsayı GJ`. Geçerlilik başlangıcı, kaynak ve not alanlarıyla saklanır
- **Okumalar** — sayaç endeksi girişi; son okumalar ve sayaç bazında geçmiş.
  Yanlış girilen okuma onay alınarak silinip yeniden girilebilir
- **Doğrudan tüketim** — sayaç endeksi olmadan, ayın tüketiminin doğrudan
  girilmesi (fatura/beyan). Ay ve enerji türü başına tek kayıt; enerji türünün
  kendi biriminde tutulur. Kayıt silinince o ay için yeniden sayaç tüketimi
  kullanılır
- **Üretim** — tarih, miktar ve birim; aynı gün ve birim için tek kayıt.
  Yanlış kayıt onay alınarak silinebilir
- **Hedefler** — ay + enerji türü bazında aylık tüketim hedefi; düzeltilebilir
  ve silinebilir
- **Rapor** — tarih aralığı ve kırılım (enerji türü / sayaç / bölüm) seçimiyle
  tek ekranlık, yazdırılabilir rapor. Enerji türü kırılımında tüketimin kaynağı,
  seçilen enerji birimindeki eşdeğeri ve kullanılan katsayı da gösterilir;
  üretim/EnPI ve hedef tabloları rapora dahildir

Tanım kayıtları silinmez; kullanılmayan tanımlar pasife alınır. Böylece geçmiş
veriler her zaman anlamlı kalır.

## Veri modeli

Dokuz tablo vardır. Türetilmiş değerler (tüketim, maliyet, EnPI, GJ
eşdeğeri) saklanmaz; her zaman ham veriden yeniden hesaplanır.

| Tablo | İçerik |
|---|---|
| `settings` | Fabrika adı, para birimi (tek satır) |
| `energy_type` | Enerji türü, birimi, birim fiyatı, aktiflik |
| `department` | Fabrika bölümleri |
| `meter` | Sayaç: enerji türü, bölüm, çarpan, ana/alt sayaç ayrımı |
| `meter_reading` | Tarih bazlı sayaç endeksi (ham veri) |
| `direct_consumption` | Doğrudan girilen aylık tüketim (ay + enerji türü benzersiz) |
| `energy_conversion` | Enerji içeriği katsayısı: 1 birim = ? GJ (enerji türü + geçerlilik başlangıcı benzersiz) |
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
  ai_tools.py   (şu an aktif değil) ileride eklenecek AI asistanı için
  ai_snapshot.py  ayrılmış, salt-okunur veri katmanı; uygulamanın hiçbir
                yerinden çağrılmaz ve çalışmasını etkilemez
  templates/  static/
migrations/     Alembic şema geçişleri
scripts/        generate_secret.py  oturum anahtarı üretir
                set_password.py     parola özeti üretir
                onkontrol.py        başlatmadan önce ortamı denetler
                tarayici_ac.py      sunucu hazır olunca tarayıcıyı açar
                backup.py           güvenli yedek alır
                restore.py          yedeği geri yükler
tests/
```
