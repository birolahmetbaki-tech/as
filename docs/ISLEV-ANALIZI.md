# Enerji İzleme ve SCADA Sistemleri — İşlev Analizi ve Tasarım Rehberi

Bu belge, piyasadaki enerji izleme / enerji yönetimi / SCADA ürünlerinin
**hangi faaliyetleri gerçekleştirdiğini** tespit eder, bu faaliyetleri
**işlev envanteri** hâlinde listeler ve **bizim programımızda hangilerinin,
nasıl tasarlanacağına** dair karar ve yöntem önerisi sunar.

Hazırlanma tarihi: 2026-09-17

---

## 0. Kapsam, yöntem ve kaynak güvenilirliği

### 0.1 Erişilemeyen kaynaklar (önemli kısıt)

Bu oturumun ağ çıkış politikası, istenen üç adresin **doğrudan okunmasına
izin vermedi**. Aşağıdaki alan adları HTTP 403 ile engellendi:

| Adres | Durum |
|---|---|
| `https://enerji.pro/` | Egress politikası: **engelli (403)** |
| `https://loggma.com/enerify/` | Egress politikası: **engelli (403)** |
| `https://loggma.com/solarify/` | Egress politikası: **engelli (403)** |
| `https://solarify.io/tr/` | Egress politikası: **engelli (403)** |
| `https://www.enverio.com.tr/...` | Egress politikası: **engelli (403)** |
| `https://www.idasotomasyon.com/...` | Egress politikası: **engelli (403)** |
| `https://energy.argekip.com/` | Egress politikası: **engelli (403)** |

Bu nedenle bu üç ürüne dair bulgular, **arama motoru üzerinden elde edilen
özetler, ürün blogları, basın haberleri ve bayi/entegratör sayfalarından**
derlendi. Özellik listeleri pazarlama diliyle yazılmış kaynaklara dayandığı
için:

- **Doğrulanmış sayılmamalıdır.** Satın alma veya rekabet kararı verilecekse
  ürünlerin demo/teknik dokümanı üzerinden teyit edilmelidir.
- Ürünlerin **var olduğu iddia edilen** işlevleri listelenmiştir; bu işlevlerin
  olgunluk seviyesi bu belgeden çıkarılamaz.

Buna karşılık **işlev analizi** bölümü (Bölüm 2) yalnızca bu üç üründen
değil, sektörün geneli, uluslararası referans ürünler ve ilgili
standartlardan beslendiği için sağlamdır ve tasarım kararlarına temel
oluşturabilir.

### 0.2 Kullanılan kaynak sınıfları

1. **Türk pazarındaki ürünler**: Enerji.pro (Enverio), Loggma Enerify,
   Loggma Solarify, Entes SmartPower, EnerIP, İda Otomasyon, Fultek,
   Teleteknik, ARGEKİP, CTS, Witteh.
2. **Uluslararası referans ürün**: Schneider Electric EcoStruxure Power
   Monitoring Expert (PME) — sektörün fiilî işlev standardı sayılabilir.
3. **Standartlar**: ISO 50001 / ISO 50006 / ISO 50015, IPMVP, EN 50160,
   IEC 61000-4-30, IEC 61724-1, GHG Protocol, ISO 14064.
4. **Mevzuat**: 5627 sayılı Enerji Verimliliği Kanunu ve ENVER Portal
   yükümlülükleri, EPDK reaktif enerji tarifesi.
5. **Mimari/teknik literatür**: MDM & VEE (Validation-Estimation-Editing),
   OPC UA / MQTT Sparkplug / Modbus veri toplama desenleri, zaman serisi
   veritabanları, NILM ve anomali tespiti üzerine akademik çalışmalar.

---

## 1. İncelenen sistemler ve tespit edilen faaliyetleri

### 1.1 Enerji.pro (Enverio) — Kurumsal enerji yönetim yazılımı

Konumlanma: Çok tesisli işletmeler için **enerji yönetimi ve ISO 50001
uyum** platformu. SCADA'nın kendisi değil, SCADA/PLC/ERP **üstünde** çalışan
bir analiz ve raporlama katmanı.

Tespit edilen faaliyetler:

- Tesislerdeki **tüm sayaçlardan gerçek zamanlı veri toplama** — elektrik,
  doğal gaz, su, buhar ve sensörler; çok kaynaklı otomatik toplama.
- **SCADA, PLC ve ERP entegrasyonu** (SAP, Oracle adı geçiyor); farklı
  sistemlerden gelen veriyi tek platformda birleştirme.
- **Modbus TCP/IP** üzerinden enerji analizörü okuma (ürün blogunda adım adım
  anlatılıyor) — yani saha protokolü desteği ürünün kendi kapsamında.
- **EnPI (enerji performans göstergesi) tanımlama ve otomatik hesaplama** —
  "üretim birimi başına tüketilen enerji" gibi özel göstergeler
  kurgulanabiliyor.
- **Önemli enerji kullanım alanlarının (SEU) tespiti** — yoğun tüketen makine,
  hat veya bölgenin belirlenip EnPI'ye bağlanması.
- **Özelleştirilebilir raporlama**: haftalık / aylık / yıllık EnPI raporlarının
  üretilip ilgili birimlere **otomatik e-posta ile gönderilmesi**.
- **Eşik aşımı alarmı ve uyarı gönderimi** — belirlenen sınır aşıldığında
  bildirim.
- **Anormal tüketim örüntüsü tespiti** — kaçak, arızalı ekipman ve verimsiz
  süreç tespiti.
- **Karbon ayak izi raporlaması** — tüketimi GHG Protokolü'ne göre otomatik
  emisyona çevirme.
- **Hedef takibi ve yatırım geri dönüşü** raporlaması.

### 1.2 Loggma Enerify — Portföy enerji izleme platformu

Konumlanma: Enerji **tüketen ve üreten** noktaları tek portföyde toplayan,
Solarify altyapısı üzerine kurulu platform. Endüstriyel tesis + santral
karışık portföyleri hedefliyor.

Tespit edilen faaliyetler:

- **Yüksek çözünürlüklü izleme** — kısa periyotlu veri toplama; "tüketimde
  minimum kayıp, üretimde maksimum kazanç" iddiası bu çözünürlüğe dayanıyor.
- **Portföy görünümü** — birden çok tesis/santralin tek platformda toplanması
  ve birlikte analizi.
- **Tüketim haritası (renkli ısı haritası)** — hangi cihazın ne zaman ne
  kadar tükettiğinin görsel karakterizasyonu; tüketim örüntüsünün
  görselleştirilmesi.
- **Formül/terim altyapılı analiz grafikleri** — kullanıcının kendi
  formülünü tanımlayabildiği, **4 eksene kadar** seri barındırabilen grafik
  motoru. (İşlev olarak en dikkat çekici özelliklerden biri.)
- **İş Emri Yönetimi (WOM)** — sahada yapılan tüm faaliyetlerin kaydı, bakım
  maliyeti analizi, **SLA takibi**.
- **Görev yönetimi ve kontrol listeleri** — periyodik bakım/onarım için
  özelleştirilmiş checklist'ler.
- **Otomatik iş emri üretimi** — arızanın hızlı çözülmesi için alarmın iş
  emrine dönüşmesi.
- **Yapay zekâ ile kayıp hesabı** — kesintilerden kaynaklanan **tahmini
  üretim/enerji kaybının** hesaplanması ve metriklerin buna göre yeniden
  hesaplanması.
- **Akıllı metrikler** — üretim ve tüketim analizi için hazır gösterge seti.
- **Mobil uygulama** (iOS/Android).

### 1.3 Loggma Solarify — GES performans izleme platformu

Konumlanma: Güneş enerjisi santralleri için **yapay zekâ tabanlı performans
izleme ve O&M** platformu; klasik inverter izleme yazılımlarından "performans
analitiği + iş yönetimi" ile ayrışmayı hedefliyor.

Tespit edilen faaliyetler:

- **7/24 uzaktan veri akışı** ve anlık izleme.
- **Performans Oranı (PR) hesabı** — santral bazında özet gösterge.
- **Emre amadelik (availability) hesabı** — zaman ağırlıklı yöntem; modülün
  incelenen aralıkta çalışıp çalışmadığına bakılır, **hangi performansla
  ürettiğine bakılmaz**. PR ve kapasite faktöründen bilinçli olarak ayrılan
  bir metrik.
- **Işınım (irradiance) ölçümü** ve üretimle ilişkilendirme.
- **Üretim haritası** — inverter ve **string** bazında üretim performansının
  renk grafiğiyle gösterimi; kötü performans gösteren string'in görsel tespiti.
- **Inverter detay sayfası** — bir inverterin tüm grafiklerinin tek sayfada
  toplanması.
- **Cihaz bazında kullanıcı tanımlı alarm kuralları** — "sahadaki her cihaz
  için kendi belirleyebileceğiniz kurallar".
- **Yapay zekâ ile bozunum (degradation) tahmini** — ~%2 hata payı iddiası;
  amacı **yanlış performans alarmlarını (false positive) azaltmak**.
- **İş emri yönetimi** — O&M operasyonlarının tek sayfadan yönetimi.
- **Yedek parça yönetimi**.
- **Aylık akıllı raporlama** ve tamamlanan operasyonların analizi.
- **Santral kontrolü** — yalnız izleme değil, uzaktan müdahale iddiası.
- **Mobil uygulama** (iOS/Android) + web.

### 1.4 Klasik enerji SCADA ürünleri (İda, Fultek, Teleteknik, ARGEKİP, Entes SmartPower, Cedetaş)

Konumlanma: Fabrika içi **elektriksel izleme ve otomasyon**. Ürün grubu
"yazılım" değil "sistem" satar: analizör + haberleşme + yazılım.

Tespit edilen faaliyetler:

- **Enerji analizöründen Modbus RTU (RS485) / Modbus TCP-IP ile okuma**;
  analizör başına **100'ün üzerinde parametre** (gerilim, akım, güç,
  frekans, harmonik...).
- **Belirlenen periyotta otomatik kayıt** (data logging / historian).
- **Lokasyon bazlı, tarih-saat aralıklı geçmişe dönük raporlama**,
  karşılaştırma ve analiz.
- **Grafik analiz + Text/Excel'e otomatik aktarım**.
- **Reaktif enerji izleme** — endüktif/kapasitif oranların anlık takibi,
  **yasal sınıra yaklaşıldığında personele alarm**; reaktif cezanın
  kompanzasyon arızasından doğduğu tespiti.
- **Güç kalitesi ölçümü ve raporlaması** — EN 50160 uyumlu olay kaydı,
  IEC 61000-4-30 Class A/S analizörlerle harmonik, THD, gerilim çökmesi
  (sag/dip), yükselme (swell), kesinti, fliker.
- **Kompanzasyon yönetimi**.
- **Mimik diyagram / tek hat şeması üzerinde canlı izleme** (SCADA HMI).
- **Puant/tarife dilimi bazlı tüketim takibi**.

### 1.5 Uluslararası referans: Schneider EcoStruxure Power Monitoring Expert

Sektörün işlev haritasını en geniş gösteren üründür; bizim "tam kapsam"
referansımız olarak kullanılabilir.

- **Güç kalitesi izleme ve analizi** — hassas ekipmanın korunması.
- **Yük tipine göre tüketim analizi** ve tesis enerji performansı.
- **Tahmin (forecasting)** — dış sıcaklık, doluluk ve diğer değişkenlere göre
  gelecek tüketimin öngörülmesi.
- **Energy Billing Module** — şube/devre seviyesinde yük ve tüketim
  raporlaması, **maliyetin tüketicilere dağıtılması (cost allocation)**,
  **gölge faturalama (shadow billing) ile tedarikçi faturasının doğrulanması**
  ve muhasebe/finans sistemlerine veri aktarımı.
- **Sanal sayaç (virtual meter)** — fiziksel sayaç ile sanal servis arasında
  grafik arayüzle modül kurgulama.
- **Açık standartlarla entegrasyon** — ODBC, OPC, XML, Modbus, Web/SOAP.
- **Bakım yönetimi** — proaktif bakım planı, varlık ve şebeke sağlığı takibi.
- **Data Quality Module (VEE)** — veri doğrulama, tahminleme, düzeltme.

### 1.6 Meter Data Management (MDM) / VEE disiplini

Ürün değil, **olgunlaşmış bir yöntem**. Bizim için en değerli bulgulardan
biri budur:

- **Validation** — her okumanın kurallara karşı denetimi: eksik aralık, sıfır
  değer, **negatif tüketim**, ani sıçrama (spike), **donmuş/sabit değer**,
  beklenen aralık dışı tüketim.
- **Estimation** — kısa boşlukların geçmiş profil veya komşu cihaz verisiyle
  doldurulması; **hangi yöntemle tahmin edildiğinin denetlenebilir kaydı**.
- **Editing** — işaretlenen istisnaların insan tarafından gözden geçirilmesi
  için kontrollü iş akışı; **her düzeltmenin tam denetim izi (audit trail)**.

Kritik ilke: **tahmin edilen değer, ölçülen değerden ayrı işaretlenir ve
raporda öyle görünür.**

---

## 2. İşlev analizi — katmanlı işlev envanteri

Aşağıdaki envanter, incelenen tüm sistemlerin faaliyetlerinin normalize
edilmiş hâlidir. Her işlev, **hangi katmanda yaşadığı** ve **hangi girdiye
bağımlı olduğu** ile birlikte verilmiştir. Bu yapı, sonraki bölümdeki
kapsam kararının zeminidir.

### Katman 0 — Saha ve veri toplama (Data Acquisition)

| # | İşlev | Açıklama |
|---|---|---|
| F0.1 | Seri/IP saha protokolü | Modbus RTU (RS485), Modbus TCP/IP |
| F0.2 | Sayaç protokolü | DLMS/COSEM, M-Bus, IEC 62056 |
| F0.3 | Endüstriyel arayüz | OPC UA, OPC DA |
| F0.4 | IIoT taşıma | MQTT, MQTT Sparkplug B |
| F0.5 | Sistem entegrasyonu | SCADA/PLC, ERP (SAP/Oracle), OSOS, dağıtım şirketi portalı |
| F0.6 | Sensör verisi | Sıcaklık, basınç, debi, ışınım (piranometre), modül sıcaklığı |
| F0.7 | Toplama periyodu yönetimi | 1 sn – 15 dk arası; yüksek çözünürlük vs. saklama maliyeti |
| F0.8 | Kenar (edge) toplayıcı | Ağ kesintisinde yerel tamponlama ve sonradan senkronizasyon |
| F0.9 | Manuel veri girişi | Sayaç endeksi, fatura, beyan; otomasyonun olmadığı noktalar |
| F0.10 | Toplu içe aktarma | Excel/CSV ile geçmiş veri yükleme |

### Katman 1 — Veri kalitesi (VEE)

| # | İşlev | Açıklama |
|---|---|---|
| F1.1 | Doğrulama kuralları | Negatif tüketim, sıfır, spike, donmuş değer, aralık dışı |
| F1.2 | Boşluk tespiti | Beklenen okuma gelmedi |
| F1.3 | Tahminleme | Geçmiş profil / komşu cihazla doldurma |
| F1.4 | Düzeltme iş akışı | İnsan onaylı istisna yönetimi |
| F1.5 | Veri kökeni etiketi | ölçüldü / tahmin edildi / elle düzeltildi |
| F1.6 | Denetim izi | Kim, ne zaman, neyi, hangi gerekçeyle değiştirdi |
| F1.7 | Sayaç sarması (rollover) | Endeksin maksimuma ulaşıp sıfırlanması |
| F1.8 | Sayaç değişimi | Eski/yeni endeks sürekliliğinin korunması |

### Katman 2 — Veri modeli ve varlık hiyerarşisi

| # | İşlev | Açıklama |
|---|---|---|
| F2.1 | Çok tesis / portföy | Şirket → tesis → bina → bölüm → hat → makine |
| F2.2 | Sayaç hiyerarşisi | Ana sayaç / alt sayaç; mükerrer sayımın önlenmesi |
| F2.3 | Sanal sayaç | Formülle türetilen sayaç: A+B−C |
| F2.4 | Çok enerji türü | Elektrik, doğal gaz, su, buhar, basınçlı hava, LPG, kömür |
| F2.5 | Ortak birim | kWh / MJ / GJ / TEP dönüşümü; yakıta göre enerji içeriği katsayısı |
| F2.6 | Zaman boyutu | Vardiya, çalışma günü, tatil, sezon takvimi |
| F2.7 | Bağlam değişkenleri | Üretim miktarı, derece-gün (HDD/CDD), çalışma saati, doluluk |
| F2.8 | Etiket/isimlendirme standardı | Ölçüm noktası adlandırma disiplini |

### Katman 3 — Hesap motoru

| # | İşlev | Açıklama |
|---|---|---|
| F3.1 | Tüketim hesabı | (endeks₂ − endeks₁) × çarpan |
| F3.2 | Dönem atama kuralı | Tüketimin hangi aya/vardiyaya yazılacağı |
| F3.3 | Yük profili | Saatlik/15 dakikalık tüketim eğrisi |
| F3.4 | Puant / tarife dilimi ayrımı | Gündüz–puant–gece dilimlerine göre kırılım |
| F3.5 | Talep (demand) hesabı | 15 dk kayan ortalama maksimum güç |
| F3.6 | EnPI | Enerji / üretim; enerji / m²; enerji / adet |
| F3.7 | Normalize EnPI | Bağlam değişkenine göre düzeltilmiş gösterge |
| F3.8 | Bölüm/maliyet dağıtımı | Ölçülen + ölçülmeyen (dağıtılmamış) payın ayrılması |
| F3.9 | Ortak birimde toplam | Farklı enerji türlerinin tek birimde toplanması |
| F3.10 | Baz çizgi (baseline) | Referans dönem tüketimi |

### Katman 4 — İzleme ve görselleştirme

| # | İşlev | Açıklama |
|---|---|---|
| F4.1 | Canlı gösterge paneli | Anlık güç, günlük tüketim, maliyet |
| F4.2 | Tek hat / mimik şema | SCADA HMI; şalt durumu, canlı değer |
| F4.3 | Trend grafiği | Çok seri, çok eksenli (Enerify: 4 eksen) |
| F4.4 | Isı haritası / tüketim haritası | Gün × saat matrisi; örüntü görselleştirme |
| F4.5 | Karşılaştırma | Dönem–dönem, tesis–tesis, hat–hat, benchmark |
| F4.6 | Sankey / akış diyagramı | Enerjinin nereye gittiği |
| F4.7 | Pareto | En çok tüketen ilk N nokta |
| F4.8 | Kullanıcı tanımlı formül/gösterge | Terim altyapısı ile hesaplanan seri |
| F4.9 | Drill-down | Tesis → bölüm → sayaç → ham okuma |
| F4.10 | Mobil arayüz | Telefon/tablet erişimi |

### Katman 5 — Alarm ve olay yönetimi

| # | İşlev | Açıklama |
|---|---|---|
| F5.1 | Eşik alarmı | Sabit sınır aşımı |
| F5.2 | Kullanıcı tanımlı kural | Cihaz bazında serbest kural kurgusu |
| F5.3 | Haberleşme alarmı | Cihaz veri göndermiyor |
| F5.4 | Reaktif oran alarmı | Yasal sınıra yaklaşma uyarısı (ceza öncesi) |
| F5.5 | Talep (puant) alarmı | Sözleşme gücü aşımı öngörüsü |
| F5.6 | Anomali alarmı | Örüntüden sapma; sabit eşik değil |
| F5.7 | Önceliklendirme | Kritik / uyarı / bilgi |
| F5.8 | Bildirim kanalı | E-posta, SMS, mobil push |
| F5.9 | Onaylama (acknowledge) | Alarmın sahiplenilmesi |
| F5.10 | Alarm baskılama | Sel (alarm flood) ve tekrar eden alarmın bastırılması |
| F5.11 | Yanlış alarm azaltma | Beklenen değerin modellenmesiyle false positive düşürme |

### Katman 6 — Analiz ve yapay zekâ

| # | İşlev | Açıklama |
|---|---|---|
| F6.1 | Regresyon tabanlı baz çizgi | Beklenen tüketim = f(üretim, sıcaklık, ...) |
| F6.2 | CUSUM | Kümülatif sapma; küçük ve kalıcı sapmaların tespiti |
| F6.3 | M&V / tasarruf doğrulama | IPMVP; yatırımın gerçek getirisi |
| F6.4 | Anomali tespiti | Kaçak, arızalı ekipman, verimsiz süreç |
| F6.5 | Tüketim tahmini | Hava durumu + üretim planı + piyasa ile ay sonu maliyet öngörüsü |
| F6.6 | Kayıp hesabı | Kesintiden doğan tahmini üretim/enerji kaybı |
| F6.7 | Bozunum tahmini | GES'te panel degradation öngörüsü |
| F6.8 | Yük ayrıştırma (NILM) | Toplam tüketimden cihaz bazlı tüketim çıkarımı |
| F6.9 | Boşta tüketim analizi | Üretim yokken tüketim (hafta sonu / vardiya dışı) |

### Katman 7 — Maliyet, fatura ve tarife

| # | İşlev | Açıklama |
|---|---|---|
| F7.1 | Birim fiyat ile maliyet | Tüketim × fiyat |
| F7.2 | Tarihli fiyat geçmişi | Fiyat değişiminin geçmişi bozmaması |
| F7.3 | Çok bileşenli tarife | Enerji + dağıtım + vergi/fon + güç bedeli |
| F7.4 | Zaman dilimli fiyatlandırma | Puant/gündüz/gece |
| F7.5 | Reaktif bedel hesabı | Endüktif/kapasitif oran ve ceza mekanizması |
| F7.6 | Gölge faturalama | Tedarikçi faturasının sayaç verisiyle doğrulanması |
| F7.7 | Maliyet dağıtımı / iç faturalama | Bölüm, kiracı, maliyet merkezi bazında |
| F7.8 | Bütçe ve sapma | Planlanan – gerçekleşen |

### Katman 8 — Uyum, raporlama ve sürdürülebilirlik

| # | İşlev | Açıklama |
|---|---|---|
| F8.1 | ISO 50001 desteği | EnPI + EnB + SEU + hedef + gözden geçirme |
| F8.2 | ISO 50006 yöntemi | Baz çizgi ve göstergenin kurulma yöntemi |
| F8.3 | Yasal bildirim | ENVER Portal; yıllık enerji tüketim bildirimi (Mart sonu) |
| F8.4 | VAP takibi | Verimlilik artırıcı projelerin izlenmesi |
| F8.5 | Karbon ayak izi | Kapsam 1 / 2 / 3; emisyon faktörü ile dönüşüm |
| F8.6 | SKDM (CBAM) verisi | İhracat için ürün bazlı gömülü emisyon |
| F8.7 | Güç kalitesi raporu | EN 50160 uyum raporu |
| F8.8 | Zamanlanmış rapor | Otomatik üretim + e-posta dağıtımı |
| F8.9 | Yazdırılabilir/dışa aktarılabilir çıktı | PDF, Excel, CSV |
| F8.10 | Denetlenebilirlik | Rapordaki her sayının ham veriye kadar izlenebilmesi |

### Katman 9 — İş süreci yönetimi (O&M)

| # | İşlev | Açıklama |
|---|---|---|
| F9.1 | İş emri yönetimi (WOM) | Sahadaki faaliyetlerin kaydı |
| F9.2 | Alarmdan iş emri üretimi | Otomatik tetikleme |
| F9.3 | Görev ve kontrol listesi | Periyodik bakım checklist'leri |
| F9.4 | SLA takibi | Müdahale/çözüm süresi |
| F9.5 | Bakım maliyeti analizi | İş emri bazlı maliyet |
| F9.6 | Yedek parça yönetimi | Stok ve kullanım |
| F9.7 | Aksiyon takibi | Tespit → sorumlu → termin → kapanış |

### Katman 10 — Üretim tarafı (GES / yenilenebilir)

| # | İşlev | Açıklama |
|---|---|---|
| F10.1 | Inverter izleme | Cihaz bazlı üretim ve durum |
| F10.2 | String izleme | String bazlı akım/performans |
| F10.3 | Performans Oranı (PR) | IEC 61724-1 yöntemi |
| F10.4 | Emre amadelik | Zaman ağırlıklı erişilebilirlik |
| F10.5 | Kapasite faktörü | Üretim / kurulu güç × süre |
| F10.6 | Işınım ve hava verisi | Piranometre, modül sıcaklığı |
| F10.7 | Üretim haritası | Inverter/string renk matrisi |
| F10.8 | Kirlenme (soiling) oranı | Temizlik kararı için |
| F10.9 | Beklenen üretim / kayıp | Teorik − gerçek |
| F10.10 | Öz tüketim / şebekeye satış | Tüketim–üretim eşleştirmesi |

### Katman 11 — Platform ve yönetişim

| # | İşlev | Açıklama |
|---|---|---|
| F11.1 | Kullanıcı ve rol yönetimi | Yetkilendirme |
| F11.2 | Çok kiracılı (multi-tenant) yapı | Portföy/müşteri ayrımı |
| F11.3 | API | Dış sistemlere veri açma |
| F11.4 | Bulut / yerel kurulum seçeneği | Dağıtım modeli |
| F11.5 | Yedekleme ve geri yükleme | Veri sürekliliği |
| F11.6 | Ölçeklenebilir depolama | Zaman serisi veritabanı, veri yaşlandırma |
| F11.7 | Güvenlik | Kimlik doğrulama, OT/IT ayrımı, ağ güvenliği |

### Katman 12 — SCADA'ya özgü işlevler

Bunlar **enerji izlemeden ayrı** bir sorumluluk alanıdır; karıştırılmamalıdır.

| # | İşlev | Açıklama |
|---|---|---|
| F12.1 | Uzaktan kumanda | Şalter açma/kapama, set değeri gönderme |
| F12.2 | Kilitleme/interlock | Güvenlik mantığı |
| F12.3 | Gerçek zamanlı çalışma | Saniye altı döngü |
| F12.4 | Yedekli (redundant) sunucu | Kesintisizlik |
| F12.5 | Historian | Yüksek hacimli ham veri arşivi |
| F12.6 | Operatör istasyonu / HMI | Vardiya operatörü arayüzü |
| F12.7 | Olay sıralama (SOE) | Milisaniye damgalı olay kaydı |

---

## 3. Karşılaştırma: kim neyi yapıyor?

| İşlev alanı | Enerji.pro | Enerify | Solarify | Klasik enerji SCADA | EcoStruxure PME |
|---|:--:|:--:|:--:|:--:|:--:|
| Otomatik veri toplama (Modbus vb.) | ✔ | ✔ | ✔ | ✔✔ | ✔✔ |
| SCADA/ERP entegrasyonu | ✔✔ | ✔ | — | ✔ | ✔✔ |
| Çok enerji türü | ✔✔ | ✔ | — | ✔ | ✔ |
| Çok tesis / portföy | ✔✔ | ✔✔ | ✔✔ | — | ✔ |
| EnPI / ISO 50001 | ✔✔ | ✔ | — | — | ✔ |
| Kullanıcı tanımlı formül/grafik | ✔ | ✔✔ | ✔ | ✔ | ✔ |
| Tüketim ısı haritası | ✔ | ✔✔ | — | — | ✔ |
| Alarm + bildirim | ✔✔ | ✔ | ✔✔ | ✔ | ✔✔ |
| Anomali / YZ | ✔ | ✔✔ | ✔✔ | — | ✔ |
| Tüketim/maliyet tahmini | ✔ | ✔ | ✔ | — | ✔✔ |
| Güç kalitesi (EN 50160) | — | — | — | ✔✔ | ✔✔ |
| Reaktif ceza takibi | ✔ | ✔ | — | ✔✔ | ✔ |
| Fatura doğrulama / gölge fatura | ✔ | ✔ | — | — | ✔✔ |
| Maliyet dağıtımı / iç faturalama | ✔ | ✔ | — | ✔ | ✔✔ |
| Karbon ayak izi | ✔✔ | ✔ | — | — | — |
| İş emri / O&M | — | ✔✔ | ✔✔ | — | ✔ |
| GES performans (PR, emre amadelik) | — | ✔ | ✔✔ | — | — |
| Mobil uygulama | ✔ | ✔✔ | ✔✔ | — | ✔ |
| Uzaktan kumanda | — | — | ✔ | ✔✔ | ✔ |

✔✔ = ürünün öne çıkardığı güçlü alan · ✔ = var · — = kapsam dışı / bilgi yok

### Okunabilir üç sonuç

1. **Pazar ikiye ayrılmış.** Bir tarafta *saha odaklı SCADA* (elektriksel
   büyüklük, güç kalitesi, reaktif, kumanda), diğer tarafta *yönetim odaklı
   EnMS* (EnPI, maliyet, karbon, rapor). Enerji.pro ikinci kampta, klasik
   entegratör ürünleri birinci kampta. Enerify ikisini birleştirmeye çalışıyor.
2. **Farklılaşma artık veri toplamada değil.** Modbus okumak herkeste var.
   Ayrışma; **formül altyapısı, anomali tespiti, iş emri yönetimi ve
   raporlamanın kalitesinde**.
3. **En değerli işlevler "ölçümden karara" geçişi sağlayanlar.** Isı haritası,
   regresyonlu baz çizgi, gölge faturalama, alarmdan iş emri üretimi. Bunların
   hepsi ham veriyi **eyleme** çeviriyor.

---

## 4. Bizim programımız: mevcut durum ve boşluk analizi

### 4.1 Elimizde olan (README'ye göre)

Bu depodaki uygulama bilinçli olarak dar kapsamlı: tek fabrika, tek
kullanıcı, **tamamen manuel veri girişi**, yerel SQLite, çevrimdışı.

Envanterdeki karşılıkları:

| Sahip olduğumuz | İşlev kodu |
|---|---|
| Manuel sayaç endeksi girişi | F0.9 |
| Doğrudan tüketim (fatura/beyan) girişi | F0.9 |
| Ana/alt sayaç hiyerarşisi, mükerrer sayım koruması | F2.2 |
| Çok enerji türü | F2.4 |
| kWh/MJ/GJ/TEP + enerji içeriği katsayısı (tarihli) | F2.5 |
| Üretim miktarı (bağlam değişkeni) | F2.7 |
| Tüketim hesabı ve dönem atama kuralı | F3.1, F3.2 |
| EnPI (enerji/üretim) | F3.6 |
| Bölüm dağılımı + "ölçülmeyen/dağıtılmamış" payı | F3.8 |
| Ortak birimde toplam | F3.9 |
| Gösterge paneli, 12 aylık trend | F4.1, F4.3 |
| Aylık hedef | F8.1 (kısmen) |
| Tarih aralıklı, yazdırılabilir rapor | F8.9 |
| Yedekleme / geri yükleme | F11.5 |
| Ham veri – türetilmiş değer ayrımı | F8.10'un temeli |

### 4.2 Mimari olarak zaten **doğru** yaptığımız üç şey

Bunlar korunmalıdır; piyasadaki birçok üründen daha sağlam kurgulanmışlar:

1. **Türetilmiş değer saklanmıyor.** Tüketim, maliyet, EnPI, GJ eşdeğeri her
   zaman ham veriden yeniden hesaplanıyor. Bu, MDM disiplininin en pahalı
   öğrendiği derstir: saklanan türev değer, kural değişince yalan söyler.
2. **Tek hesap kaynağı (`app/calc.py`).** Hiçbir ekran kendi hesabını
   yapmıyor. Çok ürün bunu beceremez; rapor ile panel farklı sayı gösterir.
3. **Belirsizlik sıfıra çevrilmiyor.** Dönüşüm katsayısı yoksa toplam
   üretilmiyor, eksikliğin kaynağı ekranda yazıyor. Bu, "sessiz yanlış"
   yerine "gürültülü doğru" tercihi — doğru tercih.

### 4.3 Boşluklar (öncelik sırasına göre)

**Kritik — mevcut kapsamda bile eksik:**

- **F1.1–F1.8 (veri kalitesi)** — Manuel girişte hata olasılığı otomasyondan
  *yüksektir*. Negatif tüketim, sarma, atlanan ay, yanlış sayaç seçimi
  denetimi yok.
- **F7.2 (tarihli fiyat)** — README bunu açıkça bir sınır olarak belirtiyor:
  fiyat değişince **geçmiş maliyetler de değişiyor**. Bu, maliyet raporunu
  geçmişe dönük olarak anlamsızlaştırır ve en yüksek getirili düzeltmedir.
- **F3.10 + F6.1 (baz çizgi)** — Hedef var, ama **baz çizgi** yok. ISO 50001'in
  ölçüm motoru EnPI *ve* EnB ikilisidir; EnB'siz "iyileşme" ispatlanamaz.
- **F8.10 (izlenebilirlik yüzeyi)** — Altyapı doğru, ama rapordaki bir sayıdan
  ham okumalara inen bir "nereden geldi?" görünümü yok.

**Yüksek değerli — düşük maliyetle eklenebilir:**

- F6.2 (CUSUM), F3.7 (normalize EnPI), F4.4 (ısı haritası — aylık veride
  sınırlı), F4.5 (dönem karşılaştırma), F4.7 (Pareto), F8.5 (karbon),
  F8.3 (ENVER bildirimi için çıktı), F9.7 (aksiyon takibi), F0.10 (Excel
  içe aktarma).

**Kapsam kararı gerektiren — ancak felsefeyi değiştirir:**

- F0.1–F0.8 (otomatik toplama), F5.x (alarm), F11.1 (çok kullanıcı),
  F4.10 (mobil), F12.x (SCADA).

---

## 5. Kapsam kararı: hangi işlevleri alalım, hangilerini almayalım

Karar ölçütü README'deki ilkedir: **"Bugün ihtiyaç duyulmayan özellik sisteme
eklenmez."** Aşağıdaki tablo bu ilkeyi işlev envanterine uygular.

### 5.1 ALINACAK — mevcut felsefeyi bozmadan değer katanlar

| İşlev | Neden | Zorluk |
|---|---|---|
| F1.1–F1.6 Veri kalitesi kuralları | Manuel girişin en büyük riski; ucuz, yüksek getiri | Düşük |
| F1.7 Sayaç sarması | Gerçek sahada olur; olduğunda veri sessizce bozulur | Düşük |
| F1.8 Sayaç değişimi | Sayaç değişince geçmiş anlamsızlaşır | Orta |
| F7.2 Tarihli birim fiyat | Bilinen ve belgelenmiş eksik | Orta |
| F3.10 Baz çizgi (referans yıl) | ISO 50001'in zorunlu yarısı | Düşük |
| F6.1 Regresyonlu beklenen tüketim | Üretim dalgalanmasından arındırılmış performans | Orta |
| F6.2 CUSUM | Küçük ama kalıcı sapmayı görür; grafik ucuz | Düşük |
| F3.7 Normalize EnPI | Ham EnPI üretim düşünce yalan söyler | Orta |
| F4.5 Dönem karşılaştırma | Yıl-yıl, ay-ay; en çok istenen görünüm | Düşük |
| F4.7 Pareto | "Nereye bakayım?" sorusunun cevabı | Düşük |
| F0.10 Excel içe aktarma | Geçmiş veriyi sisteme sokmanın tek pratik yolu | Orta |
| F8.5 Karbon ayak izi (Kapsam 1–2) | Tüketim × emisyon faktörü; katsayı altyapımız zaten var | Düşük |
| F8.3 ENVER çıktısı | Yasal yükümlülük; zaten ürettiğimiz veriden | Düşük |
| F8.10 Drill-down / izlenebilirlik | Denetimde ispat; mimarimiz buna hazır | Orta |
| F9.7 Aksiyon takibi | Tespit edilen sapmanın kapanması | Düşük |
| F6.9 Boşta tüketim analizi | Aylık veride sınırlı, günlük veride çok değerli | Orta |

### 5.2 ŞARTA BAĞLI — ancak gerçek ihtiyaç doğarsa

| İşlev | Şart |
|---|---|
| F0.1 Modbus okuma | Sahada analizör varsa ve manuel giriş yükü katlanılmaz hâle geldiyse |
| F3.3 Yük profili, F3.4 puant, F3.5 talep | Saatlik/15 dk veri girmeye başlandıysa (manuel girişle imkânsız) |
| F5.x Alarm | Otomatik toplama geldikten *sonra*; aylık manuel veride alarmın anlamı yok |
| F7.6 Gölge faturalama | Sayaç ve fatura verisi aynı dönemde birlikte tutuluyorsa |
| F7.7 Maliyet dağıtımı | Bölüm bazlı iç muhasebe talebi varsa |
| F11.1 Çok kullanıcı | Veri girişini birden fazla kişi yapmaya başladıysa |
| F2.1 Çok tesis | İkinci fabrika gerçekten geldiyse |

### 5.3 ALINMAYACAK — bilinçli ret

| İşlev | Ret gerekçesi |
|---|---|
| F12.1–F12.7 SCADA kumanda, HMI, redundancy, SOE | Farklı bir ürün sınıfı. Kumanda, güvenlik ve gerçek zamanlılık sorumluluğu getirir; tek kullanıcılı, çevrimdışı bir raporlama uygulamasının taşıyamayacağı bir yük. |
| F10.x GES modülü | Fabrika tüketim izleme ile santral performans izleme ayrı ürünlerdir. GES gelirse ayrı modül, ayrı veri modeli. |
| F6.8 NILM | Akademik olgunluk seviyesi endüstriyel kullanım için yetersiz; etiketli veri kıtlığı temel engel. Alt sayaç koymak daha ucuz ve kesin. |
| F6.7 Bozunum tahmini | GES'e özgü. |
| F11.2 Multi-tenant, F11.4 bulut | Tek fabrika, yerel kurulum tercihiyle çelişir. |
| F8.6 SKDM ürün bazlı gömülü emisyon | Ürün ağacı ve proses verisi gerektirir; enerji izlemenin çok ötesinde bir kapsam. |

---

## 6. Tasarım rehberi — seçilen işlevler nasıl kurgulanmalı

Bu bölüm, Bölüm 5.1'de "alınacak" denen işlevlerin **somut tasarımıdır**.
Her başlıkta: veri modeli, hesap kuralı, ekran ve kenar durumlar.

### 6.1 Veri kalitesi (F1.x) — "giriş anında uyar, asla sessizce düzeltme"

**İlke:** Uygulama kullanıcının verisini **düzeltmez**; şüpheli olanı
**işaretler** ve kararı kullanıcıya bırakır. Sessiz düzeltme, manuel girişli
bir sistemde en tehlikeli davranıştır.

**Doğrulama kuralları (okuma kaydedilirken çalışır):**

| Kural | Koşul | Davranış |
|---|---|---|
| Geriye giden endeks | `endeks₂ < endeks₁` | **Engelle**; sarma mı, yanlış giriş mi diye sor |
| Sıfır tüketim | `endeks₂ == endeks₁` | **Uyar**, kaydetmeye izin ver (duruş olabilir) |
| Aşırı sıçrama | tüketim > son 12 ayın medyanının 3 katı | **Uyar**, onayla kaydet |
| Aşırı düşük | tüketim < medyanın 1/3'ü | **Uyar**, onayla kaydet |
| Eksik dönem | iki okuma arası > 45 gün | **Uyar**: "Şubat atlanmış görünüyor" |
| Tarih gelecekte | `tarih > bugün` | **Engelle** |
| Aynı gün ikinci okuma | (sayaç, tarih) mükerrer | **Engelle** |
| Çakışan kaynak | Aynı ay hem doğrudan tüketim hem ana sayaç | Zaten uygulanıyor: doğrudan tüketim esas, fark bildirilir |

**Uygulama yeri:** `app/readings.py` girişte çağırır, kural motoru
`app/validation.py` içinde ayrı durur — hesapla karışmaz. `calc.py` kural
bilmez.

**Veri modeli eki:** `meter_reading` tablosuna

```
quality      TEXT  -- 'olculdu' | 'tahmin' | 'duzeltildi'
note         TEXT  -- kullanıcının uyarıyı geçerken yazdığı gerekçe
```

Raporlarda `quality != 'olculdu'` olan dönemler **yıldızla** gösterilir ve
rapor altında "Bu dönemde N kayıt ölçüm dışıdır" notu çıkar. Tahmin edilen
değer, ölçülen gibi sunulmaz — MDM disiplininin en önemli kuralı budur.

### 6.2 Sayaç sarması ve sayaç değişimi (F1.7, F1.8)

**Sarma:** `meter` tablosuna `digit_count` (endeks hane sayısı, örn. 6 →
maksimum 999999) eklenir. `endeks₂ < endeks₁` durumunda:

```
tuketim = (10^hane - endeks₁ + endeks₂) × çarpan
```

Bu hesap **otomatik yapılmaz**; kullanıcıya "Sayaç sarmış olabilir. Sarma
kabul edilirse tüketim X olur. Onaylıyor musunuz?" diye sorulur ve onaylanan
okuma `rollover = true` ile işaretlenir. Otomatik sarma varsayımı, yanlış
girilmiş bir endeksi devasa bir tüketime çevirir — sahada en sık görülen
veri felaketi budur.

**Sayaç değişimi:** Sayacı silmek veya endeksi sıfırlamak **yasak**. Yeni
tablo:

```
meter_replacement(
  meter_id, replaced_on,
  old_final_index,      -- sökülen sayacın son endeksi
  new_initial_index,    -- takılan sayacın ilk endeksi
  note
)
```

`calc.py` değişim tarihini geçen bir aralığın tüketimini iki parçada toplar:
`(old_final − önceki okuma)` + `(sonraki okuma − new_initial)`. Böylece geçmiş
bozulmaz ve değişim raporda görünür.

### 6.3 Tarihli birim fiyat (F7.2) — mevcut eksiğin kapatılması

Bugünkü davranış (fiyat değişince geçmiş maliyet de değişir) şu şekilde
düzeltilir. `energy_type.unit_price` alanı **kaldırılmaz**, ama artık
"güncel fiyat" olarak değil, yeni tablonun son satırı olarak okunur:

```
energy_price(
  energy_type_id,
  valid_from   DATE,     -- dönem başlangıcı
  unit_price   NUMERIC,
  note         TEXT,
  UNIQUE(energy_type_id, valid_from)
)
```

**Kural (dönüşüm katsayısıyla birebir aynı desen):** bir dönem için
`valid_from ≤ dönem` koşulunu sağlayan **en yeni** fiyat kullanılır. Bu,
`energy_conversion` tablosunda zaten uygulanan ve kullanıcının aşina olduğu
mantıktır — yeni bir kavram öğretmeden tutarlılık sağlar.

**Kenar durum:** İlk fiyattan **önceki** bir dönem için fiyat yoksa maliyet
**üretilmez** ve "Ocak 2024 için tanımlı birim fiyat yok" yazılır. Sıfır
maliyet gösterilmez. (Dönüşüm katsayısında verilen kararla aynı.)

**Göç (migration):** Mevcut `unit_price` değeri, `valid_from = en eski
okumanın ayı` ile tek satır olarak `energy_price`'a taşınır. Böylece
yükseltme sonrası hiçbir rapor değişmez.

### 6.4 Baz çizgi ve normalize EnPI (F3.10, F6.1, F3.7)

Bu, ISO 50001'in ölçüm motorudur ve bugünkü "hedef" mekanizmasından farklıdır:
hedef **niyet**, baz çizgi **referans**tır.

**Veri modeli:**

```
baseline(
  energy_type_id,
  name,                 -- "2025 referans yılı"
  period_start, period_end,
  model_type,           -- 'ortalama' | 'regresyon'
  slope, intercept, r2, -- regresyon ise
  created_at, note
)
```

**İki seviyeli tasarım — basitten karmaşığa:**

*Seviye 1 (önce bu yapılır): sabit baz çizgi.* Seçilen referans dönemin
aylık ortalama tüketimi. Karşılaştırma: `tasarruf = baz − gerçek`.
Anlaşılır, tartışılmaz, hemen kullanılır.

*Seviye 2: tek değişkenli regresyon.* Referans dönemdeki (üretim, tüketim)
çiftlerinden en küçük kareler ile:

```
beklenen_tüketim = a × üretim + b
```

`a` = değişken (üretime bağlı) enerji, `b` = **sabit/baz yük** — üretim sıfır
olsa bile harcanan enerji. `b`'nin büyüklüğü tek başına çok değerli bir
yönetim bulgusudur.

**Zorunlu güvenlik kuralları** (istatistiği yanlış kullanmamak için):

- En az **12 veri noktası** yoksa regresyon **önerilmez ve kurulmaz**.
- `R² < 0.5` ise model kurulur ama ekranda **"Bu model tüketimi açıklamıyor;
  sonuçlara dayanarak karar vermeyin"** uyarısı çıkar. R² sessizce
  gizlenmez.
- Referans dönem dışına **ekstrapolasyon** yapılan noktalar grafikte farklı
  gösterilir.
- `a < 0` (üretim arttıkça tüketim azalıyor) fiziksel olarak şüphelidir:
  açık uyarı verilir.

**Normalize EnPI:** `EnPI_normalize = gerçek_tüketim / beklenen_tüketim`.
1,00 = baz performans; 0,92 = %8 iyileşme. Ham EnPI (enerji/üretim) üretim
düştüğünde sabit yük yüzünden kötüleşir ve yöneticiyi yanıltır; normalize
EnPI bunu ortadan kaldırır. **İkisi yan yana gösterilir**, biri diğerinin
yerine geçmez.

### 6.5 CUSUM (F6.2) — küçük ama kalıcı sapmayı görmek

Her dönem için `sapma = gerçek − beklenen`; CUSUM bu sapmaların kümülatif
toplamıdır:

```
CUSUM_n = Σ (gerçek_i − beklenen_i),  i = 1..n
```

**Okunuşu — tek cümlelik kural:** *Grafiğin eğimi önemlidir, seviyesi değil.*

- Yatay seyir → performans baz çizgiyle uyumlu.
- Aşağı eğim → **kalıcı tasarruf**; eğimin başladığı ay, iyileştirmenin
  gerçekten devreye girdiği aydır.
- Yukarı eğim → **kalıcı kayıp**; başlangıç ayı arıza/ayar bozulmasının
  tarihidir.

CUSUM'un değeri budur: tek aylık gürültüde kaybolan %3'lük kalıcı bir kaymayı
6 ay sonra apaçık görünür yapar ve **tarihini verir**. Uygulaması yaklaşık
20 satırdır; getirisi çok yüksektir.

**Ekran:** Baz çizgi ekranında, beklenen–gerçek grafiğinin hemen altında.
Eğim değişim noktası işaretlenir ve kullanıcının o noktaya **not**
yazabilmesi sağlanır ("kompresör değişti", "yeni hat devreye alındı").
Bu notlar, sonraki yıl raporu yazan kişi için kurumsal hafızadır.

### 6.6 Karbon ayak izi (F8.5) — dönüşüm katsayısı deseninin tekrarı

Bu işlev bizde **neredeyse bedava**, çünkü altyapı kurulu: enerji içeriği
katsayısı ile aynı desen kullanılır.

```
emission_factor(
  energy_type_id,
  valid_from,
  factor,          -- kgCO2e / (enerji türünün kendi birimi)
  scope,           -- 1 | 2
  source,          -- 'IPCC 2019' | 'TEİAŞ şebeke faktörü' | ...
  note,
  UNIQUE(energy_type_id, valid_from)
)
```

**Kural:** `emisyon = tüketim × faktör`, tüketim **kendi biriminde**
(dönüştürülmeden). Bu, maliyet hesabıyla aynı ilkedir ve iki kez dönüşümden
doğan hata sınıfını tamamen ortadan kaldırır.

**Kapsam ayrımı:** Doğal gaz, kömür, motorin → **Kapsam 1** (yakma, doğrudan).
Satın alınan elektrik, buhar → **Kapsam 2** (dolaylı). Raporda ikisi **ayrı
satır** olarak gösterilir, toplanabilir ama birleştirilmez — GHG Protocol
bunu şart koşar.

**Kritik tasarım kararı — sistem faktör varsaymaz.** Şebeke emisyon faktörü
ülkeye ve yıla göre değişir; yakıt faktörü ölçüm bazına (üst/alt ısıl değer)
bağlıdır. Enerji içeriği katsayısında verdiğimiz kararın aynısı geçerlidir:
**kullanıcı tanımlar, kaynak alanını doldurur, sistem uydurmaz.** Faktör
yoksa emisyon üretilmez; "faktör tanımlı değil" yazılır.

### 6.7 Dönem karşılaştırma ve Pareto (F4.5, F4.7)

**Karşılaştırma:** Rapor ekranına ikinci bir tarih aralığı alanı eklenir.
Çıktı üç sütun: A dönemi, B dönemi, fark (mutlak ve %). Varsayılan
"geçen yılın aynı dönemi" olmalıdır — en çok istenen karşılaştırma budur.

**Dikkat:** Dönem uzunlukları farklıysa (28 vs 31 gün) **otomatik
normalleştirme yapılmaz**; ekranda "Dönemler farklı uzunlukta (28 / 31 gün)"
uyarısı çıkar. Sessiz normalleştirme, kullanıcının farkında olmadığı bir
varsayımdır.

**Pareto:** Seçilen dönemde sayaçları (veya bölümleri) tüketime göre azalan
sırala, kümülatif % ekle, %80 çizgisini işaretle. Tek ekranda "nereye
bakayım?" sorusunu cevaplar. Ortak birim (GJ) seçiliyse farklı enerji türleri
karşılaştırılabilir hâle gelir — bu, mevcut dönüşüm altyapımızın en güzel
meyvesidir. Katsayısı olmayan tür listeye **girmez** ve dipnotta belirtilir.

### 6.8 İzlenebilirlik / drill-down (F8.10)

Mimari zaten hazır (türetilmiş değer saklanmıyor); eksik olan **yüzeydir**.

Panelde ve raporda her tüketim sayısının yanına küçük bir **"?"** bağlantısı
konur. Tıklanınca açılan sayfa şunu gösterir:

```
Ocak 2026 · Elektrik · 124.500 kWh

Kaynak: Ana sayaçlar (doğrudan tüketim girilmemiş)

  TR-1  01.01.2026  125.400  →  01.02.2026  168.900   ×1     =  43.500 kWh
  TR-2  01.01.2026   88.100  →  01.02.2026  100.100   ×1     =  12.000 kWh
  TR-3  01.01.2026    2.100  →  01.02.2026    3.790   ×40    =  67.600 kWh
                                                    Toplam  = 123.100 kWh
  ⚠ TR-2'nin 01.02 okuması tahmin edilmiştir (gerekçe: "sayaç arızalı")
```

Bu ekran, ISO 50001 denetiminde "bu sayı nereden geliyor?" sorusunun tek
tıkla cevabıdır ve rakiplerin çoğunda yoktur. **En yüksek itibar getirisi
olan, en ucuz özelliktir.**

### 6.9 Aksiyon takibi (F9.7) — tam iş emri yönetimi değil

Enerify ve Solarify'ın WOM modülü büyük bir yatırımdır ve bizim kapsamımızı
aşar. Ancak arkasındaki fikir — **tespitin bir sahibi ve termini olması** —
ucuza alınabilir:

```
action(
  id, title, description,
  created_on, due_on,
  owner,                 -- serbest metin (tek kullanıcı, rol yok)
  status,                -- 'acik' | 'devam' | 'kapandi' | 'iptal'
  energy_type_id NULL, department_id NULL, period NULL,   -- bağlam
  expected_saving NULL,  -- tahmini yıllık tasarruf (kendi birimi)
  closed_on, result_note
)
```

Panelde "açık aksiyon" sayacı; gecikenler kırmızı. CUSUM'daki eğim değişim
noktasından ve Pareto'daki ilk sıradan **doğrudan aksiyon açılabilmelidir** —
analizden eyleme geçişin köprüsü budur. VAP (verimlilik artırıcı proje)
takibinin de temelini oluşturur.

### 6.10 Excel içe aktarma (F0.10)

Geçmiş veriyi sisteme sokmanın tek pratik yolu. Tasarım kuralları:

1. **Şablon indirtilir** — kullanıcının kendi dosya formatını tahmin etmeye
   çalışmayız. Sütunlar: `sayaç_adı | tarih | endeks`.
2. **Önizleme zorunlu** — yüklenen dosya *kaydedilmeden önce* satır satır
   gösterilir: kaç satır geçerli, kaç satır hatalı, hangi satır neden hatalı.
3. **Ya hep ya hiç** — tek işlemde ya bütün geçerli satırlar yazılır ya
   hiçbiri. Yarım yüklenmiş dosya, en kötü veri durumudur.
4. **Bölüm 6.1'deki tüm doğrulama kuralları içe aktarmada da çalışır.**
   İçe aktarma, kural denetiminden kaçış yolu olamaz.
5. Türkçe sayı biçimi (`1.250,50`) zaten `web.py` içinde çözülmüş; aynı
   yardımcı yeniden kullanılır.

### 6.11 ENVER bildirim çıktısı (F8.3)

5627 sayılı kanun kapsamındaki işletmeler bir önceki yılın enerji tüketim
bilgilerini **her yıl Mart ayı sonuna kadar** ENVER Portal üzerinden
bildirmekle yükümlüdür. Bizim zaten ürettiğimiz veri bu bildirimin ham
maddesidir.

**Tasarım:** Portalla **entegrasyon yapılmaz** (kimlik, oturum, değişen form
yapısı — kırılgan ve bakım maliyeti yüksek). Bunun yerine tek ekranlık bir
**"Yıllık Enerji Bildirim Özeti"** üretilir: yıl seçilir, enerji türü bazında
yıllık tüketim kendi biriminde ve **TEP karşılığıyla** listelenir, toplam TEP
verilir, üretim miktarı ve yıllık EnPI eklenir, yazdırılabilir/kopyalanabilir
olur. Kullanıcı portala kendisi girer. Yükümlülüğün kolaylaştırılması
hedeftir, otomatikleştirilmesi değil.

TEP dönüşümü için `units.py` içindeki sabit zaten doğrudur
(1 TEP = 41,868 GJ = 11.630 kWh).

---

## 7. Aşamalı yol haritası

Her faz **kendi başına kullanılabilir** bir bütün oluşturur; yarım kalırsa
bile sistem tutarlı kalır.

### Faz 1 — Sağlamlaştırma (mevcut kapsamın içi)

Yeni kavram eklenmez; var olan işlevler güvenilir hâle getirilir.

1. Veri kalitesi kuralları (6.1) — `app/validation.py`
2. Sayaç sarması ve sayaç değişimi (6.2)
3. Tarihli birim fiyat (6.3) — **belgelenmiş eksiğin kapatılması**
4. Drill-down / izlenebilirlik ekranı (6.8)
5. Dönem karşılaştırma ve Pareto (6.7)

*Çıktı: Aynı kapsam, ama denetime dayanıklı ve geçmişe dönük doğru sonuç.*

### Faz 2 — Performans ölçümü (ISO 50001'in ikinci yarısı)

6. Baz çizgi — Seviye 1, sabit ortalama (6.4)
7. Baz çizgi — Seviye 2, regresyon + R² uyarıları (6.4)
8. Normalize EnPI (6.4)
9. CUSUM grafiği ve not alma (6.5)
10. Aksiyon takibi (6.9)

*Çıktı: "Enerjimiz ne kadar?" sorusundan "enerji performansımız iyileşti mi,
ne zaman, ne kadar?" sorusuna geçiş. ISO 50001 çalışmasının fiilî motoru.*

### Faz 3 — Kapsam genişletme

11. Excel içe aktarma (6.10)
12. Karbon ayak izi Kapsam 1–2 (6.6)
13. ENVER yıllık bildirim özeti (6.11)
14. Boşta tüketim analizi (F6.9) — günlük veri varsa

*Çıktı: Yasal ve kurumsal raporlama yükünün karşılanması.*

### Faz 4 — Yalnızca gerçek ihtiyaç doğarsa

15. Modbus TCP ile tek bir analizörden otomatik okuma (pilot)
16. Saatlik veri → yük profili, puant kırılımı, talep takibi
17. Alarm ve bildirim (ancak otomatik veriyle anlamlı)
18. Çok kullanıcı / rol

**Faz 4 için açık uyarı:** Bu adımlar uygulamanın **kimliğini değiştirir**.
Manuel girişli, çevrimdışı, tek kullanıcılı bir masaüstü aracından; sürekli
çalışan, ağa bağlı, veri hacmi büyüyen bir servise dönüşür. Bu noktada
SQLite'ın, tek işlemli uvicorn'un ve "yedek al" temelli veri güvencesinin
yeniden değerlendirilmesi gerekir. Faz 4'e geçmek bir özellik kararı değil,
**bir ürün kararıdır** ve öyle ele alınmalıdır.

---

## 8. Tasarım ilkeleri ve kaçınılacak hatalar

Piyasa incelemesinden çıkan, bizim için bağlayıcı olması önerilen ilkeler:

### 8.1 Korunacak ilkeler

1. **Türetilmiş değer saklanmaz.** Yeni işlevler de bu kurala uyar: normalize
   EnPI, emisyon, CUSUM — hepsi hesaplanır, saklanmaz. Saklanan tek şey
   **model parametreleridir** (regresyon katsayısı), çünkü o bir *karardır*,
   türev değil.
2. **Tek hesap kaynağı.** Yeni hesaplar da `calc.py` veya onun yanındaki
   adlandırılmış modüllere girer (`baseline.py`, `carbon.py`); ekranlar
   hesap yapmaz.
3. **Belirsizlik sıfıra çevrilmez.** Katsayı yoksa, fiyat yoksa, faktör
   yoksa sonuç üretilmez ve **nedeni yazılır**. Bu kural yeni her işlevde
   tekrar edilir.
4. **Her varsayım görünür.** Sarma kabulü, tahmin edilen okuma, R² düşüklüğü,
   farklı dönem uzunluğu — hepsi ekranda.
5. **Geçmiş bozulmaz.** Tanım silinmez, pasife alınır; fiyat ve faktör
   tarihlidir; sayaç değişimi kayıt altındadır.

### 8.2 Piyasada gözlenen ve tekrarlanmaması gereken hatalar

| Hata | Sonucu | Bizim karşı tedbirimiz |
|---|---|---|
| Tahmin edilen veriyi ölçülen gibi göstermek | Rapora güven kalmaz | `quality` alanı + raporda yıldız ve dipnot |
| Tek "güncel fiyat" tutmak | Geçmiş maliyet raporu anlamsızlaşır | Tarihli `energy_price` (6.3) |
| Ham EnPI'yi tek gösterge saymak | Üretim düşünce "verimlilik kötüleşti" yanılgısı | Normalize EnPI yanında gösterilir (6.4) |
| R²'yi gizleyip regresyon sunmak | Kötü modele dayalı yatırım kararı | R² < 0,5'te açık uyarı |
| Sabit eşikli alarm bolluğu | Alarm seli, operatörün alarmı görmezden gelmesi | Faz 4'e ertelendi; geldiğinde beklenen-değer tabanlı |
| Ana ve alt sayacı birlikte toplamak | Mükerrer sayım, şişkin toplam | Zaten çözülmüş: yalnız alt sayaçlar dağıtıma girer |
| "Ölçülmeyen" payı gizlemek | Toplamın tutmadığı, kimsenin fark etmediği rapor | Zaten çözülmüş: ayrı satır olarak gösterilir |
| Enerji türlerini katsayısız toplamak | Fiziksel olarak anlamsız sayı | Zaten çözülmüş: katsayı yoksa toplam üretilmez |
| Otomatik sarma düzeltmesi | Yanlış endeks girişi devasa tüketime dönüşür | Onay istenir, asla otomatik değil (6.2) |
| Portal/ERP'ye doğrudan entegrasyon | Karşı taraf değişince kırılır, bakım yükü | Çıktı üret, kullanıcı taşısın (6.11) |

### 8.3 Ekran tasarımı için üç kural

1. **Her ekran tek bir soruyu cevaplar.** Panel: "durumumuz ne?" · Baz çizgi:
   "iyileştik mi?" · Pareto: "nereye bakayım?" · Drill-down: "bu sayı nereden
   geliyor?" Bir ekranın ikinci bir soruya cevap vermeye başlaması, yeni bir
   ekran gerektiğinin işaretidir.
2. **Uyarı, sonucun yanında durur.** Ayrı bir "uyarılar" sekmesine sürülen
   uyarı okunmaz. Mevcut uygulamanın çakışma/eksik katsayı uyarılarını
   ekranda göstermesi doğru yaklaşımdır; yeni işlevlerde de sürdürülür.
3. **Her sayı yazdırılabilir olmalı.** Enerji yöneticisinin çıktısı hâlâ
   kâğıda ve toplantıya gider. Mevcut rapor ekranının "tek ekranlık,
   yazdırılabilir" tasarımı korunmalı; yeni eklenen her görünüm bu ölçütü
   karşılamalıdır.

---

## 9. Özet

**Tespit:** Enerji izleme pazarı iki kutuplu — saha odaklı SCADA (elektriksel
büyüklük, güç kalitesi, reaktif, kumanda) ve yönetim odaklı EnMS (EnPI,
maliyet, karbon, rapor). Veri toplama artık bir farklılaşma alanı değil;
ayrışma **ölçümü karara çeviren** işlevlerde: esnek formül altyapısı,
regresyonlu baz çizgi, anomali tespiti, iş emri yönetimi ve raporlamanın
denetlenebilirliği.

**Konumumuz:** Uygulamamız ikinci kutupta, bilinçli olarak dar bir kesitte
duruyor ve mimari temelleri (türetilmiş değer saklamama, tek hesap kaynağı,
belirsizliği sıfıra çevirmeme) piyasadaki birçok üründen sağlam.

**En yüksek getirili beş adım:**

1. Veri kalitesi kuralları — manuel girişin en büyük riski (6.1)
2. Tarihli birim fiyat — belgelenmiş eksiğin kapatılması (6.3)
3. Baz çizgi + normalize EnPI — ISO 50001'in eksik yarısı (6.4)
4. CUSUM — ~20 satır kod, en yüksek analitik getiri (6.5)
5. Drill-down — denetimde "bu sayı nereden geliyor?" cevabı (6.8)

**En önemli kaçınma:** SCADA olmaya çalışmamak. Kumanda, gerçek zamanlılık ve
yedeklilik farklı bir ürün sınıfının sorumluluklarıdır; bu uygulamanın
tasarım hedefiyle bağdaşmaz.

---

## 10. Kaynaklar

Ürün ve sektör:

- [Enerji Kontrolü: Enerji.pro İle Tüketiminizi Hemen Yönetin — Enverio](https://www.enverio.com.tr/enerji-tuketiminizi-kontrol-altina-alin-kullanici-dostu-enerji-izleme-yazilimi-enerji-pro-ile-tanisin/)
- [Enerji Takibi Yazılımı: EnPI'lar Nasıl İzlenir? — Enverio](https://www.enverio.com.tr/enerji-takibi-yazilimi-ile-enerji-performans-gostergeleri-nasil-izlenir/)
- [Enerji Yönetiminde Kalite Güvencesi: Enerji İzleme ve ISO 50001 — Enverio](https://www.enverio.com.tr/enerji-yonetiminde-kalite-guvencesi-enerji-izleme-ve-iso-50001/)
- [Enerji Takibi için Modbus TCP/IP Nasıl Kullanılır — Enverio](https://www.enverio.com.tr/enerji-takibi-icin-modbus-tcp-ip-nasil-kullanilir/)
- [Enerji İzleme Yazılımı ile Enerji İzleme Süreçlerinde — Enerji.Pro](https://enerji.pro/enerji-izleme-yazilimi-otomasyonu/)
- [Büyük İşletmeler İçin Enerji İzleme Yazılımı Rehberi — Enerji.Pro](https://enerji.pro/buyuk-isletmeler-icin-enerji-izleme-yazilimi-rehberi/)
- [Enerify — LOGGMA](https://loggma.com/en/enerify-portal/)
- [LOGGMA, enerji yönetimini yapay zekâ ile birleştirdi — Dünya Gazetesi](https://www.dunya.com/sirketler/loggma-enerji-yonetimini-yapay-zeka-ile-birlestirdi-haberi-757477)
- [Loggma: Enerji Yönetiminde Dijital Dönüşümün Öncüsü — Solarbaba](https://solarbaba.com/haber-loggma-enerji-yonetiminde-dijital-donusumun-oncusu/)
- [Solarify — Yapay Zeka Tabanlı Performans İzleme](https://solarify.io/tr/)
- [Solarify GES Performans İzleme Sistemini Ayıran 5 Özellik — Solarify Blog](https://solarify.io/tr/blog/solarify-ges-performans-izleme-sistemini-konvansiyonel-izleme-sistemlerinden-ayiran-5-ozellik/)
- [GES'ler için emre amadelik hesabı — Solarify Blog](https://solarify.io/tr/blog/ges-ler-icin-emre-amadelik-hesabi/)
- [GES için Uzaktan İzleme Çözümü: Solarify — Kontek Enerji](https://kontekenerji.com.tr/gunes-enerjisi-santralleri-ges-icin-uzaktan-izleme-cozumu-solarify)
- [Enerji tüketimi analiz, izleme ve raporlama SCADA yazılımı — İda Otomasyon](https://www.idasotomasyon.com/enerji-tuketimi-izleme-cozumleri/)
- [Enerji Otomasyonu — Elektrik İzleme SCADA — Fultek](https://www.fultek.com.tr/enerji-otomasyonu/)
- [Enerji İzleme Sistem Çözümleri — Teleteknik](https://teleteknik.com.tr/enerji-izleme-ve-enerji-otomasyonu/)
- [Enerji Scada Sistemi — ARGEKİP](https://energy.argekip.com/)
- [SmartPower Enerji İzleme Sistemi](https://www.enerjitakibi.com/)
- [Enerji İzleme ve Fatura Doğrulama Modülleri — EnerIP](https://www.enerip.com/modules)
- [EcoStruxure Power Monitoring Expert — Schneider Electric](https://www.se.com/us/en/product-range/65404-ecostruxure-power-monitoring-expert/)
- [Energy Billing Module operation — Schneider Electric](https://product-help.se.com/docs/EcoStruxure/Power-Monitoring-Expert-2024/content/6_operating/modules/energybilling.htm)
- [What is the Data Quality Module (VEE) for PME/PSE? — Schneider Electric](https://www.se.com/us/en/faqs/FA322372/)

Standart, yöntem ve mevzuat:

- [50001 Ready Task 11: Energy Performance Indicators and Energy Baselines — LBNL](https://navigator.lbl.gov/guidance/task/11)
- [ISO 50006: EnPI & Energy Baseline Explained — Alligator Analytica](https://alligator-analytica.de/en/iso-50006.html)
- [EnPIs and energy baselines: how ISO 50001 measures — ISTO](https://www.isto.ch/insights/iso50001-enpi-baselines)
- [The Value of Regression Models in Determining Energy Performance — OSTI](https://www.osti.gov/servlets/purl/1329740)
- [Energy performance measurement, monitoring and control (ISO 50001 / ISO 50006) — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S266616592030020X)
- [ENERJİ KALİTESİ, TS EN 50160 STANDARDI VE ÜLKEMİZDEKİ UYGULAMALARI — EMO](https://www.emo.org.tr/ekler/0f027d0cc62ecbd_ek.pdf)
- [EN 50160 Güç Kalite Raporu — Teleteknik](https://teleteknik.com.tr/enerji-kalitesi-olcum-ve-raporlama/)
- [What is the IEC 61724-1 Standard? — Seven Sensor](https://www.sevensensor.com/what-is-the-iec-61724-1-standard-why-is-iec-61724-1-important-for-solar-power-plants)
- [5627 Sayılı Enerji Verimliliği Kanunu — Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr/mevzuatmetin/1.5.5627.pdf)
- [ENVER — Enerji Verimliliği Portalı](https://enerjiverimliligi.enerji.gov.tr/Home/sss)
- [Sanayide Enerji Yönetimi: Yükümlülükler ve ENVER Portal Bildirimi — Sowind Enerji](https://sowindenerji.com/yayinlarimiz/enerji-etudu/sanayide-enerji-yonetimi-yasal-yukumlulukler/)
- [Reaktif Oran Sınırları — Covolt](https://covolt.com.tr/reaktif-oran-sinirlari)
- [EPDK Reaktif Enerji Tarifesi ve Ceza Oranları — Elektraverse](https://elektraverse.com/blog/alcak-gerilim-malzemeleri/epdk-reaktif-enerji-tarifesi-reaktif-kapasitif-ceza-oranlari-2025)
- [Karbon Ayak İzi Hesaplama Metodolojileri: GHG Protokolü ve ISO 14064](https://www.surdurulebilirlikraporu.org.tr/emisyon-kontrolu-ve-yonetimi/170/karbon-ayak-izi-hesaplama-metodolojileri-ghg-protokolu-ve-iso14064)

Mimari ve teknik:

- [What Is Meter Data Management? A Complete Guide — CSA](https://www.csa1.com/what-is-meter-data-management-a-complete-guide-for-electric-cooperatives/)
- [Meter Data Management in Utilities: How Modern MDM Works — Bynry](https://www.bynry.com/blog/mdm-meter-data-management)
- [Bridging Smart Meter Gaps: Benchmark of Models for Data Imputation — arXiv](https://arxiv.org/pdf/2501.07276)
- [A Runnable Reference Architecture for Industrial IoT on InfluxDB 3 — InfluxData](https://www.influxdata.com/blog/iiot-reference-architecture-influxdb3/)
- [A Comparison of OPC UA and MQTT Sparkplug — HiveMQ](https://www.hivemq.com/resources/iiot-protocols-opc-ua-mqtt-sparkplug-comparison/)
- [Real-Time PLC Data Streaming: OPC UA and Modbus Patterns — Trout Software](https://www.trout.software/blog/real-time-plc-data-streaming-opc-ua-modbus-and-modern-integration-patterns)
- [Fostering non-intrusive load monitoring for industrial applications — Energy Informatics](https://energyinformatics.springeropen.com/articles/10.1186/s42162-025-00517-5)
- [Towards Trustworthy Energy Disaggregation: A Review of NILM — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9371074/)
- [SCADA Alarm Yönetimi ile Operasyonel Verimlilik Artışı — Bella Binary](https://www.bellabinary.com/Blog/scada-alarm-yonetimi-operasyonel-verimlilik)
- [SCADA Nedir ve Nasıl Çalışır? — DelcomRF](https://delcomrf.com/scada-nedir-ve-nasil-calisir-2025/)

---

*Not: Bölüm 0.1'de belirtildiği üzere enerji.pro, loggma.com/enerify ve
loggma.com/solarify adreslerine bu oturumda doğrudan erişilemedi. Bu üç
ürüne dair bulgular ikincil kaynaklardan derlenmiştir ve ürün
dokümanlarından teyit edilmelidir.*
