/* ekranlar/giris.js — Ekran 2: Aylık Veri Girişi (El Kitabı 9.3)
   EN ÇOK KULLANILACAK EKRAN. Ölçü: bir ayın bütün verisini en az tuşla,
   en az hatayla girmek. Dört giriş yöntemi (K-14). */

import { el, $, bosalt, say, fark, sayiOku, uyari, bildir, onayla, bosDurum,
         donemAd, donemKaydir, bugun, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { varlik, nokta, agac, altAgac, varlikNoktalari, dogrula, ENGEL,
         ROLLER, VERI_TIPLERI, devrede } from "../model.js";
import * as H from "../hesap.js";
import { miniGrafik } from "../grafik.js";

let mod = "tablo";
let donem = null;
const kapali = new Set();

const MODLAR = [
  ["tablo",  "Tablo",            "Excel benzeri tek sayfa — aylık rutin giriş"],
  ["form",   "Kategori formu",   "Tek bir alanı doldururken"],
  ["yapistir","Toplu yapıştırma","Excel'den kopyalayıp yapıştırma"],
  ["dosya",  "Dosya yükleme",    "Toplu / geçmiş veri"],
];

export function ekranGiris(k) {
  if (!donem) donem = sonDonem();

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Aylık Veri Girişi" }),
    el("p", { metin:"Bir ayın bütün ölçüm noktası değerlerini girin. Geçen ay ve geçen yılın aynı ayı yan yana gösterilir — en iyi hata yakalama aracı budur." })));

  donemSecici(k);

  const s = el("div.sekmeler", {});
  for (const [kod, ad, ipucu] of MODLAR)
    s.append(el("button.sekme", { "aria-selected":mod === kod ? "true" : "false",
      title:ipucu, metin:ad, onclick:() => { mod = kod; yenile(); } }));
  k.append(s);

  ({ tablo:modTablo, form:modForm, yapistir:modYapistir, dosya:modDosya }[mod])(k);

  if (mod === "tablo" || mod === "form") ozetSeridi(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranGiris(k); };

function sonDonem() {
  const a = V.veriAraligi();
  if (a) { const n = donemKaydir(a.son.yil, a.son.ay, 1); return n; }
  const b = bugun(); return donemKaydir(b.yil, b.ay, -1);
}

/* ------------------------------------------------------- dönem seçici */
function donemSecici(k) {
  const kaydir = n => { const d = donemKaydir(donem.yil, donem.ay, n); donem = d; yenile(); };
  const ay = el("select", { onchange:e => { donem = { ...donem, ay:+e.target.value }; yenile(); } });
  AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a, selected:donem.ay === i + 1 })));
  const yil = el("input", { type:"number", value:donem.yil, min:1990, max:2100, stil:{ width:"92px" },
    onchange:e => { donem = { ...donem, yil:+e.target.value }; yenile(); } });

  const dolu = V.durum.degerler.filter(d => d.y === donem.yil && d.a === donem.ay).length;
  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"center" } },
      el("button.dugme.kucuk", { metin:"‹", title:"Önceki ay", onclick:() => kaydir(-1) }),
      ay, yil,
      el("button.dugme.kucuk", { metin:"›", title:"Sonraki ay", onclick:() => kaydir(1) }),
      el("span.bosluk", { stil:{ flex:"1" } }),
      el("span.rozet" + (dolu ? ".iyi" : ""), { metin:dolu ? `${dolu} değer girilmiş` : "bu ay boş" }))));
}

/* ------------------------------------------------------------ mod A: tablo */
function girilebilirNoktalar() {
  return V.durum.olcum_noktalari.filter(n =>
    n.aktif !== false && (n.veri_tipi === "olculen" || n.veri_tipi === "tahmini"));
}

function modTablo(k) {
  const agacDugumleri = agac();
  const sar = el("div.kart", { stil:{ padding:"0" } });
  const t = el("table");
  t.append(el("thead", {}, el("tr", {},
    el("th", { metin:"Ölçüm noktası" }), el("th", { metin:"Birim" }),
    el("th.s", { metin:"Geçen ay" }), el("th.s", { metin:"Geçen yıl" }),
    el("th.s", { metin:"Bu ay" }), el("th.s", { metin:"Δ%" }),
    el("th", { metin:"Son 12 ay" }))));
  const govde = el("tbody");
  let yazildi = 0;
  const gez = (dugumler, derinlik) => {
    for (const d of dugumler) {
      const kendi = varlikNoktalari(d.kod).filter(n => girilebilirNoktalar().includes(n));
      const altToplam = altAgac(d.kod).reduce((s, v) =>
        s + varlikNoktalari(v.kod).filter(n => girilebilirNoktalar().includes(n)).length, 0);
      if (!altToplam) continue;
      const acik = !kapali.has(d.kod);
      govde.append(el("tr", { stil:{ background:"var(--yuzey-2)", cursor:"pointer" },
        onclick:() => { acik ? kapali.add(d.kod) : kapali.delete(d.kod); yenile(); } },
        el("td", { colspan:7, stil:{ paddingLeft:(8 + derinlik * 16) + "px", fontWeight:"600" } },
          (acik ? "▾ " : "▸ ") + d.ad,
          el("span.mini.sessiz", { metin:`  ${altToplam} nokta` }),
          !devrede(d.kod, donem.yil, donem.ay)
            ? el("span.rozet.dikkat", { stil:{ marginLeft:"8px" }, metin:"devre dışı" }) : null)));
      if (acik) { for (const n of kendi) { govde.append(satir(n, derinlik + 1)); yazildi++; }
                  gez(d.cocuklar, derinlik + 1); }
    }
  };
  gez(agacDugumleri, 0);
  t.append(govde);
  sar.append(el("div.tablo-sar", { stil:{ maxHeight:"58vh", border:"0" } }, t));
  k.append(sar);
  if (!yazildi) k.append(bosDurum("Girilebilir nokta yok",
    "Tanımlar ekranından ölçüm noktası ekleyin."));
}

function satir(n, derinlik) {
  const o  = donemKaydir(donem.yil, donem.ay, -1);
  const gy = donemKaydir(donem.yil, donem.ay, -12);
  const gecenAy  = V.deger(n.kod, o.yil, o.ay);
  const gecenYil = V.deger(n.kod, gy.yil, gy.ay);
  const simdi    = V.deger(n.kod, donem.yil, donem.ay);

  const son12 = [];
  for (let i = 11; i >= 0; i--) { const d = donemKaydir(donem.yil, donem.ay, -i);
    son12.push(V.deger(n.kod, d.yil, d.ay)); }

  const tr = el("tr");
  const uyariHucre = el("td.s");
  const farkHucre  = el("td.s");

  const giris = el("input", {
    type:"text", value:simdi !== null ? say(simdi, n.birim === "TL" ? 2 : 2) : "",
    stil:{ width:"130px", textAlign:"right" },
    placeholder:"—",
    onfocus:e => e.target.select(),
    onchange:e => degerYaz(n, e.target, farkHucre, uyariHucre, gecenAy),
  });

  const guncelle = () => {
    const d = simdi !== null && gecenAy ? (simdi / gecenAy - 1) * 100 : null;
    farkHucre.textContent = d === null ? "—" : fark(d);
    farkHucre.className = "td s".replace("td ", "") + " s";
    farkHucre.style.color = d === null ? "" : Math.abs(d) > 30 ? "var(--ciddi)" : "var(--ink-mut)";
  };

  tr.append(
    el("td", { stil:{ paddingLeft:(8 + derinlik * 16) + "px" }, title:n.not || "" },
      n.ad,
      n.rol === "satin_alinan" && n.toplama_dahil
        ? el("span.mini.sessiz", { metin:"  ·toplama dahil" }) : null),
    el("td.sessiz.mini", { metin:n.birim }),
    el("td.s.sessiz", { metin:gecenAy !== null ? say(gecenAy, 0) : "—" }),
    el("td.s.sessiz", { metin:gecenYil !== null ? say(gecenYil, 0) : "—" }),
    el("td.s", {}, giris),
    farkHucre,
    el("td", {}, miniGrafik(son12)));
  guncelle();

  // Kayıtlı uyarıları göster
  const b = simdi !== null ? dogrula(n.kod, donem.yil, donem.ay, simdi) : [];
  if (b.length) { tr.style.background = "color-mix(in srgb, var(--uyari) 9%, transparent)";
                  giris.title = b.map(x => x.mesaj).join(" · "); }
  return tr;
}

function degerYaz(n, giris, farkHucre, uyariHucre, gecenAy) {
  const s = sayiOku(giris.value);
  if (s.hata) { bildir(`${n.ad}: ${s.hata}`, "kritik"); giris.focus(); return; }
  if (s.deger === null) { V.degerYaz(n.kod, donem.yil, donem.ay, null); yenile(); return; }

  const b = dogrula(n.kod, donem.yil, donem.ay, s.deger);
  const engel = b.find(x => x.seviye === ENGEL);
  if (engel) { bildir(`${n.ad}: ${engel.mesaj}`, "kritik"); giris.focus(); return; }

  if (b.length) {
    onayla("Girişi onaylayın",
      el("div", {},
        el("p", {}, el("b", { metin:n.ad }), ` — ${say(s.deger, 2)} ${n.birim}`),
        el("ul", { stil:{ margin:"8px 0 0 18px" } },
          b.map(x => el("li", { metin:x.mesaj })))),
      "Yine de kaydet").then(ok => {
        if (ok) { V.degerYaz(n.kod, donem.yil, donem.ay, s.deger, { k:"girildi" }); }
        yenile();
      });
    return;
  }
  V.degerYaz(n.kod, donem.yil, donem.ay, s.deger, { k:"girildi" });
  yenile();
}

/* ------------------------------------------------------ mod B: kategori */
function modForm(k) {
  const gruplar = new Map();
  for (const n of girilebilirNoktalar()) {
    const yol = [];
    let v = varlik(n.varlik), g = 0;
    while (v && g++ < 20) { yol.unshift(v); v = v.ust ? varlik(v.ust) : null; }
    const ad = yol[1]?.ad || yol[0]?.ad || "Diğer";
    if (!gruplar.has(ad)) gruplar.set(ad, []);
    gruplar.get(ad).push(n);
  }
  for (const [ad, noktalar] of gruplar) {
    const kart = el("div.kart", {}, el("h2", { metin:`${ad} (${noktalar.length})` }));
    const t = el("table");
    const gv = el("tbody");
    for (const n of noktalar) gv.append(satir(n, 0));
    t.append(el("thead", {}, el("tr", {},
      el("th", { metin:"Ölçüm noktası" }), el("th", { metin:"Birim" }),
      el("th.s", { metin:"Geçen ay" }), el("th.s", { metin:"Geçen yıl" }),
      el("th.s", { metin:"Bu ay" }), el("th.s", { metin:"Δ%" }), el("th", { metin:"Son 12 ay" }))), gv);
    kart.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t));
    k.append(kart);
  }
}

/* -------------------------------------------------- mod C: yapıştırma */
function modYapistir(k) {
  const kart = el("div.kart", {}, el("h2", { metin:"Excel'den yapıştır" }));
  kart.append(el("p.kucuk.sessiz", { metin:
    "Excel'den bir blok kopyalayıp aşağıya yapıştırın. İki biçim desteklenir: " +
    "(1) her satırda ad ⇥ değer, (2) yalnız değerler — tablo modundaki sırayla eşleşir." }));
  const alan = el("textarea", { rows:10, stil:{ width:"100%", fontFamily:"ui-monospace,monospace" },
    placeholder:"Şebekeden Çekilen Elektrik\t1.421.220\nElektrik Faturası\t4.604.030\n…" });
  const sonuc = el("div");
  kart.append(alan, el("div.satir", { stil:{ marginTop:"10px" } },
    el("button.dugme.ana", { metin:"Çözümle", onclick:() => cozumle(alan.value, sonuc) })), sonuc);
  k.append(kart);
}

function cozumle(metin, hedef) {
  bosalt(hedef);
  const satirlar = metin.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  if (!satirlar.length) return hedef.append(uyari("dikkat", "Yapıştırılan içerik boş."));
  const sirali = girilebilirNoktalar();
  const eslesen = [], eslesmeyen = [];
  const adaGore = new Map();
  for (const n of sirali) {
    adaGore.set(n.ad.toLocaleLowerCase("tr"), n);
    adaGore.set(n.kod.toLocaleLowerCase("tr"), n);
  }
  satirlar.forEach((sat, i) => {
    const p = sat.split("\t");
    let n = null, ham = null;
    if (p.length >= 2) { n = adaGore.get(p[0].trim().toLocaleLowerCase("tr")); ham = p[p.length - 1]; }
    else { n = sirali[i]; ham = p[0]; }
    if (!n) { eslesmeyen.push({ sat, sebep:"Ölçüm noktası bulunamadı" }); return; }
    const s = sayiOku(ham);
    if (s.hata) { eslesmeyen.push({ sat, sebep:s.hata }); return; }
    if (s.deger === null) return;
    const b = dogrula(n.kod, donem.yil, donem.ay, s.deger);
    const engel = b.find(x => x.seviye === ENGEL);
    if (engel) { eslesmeyen.push({ sat, sebep:`${n.ad}: ${engel.mesaj}` }); return; }
    eslesen.push({ n, v:s.deger, uyari:b.map(x => x.mesaj) });
  });

  hedef.append(uyari(eslesmeyen.length ? "dikkat" : "iyi",
    el("b", { metin:`${eslesen.length} değer eşleşti` }),
    eslesmeyen.length ? `, ${eslesmeyen.length} satır çözümlenemedi.` : "."));
  if (eslesmeyen.length)
    hedef.append(el("ul", { stil:{ margin:"0 0 10px 18px" } },
      eslesmeyen.slice(0, 8).map(x => el("li.kucuk", { metin:`${x.sat.slice(0, 60)} → ${x.sebep}` }))));
  if (!eslesen.length) return;

  const t = el("table");
  t.append(el("thead", {}, el("tr", {}, el("th", { metin:"Ölçüm noktası" }),
    el("th.s", { metin:"Değer" }), el("th", { metin:"Uyarı" }))));
  const gv = el("tbody");
  for (const e of eslesen) gv.append(el("tr", {}, el("td", { metin:e.n.ad }),
    el("td.s", { metin:say(e.v, 2) }), el("td.mini.sessiz", { metin:e.uyari.join(" · ") })));
  t.append(gv);
  hedef.append(el("div.tablo-sar", {}, t));
  hedef.append(el("button.dugme.ana", { stil:{ marginTop:"10px" },
    metin:`${eslesen.length} değeri ${donemAd(donem.yil, donem.ay)} dönemine yaz`,
    onclick:() => {
      for (const e of eslesen) V.degerYaz(e.n.kod, donem.yil, donem.ay, e.v, { k:"girildi" });
      bildir(`${eslesen.length} değer yazıldı`); mod = "tablo"; yenile();
    } }));
}

/* ------------------------------------------------------ mod D: dosya */
function modDosya(k) {
  k.append(bosDurum("Dosya yükleme Veri Aktarma ekranında",
    "Toplu ve geçmiş veri aktarımı, sütun eşlemesi ve önizlemesiyle birlikte Ekran 3'te yapılır.",
    el("button.dugme.ana", { metin:"Veri Aktarma ekranına git",
      onclick:() => { location.hash = "e3"; } })));
}

/* -------------------------------------------------- canlı özet şeridi */
function ozetSeridi(k) {
  const te = H.toplamEnerji(donem.yil, donem.ay, "kWh");
  const tu = H.noktaDeger("TOPLAM_URETIM", donem.yil, donem.ay);
  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  const ep = anaKod ? H.enpi(anaKod, donem.yil, donem.ay) : { deger:null };
  const dg = H.varlikToplami("GIRIS", donem.yil, donem.ay, { birim:"kWh" });

  const parca = [];
  const ekle = (ad, deger, birim, ondalik = 0) =>
    parca.push(el("span", {}, el("span.sessiz", { metin:ad + ": " }),
      el("b.sayi", { metin:deger === null ? "—" : say(deger, ondalik) + " " + birim })));

  ekle("Toplam enerji", te.deger, "kWh");
  ekle("Üretim", tu.deger ?? null, "kg");
  ekle("EnPI", ep.deger ?? null, ep.tanim?.birim || "", 4);

  // Tablo kendi içinde kaydığı için şerit doğal olarak görünür kalır;
  // yapışkan konumlandırma tablonun üstüne biniyordu.
  const serit = el("div.kart", { stil:{ marginTop:"14px", borderColor:"var(--s1)",
    display:"flex", gap:"22px", flexWrap:"wrap", alignItems:"center", padding:"12px 16px" } }, ...parca);

  const eksikler = [te, tu, ep].filter(x => x.eksik).map(x => x.eksik);
  if (eksikler.length)
    serit.append(el("span.rozet.dikkat", { title:eksikler.join(" · "),
      metin:"⚠ " + eksikler[0].slice(0, 62) + (eksikler[0].length > 62 ? "…" : "") }));
  k.append(serit);
}
