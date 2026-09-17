# Enerji Yönetim Platformu — Sistem ve Uygulama El Kitabı

> Bu belge programın **temel referans dokümanıdır**. Programın nasıl çalışacağına
> dair bütün kurallar, ekranlar, veri yapıları, hesaplamalar ve fonksiyonlar
> burada tanımlanır. Kodlama, bu belge tamamlanıp mutabakat sağlandıktan sonra
> başlar.

| | |
|---|---|
| **Sürüm** | 0.3 — taslak, tasarım aşaması |
| **Durum** | Kodlama **başlamadı**. Tasarım görüşmesi sürüyor. |
| **Son güncelleme** | 2026-09-17 |
| **Mimari** | Tek HTML dosyası, tarayıcıda çalışır, sunucu yok (K-09) |
| **Kaynak veri** | `veri.xlsx` — tek sayfa, 108 sütun, 2018-01 → 2025-12 (96 ay) |
| **İlgili belge** | `docs/ISLEV-ANALIZI.md` — piyasa ve işlev analizi |

---

## 1. Amaç ve kapsam

### 1.1 Ne yapacağız

Bugün Excel'de tutulan aylık enerji ve üretim verilerini; **düzenli, denetlenebilir
ve analiz edilebilir** bir platforma taşımak. Kullanıcı verileri elle girecek;
sistem bu verileri otomatik işleyip grafiklere, göstergelere ve ISO 50001
çalışmasını destekleyen raporlara dönüştürecek.

### 1.2 Kapsam içi

- Aylık **elle veri girişi** (tüketim, üretim, maliyet).
- Verinin otomatik işlenmesi, türetilmiş değerlerin hesaplanması.
- Grafikler, göstergeler, karşılaştırmalar, performans analizi.
- ISO 50001 yaklaşımını destekleyen yapı: EnPI, baz çizgi, hedef, SEU, aksiyon.
- Geçmiş Excel verisinin sisteme aktarılması (2018-01'den bugüne).

### 1.3 Kapsam dışı (şimdilik)

- Otomatik sayaç okuma, Modbus/OPC/SCADA entegrasyonu.
- ERP / fatura sistemi entegrasyonu.
- Gerçek zamanlı izleme, alarm, uzaktan kumanda.
- Saatlik / günlük veri. **Dönem birimi: AY.**
- Çok kullanıcı, rol ve yetki yönetimi. **Tek kullanıcı** (K-09).
- Sunucu, bulut, mobil uygulama.

> Bunlar reddedilmiş değil, **ertelenmiştir**. Veri modeli bunları sonradan
> kaldırabilecek şekilde tasarlanır (bkz. Bölüm 6.10).

### 1.4 Tasarım hedefi

> **Sade ama büyütülebilir.** Bugün ihtiyaç duyulmayan özellik eklenmez; ancak
> hiçbir bugünkü karar, yarınki özelliği imkânsız kılmaz.

---

## 2. Mevcut durum: Excel'in analizi

### 2.1 Fiziksel yapı

Tek sayfa (`Veri`), **geniş (wide) format**: 1 satır = 1 ay, 108 sütun.
120 ay yuvası açılmış (2018-01 → 2027-12). Gerçek veri **2018-01 → 2025-12**
arası 96 ay. GES satırları 2026-03'e kadar uzuyor.

Sütun grupları:

| Aralık | Grup | İçerik |
|---|---|---|
| A–B | — | Yıl, Ay |
| C–M | ÜRETİM VERİLERİ | Hat çekirdek tüketimi, kakao ürünleri, çikolata, toplamlar |
| N–U | ELEKTRİK | Satın alınan, üretilen, toplam; Yozgat ve Adana GES |
| V–AD | DOĞALGAZ | 3 istasyon (kWh ve m³), toplamlar, TL |
| AE–AF | MOTORİN | Kg ve TL — **8 yıldır boş** |
| AG–AH | TOPLAM ENERJİ | Toplam kWh ve TL |
| AI–DD | MAKİNE/EKİPMAN | Türbin, GM-1..3, Kazan-1..2, kompresörler, chiller'lar, üretim makineleri |

### 2.2 Excel'in içindeki hesap kuralları

Formüllerden çıkarılan, **korunacak** kurallar:

| Türetilmiş değer | Kural | Değerlendirme |
|---|---|---|
| Hat-1..4 çekirdek tüketimi | `Toplam çekirdek × 0,34 / 0,12 / 0,32 / 0,22` | **Ölçüm değil, sabit oranla dağıtım.** Sistemde açıkça "dağıtılmış" olarak işaretlenecek. |
| Toplam Kakao Üretimi | `Kakao Yağı + Kakao Tozu + Kakao Likör` | Korunur |
| Toplam Üretim | `Toplam Kakao + Çikolata` | Korunur |
| Üretilen Elektrik | `Türbin + GM-1 + GM-2 + GM-3 elektrik üretimi` | Korunur |
| Toplam Elektrik Enerjisi | `Satın alınan + Üretilen` | Korunur (bilgi amaçlı; toplam enerjiye girmez) |
| Toplam Doğalgaz kWh / m³ | `İstasyon 1 + 2 + 3` | Korunur |
| **Toplam Enerji Tüketimi kWh** | **`Satın alınan elektrik + Toplam doğalgaz`** | **Doğru ve korunur.** Kendi ürettiği elektriği saymıyor → çift sayım yok. |
| Toplam Enerji TL | `Elektrik TL + Doğalgaz TL` | Korunur |
| Buhar kg → kWh | `kg × 600 / 860` = 0,6977 kWh/kg | Korunur, ancak **tarihli katsayı** olarak tanımlanır |
| Doğalgaz m³ → kWh | (formül yok, elle) ≈ **10,92 kWh/m³** | İkisi de elle girilecek; sistem tutarlılığı **denetler** |

### 2.3 Tespit edilen sorunlar

| # | Sorun | Sistemdeki çözümü |
|---|---|---|
| S1 | **Yeni makine = yeni sütun.** 108 sütuna ulaşılmış, sonu isimsiz placeholder ("1,2,3…") | Dar (long) format: yeni makine = yeni **satır**, şema değişmez |
| S2 | **Ölçüm kapsamı %26.** 2024-01: alt sayaçlar 965.134 kWh / fabrika 3.761.332 kWh. %74 ölçülmüyor, Excel bunu göstermiyor | Her düğümde **"ölçülmeyen / dağıtılmamış"** payı ayrı satır olarak gösterilir |
| S3 | **İstasyon ≠ makine toplamı.** 2024-01: İstasyon-1 doğalgaz 2.905.568 kWh, GM'ler toplamı 1.441.116 kWh | Hiyerarşi tutarlılık denetimi; fark ekranda gösterilir |
| S4 | **BX–DD sütunları tutarsız.** Sadece 2025-12 dolu; Vakum Mikser 30,3 GWh / fabrika 3,3 GWh | **Karar: aktarılmayacak** (bkz. K-02) |
| S5 | **Birim fiyat 11 kat değişmiş** (0,29 → 3,24 TL/kWh) | **Tarihli fiyat zorunlu**; tek "güncel fiyat" modeli kullanılamaz |
| S6 | **GM-1/2/3 2025'te durmuş** (12 ay boş), İstasyon-1 gazı akmaya devam ediyor | Varlıklara **devreye alma / çıkarma tarihi** |
| S7 | F sütunu başlığı "Hat-3" olarak tekrar ediyor | Aktarımda **Hat-4** olarak düzeltilir |
| S8 | Motorin tanımlı ama 8 yıldır boş | Enerji türü olarak tanımlanır, veri girilmez |
| S9 | Doğalgaz m³ ve kWh **çift elle giriş** | Kullanıcı kararı (K-04); sistem tutarlılığı denetler |

### 2.4 Verinin bize söylediği: EnPI zaten bir soru soruyor

| Yıl | Toplam enerji (kWh) | Toplam üretim (kg) | EnPI (kWh/kg) |
|---|---:|---:|---:|
| 2018 | 144.282.334 | 104.980.360 | 1,374 |
| 2019 | 155.637.609 | 101.839.334 | 1,528 |
| 2020 | 153.983.384 | 101.758.697 | 1,513 |
| 2021 | 139.997.897 | 98.148.940 | 1,426 |
| 2022 | 124.131.364 | 107.258.078 | **1,157** |
| 2023 | 129.376.725 | 111.976.787 | 1,155 |
| 2024 | 131.235.894 | 111.897.453 | 1,173 |
| 2025 | 137.367.837 | 100.503.911 | **1,367** |

2025'te EnPI %17 kötüleşmiş. Ama üretim de 111,9 → 100,5 milyon kg düşmüş.

> **Bu gerçek bir verimsizlik mi, yoksa sabit yükün düşük üretime bölünmesi mi?**
> Ham EnPI bu iki sebebi ayıramaz. Platformun en önemli işlevi bu soruyu
> cevaplamak olacak (bkz. Bölüm 7 — regresyonlu baz çizgi ve normalize EnPI).

---

## 3. Temel ilkeler

Bu ilkeler **bağlayıcıdır**. Her yeni özellik bunlara uymak zorundadır.

**İ-1 · Ham veri ile hesap ayrıdır.**
Veritabanında yalnızca **girilen** değerler saklanır. Tüketim toplamı, maliyet,
EnPI, emisyon, baz çizgi sapması gibi türetilmiş hiçbir değer saklanmaz; her
zaman ham veriden yeniden hesaplanır. Saklanan tek istisna **model
parametreleridir** (regresyon katsayısı gibi) — çünkü o bir *karardır*, türev
değil.

**İ-2 · Tek hesap kaynağı.**
Bütün hesaplar merkezî hesap modülünde yapılır. Hiçbir ekran kendi hesabını
yapmaz. Panel ile rapor asla farklı sayı gösteremez.

**İ-3 · Belirsizlik sıfıra çevrilmez.**
Katsayı yoksa, fiyat yoksa, veri yoksa sonuç **üretilmez** ve nedeni ekranda
yazılır. Eksik veri asla `0` olarak işlenmez. "Sessiz yanlış" yerine
"gürültülü doğru" tercih edilir.

**İ-4 · Her varsayım görünür.**
Dağıtılmış değer, tahmin edilmiş değer, düşük model uyumu, farklı dönem
uzunluğu — hepsi sonucun yanında gösterilir, ayrı bir sekmeye sürülmez.

**İ-5 · Geçmiş bozulmaz.**
Tanımlar silinmez, pasife alınır. Fiyat ve katsayılar tarihlidir. Varlıkların
devreye giriş/çıkış tarihi vardır. Geçmiş bir dönemin sonucu, bugün yapılan bir
tanım değişikliğiyle değişmez.

**İ-6 · Enerji dengesi ile mali denge ayrıdır.**
kWh akışı ile TL akışı farklı kurallara tabidir ve asla birbirinden türetilmez
(bkz. Bölüm 7).

**İ-7 · Veri seti ile hiyerarşi bağımsızdır.**
Ölçüm noktaları düz bir listedir. Hiyerarşi ayrı kurulur ve serbestçe
değiştirilebilir. Hiyerarşiyi değiştirmek hiçbir veriyi bozmaz.

**İ-8 · Bugün gerekmeyen eklenmez, ama yarın imkânsız kılınmaz.**

---

## 4. Karar kütüğü

Görüşme sırasında alınan kararlar. Her karar numaralıdır; sonraki bölümler bu
numaralara atıf yapar.

| # | Konu | Karar | Gerekçe |
|---|---|---|---|
| **K-01** | Başlangıç noktası | **Tamamen yeni proje.** Mevcut sayaç-endeks tabanlı uygulama devam ettirilmez. | Excel'in yapısı (aylık doğrudan değer) mevcut modelle (endeks okuma) örtüşmüyor. Temiz kurgu daha az maliyetli. |
| **K-02** | BX–DD sütunları (Vakum Mikser, Nova, Konç…) | **Aktarılmayacak.** Deneme/taslak veri. | Değerler aylık tüketim olamayacak büyüklükte (Vakum Mikser 30,3 GWh / fabrika 3,3 GWh). Sadece 1 ay dolu. |
| **K-03** | GES'ler (Yozgat, Adana) | **Ayrı tesis.** Fabrikanın enerji dengesine (kWh) **girmez**. Mali dengeye **TL mahsubu** olarak girer. | GES farklı lokasyonda, şebekeye basıyor. Mahsup TL cinsinden. Fiziksel enerji fabrikaya girmiyor. |
| **K-04** | Doğalgaz m³ / kWh | **İkisi de elle girilir.** Sistem türetmez, tutarlılığı denetler ve sapmayı uyarı olarak gösterir. | Excel'deki mevcut çalışma düzeni korunuyor. |
| **K-05** | Varlık hiyerarşisi | **Veri setinden bağımsız, serbest derinlikte ağaç.** Kullanıcı her varlığın hiyerarşideki yerini özgürce belirler ve değiştirir. Yeni varlık eklendiğinde konumu da belirlenir. | Excel'in çözemediği sorun. Hiyerarşi değişimi veriyi bozmamalı. |
| **K-06** | EnPI | **Kullanıcı tanımlı serbest EnPI seti.** Sistem hazır gösterge dayatmaz; kullanıcı pay/payda seçerek istediği kadar gösterge tanımlar. | Farklı ürün ve enerji türleri için farklı göstergeler gerekiyor. |
| **K-07** | Enerji türü sınıflandırması | **Ölçüm noktası bazında "enerji rolü" seçimi** (genişletilebilir liste). Her rolün varsayılan davranışı vardır; kullanıcı ölçüm noktası bazında değiştirebilir. | Sabit üç sınıf yetersiz; tek onay kutusu ise yanlış işaretlemeye açık. Rol listesi ikisinin ortası. |
| **K-08** | Dönem birimi | **AY.** Tüm veri girişi ve hesaplar aylık. | Kullanıcının çalışma düzeni aylık. |
| **K-09** | Dağıtım biçimi | **Tek HTML dosyası.** Tarayıcıda çalışır; sunucu, veritabanı sunucusu, Python veya kurulum yoktur. Dosyaya çift tıklanarak açılır. | İnternet ve kurulum bağımlılığı sıfır; USB ile taşınabilir; güncelleme tek dosya değişimi. Veri hacmi (≈8.600 değer) bu mimari için fazlasıyla küçük. |
| **K-10** | Veri saklama | **İki katmanlı:** (1) tarayıcı deposuna (IndexedDB) **otomatik** yazma — kaydetmeyi unutma riski yok; (2) tek tuşla **`.json` yedek dosyası** dışa/içe aktarma — yedekleme, taşıma ve geri yükleme bununla. | Tek HTML dosyası kendi içine veri yazamaz. Yalnız tarayıcı deposu kullanılsaydı, tarayıcı verisi temizlendiğinde 8 yıllık veri sessizce kaybolurdu. |
| **K-11** | Tarayıcı | **Chrome / Edge.** Bu tarayıcıların dosya erişim özelliği (File System Access API) kullanılabilir. | Kullanıcının çalışma ortamı. Gerçek dosyaya doğrudan otomatik yazma seçeneği açılabilir hale gelir. |
| **K-12** | Maliyet verisi | **Fatura tutarı elle girilir.** Sistem birim fiyatı geriye doğru hesaplar (TL ÷ tüketim) ve trendini gösterir. | Fatura gerçeği vergi, dağıtım bedeli, fon ve güç bedelini içerir; birim fiyattan hesaplanan maliyet bunları kaçırır. Excel'deki mevcut düzen de budur. |
| **K-13** | GES mahsubu | Elektrik TL'si **mahsup öncesi brüt faturadır.** GES mahsubu **ayrı kalem** olarak tutulur; net ödenen tutarı sistem hesaplar. Mahsup fazlası satış geliri ayrı izlenir. | Mahsubun sağladığı tasarruf ayrı görünür ve ölçülebilir hale gelir. |
| **K-14** | Veri girişi yöntemi | **Dört yöntem birden:** Excel benzeri tek tablo · kategori bazlı formlar · ikisi arasında geçiş · dosya yükleme. Kullanıcı duruma göre seçer. | Toplu aylık giriş ile tek bir değeri düzeltmek farklı işlerdir; her birine uygun yöntem sunulur. |
| **K-15** | İçe aktarma formatı | **`.xlsx` doğrudan okunur** (sürükle-bırak). Gerekli kütüphane dosyaya gömülür (~400 KB). | Ara dönüştürme adımı olmadan mevcut Excel dosyası kullanılabilir. |
| **K-16** | Geçmiş verinin aktarımı | **İkisi birden:** tanımlar (varlık ağacı, ölçüm noktaları, hiyerarşi, katsayılar) programa **gömülü hazır** gelir; 96 aylık değerleri kullanıcı **kendisi yükler**. Hazır `.json` da birlikte verilir. | Kurulum yükü ortadan kalkar, ama aktarma ekranı gerçek veriyle sınanmış olur ve kontrol kullanıcıda kalır. |
| **K-17** | Grafikler | **Saf SVG, sıfır dış kütüphane.** Grafik kütüphanesi kullanılmaz. | Dosya küçük kalır, internet hiç gerekmez, Türkçe sayı biçimi ve etiketler üzerinde tam kontrol olur. *Bu karar tasarımcı önerisidir; itiraz edilirse gözden geçirilir.* |
| **K-18** | Kaynak düzeni | Geliştirme sırasında kaynak **ayrı dosyalarda** tutulur; küçük bir birleştirme betiği hepsini **tek HTML çıktısına** gömer. Teslim edilen ürün yine tek dosyadır. | 10.000 satırlık tek dosya bakılamaz hale gelir. Çıktı tek dosya, kaynak düzenli. |

---

## 5. Teknik mimari

### 5.1 Genel yapı (K-09)

Program **tek bir HTML dosyasıdır**. Çift tıklanır, tarayıcıda açılır. Sunucu,
veritabanı sunucusu, Python, Node.js, kurulum ve internet **gerekmez**.

```
enerji-yonetim.html          ← programın tamamı (tek dosya, ~1 MB)
  ├── HTML  (ekran iskeletleri)
  ├── CSS   (gömülü)
  ├── JS    (gömülü: hesap motoru, ekranlar, SVG grafik motoru)
  ├── xlsx okuyucu kütüphanesi (gömülü, K-15)
  └── başlangıç tanımları (gömülü: varlık ağacı, ölçüm noktaları, K-16)

enerji-veri-2026-09-17.json  ← VERİNİZ (ayrı dosya, yedek/taşıma)
```

**Neden bu ölçekte sorun değil:** 96 ay × ~90 ölçüm noktası ≈ 8.640 değer.
JSON olarak yarım megabayt civarı. 20 yıllık veride ~2 MB. Tarayıcı bu hacmi
rahatça işler; sunucuya ihtiyaç doğuran bir büyüklük değildir.

### 5.2 Veri saklama (K-10) — mimarinin en kritik noktası

> **Temel gerçek:** Bir HTML dosyası kendi içine veri yazamaz. Program dosyası
> ile veri birbirinden ayrıdır. Bu yüzden saklama iki katmanlıdır.

**Katman 1 — Tarayıcı deposu (IndexedDB), otomatik**

- Her değişiklik anında yazılır. Kaydetmeyi unutma riski **yoktur**.
- Program kapatılıp açıldığında veri yerindedir.
- **Sınırı:** Tarayıcının site verisi temizlenirse silinir. Gizli sekmede boş
  görünür. Başka bilgisayara taşınmaz. Bu yüzden tek başına yeterli değildir.

**Katman 2 — `.json` yedek dosyası, elle**

- Tek tuşla dışa aktarılır: `enerji-veri-YYYY-AA-GG.json`
- İçe aktarma ile geri yüklenir; başka bilgisayara taşınır.
- Yedeğin tamamı tek dosyadır: tanımlar + hiyerarşi + bütün aylık değerler +
  katsayılar + EnPI tanımları + hedefler.

**Veri kaybını önleyen davranışlar:**

| Durum | Programın davranışı |
|---|---|
| Açılışta son yedek 7 günden eski | Üstte uyarı şeridi: *"Son yedek 12 gün önce alındı. Yedek al."* |
| Hiç yedek alınmamış | Açılışta kalıcı uyarı |
| Veri girildi, yedek alınmadan sekme kapatılıyor | Tarayıcı çıkış uyarısı |
| İçe aktarma yapılacak | Önce mevcut veriden **otomatik güvenlik yedeği** indirilir |

**Chrome / Edge ek kolaylığı (K-11, isteğe bağlı):**
Kullanıcı bir kez veri dosyasını seçerse, program bundan sonra doğrudan o
dosyaya yazabilir — tıpkı Excel gibi. Bu açılırsa Katman 2 elle olmaktan
çıkar, otomatikleşir. Varsayılan olarak kapalıdır; kullanıcı ister.

### 5.3 Veri dosyası biçimi

```jsonc
{
  "sema_surumu": 1,              // ileride göç için
  "olusturma": "2026-09-17T10:30:00",
  "ayarlar":   { "fabrika_adi": "...", "para_birimi": "TL" },
  "varliklar":        [ /* ağaç düğümleri */ ],
  "olcum_noktalari":  [ /* tanımlar */ ],
  "enerji_turleri":   [ ... ],
  "donusum_katsayilari": [ ... ],
  "enpi_tanimlari":   [ ... ],
  "hedefler":         [ ... ],
  "baz_cizgiler":     [ ... ],
  "aksiyonlar":       [ ... ],
  "degerler": [ { "n": "GM1_DG_M3", "y": 2024, "a": 1, "v": 44000 } ]
}
```

`degerler` dizisi kısa anahtar kullanır (`n`, `y`, `a`, `v`) — 8.600 kayıtta
dosya boyutunu belirgin küçültür. **Türetilmiş hiçbir değer dosyada yer almaz**
(İ-1); yalnızca girilen ham veriler ve tanımlar saklanır.

`sema_surumu` alanı, ileride veri yapısı değişirse eski yedeklerin otomatik
dönüştürülmesini sağlar. Bir yedek dosyası **hiçbir zaman** okunamaz hale
gelmemelidir.

### 5.4 Kütüphaneler ve grafikler (K-15, K-17)

| Bileşen | Karar | Boyut |
|---|---|---|
| Grafikler | **Saf SVG**, kendi motorumuz. Dış kütüphane yok. | ~0 |
| `.xlsx` okuma | Gömülü kütüphane | ~400 KB |
| Diğer her şey | Saf JavaScript | — |
| **Toplam** | | **~1 MB** |

Saf SVG tercihinin nedeni: internet bağımlılığı sıfır kalır, Türkçe sayı
biçimlendirmesi (`1.250,50`) ve eksen etiketleri üzerinde tam kontrol olur,
dosya küçük kalır ve grafik davranışı yıllar içinde değişmez.

Gerekli grafik tipleri SVG ile karşılanabilir: çizgi, sütun, yığılmış sütun,
ısı haritası, dağılım (regresyon için), Pareto, CUSUM, Sankey.

### 5.5 Kaynak düzeni ve derleme (K-18)

Teslim edilen ürün tek dosyadır; **geliştirme tek dosyada yapılmaz.**

```
kaynak/
  index.html          iskelet
  css/                stil
  js/
    veri.js           depolama (IndexedDB + json)
    model.js          veri modeli ve doğrulama
    hesap.js          HESAP ÇEKİRDEĞİ — tek hesap kaynağı (İ-2)
    grafik.js         SVG grafik motoru
    ekranlar/         her ekran ayrı dosya
  vendor/             xlsx okuyucu
  baslangic.json      gömülü tanımlar (K-16)
derle.py              hepsini tek HTML'e gömer
cikti/
  enerji-yonetim.html ← teslim edilen dosya
```

### 5.6 Güvenlik ve gizlilik

Veri **hiçbir yere gönderilmez.** Program ağa hiç çıkmaz; tüm işlem kullanıcının
bilgisayarında, tarayıcı içinde gerçekleşir. Sunucu olmadığı için sunucu
güvenliği, oturum yönetimi veya parola konusu yoktur. Verinin korunması,
yedek dosyasının saklanmasıyla sağlanır.

---

### 5.7 Görsel dil ve grafik standartları

Grafikler saf SVG ile çizilir (K-17). Aşağıdaki kurallar **bağlayıcıdır**;
amaç bütün ekranların tek bir sistem gibi okunmasıdır.

#### 5.7.1 Renk paleti

Renk **işine göre** seçilir, güzelliğine göre değil. Dört iş vardır:

| İş | Kullanım | Palet |
|---|---|---|
| **Kimlik** (kategorik) | Ayrı serileri ayırt etmek | Aşağıdaki 8 slot, **sabit sırayla** |
| **Büyüklük** (sequential) | Isı haritası, yoğunluk | Tek hue, açıktan koyuya (mavi) |
| **Kutupluluk** (diverging) | Sapma, CUSUM, hedefe fark | Mavi ↔ kırmızı, **nötr gri orta nokta** |
| **Durum** (status) | İyi / uyarı / ciddi / kritik | Ayrılmış; seri rengi olarak asla kullanılmaz |

**Kategorik slotlar (sıra değişmez):**

| Slot | Renk | Açık tema | Koyu tema |
|---|---|---|---|
| 1 | mavi | `#2a78d6` | `#3987e5` |
| 2 | turuncu | `#eb6834` | `#d95926` |
| 3 | deniz yeşili | `#1baf7a` | `#199e70` |
| 4 | sarı | `#eda100` | `#c98500` |
| 5 | macenta | `#e87ba4` | `#d55181` |
| 6 | yeşil | `#008300` | `#008300` |
| 7 | mor | `#4a3aa7` | `#9085e9` |
| 8 | kırmızı | `#e34948` | `#e66767` |

Bu sıra renk körlüğü testlerinden geçmiş bir sıradır; **karıştırılmaz**.
8'den fazla seri gerekirse yeni renk üretilmez — kuyruk "Diğer"e katlanır
veya grafik küçük parçalara bölünür.

**Sıralı (sequential) ramp — ısı haritası için:** tek hue mavi,
`#cde2fb` (açık) → `#0d366b` (koyu), 12 adım.

**Kutuplu (diverging) — CUSUM ve sapma için:** mavi (tasarruf) ↔ kırmızı
(kayıp), orta nokta nötr gri (`#f0efec` açık / `#383835` koyu).
Orta noktada **asla renk olmaz** — "sıfır sapma" hiçbir şey demektir.

**Durum renkleri (asla seri rengi olarak kullanılmaz):**
iyi `#0ca30c` · uyarı `#fab219` · ciddi `#ec835a` · kritik `#d03b3b`.
Her zaman **ikon + etiket** ile birlikte kullanılır; renk tek başına anlam taşımaz.

**Zemin ve mürekkep:**

| Rol | Açık | Koyu |
|---|---|---|
| Grafik zemini | `#fcfcfb` | `#1a1a19` |
| Sayfa zemini | `#f9f9f7` | `#0d0d0d` |
| Ana metin | `#0b0b0b` | `#ffffff` |
| İkincil metin | `#52514e` | `#c3c2b7` |
| Eksen / etiket | `#898781` | `#898781` |
| Kılavuz çizgi | `#e1e0d9` | `#2c2c2a` |
| Taban / eksen çizgisi | `#c3c2b7` | `#383835` |

#### 5.7.2 Yasaklar

| Yasak | Neden |
|---|---|
| **Çift eksenli grafik** (iki y-ekseni) | İki ölçeğin hizası keyfîdir; veride olmayan bir ilişki uydurur. **Bu en yaygın grafik hatasıdır.** Çözüm: iki ayrı grafik veya ortak tabana indeksleme |
| Gökkuşağı / çok renkli büyüklük rampası | Büyüklük tek hue ile gösterilir |
| Kutuplu grafiğin ortasında renk | Orta nokta "hiçbir şey" demeli |
| Sıralaması olmayan kategorilerde değer rampası | Çubuk uzunluğu zaten büyüklüğü gösterir; rengi boşa harcar |
| Her veri noktasına sayı yazmak | Okunmaz. Seçici etiketleme: uç nokta, aykırı değer, önemli seri |
| 8'den fazla kategorik renk | Renk körlüğünde ayırt edilemez |
| Kalın bloklar, kalın kılavuz çizgileri | İnce işaretler, saç teli kılavuz |
| Kesikli kılavuz veya eksen çizgisi | Gürültü yaratır, "eşik" gibi okunur |
| Durum rengini seri rengi olarak kullanmak | Kırmızı "kritik" demek; "4. seri" değil |
| 2 dilimli pasta, tek çubuklu grafik | Sayının kendisi yeterlidir → KPI kartı |

#### 5.7.3 Zorunlu davranışlar

- **≥2 seri varsa açıklama (legend) her zaman vardır**; ≤4 seri ise ayrıca
  doğrudan etiketlenir. Kimlik asla yalnız renge bırakılmaz.
- **Her grafiğin fare üstü (hover) katmanı vardır:** çizgi/alan grafiklerde
  dikey nişangâh + kutucuk, çubuk/nokta/hücrede işaret başına kutucuk.
- **Her grafiğin "tablo olarak göster" seçeneği vardır.** Renk göremeyen,
  yazdıran veya sayıyı okumak isteyen kullanıcı için.
- **Koyu tema ayrı seçilmiştir**, otomatik ters çevirme değildir. Yukarıdaki
  koyu sütun kullanılır.
- Sayı biçimi Türkçedir: `1.250,50`. Eksen etiketlerinde ve tablo sütunlarında
  hizalı rakam (`tabular-nums`) kullanılır.

#### 5.7.4 Bu platformda kullanılacak grafik tipleri

| Grafik | Form | Renk işi | Not |
|---|---|---|---|
| Aylık tüketim trendi | Sütun | Tek slot (1) | Tek seri → açıklama gerekmez |
| Enerji türü dağılımı | Yığılmış sütun | Kategorik | Segmentler arası 2px boşluk |
| EnPI trendi | Çizgi | Tek slot (1) + baz çizgi referansı | **Tüketimle aynı grafikte değil** |
| Beklenen vs gerçek | İki çizgi | Kategorik (1, 2) | Açıklama + uç nokta etiketi |
| Regresyon (üretim–enerji) | Dağılım + doğru | En fazla 3 seri | Baz dönem / sonraki dönem ayrımı |
| CUSUM | Çizgi + dolgu | **Kutuplu** | Sıfırın altı mavi (tasarruf), üstü kırmızı (kayıp) |
| Isı haritası (yıl × ay) | Hücre matrisi | **Sıralı** mavi | Ölçek açıklaması zorunlu |
| Pareto | Yatay çubuk + tablo | Tek slot (1) | Kümülatif % **tabloda**, çift eksen değil |
| Enerji akışı | Sankey | Kategorik | Enerji dengesi ekranı |
| KPI | Kart (değer + fark + mini grafik) | Durum renkleri | Grafik değil, sayının kendisi |

> **Pareto notu:** Klasik Pareto çift eksenlidir (çubuk = değer, çizgi =
> kümülatif %). Bu yasak olduğu için kümülatif yüzde, çubukların yanındaki
> **tablo sütununda** gösterilir ve %80 eşiği satır arasına konan bir ayraçla
> işaretlenir. Sonuç daha okunaklıdır ve kuralı çiğnemez.

---

## 6. Veri modeli

### 6.1 Temel fikir: geniş → dar format

Excel'de bir ay = 1 satır × 108 sütun. Sistemde bir ay = **N satır**, her satır
bir ölçüm noktasının o aydaki değeri.

```
EXCEL (geniş)                      SİSTEM (dar)
─────────────────────────          ──────────────────────────────────
Yıl  Ay    GM1_DG  GM1_EL          nokta      yıl   ay   değer
2024 Ocak  480000  180000    →     GM1_DG     2024  1    480000
                                   GM1_EL     2024  1    180000
```

**Kazanç:** Yeni makine eklemek = yeni satır. Şema değişmez, geçmiş bozulmaz,
ekranlar kendiliğinden uyum sağlar. 96 ay × ~90 nokta ≈ 8.600 satır — SQLite
için önemsiz bir hacim.

**Kullanıcıya yansıması yok:** Giriş ekranı yine Excel gibi tablo görünebilir
(bkz. Bölüm 9). Değişen sadece altındaki depolamadır.

### 6.2 Üç katman

```
┌─────────────────────────────────────────────────────┐
│ 1. ÖLÇÜM NOKTASI (düz liste)                        │
│    "GM-1 Doğalgaz Tüketimi m³"  · birim · rol       │
└──────────────────┬──────────────────────────────────┘
                   │ atama (değiştirilebilir)
┌──────────────────▼──────────────────────────────────┐
│ 2. VARLIK AĞACI (serbest derinlik, K-05)            │
│    Fabrika → Enerji Üretim → İstasyon 1 → GM-1      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 3. AYLIK DEĞER                                      │
│    (ölçüm noktası, yıl, ay) → değer                 │
└─────────────────────────────────────────────────────┘
```

Excel bu modele temiz oturuyor. Örnek: **GM-1 tek bir varlıktır** ve
Excel'deki 6 sütunu onun 6 ölçüm noktasıdır:

| Excel sütunu | Ölçüm noktası | Birim | Rol |
|---|---|---|---|
| AN | GM-1 Doğalgaz Tüketimi | kWh | Tüketim (girdi) |
| AO | GM-1 Doğalgaz Tüketimi | m³ | Tüketim (girdi) |
| AP | GM-1 Elektrik Üretimi | kWh | Tesis içi üretim |
| AQ | GM-1 Buhar Üretimi | kg | Ara enerji |
| AR | GM-1 Buhar Üretimi | kWh | Ara enerji (türetilmiş) |
| AS | GM-1 Sıcak Su Üretimi | kWh | Ara enerji |

### 6.3 Tablolar (taslak)

> **Not (K-09):** Sunucu ve SQL veritabanı yoktur. Aşağıdaki "tablolar",
> veri dosyasındaki **JSON koleksiyonlarıdır** (bkz. 5.3). Yapı aynıdır;
> yalnızca depolama biçimi farklıdır. İleride sunucuya taşınırsa bu yapı
> doğrudan SQL tablolarına karşılık gelir.

**`asset` — varlık ağacı (K-05)**

| Alan | Açıklama |
|---|---|
| `id` | |
| `parent_id` | Üst varlık; `NULL` ise kök. Serbest derinlik. |
| `kod` | Kısa benzersiz kod |
| `ad` | "GM-1", "İstasyon 1 (Gaz Motoru)" |
| `tip` | `tesis` / `bolum` / `istasyon` / `ekipman` / `grup` — serbest, gruplama amaçlı |
| `sira` | Kardeşler arası gösterim sırası |
| `devreye_giris` | Tarih; boş olabilir |
| `devreden_cikis` | Tarih; boş ise aktif (S6) |
| `aktif` | Pasife alma (İ-5) |
| `not` | |

**`measurement_point` — ölçüm noktası**

| Alan | Açıklama |
|---|---|
| `id` | |
| `asset_id` | Bağlı olduğu varlık; **değiştirilebilir** (K-05) |
| `kod` | `GM1_DG_M3` gibi benzersiz kod |
| `ad` | "GM-1 Doğalgaz Tüketimi" |
| `enerji_turu_id` | Elektrik / Doğalgaz / Buhar / Motorin / — (üretim için boş) |
| `birim` | kWh, m³, kg, TL, adet |
| `rol` | Enerji rolü (K-07, bkz. 5.4) |
| `toplama_dahil` | Fabrika toplam enerjisine girer mi? Rolden gelen varsayılan, elle değiştirilebilir |
| `veri_tipi` | `olculen` / `hesaplanan` / `dagitilmis` / `tahmini` |
| `formul` | `hesaplanan` ise türetme kuralı |
| `aktif` | |
| `not` | |

**`period_value` — aylık değer**

| Alan | Açıklama |
|---|---|
| `measurement_point_id` | |
| `yil`, `ay` | Dönem (K-08) |
| `deger` | Girilen ham değer |
| `kalite` | `girildi` / `duzeltildi` / `tahmin` (İ-4) |
| `not` | |
| | **Benzersiz:** (`measurement_point_id`, `yil`, `ay`) |

**`energy_type` — enerji türü**

| Alan | Açıklama |
|---|---|
| `id`, `kod`, `ad` | Elektrik, Doğalgaz, Buhar, Sıcak Su, Motorin |
| `ana_birim` | kWh, m³, kg |
| `aktif` | |

**`conversion` — tarihli dönüşüm katsayısı (İ-5)**

| Alan | Açıklama |
|---|---|
| `enerji_turu_id` | |
| `kaynak_birim` → `hedef_birim` | m³ → kWh, kg → kWh |
| `katsayi` | 10,92 · 0,6977 |
| `gecerli_baslangic` | Bu tarihten itibaren geçerli |
| `kaynak`, `not` | "600 kcal/kg ÷ 860 kcal/kWh" |
| | **Kural:** dönem için `gecerli_baslangic ≤ dönem` olan **en yeni** katsayı |

**`price` — tarihli birim fiyat (S5, İ-5)**

| Alan | Açıklama |
|---|---|
| `enerji_turu_id` | |
| `gecerli_baslangic` | |
| `birim_fiyat`, `birim` | TL/kWh, TL/m³ |
| | **Kural:** katsayı ile aynı — `gecerli_baslangic ≤ dönem` olan en yeni |
| | **Kenar durum:** ilk fiyattan önceki dönem için maliyet **üretilmez** (İ-3) |

> **Not:** Excel'de TL değerleri doğrudan giriliyor (fatura tutarı). Bu durumda
> fiyat tablosu ikincil kalır — açık soru A-02'ye bakınız.

### 6.4 Enerji rolleri (K-07)

Her ölçüm noktası bir **rol** seçer. Rol, varsayılan davranışı belirler;
kullanıcı gerekirse nokta bazında değiştirir.

| Rol | Toplam enerjiye | Açıklama | Örnek |
|---|---|---|---|
| `satin_alinan` | **Girer** | Dışarıdan satın alınan birincil enerji | Şebeke elektriği, doğalgaz, motorin |
| `tesis_ici_uretim` | Girmez | Tesiste, sayılan yakıttan üretilen enerji | Kojenerasyon elektriği |
| `ara_enerji` | Girmez | Dönüşüm sonucu taşıyıcı | Buhar, sıcak su |
| `ayri_tesis_uretim` | Girmez | Başka lokasyonda üretim (K-03) | Yozgat GES, Adana GES |
| `sebekeye_satilan` | Girmez | Dışarı verilen enerji | Mahsup fazlası satış |
| `uretim_miktari` | — | Enerji değil, proses çıktısı | Çikolata kg, kakao yağı kg |
| `girdi_miktari` | — | Enerji değil, proses girdisi | Çekirdek tüketimi kg |
| `maliyet` | — | TL | Elektrik faturası, doğalgaz faturası |
| `gelir` | — | TL | GES satış geliri, mahsup tutarı |

Liste **genişletilebilir**: yeni rol eklemek şema değiştirmez.

> **Çift sayım koruması:** Yalnızca `satin_alinan` rolü toplam enerjiye girer.
> Kojenerasyon elektriği girmez, çünkü onu üreten doğalgaz zaten sayılmıştır.
> GES girmez, çünkü fabrikaya fiziksel olarak hiç girmemiştir (K-03).

### 6.5 Maliyet ve GES mahsubu (K-12, K-13)

Maliyet, **fatura tutarı olarak elle girilir**; birim fiyattan hesaplanmaz.
Sistem birim fiyatı tersinden hesaplayıp gösterir.

| Ölçüm noktası | Rol | Açıklama |
|---|---|---|
| `ELEKTRIK_FATURA_TL` | `maliyet` | **Mahsup öncesi brüt** şebeke faturası (K-13) |
| `GES_MAHSUP_TL` | `gelir` | GES üretiminden faturadan düşülen tutar |
| `GES_SATIS_TL` | `gelir` | Mahsup fazlası, şebekeye satış |
| `DOGALGAZ_FATURA_TL` | `maliyet` | Doğalgaz faturası |

**Sistemin hesapladıkları (hiçbiri saklanmaz — İ-1):**

```
Net ödenen elektrik      = ELEKTRIK_FATURA_TL − GES_MAHSUP_TL
Toplam enerji maliyeti   = Net ödenen elektrik + DOGALGAZ_FATURA_TL
GES'in mali katkısı      = GES_MAHSUP_TL + GES_SATIS_TL
Ortalama birim fiyat     = ELEKTRIK_FATURA_TL ÷ Şebekeden çekilen kWh
```

Son satır, K-12'nin asıl kazancıdır: Excel'de görünmeyen **gerçek birim fiyat
trendi** (2018'de 0,29 → 2025'te 3,24 TL/kWh) otomatik ortaya çıkar ve enerji
maliyeti artışının ne kadarının **fiyattan**, ne kadarının **tüketimden**
geldiği ayrıştırılabilir.

### 6.6 Türetilmiş değerler

**Hiçbiri saklanmaz** (İ-1). İki kaynaktan üretilir:

**(a) Hiyerarşi toplamı** — bir varlığın altındaki tüm noktaların toplamı.
Hiyerarşi değişince kendiliğinden güncellenir.

**(b) Formüllü ölçüm noktası** — Excel'in formül sütunlarının karşılığı:

| Türetilmiş nokta | Formül |
|---|---|
| Toplam Kakao Üretimi | `KAKAO_YAG + KAKAO_TOZ + KAKAO_LIKOR` |
| Toplam Üretim | `TOPLAM_KAKAO + CIKOLATA` |
| Üretilen Elektrik | `TURBIN_EL + GM1_EL + GM2_EL + GM3_EL` |
| Toplam Doğalgaz kWh | `IST1_DG_KWH + IST2_DG_KWH + IST3_DG_KWH` |
| Toplam Enerji kWh | `SATIN_EL + TOPLAM_DG_KWH` |
| Hat-1..4 çekirdek | `TOPLAM_CEKIRDEK × oran` → `veri_tipi = dagitilmis` (S-2.3) |
| Buhar kWh | `BUHAR_KG × katsayı` → `conversion` tablosundan, tarihli |

### 6.7 Ölçüm kapsamı — "ölçülmeyen / dağıtılmamış" (S2)

Her varlık düğümünde üç satır gösterilir:

```
Fabrika Toplam Elektrik          3.761.332 kWh   %100
├── Ölçülen alt noktalar           965.134 kWh    %26
└── Ölçülmeyen / dağıtılmamış    2.796.198 kWh    %74   ⚠
```

Satırların toplamı **her zaman** üst toplama eşittir; üzerine eklenmez.
Fark negatifse (alt toplam üstü aşmışsa) tüketim gibi değil, **ölçüm tutarsızlığı
uyarısı** olarak gösterilir (S3).

### 6.8 Veri kalitesi

Giriş anında çalışan denetimler. **Sistem asla sessizce düzeltmez** (İ-3, İ-4):

| Kural | Davranış |
|---|---|
| Negatif değer | **Engelle** |
| Boş dönem (arada atlanan ay) | **Uyar** |
| Önceki 12 ayın medyanının 3 katından büyük | **Uyar**, onayla kaydet |
| Medyanın 1/3'ünden küçük | **Uyar**, onayla kaydet |
| Doğalgaz kWh/m³ oranı beklenen aralık dışı | **Uyar** (K-04) |
| Alt toplam > üst toplam | **Uyar**, kaydet, ekranda göster (S3) |
| Varlık devre dışıyken veri girişi | **Uyar** (S6) |

### 6.9 Excel'den ilk aktarım

- Kaynak: `veri.xlsx`, 2018-01 → 2025-12.
- BX–DD sütunları **aktarılmaz** (K-02).
- F sütunu **Hat-4** olarak düzeltilir (S7).
- Motorin noktaları **tanımlanır**, veri girilmez (S8).
- Formül sütunları **aktarılmaz** — türetilmiş olarak yeniden hesaplanır (İ-1).
- Aktarım **önizlemeli** ve **ya hep ya hiç**: kaç satır geçerli, kaç satır
  hatalı, hangisi neden — kaydetmeden önce gösterilir.

### 6.10 İleriye açık bırakılan kapılar

Bugün yapılmaz, ama model bunları kaldırır:

| İleride | Model bunu nasıl kaldırıyor |
|---|---|
| Günlük / saatlik veri | `period_value` tablosuna `donem_tipi` alanı eklenir; şema kırılmaz |
| Otomatik veri toplama | `kalite` alanına `otomatik` değeri eklenir; ölçüm noktası zaten kaynak-bağımsız |
| Çok tesis | `asset` ağacının kökü zaten çoklu olabilir |
| Çok kullanıcı | Tablolarda `olusturan` / `degistiren` alanları baştan bırakılır |
| Karbon ayak izi | `conversion` ile aynı desende `emission_factor` tablosu |
| GES performans metrikleri (PR, emre amadelik) | GES zaten ayrı varlık (K-03); ölçüm noktası eklenir |

---

## 7. Enerji dengesi ve mali denge (İ-6, K-03)

Bu bölüm platformun **en kritik kuralıdır**. İki denge ayrıdır ve birbirinden
türetilmez.

### 7.1 Enerji dengesi (kWh) — fiziksel

```
Toplam Enerji Tüketimi = Şebekeden çekilen elektrik
                       + Toplam doğalgaz
                       + Motorin (varsa)
```

**Girmeyenler ve nedenleri:**

| Girmeyen | Neden |
|---|---|
| Kojenerasyon elektriği (Türbin, GM-1..3) | Onu üreten doğalgaz zaten sayıldı → çift sayım olur |
| Buhar, sıcak su | Ara enerji taşıyıcısı; kaynağı zaten sayıldı |
| **Yozgat / Adana GES üretimi** | **Fabrikada fiziksel olarak hiç bulunmadı.** Başka lokasyonda üretilip şebekeye basılıyor (K-03) |

> GES üretimi fabrikanın enerji tüketimini **kWh olarak azaltmaz.** Eklenirse hem
> çift sayım olur hem de fiziksel olarak orada olmayan bir enerji fabrikaya
> yazılır; EnPI de bozulur.

### 7.2 Mali denge (TL)

```
Brüt elektrik faturası
  − GES mahsubu (TL)
  = Net ödenen elektrik bedeli

Mahsup sonrası artan GES üretimi → şebekeye satış → gelir faturası
```

> GES fabrikanın enerji maliyetini **TL olarak azaltır.** İlişki yalnızca mali
> düzeydedir.

### 7.3 Dönüşüm verimliliği (ayrı gösterge)

Kojenerasyon ve kazanlar toplam enerjiye girmez, ama **performansları ayrıca
izlenir**:

| Gösterge | Formül |
|---|---|
| Kojen elektrik verimi | `Elektrik üretimi kWh / Doğalgaz tüketimi kWh` |
| Kojen toplam verim | `(Elektrik + Buhar + Sıcak su) kWh / Doğalgaz kWh` |
| Kazan verimi | `Buhar üretimi kWh / Doğalgaz tüketimi kWh` |

Bu göstergeler enerji dengesinin **dışındadır**; dönüşüm ekipmanının sağlığını
ölçer. Excel'de bu hiç hesaplanmıyor; en yüksek getirili yeni analizlerden biridir.

---

## 8. Hesaplama ve analiz motoru

> Ayrıntılı tasarım görüşme ilerledikçe yazılacak. Şu an belirlenen çerçeve:

| Katman | İçerik | Durum |
|---|---|---|
| Temel hesaplar | Aylık toplam, yıllık toplam, ortak birimde toplam (kWh/GJ/TEP) | Çerçeve net |
| Maliyet | TL toplam; tarihli fiyat kuralı (S5) | Açık soru A-02 |
| EnPI | Kullanıcı tanımlı pay/payda (K-06) | Bölüm 10'da tasarlanacak |
| Baz çizgi | Seviye 1: referans dönem ortalaması · Seviye 2: regresyon | Bölüm 10'da |
| Normalize EnPI | `gerçek / beklenen` | Bölüm 10'da |
| CUSUM | Kümülatif sapma; eğim değişim noktası | Bölüm 10'da |
| Dönüşüm verimliliği | Bölüm 7.3 | Çerçeve net |
| Ölçüm kapsamı | Bölüm 6.7 | Çerçeve net |

---

## 9. Ekranlar

### 9.0 Ekran tasarımı ilkeleri

**E-1 · Her ekran tek bir soruyu cevaplar.** Bir ekran ikinci bir soruya cevap
vermeye başladıysa, yeni bir ekran gerekiyor demektir.

| Ekran | Cevapladığı soru |
|---|---|
| Gösterge Paneli | Durumumuz ne? |
| Veri Girişi | Bu ayın verilerini nasıl girerim? |
| Veri Denetimi | Verim sağlam mı? |
| Enerji Dengesi | Enerji nereye gidiyor? |
| Tüketim Analizi | Nereye bakmalıyım? |
| Performans | İyileştik mi? Ne zaman, ne kadar? |
| Verimlilik | Dönüşüm ekipmanım sağlıklı mı? |
| Maliyet | Para nereye gidiyor, neden arttı? |
| GES | Santraller ne üretti, ne kazandırdı? |

**E-2 · Uyarı, sonucun yanında durur.** Ayrı bir "uyarılar" sekmesine sürülen
uyarı okunmaz.

**E-3 · Her sayı yazdırılabilir ve tabloya çevrilebilir.** Her grafiğin
"tablo olarak göster" seçeneği vardır (5.7.3).

**E-4 · Her sayıdan ham veriye inilebilir.** Panel veya rapordaki her türetilmiş
sayının yanında bir "?" bağlantısı vardır; tıklanınca o sayının hangi ölçüm
noktalarından, hangi değerlerden ve hangi katsayılarla üretildiği gösterilir.
ISO 50001 denetiminde "bu sayı nereden geliyor?" sorusunun tek tıkla cevabıdır.

**E-5 · Boş durum öğreticidir.** Veri yokken ekran boş kalmaz; ne yapılması
gerektiğini anlatır.

### 9.1 Navigasyon haritası

Sol tarafta sabit menü, beş grup:

```
┌─ ÖZET ──────────────────┐
│  1  Gösterge Paneli     │   ← açılış ekranı
├─ VERİ ──────────────────┤
│  2  Veri Girişi         │
│  3  Veri Aktarma        │
│  4  Veri Denetimi       │
├─ ANALİZ ────────────────┤
│  5  Enerji Dengesi      │
│  6  Tüketim Analizi     │
│  7  Performans (EnPI)   │
│  8  Dönüşüm Verimliliği │
│  9  Maliyet             │
│ 10  GES                 │
├─ YÖNETİM ───────────────┤
│ 11  Hedefler ve Aksiyon │
│ 12  Raporlar            │
├─ SİSTEM ────────────────┤
│ 13  Tanımlar            │   ← sekmeli: varlık ağacı, ölçüm
│ 14  Ayarlar ve Yedek    │      noktaları, enerji türleri,
└─────────────────────────┘      katsayılar, EnPI, baz çizgi
```

**Her ekranda sabit üst şerit:**
dönem seçici · veri durumu rozeti · yedek uyarısı · tema (açık/koyu) · yazdır.

---

### 9.2 · Ekran 1 — Gösterge Paneli

#### Amaç
Program açıldığında, tek ekranda **"durumumuz ne?"** sorusunu cevaplamak.
Karar verdirmez; nereye bakılacağını gösterir.

#### Kullanıcının göreceği bilgiler

**KPI kartları** (seçilen ay; her kart: değer + geçen yılın aynı ayına göre fark
+ son 12 ayın mini grafiği):

| Kart | İçerik |
|---|---|
| Toplam enerji | kWh · fark % · mini grafik |
| Enerji maliyeti | Net ödenen TL (mahsup sonrası) · fark % |
| EnPI (ana gösterge) | kWh/kg · baz çizgiye göre durum rozeti |
| Üretim | kg · fark % |
| Ölçüm kapsamı | % · ölçülmeyen payı |
| GES katkısı | Mahsup + satış TL |

**Uyarı şeridi** (varsa, KPI'ların hemen altında — E-2):
eksik veri · şüpheli değer · hedef aşımı · alt toplam > üst toplam · yedek eski.

**Yıllık özet tablosu** (son 3 yıl + bu yılın gerçekleşen kısmı):
enerji kWh · üretim kg · EnPI · maliyet TL · ortalama birim fiyat.

**Açık aksiyonlar** (ilk 5, geciken olanlar kırmızı ikon + etiketle).

#### Kullanıcının gireceği veriler
**Yok.** Bu ekran salt okunurdur. Yalnızca dönem seçimi ve grafik zaman aralığı
değiştirilir. *(Panelde veri girişi olmaması bilinçlidir: bakılan yerle
yazılan yer ayrıdır.)*

#### Sistemin hesaplayacağı değerler
Bütün kartlar ve grafikler türetilmiştir (İ-1) — hiçbiri saklanmaz:
toplam enerji, net maliyet, EnPI, normalize EnPI, ölçüm kapsamı, yıllık
toplamlar, ortalama birim fiyat, geçen yıla göre farklar.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk | Not |
|---|---|---|---|---|
| G1 | Son 24 ay toplam enerji | Sütun | Tek slot (1) | Tek seri → açıklama yok, başlık seriyi adlandırır |
| G2 | Son 24 ay EnPI | Çizgi + baz çizgi referans hattı | Tek slot (1) | **G1 ile aynı grafikte değil** — çift eksen yasak (5.7.2) |
| G3 | Son 12 ay enerji türü dağılımı | Yığılmış sütun | Kategorik (1: elektrik, 2: doğalgaz) | Açıklama + doğrudan etiket |
| G4 | Son 24 ay CUSUM | Çizgi + kutuplu dolgu | Mavi (tasarruf) / kırmızı (kayıp) | Eğim değişim noktası işaretli |
| T1 | Yıllık özet | Tablo | — | Hizalı rakam |
| T2 | Açık aksiyonlar | Tablo | Durum renkleri + ikon | |

#### Yapılabilecek analizler
- Yıldan yıla ve aydan aya karşılaştırma.
- EnPI'nin baz çizgiye göre konumu — **iyileştik mi?**
- CUSUM eğiminden kalıcı sapmanın **başlangıç tarihini** görmek.
- Ölçüm kapsamı düşükse alt sayaç yatırımı ihtiyacını fark etmek.
- Enerji türü karmasının değişimi (elektrik ↔ doğalgaz kayması).

#### ISO 50001 ile ilişkisi
Madde 9.1 *İzleme, ölçme, analiz ve değerlendirme*'nin ana ekranıdır.
EnPI ve baz çizgi karşılaştırması madde 6.4 ve 6.5'in çıktısını görünür kılar.
Yönetimin gözden geçirmesi (madde 9.3) için doğrudan girdi üretir.

#### İleride eklenebilecekler
Kart seçiminin kullanıcı tarafından özelleştirilmesi · birden fazla panel
(üretim müdürü / enerji yöneticisi görünümü) · panelin tek tuşla PDF özeti ·
hedefe kalan süre göstergesi · hava durumu/derece-gün bağlamı.

---

### 9.3 · Ekran 2 — Aylık Veri Girişi

> **En çok kullanılacak ekran budur.** Tasarımın ölçüsü: bir ayın bütün
> verisini en az tuşla, en az hatayla girebilmek.

#### Amaç
Bir ayın bütün ölçüm noktası değerlerini hızlı ve hatasız girmek; girerken
hatayı **anında** yakalamak.

#### Dört giriş yöntemi (K-14)

Üstte ay seçici, altında dört sekme:

| Mod | Ne zaman kullanılır | Nasıl çalışır |
|---|---|---|
| **A · Tablo** (varsayılan) | Aylık rutin giriş | Excel benzeri tek sayfa; bütün noktalar gruplanmış listede, tek sütun giriş. Tab ile ilerlenir. |
| **B · Kategori formu** | Tek bir alanı doldururken | Elektrik / Doğalgaz / Üretim / Kojenerasyon / Kazan / Yardımcı / GES sekmeleri |
| **C · Toplu yapıştırma** | Excel'den aktarırken | Excel'den kopyalanan hücre bloğu yapıştırılır; sistem eşleştirip önizler |
| **D · Dosya yükleme** | Toplu/geçmiş veri | `.xlsx` sürükle-bırak → Ekran 3'e yönlendirir |

#### Kullanıcının göreceği bilgiler

Tablo modunda her satır:

```
Ölçüm noktası              Birim   Geçen ay    Geçen yıl    [ GİRİŞ ]   Δ%    Son 12 ay
─────────────────────────────────────────────────────────────────────────────────────
▸ ELEKTRİK
  Şebekeden çekilen         kWh    1.421.220   1.502.800   [        ]   —    ▁▂▄▃▅▆▄▃
  Elektrik faturası          TL    4.604.030   3.905.600   [        ]   —    ▁▂▃▄▅▆▇█
▸ DOĞALGAZ
  İstasyon 1 (Gaz Motoru)    m³       86.680      92.140   [        ]   —    ▅▄▃▂▁▂▃▄
  İstasyon 1 (Gaz Motoru)   kWh      946.382   1.006.030   [        ]   —    ▅▄▃▂▁▂▃▄  ⚠
```

- **Geçen ay** ve **geçen yılın aynı ayı** yan yana — en iyi hata yakalama aracı.
- **Δ%** girdikçe anında hesaplanır; eşik aşılırsa satır sarıya döner.
- **Son 12 ay mini grafiği** (sparkline) her satırda.
- **⚠** işareti: doğrulama uyarısı; üstüne gelince nedeni yazar.
- Varlık ağacına göre gruplanmış, gruplar katlanabilir.
- Devre dışı varlıkların noktaları **soluk** gösterilir (S6).

**Ekranın altında canlı özet şeridi** — girdikçe güncellenir:

```
Toplam doğalgaz: 10.377.180 kWh  ·  Toplam enerji: 11.798.400 kWh
Üretim: 8.042.310 kg  ·  EnPI: 1,467 kWh/kg  (baz çizgi: 1,340 → %9,5 üzerinde ⚠)
```

Bu şerit girişin **anlamını** anında gösterir; ay sonunda sürpriz olmaz.

#### Kullanıcının gireceği veriler
Seçilen aya ait bütün ölçüm noktası değerleri. Türetilmiş noktalar
(toplamlar, buhar kWh, EnPI) **girilemez** — gri gösterilir, hesaplanmış
oldukları belirtilir.

#### Sistemin hesaplayacağı değerler
Türetilmiş noktalar anlık · Δ% karşılaştırmaları · doğrulama uyarıları ·
alt şeritteki canlı özet · doğalgaz kWh/m³ tutarlılık oranı (K-04).

#### Kullanılacak grafikler ve tablolar
Ana tablo (giriş) · satır içi mini grafikler · canlı özet şeridi.
Büyük grafik yoktur: bu ekran **giriş** ekranıdır, analiz ekranı değildir (E-1).

#### Yapılabilecek analizler
- Giriş anında sapma tespiti (geçen ay / geçen yıl karşılaştırması).
- Doğalgaz m³ ↔ kWh tutarlılık denetimi (K-04): oran ≈ 10,92 beklenir;
  saparsa uyarı.
- Alt toplam / üst toplam tutarlılığı (S3).
- Eksik nokta uyarısı: "Bu ay 7 ölçüm noktası boş."

#### ISO 50001 ile ilişkisi
Madde 9.1.1 *İzleme ve ölçme* — verinin toplanma noktası. Girişteki doğrulama
ve uyarı kayıtları, verinin güvenilirliğine dair kanıt üretir.

#### İleride eklenebilecekler
Klavye kısayolları ve hızlı giriş modu · sık girilen noktalar için "favori"
listesi · otomatik veri toplama geldiğinde bu ekran **doğrulama** ekranına
dönüşür (girilen yerine gelen değer onaylanır) · çoklu ay girişi ·
fotoğraftan sayaç okuma.

---

### 9.4 · Ekran 3 — Veri Aktarma

#### Amaç
Mevcut Excel verisini sisteme almak; yedek alıp geri yüklemek. Verinin
sisteme giriş ve çıkış kapısı.

#### Bölüm 1 — Excel içe aktarma (K-15)

**Kullanıcının göreceği bilgiler:**
sürükle-bırak alanı · şablon indirme bağlantısı · sütun eşleştirme tablosu ·
**önizleme**.

**Zorunlu davranışlar:**

| Kural | Gerekçe |
|---|---|
| **Önizleme zorunlu** — kaç satır geçerli, kaç satır hatalı, hangi satır neden | Kör aktarma veri bozar |
| **Ya hep ya hiç** — ya bütün geçerli satırlar yazılır ya hiçbiri | Yarım yüklenmiş dosya en kötü veri durumudur |
| **Aktarmadan önce otomatik güvenlik yedeği** indirilir | Geri dönüş garantisi (5.2) |
| **Bölüm 6.8'deki bütün doğrulama kuralları burada da çalışır** | İçe aktarma, denetimden kaçış yolu olamaz |
| Üzerine yazma **açıkça sorulur**: "142 dönem zaten dolu. Ne yapılsın?" | Sessiz veri kaybı olmaz |
| Eşleşmeyen sütun **atlanmaz, sorulur** | "Bu sütun hangi ölçüm noktası?" |

**Sütun eşleştirme:** Sistem Excel başlıklarını ölçüm noktası adlarıyla
otomatik eşleştirmeye çalışır; eşleşmeyenleri kullanıcıya sorar ve verilen
cevabı **hatırlar** (sonraki aktarımda tekrar sormaz).

#### Bölüm 2 — Yedekleme ve geri yükleme (K-10)

| İşlem | Davranış |
|---|---|
| **Yedek al** | `enerji-veri-YYYY-AA-GG.json` indirilir. Tanımlar + bütün değerler + katsayılar + EnPI + hedefler + aksiyonlar tek dosyada |
| **Geri yükle** | Dosya seçilir → **önizleme**: "Bu yedek 2018-01 → 2025-12 arası 8.640 değer içeriyor. Mevcut veriniz silinecek." → onay |
| **Son yedek bilgisi** | "Son yedek: 12 gün önce" — 7 günden eskiyse uyarı rengi |
| **Dosyaya doğrudan yazma** (Chrome/Edge, K-11) | Bir kez dosya seçilir; sonrasında otomatik yazılır. İsteğe bağlı, varsayılan kapalı |

#### Sistemin hesaplayacağı değerler
Aktarım istatistikleri (satır/dönem/nokta sayısı, çakışma sayısı) · yedek
dosyası boyutu · son yedekten bu yana geçen gün.

#### ISO 50001 ile ilişkisi
Madde 7.5 *Dokümante edilmiş bilgi* — verinin korunması ve kontrolü.
Aktarım kayıtları verinin kaynağına dair iz bırakır.

#### İleride eklenebilecekler
Otomatik periyodik yedek hatırlatması · birden çok yedek sürümünün yönetimi ·
CSV desteği · bulut yedeği (isteğe bağlı) · seçili dönem aralığını dışa aktarma.

---

### 9.5 · Ekran 4 — Veri Denetimi

#### Amaç
**"Verim sağlam mı?"** — Bütün veri setinin sağlığını tek ekranda göstermek.
Analiz ekranlarına güvenmeden önce bakılacak yer.

#### Kullanıcının göreceği bilgiler

**Üstte dört sağlık göstergesi:**

| Gösterge | Örnek |
|---|---|
| Doluluk | 96 / 96 ay · %100 |
| Eksik değer | 7 ölçüm noktası × 3 dönem boş |
| Şüpheli değer | 4 değer eşik dışı |
| Tutarsızlık | 12 dönemde alt toplam > üst toplam |

**Eksik veri haritası** — ölçüm noktası (satır) × ay (sütun) matrisi;
dolu / boş / şüpheli hücreler. Bir bakışta hangi dönemde hangi noktanın
eksik olduğu görülür. GM-1'in 2025'te durduğu (S6) burada apaçık görünür.

**Bulgular listesi** — her satır: ölçüm noktası, dönem, sorun, değer,
önerilen işlem, **[Düzelt]** bağlantısı (giriş ekranının o hücresine gider).

#### Kullanıcının gireceği veriler
Doğrudan giriş yoktur. Bir bulgu için **not** yazılabilir veya
**"bilinçli, sorun değil"** olarak işaretlenebilir — o bulgu bir daha uyarmaz
ama kaydı kalır (İ-4).

#### Sistemin hesaplayacağı değerler
Bölüm 6.8'deki bütün doğrulama kuralları bütün veri seti üzerinde ·
doluluk oranları · ölçüm kapsamı (6.7) · hiyerarşi tutarlılığı (S3) ·
doğalgaz kWh/m³ oran sapması (K-04).

#### Kullanılacak grafikler ve tablolar

| # | Grafik | Form | Renk |
|---|---|---|---|
| G1 | Eksik veri haritası | Hücre matrisi | Durum renkleri + ikon (renk tek başına anlam taşımaz) |
| G2 | Ölçüm kapsamı zaman içinde | Sütun | Tek slot (1) |
| T1 | Bulgular | Tablo | Durum ikonları |

#### Yapılabilecek analizler
- Hangi dönemlerde veri kalitesi düşük — o dönemlerin analizlerine ne kadar
  güvenilebilir?
- Ölçüm kapsamının zaman içindeki değişimi: yeni alt sayaçlar kapsamı artırdı mı?
- Sistematik boşluklar: bir varlık gerçekten durmuş mu, yoksa veri mi girilmemiş?

#### ISO 50001 ile ilişkisi
Madde 9.1.1 — kuruluş, izleme ve ölçme sonuçlarının **geçerli** olmasını
sağlamalıdır. Bu ekran o geçerliliğin kanıtıdır. Denetimde "verinizin
doğruluğunu nasıl güvence altına alıyorsunuz?" sorusunun cevabıdır.

#### İleride eklenebilecekler
Eksik değer için tahmin önerisi (işaretlenerek, İ-4) · veri kalitesi skoru ve
zaman içindeki trendi · otomatik veri geldiğinde haberleşme kesintisi tespiti.

---

### 9.6 — Ekran 5–14

> **Henüz tasarlanmadı.** Ekran 5'ten 14'e kadar aynı şablonla, görüşmenin
> bir sonraki adımında yazılacak:
> Enerji Dengesi · Tüketim Analizi · Performans (EnPI & Baz Çizgi) ·
> Dönüşüm Verimliliği · Maliyet · GES · Hedefler ve Aksiyonlar · Raporlar ·
> Tanımlar · Ayarlar ve Yedekleme.

---

## 10. ISO 50001 ile ilişki

> Ayrıntısı ekran tasarımlarıyla birlikte yazılacak. Çerçeve:

| ISO 50001 gereği | Platformdaki karşılığı |
|---|---|
| Enerji gözden geçirmesi | Ölçüm kapsamı + Pareto + enerji dengesi |
| SEU (önemli enerji kullanımı) | Varlık ağacında işaretleme + Pareto |
| EnPI | Kullanıcı tanımlı gösterge seti (K-06) |
| EnB (enerji baz çizgisi) | Baz çizgi modülü — sabit ve regresyonlu |
| Hedefler | Aylık/yıllık hedef tanımı |
| İzleme, ölçme, analiz | Panel, trend, CUSUM, normalize EnPI |
| Eylem planları | Aksiyon takibi |
| Dokümantasyon | İzlenebilirlik (her sayı ham veriye kadar açılabilir) |

---

## 11. Açık sorular

### 11.1 Karara bağlananlar

| # | Soru | Sonuç |
|---|---|---|
| A-01 | Proje nerede yaşayacak? | **Kapandı** — K-09: tek HTML dosyası, kurulum yok |
| A-02 | Maliyet nasıl oluşacak? | **Kapandı** — K-12: fatura tutarı elle girilir |
| A-03 | Elektrik TL mahsup öncesi mi sonrası mı? | **Kapandı** — K-13: mahsup öncesi brüt |
| A-04 | Veri girişi ekranı biçimi | **Kapandı** — K-14: dört yöntem birden |

### 11.2 Açık kalanlar

| # | Soru | Neden önemli |
|---|---|---|
| **A-05** | İstasyon–makine tutarsızlığı (S3) neden kaynaklanıyor? İstasyon, makineler dışında başka tüketicileri de besliyor mu? | "Ölçülmeyen pay" hesabının doğru yorumlanması buna bağlı |
| **A-06** | Hat-1..4 çekirdek dağıtım oranları (0,34 / 0,12 / 0,32 / 0,22) sabit mi kalacak, dönemsel mi tanımlanacak? | Hat bazlı EnPI hesaplanacaksa oranın doğruluğu kritik |
| **A-07** | Motorin ileride kullanılacak mı? | Tanımlanacak ama veri girilmeyecek (S8) |
| **A-08** | Buhar 600 kcal/kg varsayımı sabit mi, basınca göre değişken mi? | Kazan ve kojen verimi hesabını doğrudan etkiler |
| **A-09** | Ekran listesi ve sırası onaylanacak | Tasarımın bir sonraki aşaması |

---

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1 | 2026-09-17 | İlk taslak. Excel analizi, temel ilkeler, K-01…K-08 kararları, veri modeli çerçevesi, enerji/mali denge ayrımı. |
| 0.3 | 2026-09-17 | **Görsel dil ve grafik standartları (5.7)**: renk paleti, yasaklar (çift eksen dahil), zorunlu davranışlar, grafik tipleri. **Ekranlar bölümü başladı (9)**: tasarım ilkeleri, navigasyon haritası (14 ekran), Ekran 1–4 tam tasarımı (Gösterge Paneli, Veri Girişi, Veri Aktarma, Veri Denetimi). |
| 0.2 | 2026-09-17 | **Teknik mimari belirlendi (Bölüm 5).** K-09…K-18 kararları: tek HTML dosyası, iki katmanlı veri saklama, Chrome/Edge, fatura tutarı girişi, GES mahsubunun ayrı kalem olması, dört yöntemli veri girişi, gömülü `.xlsx` okuyucu, saf SVG grafikler. Maliyet ve GES mahsup modeli (6.4b). A-01…A-04 kapatıldı. |
