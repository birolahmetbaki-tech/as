# Shorts Otomatik Geçiş (Chrome eklentisi)

YouTube Shorts videoları normalde bitince başa sarıp tekrar oynar. Bu eklenti,
video bittiğinde otomatik olarak **bir sonraki Shorts videosuna** geçer.

## Kurulum

1. Chrome'da `chrome://extensions` adresini açın.
2. Sağ üstten **Geliştirici modu**nu açın.
3. **Paketlenmemiş öğe yükle** düğmesine basıp bu `shorts-otomatik-gecis` klasörünü seçin.
4. `youtube.com/shorts/...` adresinde bir Shorts açın — video bitince sıradakine geçilir.

> Eklentiyi kurmadan önce açık olan YouTube sekmelerini yenileyin.

## Kullanım

- Araç çubuğundaki eklenti simgesine tıklayıp **Otomatik geçiş açık** kutusuyla
  özelliği açıp kapatabilirsiniz. Kapalıyken Shorts eskisi gibi döngüde oynar.

## Nasıl çalışır?

- Aktif Shorts videosunun döngüsünü (`loop`) kapatır; video bitince (`ended`)
  "Sonraki video" düğmesine basar.
- YouTube döngüyü yeniden açarsa, videonun sondan başa sarıldığı anı yakalayarak
  yine sonraki videoya geçer.
- Düğme bulunamazsa Aşağı ok tuşu ve kaydırma ile yedek geçiş dener.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `manifest.json` | Eklenti tanımı (Manifest V3) |
| `content.js` | YouTube sayfasında çalışan otomatik geçiş betiği |
| `popup.html`, `popup.js` | Aç/kapa penceresi |
| `icons/` | Eklenti simgeleri |
