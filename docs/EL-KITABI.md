# Enerji Yönetim Platformu — Sistem ve Uygulama El Kitabı

> Bu belge programın **temel referans dokümanıdır**. Programın nasıl çalışacağına
> dair bütün kurallar, ekranlar, veri yapıları, hesaplamalar ve fonksiyonlar
> burada tanımlanır. Kodlama, bu belge tamamlanıp mutabakat sağlandıktan sonra
> başlar.

| | |
|---|---|
| **Sürüm** | 0.1 — taslak, tasarım aşaması |
| **Durum** | Kodlama **başlamadı**. Tasarım görüşmesi sürüyor. |
| **Son güncelleme** | 2026-09-17 |
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

> Bunlar reddedilmiş değil, **ertelenmiştir**. Veri modeli bunları sonradan
> kaldırabilecek şekilde tasarlanır (bkz. Bölüm 5.9).

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
(bkz. Bölüm 6).

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

---

## 5. Veri modeli

### 5.1 Temel fikir: geniş → dar format

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
(bkz. Bölüm 8). Değişen sadece altındaki depolamadır.

### 5.2 Üç katman

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

### 5.3 Tablolar (taslak)

> Bu bölüm tasarım ilerledikçe kesinleşecektir.

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

### 5.4 Enerji rolleri (K-07)

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

### 5.5 Türetilmiş değerler

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

### 5.6 Ölçüm kapsamı — "ölçülmeyen / dağıtılmamış" (S2)

Her varlık düğümünde üç satır gösterilir:

```
Fabrika Toplam Elektrik          3.761.332 kWh   %100
├── Ölçülen alt noktalar           965.134 kWh    %26
└── Ölçülmeyen / dağıtılmamış    2.796.198 kWh    %74   ⚠
```

Satırların toplamı **her zaman** üst toplama eşittir; üzerine eklenmez.
Fark negatifse (alt toplam üstü aşmışsa) tüketim gibi değil, **ölçüm tutarsızlığı
uyarısı** olarak gösterilir (S3).

### 5.7 Veri kalitesi

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

### 5.8 Excel'den ilk aktarım

- Kaynak: `veri.xlsx`, 2018-01 → 2025-12.
- BX–DD sütunları **aktarılmaz** (K-02).
- F sütunu **Hat-4** olarak düzeltilir (S7).
- Motorin noktaları **tanımlanır**, veri girilmez (S8).
- Formül sütunları **aktarılmaz** — türetilmiş olarak yeniden hesaplanır (İ-1).
- Aktarım **önizlemeli** ve **ya hep ya hiç**: kaç satır geçerli, kaç satır
  hatalı, hangisi neden — kaydetmeden önce gösterilir.

### 5.9 İleriye açık bırakılan kapılar

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

## 6. Enerji dengesi ve mali denge (İ-6, K-03)

Bu bölüm platformun **en kritik kuralıdır**. İki denge ayrıdır ve birbirinden
türetilmez.

### 6.1 Enerji dengesi (kWh) — fiziksel

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

### 6.2 Mali denge (TL)

```
Brüt elektrik faturası
  − GES mahsubu (TL)
  = Net ödenen elektrik bedeli

Mahsup sonrası artan GES üretimi → şebekeye satış → gelir faturası
```

> GES fabrikanın enerji maliyetini **TL olarak azaltır.** İlişki yalnızca mali
> düzeydedir.

### 6.3 Dönüşüm verimliliği (ayrı gösterge)

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

## 7. Hesaplama ve analiz motoru

> Ayrıntılı tasarım görüşme ilerledikçe yazılacak. Şu an belirlenen çerçeve:

| Katman | İçerik | Durum |
|---|---|---|
| Temel hesaplar | Aylık toplam, yıllık toplam, ortak birimde toplam (kWh/GJ/TEP) | Çerçeve net |
| Maliyet | TL toplam; tarihli fiyat kuralı (S5) | Açık soru A-02 |
| EnPI | Kullanıcı tanımlı pay/payda (K-06) | Bölüm 9'da tasarlanacak |
| Baz çizgi | Seviye 1: referans dönem ortalaması · Seviye 2: regresyon | Bölüm 9'da |
| Normalize EnPI | `gerçek / beklenen` | Bölüm 9'da |
| CUSUM | Kümülatif sapma; eğim değişim noktası | Bölüm 9'da |
| Dönüşüm verimliliği | Bölüm 6.3 | Çerçeve net |
| Ölçüm kapsamı | Bölüm 5.6 | Çerçeve net |

---

## 8. Ekranlar

> **Bu bölüm henüz yazılmadı.** Görüşmenin bir sonraki aşamasında, her ekran için
> şu başlıklar tek tek kararlaştırılacak:
>
> - Ekranın amacı
> - Kullanıcının göreceği bilgiler
> - Kullanıcının gireceği veriler
> - Sistemin otomatik hesaplayacağı değerler
> - Kullanılacak grafikler ve tablolar
> - Yapılabilecek analizler
> - ISO 50001 ile ilişkisi
> - İleride eklenebilecek özellikler

Planlanan ekran listesi (taslak, görüşmede kesinleşecek):

1. Gösterge paneli
2. Aylık veri girişi
3. Varlık ağacı yönetimi
4. Ölçüm noktası tanımları
5. Enerji türleri, dönüşüm katsayıları, fiyatlar
6. EnPI tanımları
7. Baz çizgi ve performans analizi
8. Ölçüm kapsamı / enerji dengesi
9. Dönüşüm verimliliği (kojen & kazan)
10. GES takibi
11. Raporlar
12. Hedefler ve aksiyonlar
13. Excel içe aktarma
14. Ayarlar ve yedekleme

---

## 9. ISO 50001 ile ilişki

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

## 10. Açık sorular

Henüz karara bağlanmamış, görüşmede netleşecek konular:

| # | Soru |
|---|---|
| **A-01** | "Tamamen yeni proje" nerede yaşayacak: bu depoda yeni bir yapı mı, ayrı bir depo mu? |
| **A-02** | TL değerleri fatura tutarı olarak mı girilecek, yoksa tarihli birim fiyattan mı hesaplanacak? Excel'de doğrudan giriliyor. |
| **A-03** | Excel'deki "Satın Alınan Elektrik TL" mahsup **öncesi** mi **sonrası** mı? GES TL sütunu mahsup tutarı mı, toplam üretim değeri mi? |
| **A-04** | Aylık veri girişi ekranı nasıl olsun: Excel benzeri tek tablo mu, kategori bazlı form mu, ikisi birden mi? |
| **A-05** | İstasyon–makine tutarsızlığı (S3) neden kaynaklanıyor? İstasyon başka tüketicileri de besliyor mu? |
| **A-06** | Hat-1..4 çekirdek dağıtım oranları (0,34/0,12/0,32/0,22) sabit mi kalacak, yoksa dönemsel mi tanımlanacak? |
| **A-07** | Motorin ileride kullanılacak mı? |
| **A-08** | Buhar 600 kcal/kg varsayımı sabit mi, yoksa basınca göre değişken mi tanımlanmalı? |

---

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1 | 2026-09-17 | İlk taslak. Excel analizi, temel ilkeler, K-01…K-08 kararları, veri modeli çerçevesi, enerji/mali denge ayrımı. |
