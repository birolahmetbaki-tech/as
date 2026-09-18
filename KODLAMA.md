# Enerji Yönetim Platformu — geliştirme notları

Tasarımın tamamı **[docs/EL-KITABI.md](docs/EL-KITABI.md)** içindedir. Bu dosya
yalnızca kaynağın nasıl derlendiğini ve sınandığını anlatır.

## Durum

**Faz 1 · Çekirdek** ✅  **Faz 2 · Veri** ✅  **Faz 3 · Görme** ✅
**Faz 4 · Anlama** ✅  **Faz 5 · Yönetme** ✅ — **yol haritası tamamlandı**
(El Kitabı Bölüm 12)

| Adım | İçerik | Durum |
|---|---|---|
| 1.1 | İskelet: tek HTML, menü, tema, yönlendirme | ✅ |
| 1.2 | Veri katmanı: IndexedDB + `.json` dışa/içe aktarma | ✅ |
| 1.3 | Ekran 14 — Tanımlar (6 sekme) | ✅ |
| 1.4 | Ekran 15 — Ayarlar ve Yedekleme | ✅ |
| 1.5 | Hesap çekirdeği | ✅ |
| 1.6 | Hesaplanan değerler katmanı (K-23) | ✅ |

| Adım | İçerik | Durum |
|---|---|---|
| 2.1 | Ekran 2 — Veri Girişi (dört yöntem) | ✅ |
| 2.2 | Doğrulama kuralları | ✅ |
| 2.3 | Ekran 3 — Veri Aktarma (.xlsx) | ✅ |
| 2.4 | Ekran 4 — Veri Denetimi | ✅ |
| 2.5 | Ekran 5 — Hesaplanan Değerler + Excel çıktısı | ✅ |

| Adım | İçerik | Durum |
|---|---|---|
| 3.1 | SVG grafik motoru (`js/grafik.js`) | ✅ |
| 3.2 | Ekran 1 — Gösterge Paneli | ✅ |
| 3.3 | Ekran 7 — Tüketim Analizi | ✅ |
| 3.4 | Ekran 6 — Enerji Dengesi (Sankey) | ✅ |

| Adım | İçerik | Durum |
|---|---|---|
| 4.1 | Baz çizgi ve regresyon, R² uyarıları | ✅ |
| 4.2 | Ekran 8 — Performans (normalize EnPI, CUSUM) | ✅ |
| 4.3 | Ekran 9 — Dönüşüm Verimliliği | ✅ |
| 4.4 | Ekran 10 — Maliyet (fiyat/hacim ayrıştırması) | ✅ |
| 4.5 | Ekran 11 — GES | ✅ |

| Adım | İçerik | Durum |
|---|---|---|
| 5.1 | Ekran 12 — Hedefler ve Aksiyonlar | ✅ |
| 5.2 | Ekran 13 — Raporlar (üç rapor) | ✅ |
| 5.3 | İzlenebilirlik (E-4): her sayıdan ham veriye iniş | ✅ |

**15 ekranın hepsi çalışıyor.** Excel'e ihtiyaç kalmadı, veri görünür oldu,
"neden" sorusu cevaplanabiliyor ve tespitler artık sahibi ile termini olan
aksiyonlara bağlanıyor.

## İzlenebilirlik (E-4) — `js/koken.js`

Her türetilmiş sayının yanındaki `?` düğmesi, o sayının **formülünü, kuralını,
katkıda bulunan ölçüm noktalarını ham değerleriyle ve kullanılan tarihli
katsayıları** gösterir (K-28). Köken ağacı hesaplanan noktalardan ham veriye
kadar iner: `TOPLAM_URETIM → TOPLAM_KAKAO → KAKAO_YAG/TOZ/LIKOR`.

Pencerede her düğüm bir rozet taşır: `ham veri` · `hesaplanan` ·
`dağıtılmış — ölçüm değil` · `TAHMİN` · `girilmemiş` · `üretilemedi`.
Katsayı satırı hangi katsayının hangi tarihten geçerli olduğunu yazar —
S12'deki 2025 değişimi bu pencerede kendiliğinden görünür.

## Analizden eyleme köprüsü

Üç ekrandaki tespitten doğrudan aksiyon açılabilir (9.13):
Ekran 7'de Pareto'nun ilk sırası · Ekran 8'de CUSUM birikimi ve eğim
kırılımı · Ekran 9'da verim düşüşü. Aksiyon formu başlığı, açıklamayı,
kaynağı ve beklenen tasarrufu önceden doldurulmuş gelir.

## Faz 4'te gerçek veride bulunanlar

Ekran 9 yazılırken kaynak veride iki yeni sorun çıktı (El Kitabı 2.5):

- **S12** — Excel 2025 Ocak'tan itibaren buhar entalpi varsayımını
  600'den 560 kcal/kg'a düşürmüş (`0,697674` → `0,651163` kWh/kg), üstelik
  bütün ekipmanlarda. Türbinin 6,9 puanlık verim düşüşünün **1,7 puanı**
  bu varsayımdan geliyor. İkisi de **tarihli katsayı** olarak tanımlandı
  (6.6, İ-5); ekran farkı puan puan ayrıştırıyor.
- **S13** — 2025'te kazanların ürettiği buhar, kendilerine atanmış gazdan
  büyük: Kazan-1 %137, Kazan-2 %145. Satın alınan gazın **%12,9'u** hiçbir
  ekipmana atanmamış. Program sayıyı gizlemiyor ama performans da saymıyor
  (**K-25**); bu ekipmanlar yıllar arası karşılaştırmadan çıkarılıyor.

Ayrıca **K-26**: yıllar arası verim karşılaştırması tek bir birleşik yüzdeyle
yapılamaz. Gerçek veride, gaz motorları durup yük türbine kayınca karma toplam
**iyileşmiş gibi** göründü — oysa çalışan ekipmanın verimi düşmüştü. Toplanan
büyüklük artık yüzde değil, **kaçınılabilir yakıt (kWh)**.

## Grafik motoru — kütüphanesiz

`js/grafik.js` (~670 satır, sıfır bağımlılık): sütun (tekli/yığılmış), çizgi
(referans hattı destekli), ısı haritası, Pareto, Sankey, dağılım (regresyon
doğrusuyla), CUSUM (kutuplu dolgu), şelale, mini grafik, oran çubuğu. Her grafikte fare üstü kutucuğu, çizgilerde dikey nişangâh ve
**"Tablo olarak göster"** seçeneği (E-3) var.

El Kitabı 5.7.2'deki yasaklar koda gömülü: çift eksen yok, kesikli kılavuz
yok, kategorik renkler sabit sırayla, 8'den fazlası "Diğer"e katlanıyor,
Pareto'nun kümülatif yüzdesi ikinci eksende değil tablo sütununda.

## .xlsx okuma/yazma — kütüphanesiz

K-15 ~400 KB'lık bir kütüphane gömmeyi öngörüyordu. Bunun yerine `js/xlsx.js`
yazıldı (~280 satır, sıfır bağımlılık): bir .xlsx zaten XML içeren bir ZIP'tir;
tarayıcının `DecompressionStream` / `CompressionStream` ve `DOMParser`
arayüzleri işi görür (K-11: Chrome/Edge). Gerçek 108 sütunluk dosya **63 ms**'de
okunuyor; yazma gidiş-dönüş yapıyor.

## Kullanım

```bash
python3 derle.py                 # kaynak/ -> cikti/enerji-yonetim.html
```

Çıktı **tek dosyadır**; çift tıklayıp tarayıcıda açılır. Sunucu, kurulum,
internet gerekmez (K-09).

## Kaynak düzeni (K-18)

```
kaynak/
  index.html              iskelet
  css/stil.css            görsel dil — renk paleti El Kitabı 5.7'den
  js/
    ortak.js              Türkçe sayı biçimi, DOM yardımcıları
    veri.js               IndexedDB + .json  (K-10)
    model.js              varlık ağacı, birim dönüşümü, doğrulama (6.8)
    hesap.js              HESAP ÇEKİRDEĞİ — tek hesap kaynağı (İ-2)
    hesaplanan.js         hesaplanan değerler katmanı (K-23)
    uygulama.js           kabuk: menü, üst şerit, yönlendirme
    ekranlar/             her ekran ayrı dosya
  baslangic.json          gömülü tanımlar (K-16) — betikler/baslangic_uret.py üretir
derle.py                  hepsini tek HTML'e gömer
cikti/enerji-yonetim.html teslim edilen dosya
```

ES modülleri `file://` üzerinden çalışmadığı için `derle.py` küçük bir modül
kaydı kurar: her modül kendi kapsamında bir fabrika fonksiyonu olur, `__req`
ile çözülür. Modül gizliliği korunur, ad çakışması olmaz.

## Sınama

```bash
python3 betikler/sina.py     # duman testi: açılış, ekranlar, sekmeler, tema
python3 betikler/kabul.py    # El Kitabı Bölüm 13 kabul kriterleri
python3 betikler/faz2.py     # uçtan uca: Excel aktarımı + 8 yılın altın sayıları
python3 betikler/faz3.py     # grafik ekranları
python3 betikler/faz4.py     # Faz 4 ekranları + 8.8 vakasının altın sayıları
python3 betikler/faz5.py     # Faz 5 ekranları + izlenebilirlik + hedef motoru
python3 betikler/kabul13.py  # El Kitabı Bölüm 13'ün HER satırı
```

`kabul.py`, gerçek 2024 Haziran verisiyle programın **altın sayıları** üretip
üretmediğini sınar (El Kitabı 13.3):

| Kontrol | Beklenen | Sonuç |
|---|---:|---|
| Toplam enerji | 10.800.103 kWh | ✅ |
| Toplam üretim | 8.868.323 kg | ✅ |
| EnPI | 1,2178 kWh/kg | ✅ |
| Türbin toplam verimi | %58,9 | ✅ |

Ayrıca: hesap katmanının her değişimde yeniden üretilmesi (K-23), doğrulama
kuralları (6.8), motorin kenar durumu (K-24) ve yedek gidiş-dönüşü (K-10).
**16 kontrol, hepsi geçiyor.**

`faz2.py` uçtan uca çalışır: gerçek Excel'i içe aktarır, **8 yılın bütün yıllık
altın sayılarını** doğrular, kaynak veri hatalarının yakalandığını sınar ve iki
sayfalı Excel çıktısının gidiş-dönüşünü kontrol eder. **36 kontrol, hepsi
geçiyor.**

`faz3.py` grafik ekranlarını sınar: boş durum, SVG çizimi, tablo görünümüne
geçiş, kesikli çizgi olmaması ve koyu tema. **14 kontrol, hepsi geçiyor.**

`faz4.py` Faz 4'ün üç ekranını ve El Kitabı 8.8 / 9.11'deki bütün altın sayıları
doğrular: türbin toplam verimi %57,2 → %50,3, yıllık kayıp 5,58 GWh, brüt
elektrik faturası 55.712.474 TL, GES mahsubu 25.723.468 TL, toplam maliyet
195.182.337 TL, elektrik fiyat etkisi +10.682.663 TL / hacim etkisi
−5.500.767 TL, doğalgaz hacim etkisi +13.475.761 TL, 2018 → 2025 birim fiyat
artışı 11 kat. Ayrıca S12 katsayı ayrıştırması, S13 imkânsız verim işaretlemesi
ve GES üretiminin toplam enerjiye girmediği (K-03) sınanır.
**80 kontrol, hepsi geçiyor.**

`faz5.py` hedef motorunu (dört türün dördü de), aksiyon gecikme takibini,
üç raporu, veri kalitesi notunu (İ-4) ve köken ağacını sınar. Baz çizgi
altın sayıları da burada doğrulanır: `a = 0,5025 · b = 6.021.966 · R² = 0,43`
(35 nokta), normalize EnPI 1,119, CUSUM yıl sonu +14.605.848 kWh, işaret
değişimi Şubat 2025. **72 kontrol, hepsi geçiyor.**

`kabul13.py` el kitabının Bölüm 13'ünü satır satır doğrular: aktarım kontrolü
(55 sütun eşlemesi, 4.541 değer, 7 ret, 96 enerji dönemi), sekiz yılın bütün
altın sayıları, 2024 Haziran nokta kontrolü, hesap motorunun sekiz çıktısı ve
on iki davranış kuralı (negatif engeli, kWh/m³ sapma uyarısı, 12 nokta kuralı,
katman yeniden üretimi, yedek gidiş-dönüşü). **96 kontrol, hepsi geçiyor.**

Bu doğrulama üç belge hatası buldu: aktarılan değer sayısı 4.534 değil 4.541
(beklenen sayı 7 reddedilen hücreyi iki kez düşmüş), 13.2'nin maliyet sütunu
brüt olduğu hâlde programın `Toplam Maliyet`'i net (K-24), ve 13.5'teki içe
aktarma satırı 9.4'le çelişiyordu. Üçü de el kitabında düzeltildi.

> **Baz çizgi sayıları neden değişti?** El Kitabı 8.8/13.4'teki eski değerler
> (`a = 0,4254 · b = 6.774.643 · R² = 0,40`) Excel'in kendi `Toplam Üretim`
> sütunuyla, 36 ay üzerinden hesaplanmıştı. Program 2024 Ağustos'un üretimini
> S10 yüzünden üretemediği için o ay regresyona giremez; doğru model 35
> noktalıdır. Aradaki fark, tek bir bozuk hücrenin baz çizgiyi ne kadar
> kaydırdığının ölçüsüdür.

> `derle.py` artık çıktıyı `node --check` ile ayrıştırır; sözdizimi hatası
> varsa dosya **yazılmaz**. Bozuk bir paket teslim edilemez.

## Başlangıç tanımlarını yeniden üretmek

```bash
python3 betikler/baslangic_uret.py
```

Excel'in sütun yapısından varlık ağacı (38) ve ölçüm noktaları (69) üretir.
`toplama_dahil` bayrağı kritiktir: fabrika toplamına yalnız üst seviye giriş
noktaları girer; alt kırılımlar (GM-1 doğalgazı gibi) girmez — aksi hâlde çift
sayım olur (6.7).
