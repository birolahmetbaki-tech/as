# Enerji Yönetim Platformu — Sistem ve Uygulama El Kitabı

> Bu belge programın **temel referans dokümanıdır**. Programın nasıl çalışacağına
> dair bütün kurallar, ekranlar, veri yapıları, hesaplamalar ve fonksiyonlar
> burada tanımlanır. Kodlama, bu belge tamamlanıp mutabakat sağlandıktan sonra
> başlar.

| | |
|---|---|
| **Sürüm** | 1.1 — Faz 1–5 kodlandı |
| **Durum** | **Yol haritasının beş fazı da bitti.** 15 ekranın hepsi çalışıyor. |
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
| **Toplam Enerji Tüketimi kWh** | **`Satın alınan elektrik + Toplam doğalgaz`** | **Mantığı doğru ve korunur** (kendi ürettiği elektriği saymıyor → çift sayım yok), ancak **motorini dışarıda bırakıyor**. Yeni sistemde düzeltilir: toplam, rolü `satin_alinan` olan bütün türleri kapsar (K-24). |
| Toplam Enerji TL | `Elektrik TL + Doğalgaz TL` | Aynı eksik: **motorin faturası dışarıda.** Yeni sistemde rolü `maliyet` olan bütün kalemler toplanır (K-24). |
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
| S8 | Motorin tanımlı ama 8 yıldır boş; üstelik Excel'in toplam enerji ve toplam maliyet formüllerine **hiç dahil edilmemiş** | Enerji türü olarak tanımlanır ve **toplamlara dahil edilir** (K-24). Bugün değeri yok; tüketim başladığında giriş açıktır ve toplamlar kendiliğinden kapsar |
| S9 | Doğalgaz m³ ve kWh **çift elle giriş** | Kullanıcı kararı (K-04); sistem tutarlılığı denetler |
| **S10** | **Sessiz veri kaybı.** 2024 Ağustos çikolata üretimi hücresi **metin**: `286609,,4` (çift virgül). Excel'in `SUM` işlevi metni sessizce atlamış; o ayın **Toplam Üretim** değeri yalnız kakaodan oluşmuş (3.986.345 kg) ve çikolata hiç sayılmamış. Bu hata **2024 yıllık üretim toplamına ve dolayısıyla 2024 EnPI'sine** taşınmıştır | Program bu hücreyi **okumaz** ve o ayın toplam üretimini **üretmez**; nedenini yazar (İ-3). Hatayı gizlemek yerine görünür kılar. Hücre düzeltilince toplam kendiliğinden oluşur |
| **S11** | **6 negatif değer.** Kazan-1 ve Kazan-2 doğalgaz tüketiminde: 2018 Ekim (−188.616 kWh), 2022 Nisan (−204.137 kWh), 2022 Eylül (−323.794 kWh) ve bunların m³ karşılıkları. Negatif yakıt tüketimi fiziksel olarak imkânsızdır | Aktarma bu değerleri **reddeder** ve dışarıda bırakır; hangi satır ve neden olduğunu yazar (6.8, engel kuralı) |

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
> cevaplamak olacak (bkz. Bölüm 8 — regresyonlu baz çizgi ve normalize EnPI).

### 2.5 Kaynak verideki hatalar — programın ilk bulduğu şey

Excel'in 96 aylık verisi ilk kez programa aktarıldığında **7 değer reddedildi**
ve **1 dönem eksik kaldı**. Hepsi kaynak verideki gerçek hatalardır; hiçbiri
program hatası değildir.

| Bulgu | Etki | Programın davranışı |
|---|---|---|
| **S10** · 2024 Ağustos çikolata `"286609,,4"` | Excel bu ayın üretimini eksik topladı → **2024 yıllık üretim ve EnPI yanlış** | Toplam üretimi üretmez, nedenini yazar |
| **S11** · 6 negatif doğalgaz değeri | Fiziksel olarak imkânsız; kazan verimini bozar | Aktarmada reddeder |
| **S12** · Buhar kg → kWh katsayısı 2025'te değişti | 2024 ile 2025 verimleri farklı varsayımla hesaplanmış → verim düşüşü olduğundan büyük görünür | Tarihli katsayı olarak tanımlanır; ekranda etkisi puan olarak ayrıştırılır |
| **S13** · 2025'te kazan verimleri %100'ü aşıyor | Kazan-1 %137, Kazan-2 %145 — fiziksel olarak imkânsız | Sayıyı gizlemez ama performans saymaz; karşılaştırmadan çıkarır, nedenini yazar |

**S10'un büyüklüğü:**

| | Üretim (kg) | EnPI 2024 |
|---|---:|---:|
| Excel'in söylediği | 111.897.453 | 1,1728 |
| Program (Ağustos hariç) | 107.911.108 | — |
| Hücre `286.609,4` okunursa | 112.184.062 | 1,1698 |
| Hücre `2.866.094` okunursa | 114.763.547 | **1,1435** |

Komşu ayların çikolata üretimi 2,8–3,7 milyon kg aralığındadır; ikinci okuma
bu aralığa oturur. Doğrusu **kullanıcı tarafından teyit edilmelidir** — sistem
tahmin yürütmez (İ-3).

> **Bu neden önemli:** 8.8'deki 2025 vakası 2024'ü referans alıyor. 2024 EnPI'si
> 1,1728 yerine 1,1435 ise, 2025'teki bozulma %16,5 değil **%19,5**'tir.
> Tek bir hücre, yıllık performans değerlendirmesini kaydırıyor.

**S12 · Buhar entalpi varsayımı 2025'te değişti**

Excel 2018–2024 arasında buhar kilogramını kWh'e `kg × 600 / 860 = 0,697674`
ile çeviriyor. 2025 Ocak'tan itibaren, **bütün ekipmanlarda**, oran
`560 / 860 = 0,651163`'e düşüyor. Ölçülen kilogram değişmediği hâlde raporlanan
buhar enerjisi %6,7 azalıyor.

| | 2018–2024 | 2025 |
|---|---:|---:|
| Entalpi varsayımı | 600 kcal/kg | 560 kcal/kg |
| Katsayı | 0,697674 kWh/kg | 0,651163 kWh/kg |
| Türbin toplam verimine etkisi | — | **−1,7 puan** |

Türbinin 2024 → 2025 verim düşüşü **6,9 puan** ölçülüyor; bunun **1,7 puanı**
bu varsayım değişiminden, kalan **5,2 puanı** gerçek performanstan gelir.
Program iki katsayıyı da **tarihli** tutar (6.6, İ-5), her ay kendi dönemindeki
katsayıyla hesaplanır ve Ekran 9 farkı açıkça ayrıştırır. Hangi entalpinin doğru
olduğu **A-08**'e bağlıdır ve kullanıcı teyidi bekler.

**S13 · 2025 kazan enerji dengesi tutarsız**

2025'te kazanlara atanmış doğalgaz 24.060.796 kWh, ürettikleri buhar
33.942.000 kWh. Verim %100'ü aşamaz; en az **9,9 GWh yakıt eksik ölçülmüş ya da
başka bir ekipmana yazılmıştır**.

| 2025 | kWh |
|---|---:|
| İstasyon sayaçlarına göre satın alınan gaz | 120.168.406 |
| Ekipman sayaçlarına göre yakılan gaz | 104.632.257 |
| **Hiçbir ekipmana atanmamış** | **15.536.150 (%12,9)** |

Gaz motorlarının durduğu 2025'te İstasyon 1'de (gaz motoru istasyonu)
14.397.746 kWh gaz görünüyor ama bu istasyona bağlı hiçbir ekipmanda tüketim
yok. Bu gazın kazanlara gitmiş olması, kazan verimini gerçekçi bir aralığa
(≈%88) oturtur — ancak bu bir **çıkarımdır, veri değildir**; sistem tahmin
yürütmez (İ-3). Bulgu **A-05**'i somutlaştırır ve alt sayaç yatırımının nereye
yapılacağını söyler.

> Program bu sayıları gizlemez; **performans olarak da sunmaz.** Ekran 9
> imkânsız verimi kırmızı uyarıyla işaretler, o ekipmanı yıllar arası
> karşılaştırmadan çıkarır ve nedenini yazar.

---

## 3. Temel ilkeler

Bu ilkeler **bağlayıcıdır**. Her yeni özellik bunlara uymak zorundadır.

**İ-1 · Ham veri ile hesap ayrıdır — ve hesap katmanı her seferinde yeniden üretilir.**
Türetilmiş hiçbir değer **doğruluk kaynağı olarak** saklanmaz. Tüketim toplamı,
maliyet, EnPI, emisyon, baz çizgi sapması; hepsi ham veriden üretilir.

Üretilen sonuçlar ayrı bir **hesaplanan değerler katmanında** tutulur (K-23):
program açılışında ve **her veri değişiminde** baştan üretilir, bütün ekranlar
oradan okur, kullanıcı içeriğini görebilir ve dışa aktarabilir. Bu katman bir
**ayna**dır, kayıt değil: silinse hiçbir bilgi kaybolmaz, çünkü ham veriden
yeniden doğar.

Saklanan tek istisna **model parametreleridir** (regresyon katsayısı gibi) —
çünkü o bir *karardır*, türev değil.

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
| **K-19** | Baz çizgi (EnB) | **Kullanıcı tanımlı, birden çok baz çizgi.** Sistem baz çizgi dayatmaz; istenildiği kadar tanımlanır ve aralarında geçiş yapılır. | Farklı amaçlar farklı referans ister (denetim için son tam yıl, hedef için en iyi yıl, istatistik için çok yıllı). |
| **K-20** | Raporlar | Üç rapor: **aylık enerji raporu**, **yönetim gözden geçirme raporu** (ISO 50001 md. 9.3), **serbest rapor oluşturucu**. | Kullanıcı seçimi. ENVER yıllık bildirim özeti ileriye bırakıldı. |
| **K-21** | Hedefler | Dört hedef türü birden: **EnPI**, **tüketim (kWh)**, **maliyet (TL)**, **tasarruf (baz çizgiye göre %)**. | Farklı muhataplar farklı hedef diliyle konuşur; dördü de aynı motordan beslenir. |
| **K-22** | Ekran listesi | **15 ekran** (Özet 1 · Veri 4 · Analiz 6 · Yönetim 2 · Sistem 2). | Bkz. 9.1 navigasyon haritası. K-23 ile bir ekran eklendi. |
| **K-24** | Motorin ve toplamların genelleştirilmesi | **Motorin toplam enerjiye ve toplam enerji maliyetine dahil edilir.** Dahası kural sabit listeden **rol filtresine** çevrilir: toplam enerji = rolü `satin_alinan` olan bütün noktalar; toplam maliyet = rolü `maliyet` olan bütün noktalar. | Bugün motorin sıfır, ama ileride tüketim olabilir; Excel onu her iki formülün de dışında bırakmış. Sabit liste yazılsaydı yeni yakıt eklendiğinde formülün güncellenmesi gerekir ve bir gün unutulurdu. Rol filtresi bunu yapısal olarak imkânsız kılar. |
| **K-23** | Hesaplanan değerler katmanı | Hesaplanan bütün değerler **ayrı bir katmanda toplanır**; ekranlar veriyi buradan çeker. Katman **açılışta ve her veri değişiminde** baştan üretilir, kullanıcıya **görünür** (Ekran 5) ve **iki sayfalı Excel** olarak dışa aktarılır (`Ham Veri` + `Hesaplanan`). Yedek dosyasına **yazılmaz**; yazılırsa bile geri yüklemede yok sayılıp yeniden üretilir. | Kullanıcı isteği. Tek bir hesap katmanı, bütün ekranların aynı sayıyı göstermesini yapısal olarak garanti eder (İ-2) ve hesabı denetlenebilir kılar (E-4). Yedeğe yazılmaması, formül değişince bayat değerin geri gelmesini önler. |
| **K-25** | İmkânsız verim | Bir dönüşüm ekipmanının faydalı enerjisi yakıtından büyükse (verim >%102) bu sonuç **performans sayılmaz**: sayı gizlenmez, kırmızı işaretlenir, nedeni yazılır ve o ekipman **yıllar arası karşılaştırmadan çıkarılır**. | Gerçek veride görüldü (S13: Kazan-1 %137, Kazan-2 %145). Sayıyı saklamak denetlenebilirliği (E-4), performans saymak ise kararı bozar. İkisi arasındaki tek dürüst yol, göstermek ama saymamaktır (İ-3). |
| **K-26** | Yıllar arası verim karşılaştırması | Karşılaştırma **tek bir birleşik verim yüzdesiyle yapılmaz**. Yalnız iki dönemde de çalışan ve verisi tutarlı ekipmanlar, **ekipman ekipman** karşılaştırılır; toplanan büyüklük yüzde değil **kaçınılabilir yakıttır (kWh)**. Ekipman kümesi değiştiyse bu ayrıca uyarı olarak söylenir. | Birleşik yüzde karışıma bağlıdır: 2025'te yük türbine kayınca ve gaz motorları durunca, hiçbir ekipmanın verimi değişmese bile karma toplam oynar — gerçek veride bozulma **iyileşme gibi** göründü. kWh cinsinden kaçınılabilir yakıt toplanabilir ve karışımdan bağımsızdır. |
| **K-27** | Fatura ↔ tüketim bağı | Rolü `maliyet` olan her nokta, faturalandırdığı tüketim noktalarını `fatura_tuketim` alanında taşır. Birim fiyat ve fiyat/hacim ayrıştırması **faturanın kendi biriminde** yapılır (elektrik kWh, doğalgaz m³); karşılaştırmalı birim fiyat grafiği için TL/kWh'e çevrilir. | Ayrıştırma çevrilmiş birimde yapılırsa dönüşüm katsayısının hatası fiyat ve hacim etkilerine karışır. Alan boşsa tutar yine toplanır ama birim fiyat **üretilmez** (İ-3). |
| **K-28** | İzlenebilirlik düğmesi | Her türetilmiş sayının yanında bir `?` durur; açılan pencere sayının **formülünü, kuralını, katkıda bulunan ölçüm noktalarını ham değerleriyle, kullanılan tarihli katsayıları ve veri kalitesi işaretlerini** gösterir. Köken ağacı hesaplanan noktalardan ham veriye kadar iner. | E-4'ün somut hâli. ISO 50001 denetiminde sorulan ilk soru "bu sayı nereden geliyor?"dur; cevabı bir ekran gezintisi değil, tek tık olmalıdır. Aynı pencere, S12 gibi katsayı değişimlerini de kendiliğinden görünür kılar. |

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

> **Hesaplanan değerler katmanı neden dosyada yok (K-23):** Katman bellekte
> yaşar, açılışta ve her değişimde yeniden üretilir. Yedeğe yazılsaydı, bir
> formül veya katsayı değiştikten sonra eski yedeği geri yüklemek **bayat
> sonuçları** geri getirirdi. Dosyada yalnızca ham veri olduğu için yedek
> hangi program sürümüyle açılırsa açılsın **o sürümün doğru sonuçlarını**
> üretir. Katmanı görmek veya dışa aktarmak isteyen Ekran 5'i kullanır.

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

> **Durumu (K-12):** Maliyet, fatura tutarı olarak elle girilir; bu tablodan
> **hesaplanmaz**. `price` tablosu ilk sürümde **kullanılmaz**; ileride gölge
> faturalama (fatura doğrulama, 9.11) eklenirse devreye girer. Yapısı şimdiden
> tanımlıdır ki sonradan şema değişikliği gerekmesin.

**`hedef` — enerji hedefi (K-21, 9.13)**

| Alan | Açıklama |
|---|---|
| `kod` | Benzersiz kod |
| `ad` | "2027 enerji bütçesi" |
| `tur` | `enpi` / `tuketim` / `maliyet` / `tasarruf` |
| `ifade` | Neyin hedefi: EnPI kodu · baz çizgi kodu · ölçüm noktası kodu · `@TOPLAM_ENERJI_KWH` / `@TOPLAM_MALIYET_TL` |
| `deger` | Hedef değer |
| `yon` | `azalt` / `artir` — tutma yönü |
| `bas`, `son` | `{yil, ay}` — hedef dönemi |
| `sorumlu`, `not` | |
| | **Kural:** oran hedefleri (EnPI, tasarruf) dönem için **yeniden hesaplanır**, aylık değerlerin ortalaması alınmaz |

**`aksiyon` — eylem planı kaydı (9.13, ISO 50001 md. 6.2.2)**

| Alan | Açıklama |
|---|---|
| `kod` | Benzersiz kod |
| `baslik`, `aciklama` | Ne yapılacak |
| `baglam` | `{kaynak, varlik?, donem?}` — hangi tespitten doğdu (örn. "Ekran 9 · Dönüşüm Verimliliği") |
| `sorumlu`, `termin` | Kim, ne zaman (`YYYY-AA-GG`) |
| `durum` | `acik` / `devam` / `kapandi` / `iptal` |
| `beklenen`, `gerceklesen` | `{deger, birim}` — tasarruf; boş bırakılabilir (İ-3) |
| `sonuc_notu`, `olusturma`, `kapanis` | |
| | **Gecikme:** durumu açık **ve** `termin < bugün` ise gecikmiştir; ikon **ve** etiketle gösterilir (renk tek başına yetmez) |

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
| `DOGALGAZ_FATURA_TL` | `maliyet` | Doğalgaz faturası |
| `MOTORIN_FATURA_TL` | `maliyet` | Motorin faturası (K-24) |
| `GES_MAHSUP_TL` | `gelir` | GES üretiminden faturadan düşülen tutar |
| `GES_SATIS_TL` | `gelir` | Mahsup fazlası, şebekeye satış |
| `GES_TOPLAM_TL` | `gelir` | **Alternatif:** ikisi ayrıştırılamıyorsa tek kalem |

> ⚠ **Veri uyuşmazlığı (A-11).** Excel'de her santral için **tek** TL sütunu var
> (Yozgat, Adana); mahsup ile satış ayrılmamış. Anlattığınız süreçte ikisi farklı
> şeyler: mahsup faturayı düşürür, fazlası satış faturası olur. Model **her iki
> durumu da kaldırır** — ayrıştırabiliyorsanız iki kalem, ayrıştıramıyorsanız
> `GES_TOPLAM_TL` tek kalem girilir ve net ödenen hesabında aynı şekilde
> kullanılır. Ayrıştırma yapılırsa GES'in fatura üzerindeki etkisi ile şebekeye
> satıştan gelen gelir ayrı izlenebilir; yapılmazsa yalnız toplam katkı görünür.

**Sistemin hesapladıkları (hiçbiri saklanmaz — İ-1):**

```
Net ödenen elektrik      = ELEKTRIK_FATURA_TL − GES_MAHSUP_TL

Toplam enerji maliyeti   = rolü `maliyet` olan BÜTÜN noktaların toplamı
                           − GES mahsubu
                         = Net ödenen elektrik
                           + DOGALGAZ_FATURA_TL
                           + MOTORIN_FATURA_TL          (K-24)
                           + ileride eklenecek her yakıt faturası

GES'in mali katkısı      = GES_MAHSUP_TL + GES_SATIS_TL
                           (veya ayrıştırılmamışsa GES_TOPLAM_TL)
Ortalama birim fiyat     = ELEKTRIK_FATURA_TL ÷ Şebekeden çekilen kWh
```

> **Kural sabit liste değildir (K-24):** Toplam maliyet, adı sayılan kalemlerin
> toplamı değil, **rolü `maliyet` olan bütün ölçüm noktalarının** toplamıdır.
> Yarın LPG, kömür veya fuel-oil eklenirse hiçbir formül değişmeden toplama
> girer.

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
| **Toplam Enerji kWh** | **rolü `satin_alinan` olan bütün noktaların ortak birimdeki toplamı** (K-24) — bugün: `SATIN_EL + TOPLAM_DG_KWH + MOTORIN_KWH` |
| Hat-1..4 çekirdek | `TOPLAM_CEKIRDEK × oran` → `veri_tipi = dagitilmis` (bkz. 2.2) |
| Buhar kWh | `BUHAR_KG × katsayı` → `conversion` tablosundan, tarihli |
| Motorin kWh | `MOTORIN_KG × katsayı` → `conversion` tablosundan, tarihli (K-24) |

> **Toplam enerji sabit bir liste değildir (K-24).** Formül "elektrik + doğalgaz"
> diye yazılmaz; **rol filtresi** olarak çalışır. Yeni bir satın alınan enerji
> türü (LPG, kömür, fuel-oil) tanımlandığı anda, hiçbir formül değişmeden
> toplama girer. Aynısı toplam maliyet için `maliyet` rolüyle geçerlidir (6.5).

**Eksik veri ve katsayı — kenar durum kuralı (İ-3):**

| Durum | Davranış |
|---|---|
| Ölçüm noktasının o dönem için değeri **yok** | Toplama katılmaz; toplam **üretilir** |
| Değer **sıfır** | Katkısı sıfırdır; katsayı tanımlı olmasa bile toplam **üretilir** |
| Değer **sıfırdan farklı**, dönüşüm katsayısı **tanımsız** | Toplam **ÜRETİLMEZ**; eksikliğin hangi enerji türünden kaynaklandığı yazılır |

> Bu ayrım motorin için pratik önem taşır: 2018–2025 arası motorin boştur, bu
> yüzden geçmiş dönem toplamları katsayı olmadan da üretilir ve **değişmez**.
> İlk motorin değeri girildiğinde sistem katsayı ister.

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
- Motorin noktaları **tanımlanır** ve toplamlara dahil edilir (K-24); 2018–2025
  arası veri boş olduğu için aktarılacak değer yoktur ve yıllık toplamlar değişmez.
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
Toplam Enerji Tüketimi = rolü `satin_alinan` olan bütün ölçüm
                         noktalarının ortak birimdeki toplamı

bugün  =  Şebekeden çekilen elektrik
        + Toplam doğalgaz
        + Motorin                      ← K-24; bugün sıfır, yarın olabilir
        + (ileride eklenecek her satın alınan yakıt)
```

> **Neden sabit liste değil (K-24):** Toplam enerji "elektrik + doğalgaz" diye
> yazılsaydı, motorin veya yeni bir yakıt eklendiğinde formülün güncellenmesi
> gerekirdi — ve bir gün unutulurdu. Rol filtresi olarak yazıldığında yeni tür
> tanımlandığı anda toplama girer. Motorin bugün sıfır olduğu için geçmiş
> toplamlar **değişmez** (bkz. 6.6 kenar durum kuralı).

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

Bütün hesaplar tek modülde toplanır (İ-2) ve hiçbiri saklanmaz (İ-1).

### 8.1 Temel hesaplar

| Hesap | Kural |
|---|---|
| Aylık toplam | Ölçüm noktası değerlerinin dönem toplamı |
| Hiyerarşi toplamı | Bir varlığın altındaki bütün noktaların toplamı (6.6) |
| Toplam enerji | Yalnız `satin_alinan` rolündeki noktalar — **sabit liste değil, rol filtresi** (7.1, K-24). Bugün: elektrik + doğalgaz + motorin |
| Ortak birim | kWh ↔ MJ ↔ GJ ↔ TEP. Referans GJ; 1 TEP = 41,868 GJ = 11.630 kWh |
| Maliyet | Rolü `maliyet` olan bütün noktaların toplamı; net ödenen = brüt − GES mahsubu (6.5, K-24) |
| Ortalama birim fiyat | Fatura TL ÷ tüketim — **hesaplanır, girilmez** (K-12) |
| Ölçüm kapsamı | Ölçülen alt toplam ÷ üst toplam; kalan "ölçülmeyen" (6.7) |

### 8.2 EnPI (K-06)

EnPI **kullanıcı tanımlıdır**: pay ve payda ölçüm noktası (veya hiyerarşi
düğümü) olarak seçilir.

```
EnPI = pay / payda
```

Örnekler: `Toplam enerji / Toplam üretim` (kWh/kg) ·
`Şebeke elektriği / Çikolata üretimi` · `Buhar kWh / Kakao üretimi`.

Her EnPI tanımı: ad, pay, payda, birim, ondalık hane, ana gösterge mi.

> **Ham EnPI'nin tuzağı:** Üretim düştüğünde sabit yük aynı kaldığı için EnPI
> kendiliğinden kötüleşir. Bu **verimsizlik değildir**. Bu yüzden ham EnPI asla
> tek başına gösterilmez; yanında normalize EnPI durur (8.4).

### 8.3 Baz çizgi (EnB) — iki seviye (K-19)

**Seviye 1 — Sabit baz çizgi.** Seçilen referans döneminin aylık ortalaması.
Anlaşılır, tartışılmaz, hemen kullanılır.

**Seviye 2 — Regresyonlu baz çizgi.** Referans dönemdeki (bağlam değişkeni,
enerji) çiftlerinden en küçük kareler ile:

```
beklenen_enerji = a × üretim + b
```

- `a` = **değişken enerji** — üretime bağlı kısım (kWh/kg)
- `b` = **sabit / baz yük** — üretim sıfır olsa bile harcanan enerji (kWh/ay)

> `b`'nin büyüklüğü tek başına çok değerli bir yönetim bulgusudur: tasarruf
> potansiyelinin nerede olduğunu söyler.

**Zorunlu güvenlik kuralları** (istatistiği yanlış kullanmamak için):

| Kural | Davranış |
|---|---|
| En az **12 veri noktası** yoksa | Regresyon kurulmaz, sabit baz çizgi önerilir |
| `R² < 0,5` | Model kurulur ama ekranda **açık uyarı**: *"Bu model tüketimin yalnızca %X'ini açıklıyor. Sonuçlara tek başına dayanarak karar vermeyin."* R² asla gizlenmez |
| Referans dönem dışına çıkan noktalar | Grafikte farklı gösterilir (ekstrapolasyon uyarısı) |
| `a < 0` (üretim arttıkça enerji azalıyor) | Fiziksel olarak şüpheli — açık uyarı |

### 8.4 Normalize EnPI

```
Normalize EnPI = gerçek enerji / beklenen enerji
```

1,00 = baz performans · 0,92 = %8 iyileşme · 1,11 = %11 kötüleşme.
Üretim dalgalanmasından arındırılmıştır. **Ham EnPI ile yan yana gösterilir**,
yerine geçmez.

### 8.5 CUSUM

```
CUSUM_n = Σ (gerçek_i − beklenen_i),  i = 1..n
```

**Okunuşu — tek kural: eğim önemlidir, seviye değil.**

| Eğim | Anlamı |
|---|---|
| Yatay | Performans baz çizgiyle uyumlu |
| Aşağı | **Kalıcı tasarruf.** Eğimin başladığı ay, iyileştirmenin gerçekten devreye girdiği aydır |
| Yukarı | **Kalıcı kayıp.** Başlangıç ayı, arızanın/ayar bozulmasının tarihidir |

CUSUM'un değeri: tek aylık gürültüde kaybolan küçük ama kalıcı bir kaymayı
aylar sonra apaçık görünür yapar ve **tarihini verir**. Eğim değişim noktasına
kullanıcı **not** yazabilir ("gaz motorları durduruldu", "yeni hat devreye
alındı") — bu notlar kurumsal hafızadır.

### 8.6 Dönüşüm verimliliği (7.3)

| Gösterge | Formül |
|---|---|
| Kojen elektrik verimi | Elektrik üretimi kWh ÷ Doğalgaz kWh |
| Kojen toplam verimi | (Elektrik + Buhar + Sıcak su) kWh ÷ Doğalgaz kWh |
| Kazan verimi | Buhar kWh ÷ Doğalgaz kWh |

Bu göstergeler toplam enerjinin **dışındadır**; dönüşüm ekipmanının sağlığını
ölçer. Excel'de hiç hesaplanmıyor.

### 8.7 Fiyat ve hacim etkisinin ayrıştırılması

Maliyet artışının ne kadarı fiyattan, ne kadarı tüketimden geliyor?

```
Fiyat etkisi  = (fiyat₂ − fiyat₁) × tüketim₁
Hacim etkisi  = (tüketim₂ − tüketim₁) × fiyat₁
Bileşik etki  = (fiyat₂ − fiyat₁) × (tüketim₂ − tüketim₁)
```

Toplam fark = üç etkinin toplamı. Enerji yöneticisinin kontrolünde olan
**hacim etkisidir**; fiyat etkisi piyasadır. Bu ayrım yapılmazsa fiyat artışı
enerji yönetiminin başarısızlığı gibi görünür.

### 8.8 Gerçek veriyle doğrulama — 2025 vakası

> Bu bölüm, yukarıdaki motorun **sizin gerçek verinizde** ne bulduğudur.
> Tasarımın işe yarayıp yaramadığının sınavıdır.

**Soru:** 2025'te EnPI 1,173'ten 1,367'ye çıktı (%+16,5). Gerçek verimsizlik mi,
yoksa üretim düştüğü için mi?

**Adım 1 — Baz çizgi (2022–2024, kullanılabilir 35 ay):**

```
beklenen_enerji = 0,5025 × üretim_kg + 6.021.966        R² = 0,43
```

- Değişken enerji: **0,5025 kWh/kg**
- **Sabit / baz yük: 6.021.966 kWh/ay → yılda 72,3 milyon kWh**
- Baz yükün ortalama aylık tüketimdeki payı: **%56,3**

> ⚠ **R² = 0,43 < 0,50.** Kural gereği (8.3) açık uyarı: bu model tüketimin
> yalnızca %43'ünü üretimle açıklıyor. Yani tüketimin çoğunu belirleyen şey
> üretim miktarı **değil**. Bu bulgunun kendisi değerlidir: başka bir sürükleyici
> (mevsim, ürün karması, ekipman durumu) baskındır. Aşağıdaki sayı bu nedenle
> **işaret**tir, kanıt değildir.
>
> Aynı belirsizlik **sabit yük (`b`) tahminini de kapsar**: düşük R²'de kesişim
> noktasının güven aralığı geniştir. "%56,3" bir büyüklük mertebesidir —
> *"tüketimin yarısından fazlası üretimden bağımsız"* denebilir, "%56,3'tür"
> denemez. Kesinleştirmenin yolu modele ikinci bir değişken eklemektir
> (dış sıcaklık / derece-gün, ürün karması) — bkz. 9.9 "ileride eklenebilecekler".

> **Neden 36 değil 35 ay?** 2024 Ağustos'un toplam üretimi bozuk hücre yüzünden
> **üretilemiyor** (S10, bkz. 2.5); o ay regresyona giremez. Aynı regresyon
> Excel'in kendi `Toplam Üretim` sütunuyla kurulsaydı 36 nokta olur ve
> `a = 0,4254 · b = 6.774.643 · R² = 0,40` çıkardı — çünkü Excel'in `SUM`'ı
> bozuk hücreyi sessizce atlayıp o aya **eksik bir üretim** yazıyor. Program
> eksik üretimi doğru sayı gibi kullanmaz (İ-3); **bu farkın kendisi, tek bir
> bozuk hücrenin baz çizgiyi nasıl kaydırdığının ölçüsüdür.** Hücre
> düzeltildiğinde model yeniden kurulmalıdır.

**Adım 2 — Sonuç:**

| | Değer |
|---|---|
| Ham EnPI kötüleşmesi | **%+16,5** |
| Normalize EnPI (2025) | **1,119** → gerçek kötüleşme **%+11,9** |
| Üretim hacminden gelen kısım | ≈ %4,6 |

Yani bozulmanın **büyük kısmı gerçek**, küçük bir kısmı üretim düşüşünün
yarattığı görüntü. Ham EnPI tek başına bakılsaydı sorun %16,5 sanılırdı;
normalize edilince %11,9'a iniyor ama **kaybolmuyor**.

**Adım 3 — CUSUM tarihi verdi:** Ocak 2025 hâlâ baz çizginin altında
(−334.342 kWh); **Şubat 2025**'te işaret değişiyor ve birikim yıl boyu düzenli
yukarı eğimle sürüyor (yıl sonu birikimi **+14.605.848 kWh**). Tek bir kötü ay
değil, **kalıcı bir değişiklik**.

**Adım 4 — Dönüşüm verimliliği nedeni buldu:**

| | 2024 | 2025 | Fark |
|---|---:|---:|---:|
| Gaz motorları (GM-1,2,3) elektrik üretimi | 8.833.900 kWh | **0** | durdu |
| İstasyon-3 (Türbin) doğalgaz tüketimi | 44.804.077 | 81.709.864 | **+%82,4** |
| **Türbin elektrik verimi** | **%30,8** | **%26,3** | **−4,5 puan** |
| **Türbin toplam verimi** | **%57,2** | **%50,3** | **−6,9 puan** |
| Toplam doğalgaz | 111.987.169 | 120.168.406 | +%7,3 |
| Toplam üretim | 111.897.453 kg | 100.503.911 kg | −%10,2 |

**Bulgu:** Gaz motorları durdu, yük türbine kaydı ve **türbin daha düşük verimle
çalışıyor**. 80,6 milyon kWh gaz üzerinden 6,9 puanlık verim kaybı ≈
**yılda 5,6 milyon kWh**. Bu, baz çizgiye göre 14,6 milyon kWh'lik toplam
sapmanın **yaklaşık %38'idir**.

> Verim düşüşü bir **model tahmini değil, doğrudan ölçümdür** — R² uyarısı bu
> bulguyu etkilemez. Regresyon "ne kadar" sorusuna işaret verdi; dönüşüm
> verimliliği "neden" sorusunu cevapladı.

> ⚠ **6,9 puanın 1,7 puanı fizik değil, varsayımdır (S12).** Excel 2025'te buhar
> entalpi varsayımını 600'den 560 kcal/kg'a düşürmüş; aynı buhar kilogramı daha
> az kWh olarak raporlanıyor. Gerçek performans düşüşü **5,2 puan**, yıllık kayıp
> yaklaşık **4,2 milyon kWh**'dir. Program iki katsayıyı da tarihli tutar ve bu
> ayrımı Ekran 9'da yazar; hangi entalpinin doğru olduğu **A-08**'e bağlıdır.
> Bulgunun yönü değişmez, büyüklüğü değişir.

> ⚠ **Aynı dönemin kazan verimleri güvenilir değil (S13).** 2025'te kazanların
> ürettiği buhar, kendilerine atanmış gazdan büyük görünüyor (%137 ve %145).
> Bu yüzden "2025'te kazanlar iyileşti" denemez; **karşılaştırmaya yalnız türbin
> girer** (K-25, K-26). Satın alınan gazın %12,9'u hiçbir ekipmana atanmamıştır.

**Bu vaka neyi kanıtlıyor:**

| Ekran / hesap | Katkısı |
|---|---|
| Ham EnPI (8.2) | Bir sorun olduğunu gösterdi — ama abarttı |
| Normalize EnPI (8.4) | Sorunun gerçek büyüklüğünü verdi |
| CUSUM (8.5) | Sorunun **tarihini** verdi (Şubat 2025) |
| Dönüşüm verimliliği (8.6) | Sorunun **nedenini** verdi |
| R² uyarısı (8.3) | Modele fazla güvenmeyi engelledi |
| Fiyat/hacim ayrıştırması (8.7) | Bulguyu **parayla** doğruladı: doğalgazda +13,5 M TL'lik **hacim** artışı (elektrikte ise −5,5 M TL tasarruf) |

Excel bu zincirin **hiçbir halkasını** üretmiyor.

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
| Hesaplanan Değerler | Sistem bundan ne üretti? |
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
│  5  Hesaplanan Değerler │   ← hesap katmanının aynası (K-23)
├─ ANALİZ ────────────────┤
│  6  Enerji Dengesi      │
│  7  Tüketim Analizi     │
│  8  Performans (EnPI)   │
│  9  Dönüşüm Verimliliği │
│ 10  Maliyet             │
│ 11  GES                 │
├─ YÖNETİM ───────────────┤
│ 12  Hedefler ve Aksiyon │
│ 13  Raporlar            │
├─ SİSTEM ────────────────┤
│ 14  Tanımlar            │   ← sekmeli: varlık ağacı, ölçüm
│ 15  Ayarlar ve Yedek    │      noktaları, enerji türleri,
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

### 9.6 · Ekran 5 — Hesaplanan Değerler

#### Amaç
**"Sistem bu veriden ne üretti?"** — Hesaplanan bütün değerleri tek yerde,
ham veri gibi bir tablo hâlinde göstermek. Hesap motorunun **camdan kutusu**.

> **Nasıl çalışır (K-23):** Program açıldığında ham veriyi okur, hesaplanan
> her değeri yeniden üretir ve bu katmana yazar. Bütün ekranlar sayıyı
> **buradan** çeker — panel, raporlar, analizler, hepsi. Veriye her
> dokunduğunuzda katman anında yeniden üretilir.

#### Kullanıcının göreceği bilgiler

Dönem (satır) × hesaplanan değer (sütun) tablosu — tıpkı veri girişi tablosu
gibi, ama **salt okunur** ve her hücrenin altında formülü var:

```
Dönem      Toplam DG kWh   Toplam Enerji   EnPI     Beklenen   Sapma      CUSUM      Verim%
2025 Oca      10.446.686      11.868.006   1,2972  10.666.490   -381.871   -381.871    52,1
2025 Şub      11.120.372      12.572.682   1,3179  10.832.468  1.740.213  1.358.343    50,8
2025 Mar      10.602.394      12.060.768   1,2707  10.812.348  1.248.420  2.606.763    50,4
...
```

Her sütun başlığına tıklanınca **formülü ve kaynağı** açılır:

```
Toplam Enerji kWh
  = Şebekeden çekilen elektrik + Toplam doğalgaz kWh
  Kaynak: SEBEKE_EL (girildi) + IST1_DG_KWH + IST2_DG_KWH + IST3_DG_KWH (girildi)
  Rol filtresi: yalnız "satın alınan"  ·  Kural: 7.1
```

Üstte **katman durumu**:
```
Son üretim: 14:32:05 · 96 dönem × 41 hesaplanan değer = 3.936 hücre · 0,4 sn
Kaynak: 8.640 ham değer · Tüm değerler güncel ✓
```

#### Kullanıcının gireceği veriler
**Yok — ve girilemez.** Bu ekran salt okunurdur. Bir sayıyı değiştirmek
istiyorsanız, onu üreten ham veriyi değiştirmelisiniz; ekran sizi doğrudan
o hücreye götürür (E-4).

#### Sistemin hesaplayacağı değerler
Bölüm 8'in tamamı: hiyerarşi toplamları · türetilmiş noktalar · ortak birim
karşılıkları · maliyet ve net ödenen · EnPI'ler · baz çizgi beklenen değerleri ·
sapma · normalize EnPI · CUSUM · dönüşüm verimlilikleri · ölçüm kapsamı ·
fiyat/hacim etkileri.

#### Kullanılacak grafikler ve tablolar
Grafik **yok** — bu bir veri ekranıdır (E-1). Yalnızca tablo:
filtrelenebilir, sıralanabilir, sütun seçilebilir, dışa aktarılabilir.

**Excel dışa aktarma — iki sayfalı çalışma kitabı:**

```
enerji-veri-2026-09-17.xlsx
  ├── Sayfa "Ham Veri"      ← girdiğiniz değerler (dönem × ölçüm noktası)
  └── Sayfa "Hesaplanan"    ← sistemin ürettiği değerler + formül satırı
```

Bugün Excel'de tek sayfada yaptığınız işin, ham ile hesaplananın **ayrıldığı**
hâli. İstediğiniz an bu dosyayı alır, açar, sunuma veya denetçi dosyasına
koyarsınız. Fark şu: bu dosya bir **çıktıdır**, sistemin hafızası değil —
her dışa aktarmada o anki ham veriden yeniden üretilir, bayatlamaz.

#### Yapılabilecek analizler
- **Hesabın denetimi:** bir sayı beklenmedikse formülü ve girdileri görülür.
- **Dışa aktarma:** hesaplanan değerler Excel'e alınıp başka amaçlarla
  (sunum, üst yönetim tablosu, denetçi dosyası) kullanılabilir.
- **Bütünlük kontrolü:** üretilemeyen değerler ayrı işaretlenir —
  *"2019 Mart: ortak birim üretilemedi, buhar katsayısı tanımlı değil"* (İ-3).

#### ISO 50001 ile ilişkisi
Madde 9.1.1 — izleme ve ölçme sonuçlarının **geçerliliği**. Denetçiye
"bu rakamı nasıl ürettiniz?" sorusunun cevabı bu ekrandır: formül, girdi ve
sonuç aynı yerde, tek ekranda.

#### İleride eklenebilecekler
Hesaplanan değer için kullanıcı tanımlı ek sütun (kendi formülünüz) ·
iki dönem arası hesap farkı karşılaştırması · katmanın belirli bir tarihteki
hâlinin dondurulup saklanması (denetim fotoğrafı) · hesap süresi profilleme.

---

### 9.7 · Ekran 6 — Enerji Dengesi

#### Amaç
**"Enerji nereye gidiyor?"** — Satın alınan enerjinin tesise girişinden
tüketildiği yere kadar izini sürmek ve **ölçülmeyen payı dürüstçe göstermek**.

#### Kullanıcının göreceği bilgiler
- **Sankey akış diyagramı:** Şebeke elektriği ve doğalgaz → istasyonlar →
  dönüşüm (kojen elektriği, buhar, sıcak su) → ölçülen tüketiciler +
  **ölçülmeyen**.
- **Denge tablosu:** giriş, dönüşüm, ölçülen çıkış, ölçülmeyen fark.
- **Kapsam ağacı:** varlık hiyerarşisi; her düğümde toplam, ölçülen alt toplam,
  ölçülmeyen pay ve yüzdesi.
- **Tutarsızlık uyarıları:** alt toplamın üst toplamı aştığı düğümler (S3).

#### Kullanıcının gireceği veriler
Yok. Dönem aralığı, birim (kWh/GJ/TEP) ve hiyerarşi düğümü seçilir.

#### Sistemin hesaplayacağı değerler
Akış büyüklükleri · her düğümde ölçülen/ölçülmeyen · dönüşüm kayıpları ·
kapsam yüzdeleri · tutarsızlık farkları.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk |
|---|---|---|---|
| G1 | Enerji akışı | Sankey | Kategorik, enerji türüne göre |
| G2 | Ölçüm kapsamı zaman içinde | Sütun | Tek slot (1) |
| T1 | Kapsam ağacı | Katlanabilir tablo | Durum ikonları |

> **Sizin verinizde bu ekran ne gösterecek:** 2024 Ocak'ta ölçülen alt sayaçlar
> 965.134 kWh, fabrika elektriği 3.761.332 kWh → Sankey'in en kalın kolu
> **"ölçülmeyen %74"** olacak. Bu rahatsız edici ama doğrudur ve alt sayaç
> yatırımının nereye yapılacağını söyler.

#### Yapılabilecek analizler
Ölçüm kapsamının yeterliliği · dönüşüm kayıplarının büyüklüğü ·
hangi istasyonun ne kadar yakıt çektiği · alt sayaç yatırım önceliği.

#### ISO 50001 ile ilişkisi
Madde 6.3 *Enerji gözden geçirmesi*'nin ana aracı. Önemli enerji kullanımlarının
(SEU) belirlenmesi doğrudan bu ekrandan çıkar.

#### İleride eklenebilecekler
Dönem karşılaştırmalı Sankey (iki dönemin akış farkı) · ölçüm kapsamı hedefi ·
alt sayaç yatırımının geri dönüş hesabı.

---

### 9.8 · Ekran 7 — Tüketim Analizi

#### Amaç
**"Nereye bakmalıyım?"** — Tüketimi farklı kırılımlarda inceleyip en büyük
ve en anormal kalemleri bulmak.

#### Kullanıcının göreceği bilgiler
Üstte tek satır filtre çubuğu: tarih aralığı · varlık (ağaçtan seçim) ·
enerji türü · birim (kWh/GJ/TEP) · karşılaştırma dönemi.

#### Kullanıcının gireceği veriler
Yok; yalnızca filtre seçimleri. Seçim kombinasyonu **kaydedilebilir**
("Kojenerasyon 2025", "Chiller'lar son 24 ay") ve sonra tek tıkla çağrılır.

#### Sistemin hesaplayacağı değerler
Dönem toplamları · dönem–dönem farklar · kümülatif yüzdeler ·
ortak birime dönüşüm · mevsimsellik.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk | Not |
|---|---|---|---|---|
| G1 | Tüketim trendi | Sütun | Tek slot (1) | Seçilen kırılım tek seriyse |
| G2 | Enerji türü / varlık karması | Yığılmış sütun | Kategorik | ≤8 seri; fazlası "Diğer"e katlanır |
| G3 | Isı haritası (yıl × ay) | Hücre matrisi | **Sıralı mavi** | Ölçek açıklaması zorunlu; mevsimselliği açığa çıkarır |
| G4 | Pareto | Yatay çubuk + tablo | Tek slot (1) | Kümülatif % **tablo sütununda**; %80 eşiği satır ayracıyla (5.7.4) |
| G5 | Dönem karşılaştırma | Yatay çubuk (fark) | **Kutuplu** | Artan kırmızı, azalan mavi |
| T1 | Ayrıntı tablosu | Tablo | — | Dışa aktarılabilir |

> **Dönem uzunluğu uyarısı:** Karşılaştırılan dönemler farklı uzunluktaysa
> (28 vs 31 gün) sistem **otomatik normalleştirme yapmaz**; ekranda
> *"Dönemler farklı uzunlukta"* uyarısı çıkar (İ-4). Sessiz normalleştirme,
> kullanıcının farkında olmadığı bir varsayımdır.

#### Yapılabilecek analizler
En çok tüketen ilk N nokta (Pareto) · mevsimsellik (ısı haritası) ·
yıldan yıla karşılaştırma · enerji türü kayması · boşta/duruş tüketimi
(üretim düşükken tüketim yüksekse).

#### ISO 50001 ile ilişkisi
Madde 6.3 — enerji kullanım ve tüketiminin analizi; SEU belirleme.

#### İleride eklenebilecekler
Günlük/saatlik veri geldiğinde gün × saat ısı haritası · derece-gün
normalizasyonu · anomali işaretleme.

---

### 9.9 · Ekran 8 — Performans (EnPI ve Baz Çizgi)

> **Platformun kalbi bu ekrandır.** "Ne kadar enerji harcadık?" sorusundan
> "**enerji performansımız iyileşti mi, ne zaman, ne kadar?**" sorusuna geçiş
> burada olur.

#### Amaç
Enerji performansındaki gerçek değişimi, üretim dalgalanmasından arındırarak
ölçmek ve değişimin tarihini bulmak.

#### Kullanıcının göreceği bilgiler
Üstte iki seçici: **EnPI** (kullanıcı tanımlı set, K-06) ve
**baz çizgi** (birden çok tanımlı olabilir, K-19).

Dört bölüm hâlinde:

**Bölüm 1 — Baz çizgi modeli**
```
Beklenen enerji = 0,5025 × üretim (kg) + 6.021.966        R² = 0,43
Değişken enerji: 0,5025 kWh/kg    Sabit/baz yük: 6.021.966 kWh/ay (%56,3)
⚠ Bu model tüketimin yalnızca %43'ünü açıklıyor. Tek başına karar vermeyin.
```
R² uyarısı **gizlenmez, sonucun yanında durur** (İ-4, 8.3).

**Bölüm 2 — Beklenen vs gerçek** (zaman serisi)

**Bölüm 3 — Normalize EnPI** — ham EnPI ile **yan yana**, biri diğerinin
yerine geçmez.

**Bölüm 4 — CUSUM** — eğim değişim noktaları işaretli; her noktaya
kullanıcı **not** yazabilir.

#### Kullanıcının gireceği veriler
- Baz çizgi tanımı: ad, referans dönem, model tipi (sabit / regresyon),
  bağlam değişkeni (üretim, derece-gün, çalışma saati…).
- CUSUM eğim değişim noktalarına **açıklama notu** — *"Gaz motorları
  durduruldu"*. Bu notlar kurumsal hafızadır.

#### Sistemin hesaplayacağı değerler
Regresyon katsayıları (`a`, `b`), R² · beklenen enerji · sapma ·
normalize EnPI · CUSUM · kümülatif tasarruf/kayıp (kWh ve TL).

> Regresyon **katsayıları saklanır** (bir *karardır*), sapma ve CUSUM
> saklanmaz — her seferinde yeniden hesaplanır (İ-1).

#### Grafikler ve tablolar

| # | Grafik | Form | Renk | Not |
|---|---|---|---|---|
| G1 | Üretim–enerji dağılımı + regresyon doğrusu | Dağılım (scatter) | **En fazla 3 seri**: baz dönem / değerlendirme dönemi / dışarıda kalan | Dağılım grafiği tüm-çiftler kuralına tabi |
| G2 | Beklenen vs gerçek | İki çizgi | Kategorik (1, 2) | Açıklama + uç nokta etiketi |
| G3 | Ham EnPI ve normalize EnPI | İki ayrı küçük grafik | Tek slot | **Aynı grafikte değil** — farklı ölçekler, çift eksen yasak |
| G4 | CUSUM | Çizgi + kutuplu dolgu | Sıfır altı mavi (tasarruf), üstü kırmızı (kayıp) | Eğim değişim noktası + not balonu |
| T1 | Dönem bazında sapma | Tablo | — | Gerçek, beklenen, sapma, kümülatif |

#### Yapılabilecek analizler
- **Gerçek iyileşme/kötüleşme** (üretimden arındırılmış).
- **Sabit yük analizi:** baz yük toplam tüketimin %63'üyse tasarruf potansiyeli
  üretim hattında değil, **sürekli çalışan sistemlerdedir**.
- **Değişimin tarihi** (CUSUM eğim kırılımı).
- Tasarrufun parasal karşılığı (sapma × birim fiyat).
- Farklı baz çizgilerin karşılaştırılması (K-19).

#### ISO 50001 ile ilişkisi
Madde **6.4 EnPI** ve **6.5 Enerji baz çizgisi** — standardın ölçüm motoru.
Madde 9.1 izleme ve değerlendirme. Bu ekran olmadan ISO 50001'in "enerji
performansında sürekli iyileştirme" şartı **kanıtlanamaz**.

#### İleride eklenebilecekler
Çok değişkenli regresyon (üretim + dış sıcaklık + ürün karması) ·
IPMVP uyumlu tasarruf doğrulama raporu · otomatik anomali işaretleme ·
baz çizginin dönemsel olarak yeniden kurulması (rebaselining) ve gerekçesi.

---

### 9.10 · Ekran 9 — Dönüşüm Verimliliği

#### Amaç
**"Dönüşüm ekipmanım sağlıklı mı?"** — Kojenerasyon ve kazanların yakıtı ne
verimle faydalı enerjiye çevirdiğini izlemek.

> Excel'de bu hiç hesaplanmıyor. 2025 vakasında (8.8) bozulmanın **nedenini**
> bulan ekran budur.

#### Kullanıcının göreceği bilgiler
Her dönüşüm varlığı (Türbin, GM-1..3, Kazan-1..2) için kart:

```
TÜRBİN                                       2025
Doğalgaz girdisi          80.571.461 kWh
Elektrik üretimi          21.161.000 kWh    Elektrik verimi   %26,3  ▼ −4,5 puan
Buhar üretimi             19.382.753 kWh
                                            Toplam verim      %50,3  ▼ −6,9 puan
                                            Kayıp             %49,7
⚠ Verim 2024'e göre 6,9 puan düştü. 80,6 GWh gaz üzerinden ≈ 5,6 GWh/yıl kayıp.
```

Ayrıca: çalışma durumu (aktif / durduruldu), devreye giriş-çıkış tarihleri (S6).

#### Kullanıcının gireceği veriler
Yok. Veriler Ekran 2'den gelir. Varlık bazında **not** yazılabilir
(bakım, arıza, devreden çıkarma gerekçesi).

#### Sistemin hesaplayacağı değerler
Elektrik verimi · ısı verimi · toplam verim · kayıp yüzdesi ·
önceki dönemle fark · **verim kaybının kWh ve TL karşılığı**.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk |
|---|---|---|---|
| G1 | Verim trendi (aylık) | Çizgi | Varlık başına kategorik, ≤8 |
| G2 | Yakıt → faydalı enerji dağılımı | Yığılmış sütun | Kategorik (elektrik / buhar / sıcak su / kayıp) |
| G3 | Varlık karşılaştırması | Yatay çubuk | Tek slot (1) |
| T1 | Verim tablosu | Tablo | Durum ikonları (eşik altı) |

#### Yapılabilecek analizler
- Ekipman verim düşüşünün erken tespiti (bakım tetikleyicisi).
- **Yük dağıtım kararı:** aynı işi hangi ekipman daha verimli yapıyor?
  2025'te yük gaz motorlarından türbine kaydı ve verim düştü — bu karar
  sorgulanabilir hale gelir.
- Verim kaybının yıllık parasal maliyeti.
- Devreden çıkarma/devreye alma kararlarının enerji etkisi.

#### ISO 50001 ile ilişkisi
Madde 6.3 — enerji performansını etkileyen değişkenlerin belirlenmesi.
Madde 10 — iyileştirme fırsatlarının tespiti. Ekipman verimi, en somut
iyileştirme fırsatı kaynağıdır.

#### İleride eklenebilecekler
Verim eşiği alarmı · üretici katalog verisiyle karşılaştırma ·
bakım kaydıyla ilişkilendirme · kısmi yük verimi eğrisi.

---

### 9.11 · Ekran 10 — Maliyet

#### Amaç
**"Para nereye gidiyor ve maliyet neden arttı?"** — Maliyet artışının ne
kadarının **fiyattan**, ne kadarının **tüketimden** geldiğini ayrıştırmak.

#### Kullanıcının göreceği bilgiler

**Maliyet özeti — gerçek 2025 verisi:**
```
Brüt elektrik faturası         55.712.474 TL
− GES mahsubu + satış         −25.723.468 TL
= Net ödenen elektrik          29.989.006 TL
+ Doğalgaz faturası           165.193.331 TL
= Toplam enerji maliyeti      195.182.337 TL
```

**Fiyat/hacim ayrıştırması (8.7)** — bu ekranın en değerli parçası.
Gerçek verinizle 2024 → 2025:

```
ELEKTRİK          maliyet farkı            +4.044.578 TL
  ├─ Fiyat etkisi (piyasa)                +10.682.663 TL
  ├─ Hacim etkisi (bizim kontrolümüzde)    −5.500.767 TL   ✓
  └─ Bileşik etki                          −1.137.318 TL
     Birim fiyat: 2,6842 → 3,2392 TL/kWh   (+%20,7)

DOĞALGAZ          maliyet farkı           +36.066.765 TL
  ├─ Fiyat etkisi (piyasa)                +20.456.179 TL
  ├─ Hacim etkisi (bizim kontrolümüzde)   +13.475.761 TL   ⚠
  └─ Bileşik etki                          +2.134.825 TL
     Birim fiyat: 12,6264 → 14,6266 TL/m³  (+%15,8)
```

> **Bu ayrıştırmanın değeri:** Elektrik faturası 4 milyon TL arttı — bakan
> kişi "enerji yönetimi başarısız" der. Oysa **tüketim düştü ve 5,5 milyon TL
> tasarruf sağladı**; fatura yalnızca fiyat %20,7 arttığı için yükseldi.
> Doğalgazda ise durum tersidir: 13,5 milyon TL'lik artış **gerçek hacim
> artışıdır** ve 8.8'deki türbin verim kaybıyla birebir örtüşür. Aynı toplam
> tabloya bakıp iki farklı yönetim kararı verilir — ayrıştırma olmadan ikisi
> de görünmez.

**Ortalama birim fiyat trendi** (K-12 ile hesaplanır): 0,2942 → 3,2392 TL/kWh
(2018 → 2025, **11 kat**).

#### Kullanıcının gireceği veriler
Yok — fatura tutarları Ekran 2'de girilir.

#### Sistemin hesaplayacağı değerler
Net ödenen · toplam maliyet · ortalama birim fiyat · fiyat/hacim/bileşik
etkiler · GES'in mali katkısı · bütçe sapması (hedef varsa) ·
enerji türlerinin maliyet payı.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk | Not |
|---|---|---|---|---|
| G1 | Aylık maliyet | Yığılmış sütun | Kategorik (elektrik / doğalgaz) | |
| G2 | Ortalama birim fiyat trendi | Çizgi | Enerji türü başına kategorik | **Maliyetle aynı grafikte değil** |
| G3 | Fiyat/hacim ayrıştırması | Şelale (waterfall) | **Kutuplu** | Artıran kırmızı, azaltan mavi |
| G4 | GES mali katkısı | Sütun | Tek slot (3) | Mahsup + satış |
| T1 | Maliyet dökümü | Tablo | — | |

#### Yapılabilecek analizler
- **Fiyat mi, tüketim mi?** — Enerji yönetiminin başarısı yalnızca hacim
  etkisiyle ölçülebilir; fiyat piyasadır. Bu ayrım yapılmazsa zam, enerji
  yönetiminin başarısızlığı gibi görünür.
- GES'in gerçek mali katkısı.
- Enerji türleri arasında maliyet kayması (yakıt değiştirme kararı).
- Tasarrufun parasal karşılığı (Ekran 8'deki sapma × birim fiyat).

#### ISO 50001 ile ilişkisi
Standart maliyeti zorunlu tutmaz, ancak madde 9.3 yönetimin gözden geçirmesi
ve iyileştirme fırsatlarının önceliklendirilmesi için maliyet temel girdidir.

#### İleride eklenebilecekler
Tarihli birim fiyat tanımıyla **gölge faturalama** (fatura doğrulama) ·
tarife dilimi (puant/gündüz/gece) kırılımı · reaktif ceza takibi ·
bütçe planlama ve tahmin · maliyetin bölümlere dağıtılması.

---

### 9.12 · Ekran 11 — GES

#### Amaç
**"Santraller ne üretti, ne kazandırdı?"** — Yozgat ve Adana GES'lerini
ayrı tesis olarak izlemek (K-03).

> **Kritik kural:** GES üretimi fabrikanın enerji dengesine (kWh) **girmez**;
> yalnızca mali dengeye mahsup olarak girer (7.1, 7.2). Bu ekran fabrika
> EnPI'sini etkilemez.

#### Kullanıcının göreceği bilgiler
Santral başına kart: aylık üretim (kWh) · mahsup (TL) · satış geliri (TL) ·
ortalama birim değer (TL/kWh) · devreye giriş tarihi.

#### Kullanıcının gireceği veriler
Aylık üretim (kWh), mahsup tutarı (TL), satış tutarı (TL) — Ekran 2 üzerinden.

#### Sistemin hesaplayacağı değerler
Toplam üretim · toplam mali katkı · ortalama TL/kWh · mevsimsel profil ·
fabrika elektrik maliyetini karşılama oranı (%).

#### Grafikler ve tablolar

| # | Grafik | Form | Renk |
|---|---|---|---|
| G1 | Aylık üretim | Sütun | Kategorik (Yozgat / Adana) |
| G2 | Mevsimsel profil (yıl × ay) | Isı haritası | **Sıralı mavi** |
| G3 | Mali katkı | Yığılmış sütun | Kategorik (mahsup / satış) |
| T1 | Santral özeti | Tablo | — |

#### Yapılabilecek analizler
Mevsimsel üretim profili (yaz–kış farkı) · santraller arası karşılaştırma ·
fabrika elektrik maliyetinin ne kadarını karşıladığı · yıldan yıla üretim değişimi
(bozunma belirtisi).

#### ISO 50001 ile ilişkisi
Madde 6.3 — yenilenebilir enerji kaynaklarının kuruluşun enerji profilindeki
yeri. Kapsam 2 emisyon azaltımının kanıtı (ileride).

#### İleride eklenebilecekler
**Performans Oranı (PR)** — IEC 61724-1 · **emre amadelik** · ışınım verisi
ile beklenen üretim karşılaştırması · bozunma (degradation) takibi ·
inverter/string kırılımı.

---

### 9.13 · Ekran 12 — Hedefler ve Aksiyonlar

#### Amaç
Hedefleri tanımlamak, durumlarını izlemek ve tespit edilen sapmaların
**bir sahibi ve termini olmasını** sağlamak.

#### Bölüm 1 — Hedefler (K-21)

Dört hedef türü:

| Tür | Örnek | Ölçüm |
|---|---|---|
| **EnPI hedefi** | "2027'de 1,20 kWh/kg" | Ham veya normalize EnPI |
| **Tüketim hedefi** | "Ocak 2027: elektrik ≤ 1,4 GWh" | Mutlak kWh |
| **Maliyet hedefi** | "2027 enerji bütçesi 230 M TL" | TL |
| **Tasarruf hedefi** | "Baz çizgiye göre yılda %3 iyileşme" | Normalize EnPI üzerinden |

> **Uyarı, sonucun yanında (E-2):** Tüketim hedefi seçildiğinde sistem şunu
> yazar: *"Üretim düşerse bu hedef kendiliğinden tutar. Gerçek performans için
> EnPI veya tasarruf hedefi kullanın."*

Her hedef: ad, tür, kapsam (varlık/enerji türü), dönem, değer, sorumlu, not.

#### Bölüm 2 — Aksiyonlar

| Alan | Açıklama |
|---|---|
| Başlık, açıklama | Ne yapılacak |
| Bağlam | Enerji türü / varlık / dönem — hangi tespitten doğdu |
| Sorumlu, termin | Kim, ne zaman |
| Durum | Açık / Devam / Kapandı / İptal |
| Beklenen tasarruf | kWh veya TL |
| Sonuç notu | Kapanışta gerçekleşen |

**Kritik bağlantı:** CUSUM'daki eğim kırılımından, Pareto'nun ilk sırasından
ve dönüşüm verimliliği uyarısından **doğrudan aksiyon açılabilir**. Analizden
eyleme geçişin köprüsü budur.

#### Sistemin hesaplayacağı değerler
Hedefe kalan mesafe ve % · gerçekleşme trendi · gecikmiş aksiyon sayısı ·
beklenen ve gerçekleşen tasarruf toplamı.

#### Grafikler ve tablolar

| # | Grafik | Form | Renk |
|---|---|---|---|
| G1 | Hedef vs gerçekleşen | Çizgi + hedef referans hattı | Tek slot (1) + gri hedef |
| G2 | Hedefe uzaklık | Ölçer (meter) | Durum renkleri + ikon |
| T1 | Aksiyon listesi | Tablo | Durum ikonları; gecikenler ikon + etiketle |

#### ISO 50001 ile ilişkisi
Madde **6.2 Amaçlar ve enerji hedefleri** · madde **6.2.2 Eylem planları** ·
madde 9.1 izleme. Aksiyon kayıtları, Verimlilik Artırıcı Proje (VAP)
takibinin de temelidir.

#### İleride eklenebilecekler
Hedeflerin varlık bazında alt hedeflere bölünmesi · aksiyonlara dosya eki ·
gerçekleşen tasarrufun IPMVP yöntemiyle doğrulanması · hatırlatmalar.

---

### 9.14 · Ekran 13 — Raporlar (K-20)

#### Amaç
Ekranda görüleni **kâğıda ve toplantıya** taşımak. Enerji yöneticisinin
çıktısı hâlâ basılı gider.

#### Üç rapor

**1 · Aylık Enerji Raporu** — tek sayfa, yazdırılabilir:
seçilen ayın tüketimi (tür bazında, ortak birimde) · maliyeti · EnPI ve
normalize EnPI · hedef durumu · geçen yılın aynı ayıyla karşılaştırma ·
açık aksiyonlar · veri kalitesi notu.

**2 · Yönetim Gözden Geçirme Raporu** (ISO 50001 md. 9.3):
dönem performans özeti · bütün EnPI'ler ve baz çizgiye göre durum ·
önemli enerji kullanımları (SEU) · hedeflerin gerçekleşme durumu ·
aksiyonların durumu · dönüşüm verimliliği özeti · iyileştirme fırsatları.

**3 · Serbest Rapor Oluşturucu:**
tarih aralığı + kırılım (enerji türü / varlık / bölüm) + birim + grafik
seçimi. Oluşan rapor yazdırılabilir ve dışa aktarılabilir.

#### Zorunlu davranışlar
- Her rapor **yazdırma dostu** (tek sütun, sayfa sonları doğru, koyu tema
  baskıda açığa döner).
- Her rapor **veri kalitesi notu** taşır: *"Bu dönemde 3 değer tahmin
  edilmiştir"* (İ-4).
- Her sayının kaynağına inilebilir (E-4).

#### ISO 50001 ile ilişkisi
Madde 7.5 dokümante edilmiş bilgi · madde 9.3 yönetimin gözden geçirmesi ·
denetimde sunulacak kanıtların üretildiği yer.

#### İleride eklenebilecekler
**ENVER yıllık bildirim özeti** (5627 sayılı kanun; enerji türü bazında yıllık
tüketim + TEP karşılığı + toplam TEP; portala kullanıcı kendisi girer) ·
karbon ayak izi raporu (Kapsam 1–2) · rapor şablonu özelleştirme ·
zamanlanmış rapor üretimi.

---

### 9.15 · Ekran 14 — Tanımlar

#### Amaç
Sistemin **iskeletini** kurmak ve değiştirmek. Altı sekmeli tek ekran.

#### Sekme 1 — Varlık Ağacı (K-05)
Serbest derinlikte ağaç; sürükle-bırak ile yeniden düzenlenir.
**Hiyerarşiyi değiştirmek hiçbir veriyi bozmaz** (İ-7) — bu ekranın en önemli
özelliği ve Excel'in çözemediği sorunun çözümü.
Her düğüm: ad, kod, tip, sıra, devreye giriş/çıkış tarihi (S6), aktiflik, not.

#### Sekme 2 — Ölçüm Noktaları
Düz liste; filtrelenebilir. Her nokta: kod, ad, bağlı varlık (**değiştirilebilir**),
enerji türü, birim, **rol** (6.4), toplama dahil mi, veri tipi
(ölçülen/hesaplanan/dağıtılmış/tahmini), formül, aktiflik.

> Yeni bir makine eklemek burada **tek satır** eklemektir. Excel'de bu, yeni
> sütun açmak ve bütün formülleri güncellemek demekti (S1).

#### Sekme 3 — Enerji Türleri
Elektrik, Doğalgaz, Buhar, Sıcak Su, Motorin. Ad, kod, ana birim, aktiflik.

#### Sekme 4 — Dönüşüm Katsayıları
Tarihli (İ-5): doğalgaz m³→kWh (≈10,92), buhar kg→kWh (600/860 = 0,6977),
**motorin kg→kWh (tanımsız — ilk motorin verisi girilince istenir, K-24)**.
Her kayıt: enerji türü, kaynak/hedef birim, katsayı, geçerlilik başlangıcı,
**kaynak** ve **not** (örn. *"600 kcal/kg ÷ 860 kcal/kWh"*).

> **Sistem katsayı varsaymaz** (İ-3). Katsayı yoksa dönüştürülmüş değer
> üretilmez ve nedeni yazılır.

#### Sekme 5 — EnPI Tanımları (K-06)
Ad, pay, payda, birim, ondalık hane, ana gösterge mi. Serbest sayıda.

#### Sekme 6 — Baz Çizgiler (K-19)
Ad, referans dönem, model tipi (sabit/regresyon), bağlam değişkeni,
hesaplanan katsayılar (`a`, `b`, R²), not. Birden çok tanımlanabilir.

#### Ortak kural
**Tanımlar silinmez, pasife alınır** (İ-5). Veri girilmiş bir noktanın enerji
türü veya birimi, geçmiş verinin anlamı değişeceği için ancak **açık onayla**
değiştirilebilir.

#### ISO 50001 ile ilişkisi
Madde 6.3 enerji gözden geçirmesinin kapsamı · madde 6.4 EnPI tanımları ·
madde 6.5 baz çizgi · madde 7.5 dokümante edilmiş bilgi.

#### İleride eklenebilecekler
Ağacın dışa/içe aktarımı · varlık şablonları (yeni kojen eklerken hazır
ölçüm noktası seti) · birden çok hiyerarşi görünümü (fiziksel / maliyet
merkezi) · ölçüm noktası için hedef ve eşik tanımı.

---

### 9.16 · Ekran 15 — Ayarlar ve Yedekleme

#### Amaç
Sistem ayarları ve **verinin güvenliği**. Tek HTML mimarisinde (K-09) bu ekran
veri güvenliğinin merkezidir.

#### Kullanıcının göreceği ve gireceği bilgiler

**Genel:** fabrika adı · para birimi · varsayılan enerji birimi (kWh/GJ/TEP) ·
ana EnPI · varsayılan baz çizgi · tema (açık/koyu) · ondalık hane.

**Veri ve yedekleme (5.2):**

| Alan | İçerik |
|---|---|
| Veri özeti | 8.640 değer · 96 dönem · 87 ölçüm noktası · 2018-01 → 2025-12 |
| Son yedek | "12 gün önce" — 7 günden eskiyse uyarı rengi + ikon |
| Yedek al | `.json` indirir |
| Geri yükle | Önizleme + onay; öncesinde otomatik güvenlik yedeği |
| Dosyaya doğrudan yazma | Chrome/Edge (K-11); isteğe bağlı, varsayılan kapalı |
| Bütün veriyi sil | **Çift onay** + zorunlu yedek |

**Tanılama:** program sürümü · veri şema sürümü · tarayıcı depo kullanımı.

#### Sistemin hesaplayacağı değerler
Veri istatistikleri · son yedekten bu yana geçen süre · depo doluluk oranı.

#### Zorunlu davranış
Uygulama **her açılışta** yedek yaşını denetler ve gerekiyorsa üst şeritte
uyarır. Veri kaybı riski, bu mimarinin tek ciddi riskidir (5.2) ve bu ekran
onu görünür tutar.

#### ISO 50001 ile ilişkisi
Madde 7.5.3 — dokümante edilmiş bilginin korunması, depolanması ve
kaybolmaya karşı güvence altına alınması.

#### İleride eklenebilecekler
Otomatik periyodik yedek · yedek sürüm geçmişi · çok kullanıcı geldiğinde
kullanıcı ve yetki ayarları · dil seçimi.

---

## 10. ISO 50001 ile ilişki

> **Dürüst çerçeve:** Bu platform ISO 50001 çalışmasını **destekler**; eksiksiz
> bir ISO 50001 yönetim sistemi değildir. Standardın politika, yetkinlik,
> iç denetim, uygunsuzluk gibi maddeleri kuruluşun süreçleriyle karşılanır.
> Platformun kapsadığı, standardın **ölçüm ve analiz omurgasıdır** — ve o
> omurga olmadan "enerji performansında sürekli iyileştirme" şartı
> kanıtlanamaz.

### 10.1 Madde eşlemesi

| ISO 50001:2018 maddesi | Platformdaki karşılığı | Ekran |
|---|---|---|
| **6.3** Enerji gözden geçirmesi | Enerji dengesi, ölçüm kapsamı, Pareto, tüketim analizi | 6, 7 |
| **6.3** Önemli enerji kullanımları (SEU) | Varlık ağacında işaretleme + Pareto sıralaması | 6, 7, 14 |
| **6.3** Performansı etkileyen değişkenler | Bağlam değişkenleri (üretim, ileride derece-gün), dönüşüm verimliliği | 8, 9, 14 |
| **6.4** EnPI | Kullanıcı tanımlı EnPI seti (K-06) | 8, 14 |
| **6.5** Enerji baz çizgisi (EnB) | Sabit ve regresyonlu baz çizgi, birden çok (K-19) | 8, 14 |
| **6.2** Amaçlar ve enerji hedefleri | Dört hedef türü (K-21) | 12 |
| **6.2.2** Eylem planları | Aksiyon takibi, beklenen/gerçekleşen tasarruf | 12 |
| **7.5** Dokümante edilmiş bilgi | Veri dosyası, yedekleme, izlenebilirlik (E-4) | 3, 13, 15 |
| **9.1.1** İzleme ve ölçme | Veri girişi, veri denetimi, panel | 1, 2, 4 |
| **9.1.1** Sonuçların geçerliliği | Doğrulama kuralları, veri kalitesi göstergeleri | 2, 4, 5 |
| **9.1** Analiz ve değerlendirme | Normalize EnPI, CUSUM, sapma analizi | 8 |
| **9.3** Yönetimin gözden geçirmesi | Yönetim gözden geçirme raporu (K-20) | 13 |
| **10** İyileştirme | Dönüşüm verimliliği bulguları → aksiyon | 9, 12 |

### 10.2 Platformun ISO 50001'e asıl katkısı

Standardın en zor kanıtlanan şartı şudur: *enerji performansı iyileşti mi?*

Çoğu kuruluş bunu **ham EnPI** ile cevaplamaya çalışır ve tökezler; çünkü ham
EnPI üretim düştüğünde kendiliğinden kötüleşir. 8.8'deki gerçek vaka bunu
gösteriyor: ham EnPI %16,5 kötüleşme diyor, gerçek kötüleşme %10,7.

Platformun sunduğu kanıt zinciri:

```
EnPI          →  bir şey değişti
Baz çizgi     →  neye göre değişti
Normalize EnPI→  gerçekte ne kadar değişti
CUSUM         →  ne zaman değişti
Verimlilik    →  neden değişti
Fiyat/hacim   →  parasal karşılığı ne
Aksiyon       →  ne yapılıyor
```

Denetçinin sorduğu her soru bu zincirde bir halkadır ve her halka ham veriye
kadar açılabilir (E-4).

### 10.3 Platformun kapsamadıkları

Enerji politikası · organizasyon ve yetkinlik · iç denetim · uygunsuzluk ve
düzeltici faaliyet · tedarik ve tasarım şartları (md. 8.2, 8.3) · yasal
yükümlülük takibi. Bunlar kuruluşun kendi süreçleridir; platform yalnızca
bunlara **veri ve kanıt** üretir.

---

## 11. Açık sorular

### 11.1 Karara bağlananlar

| # | Soru | Sonuç |
|---|---|---|
| A-01 | Proje nerede yaşayacak? | **Kapandı** — K-09: tek HTML dosyası |
| A-02 | Maliyet nasıl oluşacak? | **Kapandı** — K-12: fatura tutarı elle girilir |
| A-03 | Elektrik TL mahsup öncesi mi sonrası mı? | **Kapandı** — K-13: mahsup öncesi brüt |
| A-04 | Veri girişi ekranı biçimi | **Kapandı** — K-14: dört yöntem birden |
| A-09 | Ekran listesi | **Kapandı** — K-22: 15 ekran onaylandı |
| A-07 | Motorin ileride kullanılacak mı? | **Kapandı** — K-24: evet; toplam enerjiye ve maliyete dahil edildi |

### 11.2 Açık kalanlar

Bunlar **kodlamayı engellemez**; ilk sürüm makul varsayımlarla çalışır,
cevap gelince tanım ekranından değiştirilir.

| # | Soru | Şimdilik varsayım | Neden önemli |
|---|---|---|---|
| **A-05** | İstasyon–makine tutarsızlığı (S3, **S13**) neden kaynaklanıyor? 2025'te İstasyon 1'deki 14,4 GWh gaz hangi ekipmanda yakıldı? | Fark "ölçülmeyen / atanmamış" olarak gösterilir; ekipman verimi %100'ü aşarsa karşılaştırmadan çıkarılır | Ölçüm kapsamı yorumu ve **bütün kazan verimleri** buna bağlı |
| **A-06** | Hat çekirdek dağıtım oranları (0,34/0,12/0,32/0,22) sabit mi, dönemsel mi? | Sabit; `veri_tipi = dagitilmis` olarak işaretli | Hat bazlı EnPI hesaplanacaksa kritik |
| **A-08** | Buhar entalpi varsayımı **2025'te 600'den 560 kcal/kg'a düşürülmüş (S12)** — bu bilinçli bir düzeltme mi, hata mı? Hangisi doğru? | İkisi de tarihli katsayı olarak tanımlı: 2018-01'den 0,697674 · 2025-01'den 0,651163 kWh/kg | Kazan ve kojen verimini doğrudan etkiler — türbinin 6,9 puanlık düşüşünün **1,7 puanı** bu varsayımdan gelir |
| **A-12** | Motorin kg → kWh dönüşüm katsayısı ne olacak? | Tanımsız bırakılır; ilk motorin verisi girildiğinde sistem ister (K-24, 6.6) | Sistem katsayı varsaymaz (İ-3). Dizel için tipik değer ~11,9 kWh/kg'dır ama ölçüm bazına ve yakıt özelliğine göre değişir; kullanıcı kendi kaynağıyla tanımlar |
| **A-10** | Ekran 14'teki başlangıç varlık ağacı nasıl kurulsun? | Excel'in istasyon–makine yapısı temel alınır | K-16 gömülü tanımların içeriği |
| **A-11** | GES'in TL değeri mahsup ve satış olarak ayrıştırılabiliyor mu? Excel'de tek sütun var. | Tek kalem (`GES_TOPLAM_TL`); ayrıştırma isteğe bağlı | Mahsubun faturaya etkisi ile satış gelirinin ayrı izlenip izlenemeyeceğini belirler (6.5) |

---

## 12. Geliştirme yol haritası

Kodlama bu sırayla yapılır. Her faz **kendi başına çalışır bir bütündür**;
yarıda kalsa bile ortada kullanılabilir bir program olur.

### Faz 1 — Çekirdek (programın ayakta durması)

| Adım | İçerik | Biten ne demek |
|---|---|---|
| 1.1 | İskelet: tek HTML, menü, tema, yönlendirme | Ekranlar arası geçiş çalışıyor |
| 1.2 | Veri katmanı: IndexedDB + `.json` dışa/içe aktarma (5.2) | Veri kaydediliyor, yedek alınıp geri yükleniyor |
| 1.3 | **Ekran 14 — Tanımlar** (varlık ağacı, ölçüm noktaları, türler, katsayılar) | Sistem iskeleti kurulabiliyor |
| 1.4 | **Ekran 15 — Ayarlar ve Yedekleme** | Veri güvenliği yerinde |
| 1.5 | Hesap çekirdeği (8.1): toplamlar, hiyerarşi, ortak birim | Sayılar üretiliyor |
| 1.6 | **Hesaplanan değerler katmanı** (K-23): açılışta ve her değişimde yeniden üretim | Ekranların tek veri kaynağı hazır |

### Faz 2 — Veri (Excel'den kurtulma)

| Adım | İçerik | Biten ne demek |
|---|---|---|
| 2.1 | **Ekran 2 — Veri Girişi** (dört yöntem, K-14) | Aylık veri girilebiliyor |
| 2.2 | Doğrulama kuralları (6.8) | Hatalı giriş yakalanıyor |
| 2.3 | **Ekran 3 — Veri Aktarma** (`.xlsx`, K-15) | 96 aylık geçmiş içeri alınabiliyor |
| 2.4 | **Ekran 4 — Veri Denetimi** | Veri sağlığı görülebiliyor |
| 2.5 | **Ekran 5 — Hesaplanan Değerler** + Excel/CSV dışa aktarma | Hesap camdan kutu; sonuçlar dışarı alınabiliyor |

> **Faz 2 sonunda Excel'e ihtiyaç kalmaz.** Bu, projenin asıl eşiğidir.

### Faz 3 — Görme (veri anlam kazanır)

| Adım | İçerik |
|---|---|
| 3.1 | SVG grafik motoru (5.7): sütun, çizgi, yığılmış, ısı haritası, dağılım |
| 3.2 | **Ekran 1 — Gösterge Paneli** |
| 3.3 | **Ekran 7 — Tüketim Analizi** |
| 3.4 | **Ekran 6 — Enerji Dengesi** (Sankey) |

### Faz 4 — Anlama (ISO 50001'in ölçüm motoru) ✔ bitti

| Adım | İçerik | Durum |
|---|---|---|
| 4.1 | Baz çizgi ve regresyon (8.3), R² uyarıları | ✔ |
| 4.2 | **Ekran 8 — Performans**: normalize EnPI, CUSUM | ✔ |
| 4.3 | **Ekran 9 — Dönüşüm Verimliliği** | ✔ · S12 ve S13'ü bulan ekran |
| 4.4 | **Ekran 10 — Maliyet**: fiyat/hacim ayrıştırması (8.7) | ✔ |
| 4.5 | **Ekran 11 — GES** | ✔ |

### Faz 5 — Yönetme ✔ bitti

| Adım | İçerik | Durum |
|---|---|---|
| 5.1 | **Ekran 12 — Hedefler ve Aksiyonlar** | ✔ · dört hedef türü, ölçer, gecikme takibi |
| 5.2 | **Ekran 13 — Raporlar** (K-20) | ✔ · üç rapor, yazdırma dostu, veri kalitesi notlu |
| 5.3 | İzlenebilirlik (E-4): her sayıdan ham veriye iniş | ✔ · `?` düğmesi + köken ağacı |

> **Not:** Faz 1–2 bittiğinde elinizde Excel'in yerini alan çalışan bir program
> olur. Faz 3–4, Excel'in hiç yapamadığını yapar. Faz 5, ISO 50001 dosyasını
> besler. Fazlar arasında durup değerlendirmek mümkündür.

---

## 13. Kabul kriterleri ve doğrulama

> Yazılımın **doğru** çalıştığını nasıl bileceğiz? Excel'in bilinen sonuçlarını
> birebir üretmesiyle. Aşağıdaki değerler kaynak veriden hesaplanmıştır ve
> **sınav sorularıdır**: Excel içe aktarıldıktan sonra program bu sayıları
> tam olarak üretmelidir.

### 13.1 Aktarım kontrolü

| Kontrol | Beklenen |
|---|---|
| Enerji verisi olan dönem | **96** (2018-01 → 2025-12) |
| Kayıt bulunan toplam dönem | **99** (GES verisi 2026-03'e uzanır) |
| İlk dönem | 2018 Ocak |
| Son dönem (enerji) | 2025 Aralık |
| Son dönem (herhangi bir kayıt) | 2026 Mart |
| Aktarılmayan sütunlar | BX–DD (K-02) |
| Hat-4 başlığı | "Hat-3" değil **"Hat-4"** (S7) |
| Motorin noktaları | **Tanımlı ve toplamlara dahil** (K-24); veri boş, yıllık toplamlar **değişmiyor** |
| Reddedilen değer | **7** — 6 negatif doğalgaz (S11) + 1 metin hücre (S10) |
| Otomatik eşleşen sütun | **55** (K-15) |
| Aktarılan ham değer | **4.541** |

### 13.2 Altın sayılar — yıllık toplamlar

Program içe aktarma sonrası bu tabloyu **hesaplayarak** üretmelidir
(hiçbiri veri dosyasında saklı değildir — İ-1):

| Yıl | Şebeke elektriği (kWh) | Doğalgaz (kWh) | **Toplam enerji (kWh)** | Üretim (kg) | **EnPI** | Maliyet (brüt, TL) |
|---|---:|---:|---:|---:|---:|---:|
| 2018 | 15.919.712 | 128.362.622 | **144.282.334** | 104.980.360 | **1,3744** | 18.090.355 |
| 2019 | 4.388.200 | 151.249.409 | **155.637.609** | 101.839.334 | **1,5283** | 24.838.813 |
| 2020 | 6.559.460 | 147.423.923 | **153.983.384** | 101.758.697 | **1,5132** | 25.453.964 |
| 2021 | 12.425.346 | 127.572.551 | **139.997.897** | 98.148.940 | **1,4264** | 41.002.718 |
| 2022 | 24.482.137 | 99.649.227 | **124.131.364** | 107.258.078 | **1,1573** | 185.374.960 |
| 2023 | 18.097.125 | 111.279.600 | **129.376.725** | 111.976.787 | **1,1554** | 167.503.412 |
| 2024 | 19.248.726 | 111.987.169 | **131.235.894** | 111.897.453 ⚠ | **1,1728** ⚠ | 180.794.462 |
| 2025 | 17.199.431 | 120.168.406 | **137.367.837** | 100.503.911 | **1,3668** | 220.905.805 |

**8 yıl toplamı:** enerji **1.116.013.044 kWh** · üretim **834.377.214 kg** ⚠ ·
brüt maliyet **863.964.489 TL** · **net maliyet 838.241.020 TL**

> **Maliyet sütunu brüttür.** Programın ürettiği `Toplam Maliyet`, tanım gereği
> **GES mahsubu düşülmüş nettir** (K-13, K-24, 6.5) — 9.11'deki maliyet özeti de
> bu sayıyı gösterir. GES geliri yalnızca 2025'te bulunduğu için iki sütun
> yalnız o yılda ayrışır:
>
> | 2025 | TL |
> |---|---:|
> | Brüt (fatura toplamı) | 220.905.805 |
> | − GES mahsubu + satışı | −25.723.469 |
> | **= Net toplam maliyet** | **195.182.336** |
>
> Kabul testi her iki sayıyı da ayrı ayrı doğrular.

> ⚠ **2024 üretim ve EnPI değerleri kaynak veri hatası içerir (S10, bkz. 2.5).**
> Program bu iki sayıyı **kasten üretmez**: 2024 Ağustos'un toplam üretimi
> hesaplanamaz olduğu için yıllık toplam **107.911.108 kg** çıkar. Bu bir sapma
> değil, **doğru davranıştır** — kabul testi bu değeri bekler. Kaynak hücre
> düzeltildiğinde beklenen değer de güncellenmelidir.

### 13.3 Nokta kontrolü — tek ay

**2024 Haziran:**

| Değer | Beklenen |
|---|---|
| Şebeke elektriği | 1.789.176 kWh |
| Toplam doğalgaz | 9.010.928 kWh |
| **Toplam enerji** | **10.800.103 kWh** |
| Toplam üretim | 8.868.323 kg |
| **EnPI** | **1,2178 kWh/kg** |

### 13.4 Hesap motoru kontrolleri

| Hesap | Beklenen sonuç |
|---|---|
| Baz çizgi 2022–2024 regresyonu (8.3) | `a = 0,5025` · `b = 6.021.966` · `R² = 0,43` · **35 nokta** ⚠ |
| Normalize EnPI 2025 (8.4) | **1,119** |
| CUSUM 2025 yıl sonu (8.5) | **+14.605.848 kWh** |
| CUSUM işaret değiştirdiği ay | **Şubat 2025** |
| Türbin toplam verimi 2024 / 2025 (8.6) | **%57,2 / %50,3** |
| Elektrik fiyat etkisi 2024→2025 (8.7) | **+10.682.663 TL** |
| Elektrik hacim etkisi 2024→2025 | **−5.500.767 TL** |
| Doğalgaz hacim etkisi 2024→2025 | **+13.475.761 TL** |

> ⚠ **Baz çizgi satırı 2024 Ağustos'suz kurulur.** O ayın toplam üretimi bozuk
> hücre yüzünden üretilemediği için (S10, bkz. 2.5) regresyon 36 değil **35**
> nokta kullanır. Excel'in kendi `Toplam Üretim` sütunuyla aynı regresyon
> `a = 0,4254 · b = 6.774.643 · R² = 0,40` verir; aradaki fark, tek bir bozuk
> hücrenin baz çizgiyi ne kadar kaydırdığıdır. Hücre düzeltildiğinde bu satırın
> beklenen değerleri de güncellenmelidir.

### 13.5 Davranış kontrolleri

| Senaryo | Beklenen davranış |
|---|---|
| Dönüşüm katsayısı olmayan tür için ortak birim isteniyor | Sonuç **üretilmez**, nedeni yazılır (İ-3) |
| Negatif değer giriliyor | **Engellenir** (6.8) |
| Alt toplam üst toplamı aşıyor | Kaydedilir ama **uyarı gösterilir** (S3) |
| Doğalgaz kWh/m³ oranı 10,92'den saptı | **Uyarı** (K-04) |
| Regresyonda 12'den az veri noktası | Regresyon **kurulmaz** (8.3) |
| R² < 0,5 | Model kurulur, **açık uyarı** gösterilir |
| Tarayıcı deposu boş, yedek yok | Boş durum ekranı **ne yapılacağını anlatır** (E-5) |
| Bir ham değer değiştirildi | Hesaplanan değerler katmanı **anında** yeniden üretilir; Ekran 5 ve bütün ekranlar yeni sayıyı gösterir (K-23) |
| Katsayı değiştirildi | Katmanın tamamı yeniden üretilir; hiçbir ekranda eski değer kalmaz |
| Eski bir yedek geri yüklendi | Katman **sıfırdan üretilir**; yedekteki hesaplanmış değer (varsa) yok sayılır (K-23) |
| Yedek 7 günden eski | Üst şeritte **uyarı** (5.2) |
| İçe aktarmada 1 satır hatalı | **Geçerli değerlerin hepsi tek işlemde yazılır**, hatalı hücreler yazılmaz ve satır satır listelenir (9.4: "ya bütün geçerli satırlar ya hiçbiri") |

### 13.6 Bu bölümün kullanımı

Her faz sonunda ilgili kontroller çalıştırılır: `betikler/kabul13.py` bu
bölümün **her satırını** makineyle doğrular.

Bir sayı tutmadığında sırayla şuna bakılır:

1. **Hesabın kendisi** — formül, birim, katsayı.
2. **Aktarım** — sütun eşlemesi, reddedilen hücreler.
3. **Beklenen sayının hangi varsayımla üretildiği.**

Üçüncü madde, bu belge yazılırken beklenenden daha sık devreye girdi. Bölüm
13'ün sayıları tasarım aşamasında **Excel'in kendi sütunlarından** elle
hesaplandı; program ise kendi kurallarını uyguluyor. İkisi ayrıldığında
**hangisinin neyi ölçtüğü** sorulmalıdır:

| Tutmayan sayı | Neden | Sonuç |
|---|---|---|
| 2024 üretim ve EnPI | Excel'in `SUM`'ı bozuk hücreyi sessizce atlıyor (S10); program eksik üretimi doğru sayı gibi kullanmıyor (İ-3) | **Program haklı**, beklenen değer düzeltildi |
| Baz çizgi `a`, `b`, `R²` | Aynı nedenle: regresyon 36 değil 35 nokta kullanıyor | **Program haklı**, 8.8 ve 13.4 düzeltildi |
| Aktarılan ham değer | Beklenen sayı, reddedilen 7 hücreyi iki kez düşmüş | **Program haklı**, 4.534 → **4.541** |
| 2025 maliyeti | 13.2'nin sütunu **brüt**, programın `Toplam Maliyet`'i tanım gereği **net** (K-13, K-24) | **İkisi de doğru, farklı şeyi ölçüyor** — tablo brüt olarak etiketlendi, net ayrıca yazıldı |

Yani kural şudur: **tutmayan sayı bir hata değil, bir sorudur.** Cevabı
bulunmadan hiçbiri düzeltilmez ve bulunan cevap buraya yazılır.

---

## Değişiklik geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 0.1 | 2026-09-17 | İlk taslak. Excel analizi, temel ilkeler, K-01…K-08 kararları, veri modeli çerçevesi, enerji/mali denge ayrımı. |
| 0.9 | 2026-09-17 | **Faz 3 kodlandı.** SVG grafik motoru (kütüphanesiz), Gösterge Paneli, Tüketim Analizi, Enerji Dengesi. Ölçüm kapsamının iki ekranda farklı hesaplandığı fark edildi ve tek tanıma indirildi (İ-2): `hesap.js › elektrikKapsami()`; payda şebeke + kojenerasyon elektriğidir. Varsayılan dönem aralıkları veri aralığının sonuna değil, enerji verisinin bulunduğu son döneme göre seçiliyor (GES kayıtları 2026-03'e uzandığı için). |
| 0.8 | 2026-09-17 | **Faz 2 kodlandı.** Gerçek Excel aktarımında kaynak veride iki hata bulundu ve belgeye işlendi: **S10** (2024 Ağustos çikolata hücresi metin — Excel sessizce atlamış, 2024 EnPI'si yanlış) ve **S11** (6 negatif doğalgaz değeri). Yeni bölüm 2.5. Kabul kriterlerindeki 2024 üretim beklentisi, programın doğru davranışına göre düzeltildi (13.1, 13.2). |
| 0.7 | 2026-09-17 | **Bölüm bölüm gözden geçirme tamamlandı.** D-01: 2.4'teki Bölüm 7 atfı Bölüm 8 olarak düzeltildi. **D-02 (K-24): motorin toplam enerjiye ve toplam maliyete dahil edildi** ve kural sabit listeden **rol filtresine** genelleştirildi; eksik değer/katsayı kenar durum kuralı yazıldı; A-07 kapandı, A-12 açıldı. D-03: 6.5'te tablo dışına düşmüş satır tabloya alındı. D-04: geçersiz `(S-2.3)` atfı düzeltildi. |
| 1.0 | 2026-09-17 | **Faz 4 kodlandı.** Ekran 9 (Dönüşüm Verimliliği), Ekran 10 (Maliyet, fiyat/hacim ayrıştırması) ve Ekran 11 (GES) yazıldı. Gerçek veride iki yeni bulgu: **S12** (buhar entalpi varsayımı 2025'te 600 → 560 kcal/kg) ve **S13** (2025 kazan verimleri %100'ü aşıyor, gazın %12,9'u ekipmana atanmamış). Bunlara karşılık **K-25** (imkânsız verim performans sayılmaz), **K-26** (yıllar arası karşılaştırma birleşik yüzdeyle değil, ekipman bazında kaçınılabilir yakıtla) ve **K-27** (fatura ↔ tüketim bağı) kararları eklendi. A-05 ve A-08 somutlaştırıldı. 8.8 vakası S12/S13 çekinceleriyle güncellendi. 80 kabul sınaması geçiyor.
| 1.1 | 2026-09-17 | **Faz 5 kodlandı — yol haritası tamamlandı.** Ekran 12 (Hedefler ve Aksiyonlar), Ekran 13 (Raporlar: aylık · yönetim gözden geçirme · serbest) ve izlenebilirlik (E-4) yazıldı; **K-28** eklendi, `hedef` ve `aksiyon` şemaları 6.3'e girdi. **Düzeltme:** 8.8 ve 13.4'teki baz çizgi sayıları, Excel'in kendi `Toplam Üretim` sütunuyla kurulmuş 36 noktalı bir regresyondan geliyordu; program S10 yüzünden 2024 Ağustos'u kullanamadığı için doğru model **35 nokta** üzerinden `a = 0,5025 · b = 6.021.966 · R² = 0,43`tür. Buna bağlı normalize EnPI (1,107 → **1,119**), CUSUM yıl sonu (13,3 → **14,6 milyon kWh**) ve türbin payı (%42 → **%38**) güncellendi. Bulgunun yönü değişmedi. 218 kabul sınaması geçiyor.
| 1.2 | 2026-09-18 | **Bölüm 13'ün tamamı makineyle doğrulandı** (`betikler/kabul13.py`, 96 kontrol; toplam 314 kontrol geçiyor). Doğrulama üç belge hatası buldu: (1) **13.1** aktarılan ham değer 4.534 değil **4.541** — beklenen sayı reddedilen 7 hücreyi iki kez düşmüş; bağımsız bir XLSX sayımıyla teyit edildi. (2) **13.2**'nin maliyet sütunu **brüttür**; programın `Toplam Maliyet`'i tanım gereği GES mahsubu düşülmüş **nettir** (K-13, K-24) — sütun etiketlendi, 2025 için net 195.182.336 TL ve 8 yıl net toplamı 838.241.020 TL eklendi, 8 yıl üretim toplamı S10'a göre 834.377.214 kg olarak düzeltildi. (3) **13.5**'teki "1 satır hatalıysa hiçbiri yazılmaz" satırı 9.4'ün "ya bütün geçerli satırlar ya hiçbiri" kuralıyla çelişiyordu; 9.4 esas alınarak düzeltildi. 13.1'e otomatik eşleşen sütun sayısı ve dönem ayrımı (96 enerji / 99 kayıt) eklendi. **13.6 yeniden yazıldı:** tutmayan sayı bir hata değil, bir sorudur.
| 0.6 | 2026-09-17 | **K-23: hesaplanan değerler katmanı.** Hesaplanan bütün değerler ayrı bir katmanda toplanır; ekranlar veriyi buradan çeker; katman açılışta ve her veri değişiminde baştan üretilir. Kullanıcıya görünür ve dışa aktarılabilir hale getirildi: **yeni Ekran 5 — Hesaplanan Değerler**. İ-1 ilkesi buna göre yeniden yazıldı. Ekranlar 5–14 → 6–15 olarak yeniden numaralandı. Katmanın yedek dosyasına yazılmama gerekçesi 5.3'e eklendi. |
| 0.5 | 2026-09-17 | **Gözden geçirme düzeltmeleri.** Bayat atıf giderildi; `price` tablosunun ilk sürümde kullanılmadığı netleşti; düşük R²'nin sabit yük tahminini de kapsadığı belirtildi; GES TL'sinin ayrıştırılamama ihtimali modellendi (A-11). **Yeni: Bölüm 12 geliştirme yol haritası** (5 faz) ve **Bölüm 13 kabul kriterleri** — Excel'den hesaplanmış altın sayılar, hesap motoru ve davranış kontrolleri. |
| 0.4 | 2026-09-17 | **Analiz motoru (8) yazıldı**: EnPI, iki seviyeli baz çizgi, normalize EnPI, CUSUM, dönüşüm verimliliği, fiyat/hacim ayrıştırması. **Gerçek veriyle doğrulama (8.8)**: 2025 bozulmasının kaynağı bulundu. **Ekran 5–14 tasarlandı.** K-19…K-22 kararları. |
| 0.3 | 2026-09-17 | **Görsel dil ve grafik standartları (5.7)**: renk paleti, yasaklar (çift eksen dahil), zorunlu davranışlar, grafik tipleri. **Ekranlar bölümü başladı (9)**: tasarım ilkeleri, navigasyon haritası (14 ekran), Ekran 1–4 tam tasarımı (Gösterge Paneli, Veri Girişi, Veri Aktarma, Veri Denetimi). |
| 0.2 | 2026-09-17 | **Teknik mimari belirlendi (Bölüm 5).** K-09…K-18 kararları: tek HTML dosyası, iki katmanlı veri saklama, Chrome/Edge, fatura tutarı girişi, GES mahsubunun ayrı kalem olması, dört yöntemli veri girişi, gömülü `.xlsx` okuyucu, saf SVG grafikler. Maliyet ve GES mahsup modeli (6.4b). A-01…A-04 kapatıldı. |
