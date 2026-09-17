/* ekranlar/ayarlar.js — Ekran 15: Ayarlar ve Yedekleme (El Kitabı 9.16)
   Tek HTML mimarisinde (K-09) bu ekran veri güvenliğinin merkezidir. */

import { el, $, bosalt, say, kisa, uyari, bildir, onayla, tarihMetni,
         donemAd, dosyaIndir, tablo } from "../ortak.js";
import * as V from "../veri.js";
import { katman, uret } from "../hesaplanan.js";

export function ekranAyarlar(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Ayarlar ve Yedekleme" }),
    el("p", { metin:"Program tek bir HTML dosyasıdır ve veriniz ayrı durur. Veri kaybı bu mimarinin tek ciddi riskidir — bu ekran onu görünür tutar." })));

  genel(k); veri(k); yedek(k); tanilama(k); tehlikeli(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranAyarlar(k); };

/* ------------------------------------------------------------- genel */
function genel(k) {
  const a = V.durum.ayarlar;
  const kart = el("div.kart", {}, el("h2", { metin:"Genel" }));
  const alan = (etiket, deger, uygula, ipucu) => {
    const g = el("input", { type:"text", value:deger ?? "",
      onchange:e => { uygula(e.target.value); V.degisti("ayar"); bildir("Kaydedildi"); } });
    kart.append(el("div.alan", {}, el("label", { metin:etiket }), g,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null));
  };
  alan("Fabrika adı", a.fabrika_adi, v => a.fabrika_adi = v);
  alan("Para birimi", a.para_birimi, v => a.para_birimi = v);

  const sec = (etiket, deger, secenekler, uygula, ipucu) => {
    const g = el("select", { onchange:e => { uygula(e.target.value); V.degisti("ayar"); bildir("Kaydedildi"); } });
    for (const [d, ad] of secenekler)
      g.append(el("option", { value:d, metin:ad, selected:deger === d }));
    kart.append(el("div.alan", {}, el("label", { metin:etiket }), g,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null));
  };
  sec("Varsayılan enerji birimi", a.varsayilan_birim,
      [["kWh","kWh"],["MJ","MJ"],["GJ","GJ"],["TEP","TEP"]], v => a.varsayilan_birim = v,
      "Ortak birimde toplam gösterilirken kullanılır. 1 TEP = 41,868 GJ = 11.630 kWh");
  sec("Ana EnPI göstergesi", a.ana_enpi,
      V.durum.enpi_tanimlari.map(t => [t.kod, t.ad]), v => a.ana_enpi = v);
  sec("Tema", a.tema || "otomatik",
      [["otomatik","İşletim sistemine uy"],["acik","Açık"],["koyu","Koyu"]],
      v => { a.tema = v; document.documentElement.dataset.tema = v; });
  k.append(kart);
}

/* -------------------------------------------------------------- veri */
function veri(k) {
  const ar = V.veriAraligi();
  const kart = el("div.kart", {}, el("h2", { metin:"Veri özeti" }));
  const sat = [
    ["Ham değer", say(V.durum.degerler.length)],
    ["Dönem aralığı", ar ? `${donemAd(ar.ilk.yil, ar.ilk.ay)} → ${donemAd(ar.son.yil, ar.son.ay)}` : "— veri yok"],
    ["Varlık", say(V.durum.varliklar.length)],
    ["Ölçüm noktası", say(V.durum.olcum_noktalari.length)],
    ["  · ölçülen", say(V.durum.olcum_noktalari.filter(n => n.veri_tipi === "olculen").length)],
    ["  · hesaplanan", say(V.durum.olcum_noktalari.filter(n => n.veri_tipi !== "olculen").length)],
    ["Dönüşüm katsayısı", say(V.durum.donusum_katsayilari.length)],
    ["EnPI tanımı", say(V.durum.enpi_tanimlari.length)],
    ["Baz çizgi", say(V.durum.baz_cizgiler.length)],
  ];
  const t = el("table");
  for (const [a, b] of sat) t.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td.s", { metin:String(b) })));
  kart.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t));

  kart.append(el("h3", { metin:"Hesaplanan değerler katmanı", stil:{ marginTop:"16px" } }));
  kart.append(el("p.kucuk.sessiz", { metin:
    "Bu katman bir aynadır, kayıt değil (K-23). Açılışta ve her veri değişiminde baştan üretilir; yedek dosyasına yazılmaz." }));
  const t2 = el("table");
  for (const [a, b] of [
    ["Son üretim", katman.uretim ? tarihMetni(katman.uretim) : "—"],
    ["Süre", katman.sure + " ms"],
    ["Dönem × değer", `${katman.satirlar.length} × ${katman.sutunlar.length} = ${say(katman.hucre)} hücre`],
    ["Üretilemeyen değer", say(katman.eksikler.length)],
  ]) t2.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td.s", { metin:String(b) })));
  kart.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t2));
  kart.append(el("button.dugme.kucuk", { metin:"Katmanı yeniden üret", stil:{ marginTop:"10px" },
    onclick:() => { uret(); yenile(); bildir(`Katman yeniden üretildi (${katman.sure} ms)`); } }));

  if (katman.eksikler.length) {
    const ilk = katman.eksikler.slice(0, 5);
    kart.append(uyari("dikkat",
      el("b", { metin:`${katman.eksikler.length} değer üretilemedi. ` }),
      "Sistem eksik veriyi sıfır saymaz (İ-3); nedeni aşağıda:",
      el("ul.kuciik", { stil:{ margin:"6px 0 0 18px", padding:"0" } },
        ilk.map(e => el("li", { metin:`${e.donem} · ${e.ad}: ${e.sebep}` })),
        katman.eksikler.length > 5 ? el("li.sessiz", { metin:`…ve ${katman.eksikler.length - 5} tane daha` }) : null)));
  }
  k.append(kart);
}

/* ----------------------------------------------------------- yedekleme */
function yedek(k) {
  const y = V.yedekDurumu();
  const kart = el("div.kart", {}, el("h2", { metin:"Yedekleme" }));

  kart.append(uyari(y.uyarmali ? "dikkat" : "iyi",
    el("b", { metin:y.aciklama }),
    y.tarih ? el("div.kucuk", { metin:y.metin }) : null,
    el("div.kucuk", { stil:{ marginTop:"4px" }, metin:
      "Veri tarayıcının deposunda otomatik saklanır. Ancak tarayıcı verisi temizlenirse silinir, gizli sekmede görünmez ve başka bilgisayara taşınmaz. Yedek dosyası bu üçünün de çözümüdür." })));

  kart.append(el("div.satir", {},
    el("button.dugme.ana", { metin:"Yedek al (.json)",
      onclick:() => { V.yedekAl(); yenile(); bildir("Yedek indirildi"); } }),
    el("label.dugme", { metin:"Geri yükle…", stil:{ cursor:"pointer" } },
      el("input", { type:"file", accept:".json,application/json", stil:{ display:"none" },
        onchange:e => geriYukle(e.target.files[0]) }))));

  /* Chrome/Edge: dosyaya doğrudan yazma (K-11) */
  kart.append(el("h3", { metin:"Dosyaya doğrudan yazma", stil:{ marginTop:"18px" } }));
  if (!V.dosyaYazmaDestegi())
    kart.append(el("p.kucuk.sessiz", { metin:
      "Bu tarayıcı desteklemiyor. Chrome veya Edge'de program veriyi seçtiğiniz dosyaya doğrudan yazabilir — tıpkı Excel gibi." }));
  else if (V.dosyaYazmaAcik())
    kart.append(uyari("iyi", "Açık — her değişiklik doğrudan dosyaya yazılıyor.",
      el("div", { stil:{ marginTop:"6px" } }, el("button.dugme.kucuk", { metin:"Kapat",
        onclick:() => { V.dosyaYazmaKapat(); yenile(); } }))));
  else
    kart.append(el("div", {},
      el("p.kucuk.sessiz", { metin:"Bir kez veri dosyası seçersiniz; program bundan sonra her değişikliği doğrudan o dosyaya yazar. Yedek alma işi kendiliğinden halledilir." }),
      el("button.dugme", { metin:"Veri dosyası seç", onclick:async () => {
        try { const ad = await V.dosyaYazmaAc(); yenile(); bildir("Bağlandı: " + ad); }
        catch (e) { if (e.name !== "AbortError") bildir(e.message, "kritik"); } } })));
  k.append(kart);
}

async function geriYukle(dosya) {
  if (!dosya) return;
  let c;
  try { c = await V.yedegiCoz(dosya); }
  catch (e) { return bildir(e.message, "kritik"); }
  const o = c.ozet;
  const ozet = el("div", {},
    el("p", {}, "Bu yedek dosyasının içeriği:"),
    el("div.tablo-sar", { stil:{ maxHeight:"none" } }, (() => {
      const t = el("table");
      for (const [a, b] of [
        ["Ham değer", say(o.deger)],
        ["Dönem aralığı", o.ilk ? `${donemAd(o.ilk.y, o.ilk.a)} → ${donemAd(o.son.y, o.son.a)}` : "veri yok"],
        ["Ölçüm noktası", say(o.nokta)], ["Varlık", say(o.varlik)],
        ["Oluşturma", tarihMetni(o.olusturma)], ["Son güncelleme", tarihMetni(o.guncelleme)],
      ]) t.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td.s", { metin:String(b) })));
      return t;
    })()),
    uyari("kritik", el("b", { metin:"Mevcut veriniz silinecek ve bu yedekle değiştirilecek. " }),
      `Şu an sistemde ${say(V.durum.degerler.length)} ham değer var.`),
    el("p.kucuk.sessiz", { metin:"Onaylarsanız önce mevcut verinizin güvenlik yedeği indirilecek." }));

  const ok = await onayla("Yedeği geri yükle", ozet, "Geri yükle", true);
  if (!ok) return;
  V.guvenlikYedegi();
  V.yedegiUygula(c.nesne);
  yenile();
  bildir(`Geri yüklendi — ${say(o.deger)} değer`);
}

/* ----------------------------------------------------------- tanılama */
function tanilama(k) {
  const kart = el("div.kart", {}, el("h2", { metin:"Tanılama" }));
  const t = el("table");
  const sat = [
    ["Program sürümü", "Faz 1 · Çekirdek"],
    ["Veri şema sürümü", String(V.SEMA_SURUMU)],
    ["Tarayıcı", navigator.userAgent.includes("Edg") ? "Edge"
                : navigator.userAgent.includes("Chrome") ? "Chrome"
                : navigator.userAgent.includes("Firefox") ? "Firefox" : "Diğer"],
    ["Dosyaya yazma desteği", V.dosyaYazmaDestegi() ? "Var" : "Yok"],
  ];
  for (const [a, b] of sat) t.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td", { metin:b })));
  kart.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t));
  V.depoKullanimi().then(d => {
    if (!d) return;
    kart.append(el("p.kucuk.sessiz", { stil:{ marginTop:"8px" }, metin:
      `Tarayıcı deposu: ${kisa(d.kullanim / 1048576, 1)} MB kullanılıyor / ${kisa(d.kota / 1048576, 0)} MB ayrılmış` }));
  });
  k.append(kart);
}

/* ---------------------------------------------------------- tehlikeli */
function tehlikeli(k) {
  const kart = el("div.kart", { stil:{ borderColor:"var(--kritik)" } },
    el("h2", { metin:"Tehlikeli işlemler" }),
    el("p.kucuk.sessiz", { metin:"Bu işlemler geri alınamaz." }));
  kart.append(el("button.dugme.tehlike", { metin:"Bütün ham veriyi sil", onclick:async () => {
    if (!V.durum.degerler.length) return bildir("Zaten veri yok");
    const ok1 = await onayla("Bütün ham veriyi sil",
      `${say(V.durum.degerler.length)} ham değer silinecek. Tanımlar (varlık ağacı, ölçüm noktaları) kalacak. Bu işlem geri alınamaz.`,
      "Devam et", true);
    if (!ok1) return;
    const ok2 = await onayla("Emin misiniz?",
      "Önce güvenlik yedeği indirilecek. Yine de devam edilsin mi?", "Evet, sil", true);
    if (!ok2) return;
    V.guvenlikYedegi();
    await V.hepsiniSil();
    yenile(); bildir("Ham veri silindi", "kritik");
  } }));
  k.append(kart);
}
