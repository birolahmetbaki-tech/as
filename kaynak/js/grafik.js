/* grafik.js — saf SVG grafik motoru (K-17, El Kitabı 5.7)
   SIFIR DIŞ KÜTÜPHANE.

   BAĞLAYICI KURALLAR (5.7.2):
     · ÇİFT EKSENLİ GRAFİK YOK — iki ölçeğin hizası keyfîdir
     · kategorik renkler SABİT SIRAYLA, 8'den fazlası "Diğer"e katlanır
     · büyüklük tek hue, kutupluluk iki hue + nötr gri orta nokta
     · ince işaretler, saç teli kılavuz, KESİKLİ ÇİZGİ YOK
     · her veri noktasına sayı yazılmaz — seçici etiketleme
     · ≥2 seride açıklama HER ZAMAN var
     · her grafiğin "tablo olarak göster" seçeneği var (E-3)
     · her grafiğin fare üstü katmanı var (5.7.3) */

import { el, say, kisa } from "./ortak.js";

const NS = "http://www.w3.org/2000/svg";
export const SLOT = ["--s1","--s2","--s3","--s4","--s5","--s6","--s7","--s8"];
export const renk = i => `var(${SLOT[i % SLOT.length]})`;

export function s(ad, ozellik = {}, ...cocuk) {
  const d = document.createElementNS(NS, ad);
  for (const [k, v] of Object.entries(ozellik))
    if (v !== null && v !== undefined) d.setAttribute(k, v);
  for (const c of cocuk.flat()) if (c) d.append(c);
  return d;
}

/* ---------------------------------------------------------- ölçek */
/** İnsan dostu eksen adımı: 1, 2, 2.5, 5, 10 × 10^n */
function guzelAdim(kaba) {
  if (kaba <= 0) return 1;
  const us = Math.pow(10, Math.floor(Math.log10(kaba)));
  const b = kaba / us;
  return (b <= 1 ? 1 : b <= 2 ? 2 : b <= 2.5 ? 2.5 : b <= 5 ? 5 : 10) * us;
}
function eksen(enk, enb, adet = 5) {
  if (enk === enb) { enb = enk + 1; }
  const adim = guzelAdim((enb - enk) / adet);
  const alt = Math.floor(enk / adim) * adim;
  const ust = Math.ceil(enb / adim) * adim;
  const ticks = [];
  for (let v = alt; v <= ust + adim / 1000; v += adim) ticks.push(+v.toFixed(10));
  return { alt, ust, ticks };
}

/* ------------------------------------------------- ortak iskelet */
const KENAR = { ust:14, sag:16, alt:34, sol:66 };

function iskelet(kap, { boy = 260, baslik = null } = {}) {
  const en = Math.max(320, (kap.clientWidth || 720) - 4);
  const svg = s("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
    style:"display:block;max-width:100%;overflow:visible", role:"img" });
  if (baslik) svg.append(s("title", {}, document.createTextNode(baslik)));
  return { svg, en, boy,
    ic: { x:KENAR.sol, y:KENAR.ust, en:en - KENAR.sol - KENAR.sag, boy:boy - KENAR.ust - KENAR.alt } };
}

function ykilavuz(svg, ic, olcek, birim, ondalik = 0) {
  for (const t of olcek.ticks) {
    const y = ic.y + ic.boy - ((t - olcek.alt) / (olcek.ust - olcek.alt)) * ic.boy;
    svg.append(s("line", { x1:ic.x, y1:y, x2:ic.x + ic.en, y2:y,
      stroke:"var(--kilavuz)", "stroke-width":1 }));           // saç teli, KESİKSİZ
    svg.append(s("text", { x:ic.x - 8, y:y + 4, "text-anchor":"end",
      fill:"var(--ink-mut)", "font-size":10, "font-variant-numeric":"tabular-nums" },
      document.createTextNode(kisa(t, ondalik))));
  }
  svg.append(s("line", { x1:ic.x, y1:ic.y + ic.boy, x2:ic.x + ic.en, y2:ic.y + ic.boy,
    stroke:"var(--taban)", "stroke-width":1 }));
  if (birim) svg.append(s("text", { x:ic.x - 8, y:ic.y - 3, "text-anchor":"end",
    fill:"var(--ink-mut)", "font-size":9 }, document.createTextNode(birim)));
}

function xetiket(svg, ic, etiketler) {
  const adim = Math.max(1, Math.ceil(etiketler.length / Math.floor(ic.en / 52)));
  etiketler.forEach((e, i) => {
    if (i % adim) return;
    const x = ic.x + (i + 0.5) * (ic.en / etiketler.length);
    svg.append(s("text", { x, y:ic.y + ic.boy + 15, "text-anchor":"middle",
      fill:"var(--ink-mut)", "font-size":10 }, document.createTextNode(e)));
  });
}

/* ------------------------------------------------------- açıklama */
function aciklama(seriler) {
  if (seriler.length < 2) return null;              // tek seri → başlık adlandırır
  return el("div", { stil:{ display:"flex", flexWrap:"wrap", gap:"14px",
    margin:"8px 0 0", fontSize:"12px" } },
    seriler.map((d, i) => el("span", { stil:{ display:"inline-flex", alignItems:"center", gap:"6px" } },
      el("span", { stil:{ width:"10px", height:"10px", borderRadius:"2px",
        background:d.renk || renk(i), display:"inline-block" } }),
      el("span.sessiz", { metin:d.ad }))));
}

/* ------------------------------------------------- fare üstü katmanı */
function kutucuk() {
  const d = el("div", { stil:{ position:"fixed", pointerEvents:"none", zIndex:"40",
    background:"var(--yuzey)", border:"1px solid var(--cerceve)", borderRadius:"6px",
    padding:"7px 10px", fontSize:"12px", boxShadow:"0 4px 16px rgba(0,0,0,.18)",
    display:"none", maxWidth:"280px" } });
  document.body.append(d);
  return {
    goster(olay, icerik) {
      d.innerHTML = ""; d.append(icerik); d.style.display = "block";
      const k = d.getBoundingClientRect();
      d.style.left = Math.min(olay.clientX + 14, innerWidth - k.width - 8) + "px";
      d.style.top  = Math.max(8, olay.clientY - k.height - 12) + "px";
    },
    gizle() { d.style.display = "none"; },
    yok() { d.remove(); },
  };
}

/* ------------------------------------------- tablo olarak göster (E-3) */
function sarmala(kap, svg, ek, tabloVeri) {
  const govde = el("div", {}, svg, ek);
  const tbl = el("div", { stil:{ display:"none", marginTop:"8px" } });
  let acik = false;
  const dugme = el("button.dugme.kucuk", { metin:"Tablo olarak göster",
    stil:{ marginTop:"8px" }, onclick:() => {
      acik = !acik;
      tbl.style.display = acik ? "block" : "none";
      govde.style.display = acik ? "none" : "block";
      dugme.textContent = acik ? "Grafiğe dön" : "Tablo olarak göster";
      if (acik && !tbl.firstChild) tbl.append(tabloVeri());
    } });
  kap.append(govde, dugme, tbl);
  return kap;
}

const basitTablo = (basliklar, satirlar) => {
  const t = el("table");
  t.append(el("thead", {}, el("tr", {}, basliklar.map((b, i) =>
    el(i ? "th.s" : "th", { metin:b })))));
  const gv = el("tbody");
  for (const r of satirlar)
    gv.append(el("tr", {}, r.map((c, i) => el(i ? "td.s" : "td",
      { metin: c === null || c === undefined ? "—" : typeof c === "number" ? say(c, 0) : String(c) }))));
  t.append(gv);
  return el("div.tablo-sar", {}, t);
};

/* =============================================================== SÜTUN */
/**
 * @param seriler [{ad, degerler:[], renk?}]  · yigili:true → yığılmış sütun
 * Tek seri → açıklama yok, başlık seriyi adlandırır (5.7.3).
 */
export function sutun(kap, { seriler, etiketler, birim = "", yigili = false,
                             boy = 260, ondalik = 0, baslik = "" } = {}) {
  kap = kap || el("div");
  const { svg, ic } = iskelet(kap, { boy, baslik });
  const n = etiketler.length;

  const toplamlar = etiketler.map((_, i) =>
    yigili ? seriler.reduce((t, d) => t + (d.degerler[i] || 0), 0)
           : Math.max(...seriler.map(d => d.degerler[i] || 0)));
  const enb = Math.max(0, ...toplamlar);
  const enk = Math.min(0, ...seriler.flatMap(d => d.degerler.filter(Number.isFinite)));
  const ol = eksen(enk, enb);
  ykilavuz(svg, ic, ol, birim, ondalik);
  xetiket(svg, ic, etiketler);

  const adim = ic.en / n;
  const y0 = v => ic.y + ic.boy - ((v - ol.alt) / (ol.ust - ol.alt)) * ic.boy;
  const kt = kutucuk();
  const grup = s("g");

  for (let i = 0; i < n; i++) {
    let taban = 0;
    const seriSay = yigili ? 1 : seriler.length;
    const cw = Math.max(2, (adim * 0.68) / seriSay);
    seriler.forEach((d, j) => {
      const v = d.degerler[i];
      if (!Number.isFinite(v)) return;
      const x = yigili ? ic.x + i * adim + (adim - cw) / 2
                       : ic.x + i * adim + (adim - cw * seriSay) / 2 + j * cw;
      const yUst = yigili ? y0(taban + v) : y0(v);
      const yTab = yigili ? y0(taban) : y0(0);
      const h = Math.max(0, yTab - yUst);
      grup.append(s("rect", { x:x.toFixed(1), y:yUst.toFixed(1),
        width:(cw - (yigili ? 0 : 1)).toFixed(1),
        height:Math.max(0, h - (yigili && j < seriler.length - 1 ? 2 : 0)).toFixed(1),
        rx:Math.min(4, cw / 3), fill:d.renk || renk(j) }));   // 4px yuvarlak uç
      taban += v;
    });
    // fare üstü: bütün sütunu kaplayan saydam hedef
    const hedef = s("rect", { x:(ic.x + i * adim).toFixed(1), y:ic.y,
      width:adim.toFixed(1), height:ic.boy, fill:"transparent" });
    hedef.addEventListener("mousemove", ev => kt.goster(ev,
      el("div", {}, el("b", { metin:etiketler[i] }),
        seriler.map((d, j) => el("div", {},
          el("span", { stil:{ display:"inline-block", width:"8px", height:"8px",
            borderRadius:"2px", background:d.renk || renk(j), marginRight:"6px" } }),
          `${d.ad}: ${say(d.degerler[i], ondalik)} ${birim}`)))));
    hedef.addEventListener("mouseleave", kt.gizle);
    grup.append(hedef);
  }
  svg.append(grup);

  return sarmala(kap, svg, aciklama(seriler),
    () => basitTablo(["Dönem", ...seriler.map(d => d.ad)],
      etiketler.map((e, i) => [e, ...seriler.map(d => d.degerler[i])])));
}

/* =============================================================== ÇİZGİ */
/** @param referans {deger, ad} → yatay referans hattı (baz çizgi vb.) */
export function cizgi(kap, { seriler, etiketler, birim = "", boy = 260,
                             ondalik = 0, referans = null, baslik = "" } = {}) {
  kap = kap || el("div");
  const { svg, ic } = iskelet(kap, { boy, baslik });
  const hepsi = seriler.flatMap(d => d.degerler).filter(Number.isFinite);
  if (referans) hepsi.push(referans.deger);
  const ol = eksen(Math.min(...hepsi), Math.max(...hepsi));
  ykilavuz(svg, ic, ol, birim, ondalik);
  xetiket(svg, ic, etiketler);

  const n = etiketler.length;
  const dx = n > 1 ? ic.en / (n - 1) : 0;
  const px = i => ic.x + i * dx;
  const py = v => ic.y + ic.boy - ((v - ol.alt) / (ol.ust - ol.alt)) * ic.boy;

  if (referans) {
    svg.append(s("line", { x1:ic.x, y1:py(referans.deger), x2:ic.x + ic.en, y2:py(referans.deger),
      stroke:"var(--ink-mut)", "stroke-width":1 }));
    svg.append(s("text", { x:ic.x + ic.en, y:py(referans.deger) - 5, "text-anchor":"end",
      fill:"var(--ink-mut)", "font-size":10 }, document.createTextNode(referans.ad)));
  }

  seriler.forEach((d, j) => {
    let yol = "", kalem = false;
    d.degerler.forEach((v, i) => {
      if (!Number.isFinite(v)) { kalem = false; return; }
      yol += (kalem ? "L" : "M") + px(i).toFixed(1) + "," + py(v).toFixed(1) + " ";
      kalem = true;
    });
    svg.append(s("path", { d:yol, fill:"none", stroke:d.renk || renk(j),
      "stroke-width":2, "stroke-linejoin":"round", "stroke-linecap":"round" }));
    // Seçici etiketleme: yalnız uç nokta (5.7.2)
    const son = d.degerler.map((v, i) => [v, i]).filter(([v]) => Number.isFinite(v)).pop();
    if (son) {
      svg.append(s("circle", { cx:px(son[1]), cy:py(son[0]), r:3.5,
        fill:d.renk || renk(j), stroke:"var(--yuzey)", "stroke-width":2 }));
      if (seriler.length <= 4)
        svg.append(s("text", { x:px(son[1]) - 8, y:py(son[0]) - 9, "text-anchor":"end",
          fill:"var(--ink-2)", "font-size":11, "font-weight":600 },
          document.createTextNode(say(son[0], ondalik))));
    }
  });

  // dikey nişangâh + kutucuk
  const kt = kutucuk();
  const nisan = s("line", { y1:ic.y, y2:ic.y + ic.boy, stroke:"var(--taban)",
    "stroke-width":1, opacity:0 });
  svg.append(nisan);
  const kapak = s("rect", { x:ic.x, y:ic.y, width:ic.en, height:ic.boy, fill:"transparent" });
  kapak.addEventListener("mousemove", ev => {
    const kutu = svg.getBoundingClientRect();
    const i = Math.max(0, Math.min(n - 1, Math.round((ev.clientX - kutu.left - ic.x) / (dx || 1))));
    nisan.setAttribute("x1", px(i)); nisan.setAttribute("x2", px(i));
    nisan.setAttribute("opacity", .6);
    kt.goster(ev, el("div", {}, el("b", { metin:etiketler[i] }),
      seriler.map((d, j) => el("div", {},
        el("span", { stil:{ display:"inline-block", width:"8px", height:"8px",
          borderRadius:"2px", background:d.renk || renk(j), marginRight:"6px" } }),
        `${d.ad}: ${Number.isFinite(d.degerler[i]) ? say(d.degerler[i], ondalik) + " " + birim : "—"}`))));
  });
  kapak.addEventListener("mouseleave", () => { nisan.setAttribute("opacity", 0); kt.gizle(); });
  svg.append(kapak);

  return sarmala(kap, svg, aciklama(seriler),
    () => basitTablo(["Dönem", ...seriler.map(d => d.ad)],
      etiketler.map((e, i) => [e, ...seriler.map(d => d.degerler[i])])));
}

/* ========================================================= ISI HARİTASI */
/** Sıralı tek hue (5.7.1). Ölçek açıklaması ZORUNLU. */
export function isiHaritasi(kap, { satirAd, sutunAd, degerler, birim = "", ondalik = 0 } = {}) {
  kap = kap || el("div");
  const duz = degerler.flat().filter(Number.isFinite);
  const enk = Math.min(...duz), enb = Math.max(...duz);
  const RAMP = ["--r100","--r250","--r400","--r550","--r700"];
  const kova = v => {
    if (!Number.isFinite(v)) return null;
    const o = (v - enk) / ((enb - enk) || 1);
    return RAMP[Math.min(RAMP.length - 1, Math.floor(o * RAMP.length))];
  };
  const kt = kutucuk();
  const t = el("table", { stil:{ fontSize:"11px" } });
  t.append(el("thead", {}, el("tr", {}, el("th", { metin:"" }),
    sutunAd.map(a => el("th.s", { stil:{ padding:"2px 4px" }, metin:a })))));
  const gv = el("tbody");
  satirAd.forEach((sa, i) => {
    const tr = el("tr", {}, el("td", { stil:{ whiteSpace:"nowrap", fontWeight:"600" }, metin:sa }));
    sutunAd.forEach((su, j) => {
      const v = degerler[i]?.[j];
      const k = kova(v);
      const h = el("td", { stil:{ padding:"1px" } },
        el("div", { stil:{ height:"22px", borderRadius:"3px",
          background:k ? `var(${k})` : "var(--yuzey-2)",
          border:k ? "none" : "1px dashed var(--kilavuz)" } }));
      if (k) {
        h.addEventListener("mousemove", ev => kt.goster(ev,
          el("div", {}, el("b", { metin:`${sa} ${su}` }),
            el("div", { metin:`${say(v, ondalik)} ${birim}` }))));
        h.addEventListener("mouseleave", kt.gizle);
      }
      tr.append(h);
    });
    gv.append(tr);
  });
  t.append(gv);

  const olcek = el("div", { stil:{ display:"flex", alignItems:"center", gap:"7px",
    marginTop:"10px", fontSize:"11px" } },
    el("span.sessiz", { metin:`${kisa(enk, ondalik)} ${birim}` }),
    ...RAMP.map(r => el("span", { stil:{ width:"26px", height:"11px",
      background:`var(${r})`, display:"inline-block", borderRadius:"2px" } })),
    el("span.sessiz", { metin:`${kisa(enb, ondalik)} ${birim}` }));

  return sarmala(kap, el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t), olcek,
    () => basitTablo(["", ...sutunAd], satirAd.map((sa, i) => [sa, ...degerler[i]])));
}

/* =============================================================== PARETO */
/**
 * Klasik Pareto ÇİFT EKSENLİDİR — yasak (5.7.2).
 * Kümülatif yüzde tablo sütununda gösterilir, %80 eşiği satır ayracıyla.
 */
export function pareto(kap, { kalemler, birim = "", ondalik = 0 } = {}) {
  kap = kap || el("div");
  const sirali = [...kalemler].filter(k => Number.isFinite(k.deger) && k.deger > 0)
    .sort((a, b) => b.deger - a.deger);
  const toplam = sirali.reduce((t, k) => t + k.deger, 0);
  let birikim = 0;
  const satirlar = sirali.map(k => {
    birikim += k.deger;
    return { ...k, oran:k.deger / toplam, kumulatif:birikim / toplam };
  });
  const esikIndeks = satirlar.findIndex(s2 => s2.kumulatif >= 0.8);
  const enb = satirlar[0]?.deger || 1;

  const t = el("table");
  t.append(el("thead", {}, el("tr", {},
    el("th", { metin:"Kalem" }), el("th.s", { metin:`Değer (${birim})` }),
    el("th", { metin:"" }), el("th.s", { metin:"Pay" }), el("th.s", { metin:"Kümülatif" }))));
  const gv = el("tbody");
  satirlar.forEach((r, i) => {
    const tr = el("tr", {},
      el("td", { metin:r.ad }),
      el("td.s", { metin:say(r.deger, ondalik) }),
      el("td", { stil:{ width:"46%" } },
        el("div", { stil:{ height:"13px", borderRadius:"3px", background:"var(--s1)",
          width:(r.deger / enb * 100).toFixed(1) + "%" } })),
      el("td.s", { metin:"%" + say(r.oran * 100, 1) }),
      el("td.s", { metin:"%" + say(r.kumulatif * 100, 1) }));
    gv.append(tr);
    if (i === esikIndeks)
      gv.append(el("tr", {}, el("td", { colspan:5, stil:{ padding:"3px 10px",
        borderTop:"2px solid var(--ciddi)", background:"var(--yuzey-2)",
        fontSize:"11px", color:"var(--ink-2)" },
        metin:`▲ Buraya kadar olan ${i + 1} kalem toplamın %80'ini oluşturuyor` })));
  });
  t.append(gv);
  kap.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t));
  return kap;
}

/* =============================================================== SANKEY */
/** @param dugumler [{kod, ad, katman}] · akislar [{kaynak, hedef, deger}] */
export function sankey(kap, { dugumler, akislar, birim = "", boy = 380 } = {}) {
  kap = kap || el("div");
  const en = Math.max(360, (kap.clientWidth || 860) - 4);
  const svg = s("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
    style:"display:block;max-width:100%" });
  const kt = kutucuk();

  const katmanlar = [...new Set(dugumler.map(d => d.katman))].sort((a, b) => a - b);
  const kx = new Map(katmanlar.map((k, i) =>
    [k, 130 + i * ((en - 260) / Math.max(1, katmanlar.length - 1))]));

  const buyukluk = new Map();
  for (const d of dugumler) {
    const giren = akislar.filter(a => a.hedef === d.kod).reduce((t, a) => t + a.deger, 0);
    const cikan = akislar.filter(a => a.kaynak === d.kod).reduce((t, a) => t + a.deger, 0);
    buyukluk.set(d.kod, Math.max(giren, cikan));
  }
  const enbKatman = Math.max(...katmanlar.map(k =>
    dugumler.filter(d => d.katman === k).reduce((t, d) => t + buyukluk.get(d.kod), 0)));
  const olcek = (boy - 60) / (enbKatman || 1);

  const kutu = new Map();
  for (const k of katmanlar) {
    const grup = dugumler.filter(d => d.katman === k);
    const toplamBoy = grup.reduce((t, d) => t + buyukluk.get(d.kod) * olcek, 0);
    let y = (boy - toplamBoy - (grup.length - 1) * 10) / 2;
    for (const d of grup) {
      const h = Math.max(3, buyukluk.get(d.kod) * olcek);
      kutu.set(d.kod, { x:kx.get(k), y, h, d });
      y += h + 10;
    }
  }

  // akışlar (önce, düğümlerin altında kalsın)
  const kaynakOfset = new Map(), hedefOfset = new Map();
  for (const a of [...akislar].sort((x, y2) => y2.deger - x.deger)) {
    const k = kutu.get(a.kaynak), h = kutu.get(a.hedef);
    if (!k || !h || !(a.deger > 0)) continue;
    const kh = a.deger * olcek;
    const ko = kaynakOfset.get(a.kaynak) || 0, ho = hedefOfset.get(a.hedef) || 0;
    const x1 = k.x + 96, x2 = h.x;
    const y1 = k.y + ko, y2 = h.y + ho;
    const om = (x1 + x2) / 2;
    const yol = `M${x1},${y1} C${om},${y1} ${om},${y2} ${x2},${y2} ` +
                `L${x2},${y2 + kh} C${om},${y2 + kh} ${om},${y1 + kh} ${x1},${y1 + kh} Z`;
    const p = s("path", { d:yol, fill:a.renk || renk(a.slot ?? 0), opacity:.32 });
    p.addEventListener("mousemove", ev => { p.setAttribute("opacity", .55);
      kt.goster(ev, el("div", {}, el("b", { metin:`${k.d.ad} → ${h.d.ad}` }),
        el("div", { metin:`${say(a.deger, 0)} ${birim}` }))); });
    p.addEventListener("mouseleave", () => { p.setAttribute("opacity", .32); kt.gizle(); });
    svg.append(p);
    kaynakOfset.set(a.kaynak, ko + kh); hedefOfset.set(a.hedef, ho + kh);
  }

  for (const [kod, k] of kutu) {
    svg.append(s("rect", { x:k.x, y:k.y, width:96, height:k.h, rx:3,
      fill:k.d.renk || "var(--ink-mut)", opacity:.9 }));
    svg.append(s("text", { x:k.x + 48, y:k.y + k.h / 2 + 4, "text-anchor":"middle",
      fill:"var(--yuzey)", "font-size":10, "font-weight":600,
      style:"paint-order:stroke;stroke:rgba(0,0,0,.35);stroke-width:2px" },
      document.createTextNode(k.d.ad.length > 15 ? k.d.ad.slice(0, 14) + "…" : k.d.ad)));
    svg.append(s("text", { x:k.x + 48, y:k.y - 4, "text-anchor":"middle",
      fill:"var(--ink-mut)", "font-size":9 },
      document.createTextNode(kisa(buyukluk.get(kod), 1))));
  }

  return sarmala(kap, svg, null,
    () => basitTablo(["Kaynak","Hedef",`Değer (${birim})`],
      akislar.map(a => [kutu.get(a.kaynak)?.d.ad || a.kaynak,
                        kutu.get(a.hedef)?.d.ad || a.hedef, a.deger])));
}


/* ============================================================== DAĞILIM */
/**
 * Dağılım + regresyon doğrusu (8.3).
 * TÜM-ÇİFTLER kuralı: dağılım grafiğinde en fazla 3 seri (5.7.1).
 * @param seriler [{ad, noktalar:[{x,y,etiket}]}]
 * @param dogru   {a, b, r2, n, zayif} — regresyon
 */
export function dagilim(kap, { seriler, dogru = null, xAd = "", yAd = "",
                               boy = 320, baslik = "" } = {}) {
  kap = kap || el("div");
  if (seriler.length > 3) seriler = seriler.slice(0, 3);   // tüm-çiftler kapağı
  const { svg, ic } = iskelet(kap, { boy, baslik });
  const hepsi = seriler.flatMap(d => d.noktalar);
  if (!hepsi.length) { kap.append(el("p.sessiz", { metin:"Veri yok." })); return kap; }

  const xo = eksen(Math.min(...hepsi.map(p => p.x)), Math.max(...hepsi.map(p => p.x)));
  const yo = eksen(Math.min(...hepsi.map(p => p.y)), Math.max(...hepsi.map(p => p.y)));
  ykilavuz(svg, ic, yo, yAd, 0);

  const px = v => ic.x + ((v - xo.alt) / (xo.ust - xo.alt)) * ic.en;
  const py = v => ic.y + ic.boy - ((v - yo.alt) / (yo.ust - yo.alt)) * ic.boy;

  for (const t of xo.ticks) {
    svg.append(s("text", { x:px(t), y:ic.y + ic.boy + 15, "text-anchor":"middle",
      fill:"var(--ink-mut)", "font-size":10 }, document.createTextNode(kisa(t, 1))));
  }
  svg.append(s("text", { x:ic.x + ic.en, y:ic.y + ic.boy + 30, "text-anchor":"end",
    fill:"var(--ink-mut)", "font-size":10 }, document.createTextNode(xAd)));

  if (dogru && Number.isFinite(dogru.a)) {
    const x1 = xo.alt, x2 = xo.ust;
    svg.append(s("line", { x1:px(x1), y1:py(dogru.a * x1 + dogru.b),
      x2:px(x2), y2:py(dogru.a * x2 + dogru.b),
      stroke:"var(--ink-2)", "stroke-width":2, opacity:.75 }));
  }

  const kt = kutucuk();
  seriler.forEach((d, j) => {
    for (const p of d.noktalar) {
      const c = s("circle", { cx:px(p.x).toFixed(1), cy:py(p.y).toFixed(1), r:4,
        fill:d.renk || renk(j), stroke:"var(--yuzey)", "stroke-width":1.5, opacity:.9 });
      c.addEventListener("mousemove", ev => kt.goster(ev,
        el("div", {}, el("b", { metin:p.etiket || d.ad }),
          el("div", { metin:`${xAd}: ${say(p.x, 0)}` }),
          el("div", { metin:`${yAd}: ${say(p.y, 0)}` }))));
      c.addEventListener("mouseleave", kt.gizle);
      svg.append(c);
    }
  });

  const alt = el("div", {});
  if (dogru && Number.isFinite(dogru.a)) {
    alt.append(el("div.kucuk", { stil:{ marginTop:"8px", fontFamily:"ui-monospace,monospace" },
      metin:`beklenen = ${say(dogru.a, 4)} × ${xAd} + ${say(dogru.b, 0)}   ·   R² = ${say(dogru.r2, 2)}   ·   n = ${dogru.n}` }));
  }
  return sarmala(kap, svg, el("div", {}, aciklama(seriler), alt),
    () => basitTablo(["Nokta", xAd, yAd],
      seriler.flatMap(d => d.noktalar.map(p => [p.etiket || d.ad, p.x, p.y]))));
}

/* ================================================================ CUSUM */
/**
 * Kümülatif sapma (8.5). KUTUPLU renk: sıfırın altı mavi (tasarruf),
 * üstü kırmızı (kayıp). Orta nokta NÖTR — sıfır sapma "hiçbir şey" demektir.
 * Okunuşu: EĞİM önemlidir, seviye değil.
 */
export function cusum(kap, { degerler, etiketler, birim = "kWh", boy = 280,
                             isaretler = [] } = {}) {
  kap = kap || el("div");
  const { svg, ic } = iskelet(kap, { boy });
  const g = degerler.filter(Number.isFinite);
  if (!g.length) { kap.append(el("p.sessiz", { metin:"Veri yok." })); return kap; }
  const ol = eksen(Math.min(0, ...g), Math.max(0, ...g));
  ykilavuz(svg, ic, ol, birim, 0);
  xetiket(svg, ic, etiketler);

  const n = etiketler.length;
  const dx = n > 1 ? ic.en / (n - 1) : 0;
  const px = i => ic.x + i * dx;
  const py = v => ic.y + ic.boy - ((v - ol.alt) / (ol.ust - ol.alt)) * ic.boy;
  const y0 = py(0);

  // sıfır çizgisi — nötr
  svg.append(s("line", { x1:ic.x, y1:y0, x2:ic.x + ic.en, y2:y0,
    stroke:"var(--taban)", "stroke-width":1.5 }));

  // dolgu: sıfırın üstü kırmızı (kayıp), altı mavi (tasarruf)
  const dolgu = (yon, dolguRenk) => {
    let d = "", acik = false;
    degerler.forEach((v, i) => {
      const uygun = Number.isFinite(v) && (yon > 0 ? v > 0 : v < 0);
      if (uygun) { if (!acik) { d += `M${px(i)},${y0} `; acik = true; }
                   d += `L${px(i)},${py(v)} `; }
      else if (acik) { d += `L${px(i - 1)},${y0} Z `; acik = false; }
    });
    if (acik) d += `L${px(n - 1)},${y0} Z`;
    if (d) svg.append(s("path", { d, fill:dolguRenk, opacity:.22 }));
  };
  dolgu(1, "var(--s8)");     // kayıp
  dolgu(-1, "var(--s1)");    // tasarruf

  let yol = "", kalem = false;
  degerler.forEach((v, i) => {
    if (!Number.isFinite(v)) { kalem = false; return; }
    yol += (kalem ? "L" : "M") + px(i).toFixed(1) + "," + py(v).toFixed(1) + " ";
    kalem = true;
  });
  svg.append(s("path", { d:yol, fill:"none", stroke:"var(--ink-2)", "stroke-width":2,
    "stroke-linejoin":"round" }));

  // eğim değişim noktaları
  for (const im of isaretler) {
    if (!(im.indeks >= 0 && im.indeks < n)) continue;
    svg.append(s("line", { x1:px(im.indeks), y1:ic.y, x2:px(im.indeks), y2:ic.y + ic.boy,
      stroke:"var(--ciddi)", "stroke-width":1.5, opacity:.7 }));
    svg.append(s("text", { x:px(im.indeks) + 5, y:ic.y + 11, fill:"var(--ciddi)",
      "font-size":10, "font-weight":600 }, document.createTextNode(im.ad)));
  }

  const kt = kutucuk();
  const nisan = s("line", { y1:ic.y, y2:ic.y + ic.boy, stroke:"var(--taban)",
    "stroke-width":1, opacity:0 });
  svg.append(nisan);
  const kapak = s("rect", { x:ic.x, y:ic.y, width:ic.en, height:ic.boy, fill:"transparent" });
  kapak.addEventListener("mousemove", ev => {
    const kutu = svg.getBoundingClientRect();
    const i = Math.max(0, Math.min(n - 1, Math.round((ev.clientX - kutu.left - ic.x) / (dx || 1))));
    nisan.setAttribute("x1", px(i)); nisan.setAttribute("x2", px(i));
    nisan.setAttribute("opacity", .6);
    const v = degerler[i];
    kt.goster(ev, el("div", {}, el("b", { metin:etiketler[i] }),
      el("div", { metin:Number.isFinite(v)
        ? `Kümülatif sapma: ${say(v, 0)} ${birim}` : "—" }),
      el("div.mini.sessiz", { metin:Number.isFinite(v)
        ? (v > 0 ? "baz çizginin üzerinde — kayıp" : v < 0 ? "baz çizginin altında — tasarruf" : "baz çizgide") : "" })));
  });
  kapak.addEventListener("mouseleave", () => { nisan.setAttribute("opacity", 0); kt.gizle(); });
  svg.append(kapak);

  const efsane = el("div.satir", { stil:{ gap:"16px", marginTop:"8px", fontSize:"12px" } },
    el("span", { stil:{ display:"inline-flex", alignItems:"center", gap:"6px" } },
      el("span", { stil:{ width:"14px", height:"9px", background:"var(--s1)", opacity:".35",
        borderRadius:"2px", display:"inline-block" } }),
      el("span.sessiz", { metin:"aşağı eğim = kalıcı tasarruf" })),
    el("span", { stil:{ display:"inline-flex", alignItems:"center", gap:"6px" } },
      el("span", { stil:{ width:"14px", height:"9px", background:"var(--s8)", opacity:".35",
        borderRadius:"2px", display:"inline-block" } }),
      el("span.sessiz", { metin:"yukarı eğim = kalıcı kayıp" })));

  return sarmala(kap, svg, efsane,
    () => basitTablo(["Dönem", `Kümülatif sapma (${birim})`],
      etiketler.map((e, i) => [e, degerler[i]])));
}

/* =============================================================== ŞELALE */
/** Fiyat / hacim ayrıştırması (8.7). Kutuplu: artıran kırmızı, azaltan mavi. */
export function selale(kap, { kalemler, birim = "TL", boy = 280 } = {}) {
  kap = kap || el("div");
  const { svg, ic } = iskelet(kap, { boy });
  let kum = 0;
  const bar = kalemler.map(k => {
    const bas = kum; kum += k.deger;
    return { ...k, bas, son:kum };
  });
  const hepsi = [0, ...bar.map(b => b.bas), ...bar.map(b => b.son)];
  const ol = eksen(Math.min(...hepsi), Math.max(...hepsi));
  ykilavuz(svg, ic, ol, birim, 0);
  xetiket(svg, ic, kalemler.map(k => k.ad));

  const adim = ic.en / bar.length;
  const py = v => ic.y + ic.boy - ((v - ol.alt) / (ol.ust - ol.alt)) * ic.boy;
  svg.append(s("line", { x1:ic.x, y1:py(0), x2:ic.x + ic.en, y2:py(0),
    stroke:"var(--taban)", "stroke-width":1.5 }));

  const kt = kutucuk();
  bar.forEach((b, i) => {
    const cw = adim * 0.6;
    const x = ic.x + i * adim + (adim - cw) / 2;
    const yUst = py(Math.max(b.bas, b.son)), yAlt = py(Math.min(b.bas, b.son));
    const dolguRenk = b.toplam ? "var(--ink-mut)" : b.deger > 0 ? "var(--s8)" : "var(--s1)";
    const g = s("rect", { x:x.toFixed(1), y:yUst.toFixed(1), width:cw.toFixed(1),
      height:Math.max(2, yAlt - yUst).toFixed(1), rx:3, fill:dolguRenk });
    g.addEventListener("mousemove", ev => kt.goster(ev,
      el("div", {}, el("b", { metin:b.ad }),
        el("div", { metin:`${b.deger > 0 ? "+" : "−"}${say(Math.abs(b.deger), 0)} ${birim}` }))));
    g.addEventListener("mouseleave", kt.gizle);
    svg.append(g);
    svg.append(s("text", { x:x + cw / 2, y:yUst - 6, "text-anchor":"middle",
      fill:"var(--ink-2)", "font-size":11, "font-weight":600 },
      document.createTextNode((b.deger > 0 ? "+" : "−") + kisa(Math.abs(b.deger), 1))));
    if (i < bar.length - 1)
      svg.append(s("line", { x1:x + cw, y1:py(b.son), x2:ic.x + (i + 1) * adim + (adim - cw) / 2,
        y2:py(b.son), stroke:"var(--kilavuz)", "stroke-width":1 }));
  });

  return sarmala(kap, svg, null,
    () => basitTablo(["Kalem", `Etki (${birim})`], kalemler.map(k => [k.ad, k.deger])));
}

/* ------------------------------------------------------ mini grafik */
export function miniGrafik(degerler, { en = 84, boy = 20, cizgiRenk = "var(--s1)" } = {}) {
  const g = degerler.filter(v => v !== null && Number.isFinite(v));
  const svg = s("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
    "aria-hidden":"true", style:"display:block;overflow:visible" });
  if (g.length < 2) return svg;
  const enk = Math.min(...g), enb = Math.max(...g), ar = enb - enk || 1;
  const dx = en / Math.max(1, degerler.length - 1);
  const y = v => boy - 2 - ((v - enk) / ar) * (boy - 4);
  let d = "", kalem = false;
  degerler.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) { kalem = false; return; }
    d += (kalem ? "L" : "M") + (i * dx).toFixed(1) + "," + y(v).toFixed(1) + " ";
    kalem = true;
  });
  svg.append(s("path", { d, fill:"none", stroke:cizgiRenk, "stroke-width":1.5,
    "stroke-linejoin":"round", "stroke-linecap":"round", opacity:.85 }));
  const son = degerler.map((v, i) => [v, i]).filter(([v]) => v !== null && Number.isFinite(v)).pop();
  if (son) svg.append(s("circle", { cx:(son[1] * dx).toFixed(1), cy:y(son[0]).toFixed(1),
    r:2, fill:cizgiRenk }));
  return svg;
}

export function oranCubugu(oran, { en = 120, boy = 8, cizgiRenk = "var(--s1)" } = {}) {
  const svg = s("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
    "aria-hidden":"true", style:"display:block" });
  svg.append(s("rect", { x:0, y:0, width:en, height:boy, rx:boy / 2, fill:"var(--kilavuz)" }));
  const g = Math.max(0, Math.min(1, oran || 0));
  if (g > 0) svg.append(s("rect", { x:0, y:0, width:(en * g).toFixed(1), height:boy,
    rx:boy / 2, fill:cizgiRenk }));
  return svg;
}
