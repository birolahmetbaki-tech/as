/* ekranlar/denetim.js — Ekran 4: Veri Denetimi (El Kitabı 9.5)
   "Verim sağlam mı?" — Analiz ekranlarına güvenmeden önce bakılacak yer. */

import { el, $, bosalt, say, yuzde, uyari, bildir, tablo, bosDurum,
         donemAd, donemKisa, donemAraligi } from "../ortak.js";
import * as V from "../veri.js";
import { nokta, varlik, dogrula, ENGEL, devrede } from "../model.js";
import { katman } from "../hesaplanan.js";
import { oranCubugu } from "../grafik.js";

let sekme = "bulgu";

export function ekranDenetim(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Veri Denetimi" }),
    el("p", { metin:"Bütün veri setinin sağlığı. Analiz ekranlarındaki sayılara güvenmeden önce buraya bakın." })));

  const ar = V.veriAraligi();
  if (!ar) { k.append(bosDurum("Henüz veri yok",
    "Veri Aktarma ekranından Excel dosyanızı alın veya Veri Girişi ekranından elle girin.",
    el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));
    return; }

  const rapor = denetle(ar);
  gostergeler(k, rapor);

  const s = el("div.sekmeler", {});
  for (const [kod, ad] of [["bulgu", `Bulgular (${rapor.bulgular.length})`],
                           ["harita","Eksik veri haritası"],
                           ["kapsam","Ölçüm kapsamı"]])
    s.append(el("button.sekme", { "aria-selected":sekme === kod ? "true" : "false",
      metin:ad, onclick:() => { sekme = kod; yenile(); } }));
  k.append(s);

  ({ bulgu:cizBulgular, harita:cizHarita, kapsam:cizKapsam }[sekme])(k, rapor);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranDenetim(k); };

/* -------------------------------------------------------------- denetim */
function denetle(ar) {
  const donemler = donemAraligi(ar.ilk.yil, ar.ilk.ay, ar.son.yil, ar.son.ay);
  const noktalar = V.durum.olcum_noktalari.filter(n =>
    n.aktif !== false && (n.veri_tipi === "olculen" || n.veri_tipi === "tahmini"));
  const bulgular = [];
  const yoksayilan = V.durum.ayarlar?.yoksayilan_bulgular || {};
  let dolu = 0, beklenen = 0, bos = 0;

  for (const n of noktalar) {
    for (const d of donemler) {
      const v = V.deger(n.kod, d.yil, d.ay);
      const varlikAktif = devrede(n.varlik, d.yil, d.ay);
      if (varlikAktif) beklenen++;
      if (v === null) { if (varlikAktif) bos++; continue; }
      dolu++;
      for (const b of dogrula(n.kod, d.yil, d.ay, v)) {
        const anahtar = `${n.kod}|${d.yil}-${d.ay}|${b.mesaj.slice(0, 30)}`;
        if (yoksayilan[anahtar]) continue;
        bulgular.push({ anahtar, kod:n.kod, ad:n.ad, varlik:varlik(n.varlik)?.ad || "",
          yil:d.yil, ay:d.ay, donem:donemAd(d.yil, d.ay), deger:v,
          seviye:b.seviye, mesaj:b.mesaj });
      }
    }
  }
  // Hesap katmanının üretemedikleri (İ-3)
  const uretilemeyen = katman.eksikler || [];
  return { donemler, noktalar, bulgular, dolu, beklenen, bos, uretilemeyen,
           doluluk: beklenen ? dolu / beklenen : 0 };
}

/* ---------------------------------------------------------- göstergeler */
function gostergeler(k, r) {
  const kutu = (baslik, deger, alt, durum) => el("div.kart", {
    stil:{ flex:"1 1 190px", margin:"0" } },
    el("div.mini.sessiz", { metin:baslik }),
    el("div", { stil:{ fontSize:"22px", fontWeight:"600", margin:"4px 0 2px" } },
      el("span.sayi", { metin:deger })),
    el("div.mini" + (durum ? ".sessiz" : ".sessiz"), { metin:alt }));

  k.append(el("div.satir", { stil:{ marginBottom:"16px" } },
    kutu("Doluluk", yuzde(r.doluluk * 100, 1),
         `${say(r.dolu)} / ${say(r.beklenen)} hücre`),
    kutu("Boş hücre", say(r.bos), "varlık devredeyken beklenen ama girilmemiş"),
    kutu("Şüpheli değer", say(r.bulgular.filter(b => b.seviye !== ENGEL).length), "doğrulama uyarısı"),
    kutu("Üretilemeyen", say(r.uretilemeyen.length), "hesaplanamayan türetilmiş değer")));

  if (r.bulgular.some(b => b.seviye === ENGEL))
    k.append(uyari("kritik", el("b", { metin:"Kural dışı değer var. " }),
      "Aşağıdaki bulgularda 'engel' seviyesindekiler normalde girilemez; " +
      "eski bir yedekten gelmiş olabilirler."));
}

/* ------------------------------------------------------------ bulgular */
function cizBulgular(k, r) {
  if (!r.bulgular.length && !r.uretilemeyen.length) {
    k.append(uyari("iyi", el("b", { metin:"Temiz. " }),
      "Doğrulama kurallarının hiçbiri tetiklenmedi ve bütün türetilmiş değerler üretilebiliyor."));
    return;
  }
  if (r.bulgular.length) {
    k.append(el("h2", { metin:"Doğrulama bulguları" }));
    k.append(tablo([
      { ad:"Dönem", anahtar:"donem" },
      { ad:"Ölçüm noktası", deger:b => el("span", {}, b.ad,
          el("span.mini.sessiz", { metin:"  " + b.varlik })) },
      { ad:"Değer", sayi:true, ondalik:2, anahtar:"deger" },
      { ad:"Bulgu", deger:b => el("span", {},
          el("span.rozet" + (b.seviye === ENGEL ? ".kritik" : ".dikkat"),
             { metin:b.seviye === ENGEL ? "engel" : "uyarı" }),
          " " + b.mesaj) },
      { ad:"", deger:b => el("div.satir", { stil:{ gap:"4px" } },
          el("button.dugme.kucuk", { metin:"Düzelt", title:"Bu hücrenin giriş ekranına git",
            onclick:() => { location.hash = "e2"; bildir(`${b.donem} · ${b.ad}`); } }),
          el("button.dugme.kucuk", { metin:"Sorun değil",
            title:"Bilinçli — bir daha uyarma (kaydı kalır)",
            onclick:() => yoksay(b) })) },
    ], r.bulgular.slice(0, 200)));
    if (r.bulgular.length > 200)
      k.append(el("p.kucuk.sessiz", { metin:`İlk 200 bulgu gösteriliyor (toplam ${say(r.bulgular.length)}).` }));
  }

  if (r.uretilemeyen.length) {
    k.append(el("h2", { metin:"Üretilemeyen değerler", stil:{ marginTop:"22px" } }));
    k.append(el("p.kucuk.sessiz", { metin:
      "Sistem eksik veriyi sıfır saymaz (İ-3). Aşağıdaki türetilmiş değerler üretilemedi ve nedeni yazılı." }));
    k.append(tablo([
      { ad:"Dönem", anahtar:"donem" }, { ad:"Değer", anahtar:"ad" },
      { ad:"Neden", anahtar:"sebep" },
    ], r.uretilemeyen.slice(0, 200)));
  }

  const y = V.durum.ayarlar?.yoksayilan_bulgular || {};
  const n = Object.keys(y).length;
  if (n) k.append(el("p.kucuk.sessiz", { stil:{ marginTop:"14px" } },
    `${n} bulgu "sorun değil" olarak işaretlendi. `,
    el("button.dugme.kucuk", { metin:"İşaretleri temizle",
      onclick:() => { V.durum.ayarlar.yoksayilan_bulgular = {}; V.degisti("denetim"); yenile(); } })));
}

function yoksay(b) {
  V.durum.ayarlar.yoksayilan_bulgular ||= {};
  V.durum.ayarlar.yoksayilan_bulgular[b.anahtar] =
    { tarih:new Date().toISOString(), mesaj:b.mesaj };
  V.degisti("denetim"); yenile();
  bildir("İşaretlendi — bir daha uyarmayacak");
}

/* ------------------------------------------------- eksik veri haritası */
function cizHarita(k, r) {
  k.append(el("p.kucuk.sessiz", { metin:
    "Satır: ölçüm noktası · Sütun: dönem. Dolu, boş ve devre dışı hücreler ayrı gösterilir. " +
    "Bir varlığın ne zaman durduğu burada apaçık görünür." }));

  const t = el("table", { stil:{ fontSize:"11px" } });
  const bas = el("tr", {}, el("th", { stil:{ minWidth:"200px" }, metin:"Ölçüm noktası" }));
  const adim = Math.max(1, Math.ceil(r.donemler.length / 60));
  const gosterilen = r.donemler.filter((_, i) => i % adim === 0);
  for (const d of gosterilen)
    bas.append(el("th", { stil:{ padding:"2px", writingMode:"vertical-rl", fontSize:"9px" },
      metin:donemKisa(d.yil, d.ay) }));
  t.append(el("thead", {}, bas));

  const gv = el("tbody");
  for (const n of r.noktalar) {
    const tr = el("tr", {}, el("td", { stil:{ whiteSpace:"nowrap" }, title:n.kod, metin:n.ad }));
    for (const d of r.donemler.filter((_, i) => i % adim === 0)) {
      const v = V.deger(n.kod, d.yil, d.ay);
      const aktif = devrede(n.varlik, d.yil, d.ay);
      const renk = v !== null ? "var(--s1)" : !aktif ? "var(--kilavuz)" : "var(--uyari)";
      const baslik = `${n.ad}\n${donemAd(d.yil, d.ay)}\n` +
        (v !== null ? say(v, 2) + " " + n.birim : !aktif ? "varlık devre dışı" : "BOŞ");
      tr.append(el("td", { stil:{ padding:"1px" }, title:baslik },
        el("div", { stil:{ width:"9px", height:"14px", borderRadius:"2px", background:renk,
          opacity:v !== null ? .85 : aktif ? .9 : .35 } })));
    }
    gv.append(tr);
  }
  t.append(gv);
  k.append(el("div.tablo-sar", { stil:{ maxHeight:"62vh" } }, t));
  k.append(el("div.satir", { stil:{ marginTop:"10px", gap:"16px", fontSize:"12px" } },
    isaret("var(--s1)", "dolu"), isaret("var(--uyari)", "boş — beklenen"),
    isaret("var(--kilavuz)", "varlık devre dışı")));
  if (adim > 1) k.append(el("p.mini.sessiz", { metin:`Her ${adim}. dönem gösteriliyor.` }));
}

const isaret = (renk, ad) => el("span", { stil:{ display:"inline-flex", alignItems:"center", gap:"5px" } },
  el("span", { stil:{ width:"9px", height:"14px", borderRadius:"2px", background:renk, display:"inline-block" } }),
  el("span.sessiz", { metin:ad }));

/* --------------------------------------------------------- kapsam */
function cizKapsam(k, r) {
  k.append(el("p.kucuk.sessiz", { metin:
    "Fabrika toplamına giren noktalar ile bunların altındaki ölçülen noktaların oranı. " +
    "Ölçülmeyen pay, alt sayaç yatırımının nereye yapılacağını söyler (6.7)." }));

  const son = r.donemler[r.donemler.length - 1];
  const altSayaclar = V.durum.olcum_noktalari.filter(n =>
    n.rol === "satin_alinan" && !n.toplama_dahil && n.birim === "kWh" &&
    n.enerji_turu === "ELK" && n.veri_tipi === "olculen");

  const satirlar = [];
  for (const d of r.donemler) {
    const ust = V.deger("SEBEKE_ELK", d.yil, d.ay);
    if (ust === null) continue;
    let olculen = 0, say_ = 0;
    for (const n of altSayaclar) {
      const v = V.deger(n.kod, d.yil, d.ay);
      if (v !== null) { olculen += v; say_++; }
    }
    satirlar.push({ donem:donemAd(d.yil, d.ay), ust, olculen,
      olcumeyen:ust - olculen, oran:ust ? olculen / ust : 0, say:say_ });
  }
  if (!satirlar.length) { k.append(bosDurum("Kapsam hesaplanamadı",
    "Şebeke elektriği verisi bulunamadı.")); return; }

  const sonS = satirlar[satirlar.length - 1];
  k.append(uyari(sonS.oran < 0.5 ? "dikkat" : "iyi",
    el("b", { metin:`Son dönem ölçüm kapsamı: ${yuzde(sonS.oran * 100, 1)}. ` }),
    `Elektriğin ${yuzde((1 - sonS.oran) * 100, 1)}'i ölçülmüyor. ` +
    "Bu, tüketimin nereye gittiğini bilmediğiniz kısımdır."));

  k.append(tablo([
    { ad:"Dönem", anahtar:"donem" },
    { ad:"Şebeke (kWh)", sayi:true, anahtar:"ust" },
    { ad:"Ölçülen (kWh)", sayi:true, anahtar:"olculen" },
    { ad:"Ölçülmeyen (kWh)", sayi:true, anahtar:"olcumeyen" },
    { ad:"Kapsam", deger:s => el("div.satir", { stil:{ gap:"8px", alignItems:"center" } },
        oranCubugu(s.oran, { en:70 }), el("span.sayi.mini", { metin:yuzde(s.oran * 100, 1) })) },
    { ad:"Sayaç", sayi:true, anahtar:"say" },
  ], satirlar.slice().reverse()));
}
