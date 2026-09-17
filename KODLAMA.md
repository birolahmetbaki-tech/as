# Enerji Yönetim Platformu — geliştirme notları

Tasarımın tamamı **[docs/EL-KITABI.md](docs/EL-KITABI.md)** içindedir. Bu dosya
yalnızca kaynağın nasıl derlendiğini ve sınandığını anlatır.

## Durum

**Faz 1 — Çekirdek · tamamlandı.** (El Kitabı Bölüm 12)

| Adım | İçerik | Durum |
|---|---|---|
| 1.1 | İskelet: tek HTML, menü, tema, yönlendirme | ✅ |
| 1.2 | Veri katmanı: IndexedDB + `.json` dışa/içe aktarma | ✅ |
| 1.3 | Ekran 14 — Tanımlar (6 sekme) | ✅ |
| 1.4 | Ekran 15 — Ayarlar ve Yedekleme | ✅ |
| 1.5 | Hesap çekirdeği | ✅ |
| 1.6 | Hesaplanan değerler katmanı (K-23) | ✅ |

Sıradaki: **Faz 2 — Veri** (Ekran 2 Veri Girişi, 3 Aktarma, 4 Denetim, 5 Hesaplanan Değerler).
Faz 2 bittiğinde Excel'e ihtiyaç kalmaz.

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

## Başlangıç tanımlarını yeniden üretmek

```bash
python3 betikler/baslangic_uret.py
```

Excel'in sütun yapısından varlık ağacı (38) ve ölçüm noktaları (69) üretir.
`toplama_dahil` bayrağı kritiktir: fabrika toplamına yalnız üst seviye giriş
noktaları girer; alt kırılımlar (GM-1 doğalgazı gibi) girmez — aksi hâlde çift
sayım olur (6.7).
