# Kullanım Kılavuzu

Bu belge günlük kullanım içindir. Kurulum ve teknik ayrıntılar için
[README.md](README.md) dosyasına bakın.

## İlk kullanım — kısa sıra

Kurulumu bitirdiyseniz sırasıyla şunları yapın. Her adımın ayrıntısı aşağıda:

| # | Adım | Nerede |
|---|---|---|
| 1 | **Başlat** — `baslat.bat` dosyasına çift tıklayın | masaüstü / proje klasörü |
| 2 | **Tarayıcı** açılır, giriş yapın | `http://127.0.0.1:8000` |
| 3 | **Enerji türü** ekleyin (Elektrik / kWh, Doğal Gaz / Sm³) | Enerji Türleri |
| 4 | **Departman** ekleyin (Pres, Paketleme…) | Bölümler |
| 5 | **Sayaç** ekleyin (ana ve alt sayaçlar, çarpan) | Sayaçlar |
| 6 | **Okuma** girin (ilk endeks, sonra her ayın 1'i) | Okumalar |
| 7 | **Üretim** girin (ton, adet…) | Üretim |
| 8 | **Katsayı** girin (yalnızca Sm³, kg gibi birimler için) | Katsayılar |
| 9 | **Hedef** girin (isteğe bağlı) | Hedefler |
| 10 | **Dashboard / Rapor** ile sonuçlara bakın | Panel, Rapor |
| 11 | **Yedek** alın (`yedekle.bat`) | proje klasörü |

Sayacı olmayan bir enerji türünüz varsa 6. adım yerine **Doğrudan Tüketim**
ekranından ayın tüketimini girin.

## Uygulamayı açma

Windows'ta `baslat.bat` dosyasına çift tıklayın. Tarayıcı, sunucu hazır olur
olmaz <http://127.0.0.1:8000> adresini kendiliğinden açar (yavaş bir
bilgisayarda birkaç saniye sürebilir; bekleyin). Açılan siyah pencere
uygulamanın kendisidir, **kapatmayın**; işiniz bitince kapatarak uygulamayı
durdurabilirsiniz.

Bir eksik varsa uygulama açılmaz ve siyah pencerede ne yapmanız gerektiği
yazar (örneğin `.env` dosyası yoksa veya veritabanı henüz oluşturulmamışsa).

Giriş ekranında kurulum sırasında belirlediğiniz parolayı yazın. Tek kullanıcı
vardır; parola `.env` dosyasında yalnızca özeti (geri çevrilemez karşılığı)
tutulur.

## İlk kurulumda sırasıyla ne yapılmalı

Sistem boşken gösterge paneli zaten sizi yönlendirir. Önerilen sıra:

1. **Enerji türleri** — Elektrik, Doğal Gaz, Buhar gibi. Her biri için birim
   (kWh, Sm³, ton) ve birim fiyat girilir.
2. **Bölümler** — Pres, Paketleme, Kazan Dairesi gibi. Yalnızca tüketimi bölüm
   bazında görmek istiyorsanız gerekir.
3. **Sayaçlar** — hangi enerji türünü ölçtüğü, varsa bağlı olduğu bölüm,
   ana/alt sayaç olduğu ve çarpanı.
4. **Okumalar** — sayaç endekslerini girmeye başlayın.
5. Gerekiyorsa **doğrudan tüketim**, **üretim**, **hedef** ve **dönüşüm
   katsayısı**.

Tanımları sonradan da ekleyebilirsiniz; sıralama zorunlu değildir.

## Enerji türü

- **Birim**, o türün temel tüketim birimidir. Sayaç okumaları ve doğrudan
  tüketim kayıtları bu birimdedir, birim fiyat da bu birim başınadır.
- `kWh`, `MJ`, `GJ` gibi standart enerji birimleri GJ/TEP toplamına
  kendiliğinden çevrilir. `Sm³`, `kg` gibi birimlerde çevrim için ayrıca
  **dönüşüm katsayısı** gerekir (aşağıda).
- Kullanmadığınız bir enerji türünü silmek yerine **pasife alın**: geçmiş
  kayıtları ve raporları korunur, yeni kayıt girilemez.

## Sayaç ve çarpan

- **Ana sayaç**, fabrika toplamını veren sayaçtır. Bir enerji türünde ana sayaç
  tanımlıysa fabrika toplamı **yalnızca** ana sayaçlardan hesaplanır.
- **Alt sayaçlar** bölüm dağılımını verir. Ana sayaçlar bölüm dağılımına dahil
  edilmez; edilseydi aynı tüketim iki kez sayılırdı.
- **Çarpan**, iki okuma arasındaki endeks farkının kaçla çarpılacağıdır. Ölçü
  trafosu (örn. 200/5) gibi bir dönüştürme varsa o katsayıyı girin; endeksi
  doğrudan okunan sayaçlarda çoğunlukla 1'dir. Emin değilseniz sayacın
  etiketine bakın: **yanlış çarpan tüketimi sessizce yanlış hesaplar.**

## Sayaç okuması

Endeksi okuduğunuz tarihle birlikte girin. Gelecek tarihli okuma kabul
edilmez; aynı sayaç için aynı güne ikinci okuma girilemez.

**Dönem kuralı:** iki okuma arasındaki tüketim, **birinci okumanın bulunduğu
aya** yazılır. Endeksler her ayın ertesi ayın 1'inde okunduğu için:

| Okuma | Endeks | Sonuç |
|---|---|---|
| 01.01.2026 | 0 | — |
| 01.02.2026 | 1.000 | **Ocak 2026 = 1.000** |
| 01.03.2026 | 2.200 | **Şubat 2026 = 1.200** |

Yani bir ayın tüketimi, ertesi ayın 1'indeki okuma girilince oluşur.

Yanlış girilen okuma silinebilir. Silmeden önce uyarı çıkar: o okumanın
silinmesi ilgili dönem tüketimini, raporları, maliyeti ve EnPI'yi değiştirir.

## Doğrudan tüketim

Sayaç endeksi yerine, bir ayın tüketimini doğrudan girmek için kullanılır.
**Ne zaman:**

- o enerji türünde sayaç yoksa (örneğin yalnızca fatura geliyorsa),
- sayaç var ama o ay okunamadıysa,
- faturadaki değeri esas almak istiyorsanız.

Ay ve enerji türü başına tek kayıt tutulur, enerji türünün kendi birimindedir.

**Öncelik:** bir ay için doğrudan tüketim girilmişse fabrika toplamı odur.
Aynı ayda sayaç tüketimi de varsa **değerler toplanmaz**; panelde iki değer ve
aralarındaki fark uyarı olarak gösterilir. Doğrudan kaydı silerseniz o ay için
yeniden sayaç tüketimi kullanılır.

## Üretim

Tarih, miktar ve birim (ton, adet…) girilir. Aynı gün ve aynı birim için tek
kayıt tutulur. Farklı üretim birimleri **birbirine toplanmaz**; EnPI her birim
için ayrı hesaplanır.

## Hedef

Ay ve enerji türü bazında aylık tüketim hedefi girilir. Panelde gerçekleşme
yüzdesi ve hedefin aşılıp aşılmadığı gösterilir. Hedefler enerji türünün kendi
birimindedir.

## Dönüşüm katsayısı

Farklı enerji türlerini ortak bir birimde (GJ/TEP) toplayabilmek için gerekir.

Kural: **1 enerji türü birimi = katsayı GJ**. Örnek: doğal gaz için `0,0385`
girilirse 1 Sm³ = 0,0385 GJ kabul edilir.

- `kWh`, `MJ`, `GJ` gibi birimler için katsayı girmenize gerek yoktur.
- `Sm³`, `kg`, `ton` gibi birimlerde katsayı **siz girmezseniz sistem tahmin
  etmez**: o enerji türü ortak toplama katılmaz ve panelde eksik olduğu yazılır.
- Katsayı faturanızdan veya tedarikçinizden gelir. Hangi değeri kullandığınızı
  **Kaynak** ve **Not** alanlarına yazın (örneğin üst ısıl değer mi alt ısıl
  değer mi kullandığınızı).
- Katsayı zamanla değişirse eskisini silmeyin, yeni bir **geçerlilik
  başlangıcı** ile ikinci bir katsayı ekleyin. Her dönem, o döneme uyan en yeni
  katsayıyla hesaplanır.

## Gösterge paneli

Ay, enerji türü ve toplam enerji birimi (kWh / MJ / GJ / TEP) seçilir. Panelde:

- dönem tüketimi ve kaynağı (sayaç / doğrudan),
- önceki ayla karşılaştırma, maliyet, varsa hedef durumu,
- üretim birimine göre EnPI,
- bütün enerji türlerinin seçilen birimdeki toplamı,
- bölüm dağılımı ve **"ölçülmeyen / dağıtılmamış"** payı,
- son 12 ayın tüketim, toplam enerji ve EnPI eğrileri yer alır.

**"Ölçülmeyen / dağıtılmamış"**, fabrika toplamı ile bölüm sayaçlarının toplamı
arasındaki farktır — kayıp veya kaçak değil, henüz ölçülmemiş/bir bölüme
atanmamış paydır.

Panel gerektiğinde uyarı gösterir: doğrudan tüketim ile sayaç çakışması, ana
sayaç okumasının eksik olması, dönüşüm katsayısının bulunmaması.

## Rapor

Tarih aralığı ve kırılım (enerji türü / sayaç / bölüm) seçilir; sayfa
yazdırılabilir. Enerji türü kırılımında tüketimin kaynağı, seçilen birimdeki
eşdeğeri ve kullanılan katsayı da görünür. Üretim/EnPI ve hedef tabloları
rapora dahildir.

## Tanımları değiştirmek

Tanımların geçmiş sürümü tutulmaz. Bir sayacın bölümünü, ana/alt durumunu veya
çarpanını değiştirirseniz **geçmiş raporlar da değişir**. Ekranlarda bu
uyarılar yazılıdır; okuması olan bir sayacın enerji türü ancak açık onayla
değiştirilebilir.

## Yedekleme ve geri yükleme

Bütün veriler tek bir dosyadadır: `data\enerji.db`.

**Yedek almak:** `yedekle.bat` dosyasına çift tıklayın (veya
`python scripts/backup.py`). Uygulama açıkken de güvenlidir. Yedek
`backups` klasörüne tarih-saat adıyla yazılır.

Ayda bir, mümkünse her veri girişinden sonra yedek alın ve yedeği **ayrıca bir
USB belleğe kopyalayın**. Aynı bilgisayarda kalan yedek, disk arızasında
veriyle birlikte kaybolur.

> **`data\enerji.db` dosyasını Windows Dosya Gezgini'nden kopyalayıp yedek
> saymayın.** Uygulama SQLite'ı WAL kipinde çalıştırır; son girdiğiniz kayıtlar
> henüz ana dosyaya yazılmamış, yanındaki `enerji.db-wal` dosyasında bekliyor
> olabilir. Uygulama açıkken yapılan böyle bir kopya **sessizce eksik** olur ve
> bunu ancak geri yüklemeye çalıştığınızda fark edersiniz. Her zaman
> `yedekle.bat` dosyasını (veya `scripts/backup.py`) kullanın: bu yöntem
> SQLite'ın kendi yedekleme arayüzünü kullandığı için uygulama açıkken de tam
> ve tutarlı bir kopya üretir.

**Geri yüklemek:** önce uygulamayı kapatın, sonra:

```
.venv\Scripts\python scripts\restore.py
```

Komut mevcut yedekleri listeler; geri yüklemek istediğiniz dosyayı ikinci kez
komuta ekleyerek çalıştırın. Üzerine yazmadan önce mevcut veritabanı
kendiliğinden yedeklenir, bu yüzden yanlış dosya seçseniz bile eski duruma
dönebilirsiniz.

## Sık karşılaşılanlar

| Durum | Nedeni / çözümü |
|---|---|
| Giriş sonrası "Internal Server Error" | Veritabanı tabloları oluşmamış. Uygulamayı kapatıp `alembic upgrade head` çalıştırın. (`baslat.bat` bunu başlamadan önce kontrol eder ve uyarır.) |
| Tarayıcı açılmadı | Adres çubuğuna `http://127.0.0.1:8000` yazın. Sunucu 60 saniyede hazır olmazsa siyah penceredeki mesajı okuyun. |
| "Sunucu baslatilamadi" | 8000 portu kullanımda — uygulama zaten açık olabilir. Diğer siyah pencereleri kapatıp tekrar deneyin. |
| Panelde tüketim 0 görünüyor | O ay için **ikinci** okuma (ertesi ayın 1'i) henüz girilmemiş olabilir. |
| "Ana sayaç okuması yok" uyarısı | Ana sayaç tanımlı ama o dönemde okuması yok. Alt sayaçlar ana sayacın yerine geçmez; eksik okumayı girin. |
| "Toplam enerji hesaplanamadı" | O enerji türünün dönüşüm katsayısı yok. Katsayılar ekranından tanımlayın. |
| Bölüm dağılımı fabrika toplamından fazla | Alt sayaçlar ana sayaçtan fazla ölçüyor: sayaç tanımlarını, çarpanları ve ana sayaç seçimini gözden geçirin. |
| Parolayı unuttum | `python scripts/set_password.py` ile yeni özet üretip `.env` içindeki `APP_PASSWORD_HASH` satırını değiştirin. Veriler etkilenmez. |
