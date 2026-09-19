/* ekranlar/tuketim.js — Ekran 7: Tüketim Analizi (El Kitabı 9.8)
   "Nereye bakmalıyım?" */

import { el, $, bosalt, say, kisa, yuzde, fark, uyari, bosDurum, tablo,
         donemAd, donemKisa, donemKaydir, donemAraligi, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { nokta, varlik, agac, altAgac, varlikNoktalari, cevir,
         ENERJI_BIRIMLERI } from "../model.js";
import * as H from "../hesap.js";
import { sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";
import { aksiyonAc } from "./hedefler.js";

let f = null;   // filtre durumu

export function ekranTuketim(k) {
  const ar = V.veriAraligi();
  if (!ar) { k.append(el("div.sayfa-basi", {}, el("h1", { metin:"Tüketim Analizi" })));
    k.append(bosDurum("Henüz veri yok", "Önce Veri ekranının Aktar sekmesinden verinizi alın.",
      el("button.dugme.ana", { metin:"Veri ekranına git", onclick:() => { location.hash = "e2"; } })));
    return; }

  if (!f) {
    const son = sonEnerjiDonemi() || ar.son;          // GES'e değil, enerji verisine göre
    f = { bas:{ yil:Math.max(ar.ilk.yil, son.yil - 2), ay:1 },
          son:{ yil:son.yil, ay:son.ay }, varlik:"FAB", birim:"kWh",
          karsilastir:true, sekme:"trend" };
  }

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Tüketim Analizi" }),
    el("p", { metin:"Tüketimi farklı kırılımlarda inceleyip en büyük ve en anormal kalemleri bulun." })));

  filtreCubugu(k, ar);

  const s = el("div.sekmeler", {});
  for (const [kod, ad] of [["trend","Trend"],["isi","Isı haritası"],
                           ["pareto","Pareto"],["karsilastir","Dönem karşılaştırma"]])
    s.append(el("button.sekme", { "aria-selected":f.sekme === kod ? "true" : "false",
      metin:ad, onclick:() => { f.sekme = kod; yenile(); } }));
  k.append(s);

  ({ trend:cizTrend, isi:cizIsi, pareto:cizPareto, karsilastir:cizKarsilastir }[f.sekme])(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranTuketim(k); };

/* --------------------------------------------------------- filtreler */
function filtreCubugu(k, ar) {
  const donemSec = (etiket, hedef) => {
    const ay = el("select", { onchange:e => { f[hedef].ay = +e.target.value; yenile(); } });
    AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a.slice(0, 3),
      selected:f[hedef].ay === i + 1 })));
    const yil = el("select", { onchange:e => { f[hedef].yil = +e.target.value; yenile(); } });
    for (let y = ar.ilk.yil; y <= ar.son.yil; y++)
      yil.append(el("option", { value:y, metin:y, selected:f[hedef].yil === y }));
    return el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:etiket }),
      el("div.satir", { stil:{ gap:"4px" } }, ay, yil));
  };

  const vSec = el("select", { onchange:e => { f.varlik = e.target.value; yenile(); } });
  const gez = (d, derinlik) => {
    for (const x of d) {
      vSec.append(el("option", { value:x.kod, metin:"　".repeat(derinlik) + x.ad,
        selected:f.varlik === x.kod }));
      gez(x.cocuklar, derinlik + 1);
    }
  };
  gez(agac(), 0);

  const bSec = el("select", { onchange:e => { f.birim = e.target.value; yenile(); } });
  for (const b of ENERJI_BIRIMLERI)
    bSec.append(el("option", { value:b, metin:b, selected:f.birim === b }));

  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      donemSec("Başlangıç", "bas"), donemSec("Bitiş", "son"),
      el("div.alan", { stil:{ margin:"0", minWidth:"200px" } },
        el("label", { metin:"Varlık" }), vSec),
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Birim" }), bSec))));
}

const donemler = () => donemAraligi(f.bas.yil, f.bas.ay, f.son.yil, f.son.ay);

/** Seçilen varlığın altındaki enerji tüketimi (seçilen birimde) */
function seriDeger(varlikKod, yil, ay) {
  const r = H.varlikToplami(varlikKod, yil, ay, { rol:"satin_alinan", birim:f.birim });
  return r.deger;
}

/* ------------------------------------------------------------- trend */
function cizTrend(k) {
  const d = donemler();
  if (d.length > 120) { k.append(uyari("dikkat", "Seçilen aralık çok uzun (120 aydan fazla).")); return; }
  const et = d.map(x => donemKisa(x.yil, x.ay));
  const deg = d.map(x => seriDeger(f.varlik, x.yil, x.ay));
  const v = varlik(f.varlik);

  if (!deg.some(Number.isFinite)) {
    k.append(bosDurum(`${v?.ad} için veri yok`,
      "Bu varlığın altında bu dönem aralığında ölçüm yok. Başka bir varlık veya aralık seçin."));
    return;
  }
  const kart = el("div.kart", {}, el("h2", { metin:`${v?.ad} · tüketim trendi` }));
  k.append(kart);
  G.sutun(kart, { seriler:[{ ad:v?.ad || "Tüketim", degerler:deg }], etiketler:et,
                  birim:f.birim, boy:280 });

  const gecerli = deg.filter(Number.isFinite);
  if (gecerli.length) {
    const t = gecerli.reduce((a, b) => a + b, 0);
    kart.append(el("div.satir", { stil:{ gap:"22px", marginTop:"10px", fontSize:"13px" } },
      el("span", {}, el("span.sessiz", { metin:"Toplam: " }),
        el("b.sayi", { metin:`${say(t, 0)} ${f.birim}` })),
      el("span", {}, el("span.sessiz", { metin:"Ortalama: " }),
        el("b.sayi", { metin:`${say(t / gecerli.length, 0)} ${f.birim}/ay` })),
      el("span", {}, el("span.sessiz", { metin:"En yüksek: " }),
        el("b.sayi", { metin:say(Math.max(...gecerli), 0) })),
      el("span", {}, el("span.sessiz", { metin:"En düşük: " }),
        el("b.sayi", { metin:say(Math.min(...gecerli), 0) }))));
  }
}

/* ------------------------------------------------------- ısı haritası */
function cizIsi(k) {
  const d = donemler();
  const yillar = [...new Set(d.map(x => x.yil))];
  const deg = yillar.map(y => AYLAR.map((_, i) => {
    const bul = d.find(x => x.yil === y && x.ay === i + 1);
    return bul ? seriDeger(f.varlik, y, i + 1) : null;
  }));
  const v = varlik(f.varlik);
  const kart = el("div.kart", {}, el("h2", { metin:`${v?.ad} · yıl × ay` }),
    el("p.mini.sessiz", { metin:
      "Mevsimselliği açığa çıkarır: aynı ayın yıllar boyunca nasıl değiştiği ve " +
      "yıl içindeki aylık örüntü tek bakışta görünür." }));
  k.append(kart);
  if (!deg.flat().some(Number.isFinite)) { kart.append(el("p.sessiz", { metin:"Veri yok." })); return; }
  G.isiHaritasi(kart, { satirAd:yillar.map(String), sutunAd:AYLAR.map(a => a.slice(0, 3)),
                        degerler:deg, birim:f.birim });
}

/* ------------------------------------------------------------ Pareto */
function cizPareto(k) {
  const d = donemler();
  const alt = altAgac(f.varlik).filter(x => x.kod !== f.varlik);
  const kalemler = [];
  for (const v of alt) {
    // yalnız en yakın seviye: kendi altında başka düğüm olanları atla
    if (alt.some(y => y.ust === v.kod)) continue;
    let t = 0, varMi = false;
    for (const x of d) {
      const r = H.varlikToplami(v.kod, x.yil, x.ay, { rol:"satin_alinan", birim:f.birim });
      if (Number.isFinite(r.deger)) { t += r.deger; varMi = true; }
    }
    if (varMi && t > 0) kalemler.push({ ad:v.ad, deger:t });
  }
  const kart = el("div.kart", {},
    el("h2", { metin:`${varlik(f.varlik)?.ad} altındaki kalemler · ${f.birim}` }),
    el("p.mini.sessiz", { metin:
      "Klasik Pareto çift eksenlidir (çubuk + kümülatif % çizgisi) — bu yasaktır (5.7.2). " +
      "Kümülatif yüzde tablo sütununda, %80 eşiği satır ayracıyla gösterilir." }));
  k.append(kart);
  if (!kalemler.length) { kart.append(bosDurum("Kırılacak kalem yok",
    "Seçilen varlığın altında ölçüm noktası bulunan alt varlık yok.")); return; }
  G.pareto(kart, { kalemler, birim:f.birim });

  // Analizden eyleme köprüsü (9.13): en büyük kalem doğrudan aksiyona dönüşür
  const enb = [...kalemler].sort((a, b) => b.deger - a.deger)[0];
  const toplam = kalemler.reduce((t2, x) => t2 + x.deger, 0);
  if (enb && toplam)
    kart.append(el("div", { stil:{ marginTop:"10px" } },
      el("span.mini.sessiz", { stil:{ marginRight:"8px" },
        metin:`En büyük kalem ${enb.ad}: toplamın ${yuzde(enb.deger / toplam * 100, 1)}'i.` }),
      el("button.dugme.kucuk", { metin:"→ Aksiyon aç", onclick:() => aksiyonAc({
        baslik:`${enb.ad} tüketimini azalt`,
        aciklama:`${varlik(f.varlik)?.ad} altındaki en büyük kalem: ` +
          `${say(enb.deger, 0)} ${f.birim} (toplamın ${yuzde(enb.deger / toplam * 100, 1)}'i). ` +
          "Pareto sıralamasında ilk sırada olduğu için iyileştirmenin en yüksek " +
          "getirili olduğu yerdir.",
        baglam:{ kaynak:`Ekran 7 · Pareto (${varlik(f.varlik)?.ad})`, varlik:f.varlik } }) })));
}

/* --------------------------------------------------- dönem karşılaştırma */
function cizKarsilastir(k) {
  const d = donemler();
  const uzunluk = d.length;
  const oncekiBas = donemKaydir(f.bas.yil, f.bas.ay, -uzunluk);
  const oncekiSon = donemKaydir(f.son.yil, f.son.ay, -uzunluk);
  const onceki = donemAraligi(oncekiBas.yil, oncekiBas.ay, oncekiSon.yil, oncekiSon.ay);

  const alt = altAgac(f.varlik).filter(x => x.kod !== f.varlik &&
    !altAgac(f.varlik).some(y => y.ust === x.kod));
  const topla = (kod, liste) => {
    let t = 0, varMi = false;
    for (const x of liste) {
      const r = H.varlikToplami(kod, x.yil, x.ay, { rol:"satin_alinan", birim:f.birim });
      if (Number.isFinite(r.deger)) { t += r.deger; varMi = true; }
    }
    return varMi ? t : null;
  };

  const satirlar = alt.map(v => {
    const a = topla(v.kod, d), b = topla(v.kod, onceki);
    return { ad:v.ad, simdi:a, once:b,
      fark:a !== null && b !== null ? a - b : null,
      oran:a !== null && b ? (a / b - 1) * 100 : null };
  }).filter(r => r.simdi !== null || r.once !== null)
    .sort((x, y) => Math.abs(y.fark ?? 0) - Math.abs(x.fark ?? 0));

  const kart = el("div.kart", {},
    el("h2", { metin:"Dönem karşılaştırma" }),
    el("p.kucuk.sessiz", { metin:
      `${donemAd(f.bas.yil, f.bas.ay)} – ${donemAd(f.son.yil, f.son.ay)}  ↔  ` +
      `${donemAd(oncekiBas.yil, oncekiBas.ay)} – ${donemAd(oncekiSon.yil, oncekiSon.ay)}  ` +
      `(${uzunluk} ay)` }));
  k.append(kart);

  if (uzunluk % 12) kart.append(uyari("dikkat",
    "Karşılaştırılan aralık tam yıl değil; mevsimsellik farkı sonucu etkileyebilir. " +
    "Sistem otomatik normalleştirme yapmaz."));

  kart.append(tablo([
    { ad:"Kalem", anahtar:"ad" },
    { ad:`Bu dönem (${f.birim})`, sayi:true, anahtar:"simdi" },
    { ad:`Önceki (${f.birim})`, sayi:true, anahtar:"once" },
    { ad:"Fark", deger:r => r.fark === null ? "—"
        : el("span", { stil:`color:${r.fark > 0 ? "var(--kritik)" : "var(--iyi-ink)"}` },
            (r.fark > 0 ? "+" : "−") + say(Math.abs(r.fark), 0)) },
    { ad:"%", deger:r => r.oran === null ? "—"
        : el("span", { stil:`color:${r.oran > 0 ? "var(--kritik)" : "var(--iyi-ink)"}` },
            fark(r.oran)) },
  ], satirlar));

  kart.append(el("p.mini.sessiz", { metin:
    "Kutuplu renk (5.7.1): artan kırmızı, azalan mavi/yeşil. Renk tek başına anlam " +
    "taşımaz — işaret ve sayı da yazılıdır." }));
}
