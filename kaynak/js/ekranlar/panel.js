/* ekranlar/panel.js — Ekran 1: Gösterge Paneli (El Kitabı 9.2)
   "Durumumuz ne?" Karar verdirmez; nereye bakılacağını gösterir.
   SALT OKUNUR — bakılan yerle yazılan yer ayrıdır. */

import { el, $, bosalt, say, kisa, yuzde, fark, uyari, bosDurum, tablo,
         donemAd, donemKisa, donemKaydir, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { nokta, varlik } from "../model.js";
import * as H from "../hesap.js";
import { katman, hucre, sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";
import { kokenDugmesi } from "../koken.js";

let donem = null;

export function ekranPanel(k) {
  const ar = V.veriAraligi();
  if (!ar) {
    k.append(el("div.sayfa-basi", {}, el("h1", { metin:"Gösterge Paneli" })));
    k.append(bosDurum("Henüz veri yok",
      "Panel, girdiğiniz veriden beslenir. Excel dosyanızı Veri Aktarma ekranından alın; " +
      "panel anında dolar.",
      el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));
    return;
  }
  if (!donem || !V.durum.degerler.some(d => d.y === donem.yil && d.a === donem.ay))
    donem = sonDoluDonem(ar);

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Gösterge Paneli" }),
    el("p", { metin:`${donemAd(donem.yil, donem.ay)} · ${V.durum.ayarlar?.fabrika_adi || "Fabrika"}` })));

  donemSecici(k, ar);
  kartlar(k);
  uyarilar(k);
  grafikler(k);
  yillikOzet(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranPanel(k); };

const sonDoluDonem = ar => sonEnerjiDonemi() || { yil:ar.son.yil, ay:ar.son.ay };

function donemSecici(k, ar) {
  const ay = el("select", { onchange:e => { donem = { ...donem, ay:+e.target.value }; yenile(); } });
  AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a, selected:donem.ay === i + 1 })));
  const yil = el("select", { onchange:e => { donem = { ...donem, yil:+e.target.value }; yenile(); } });
  for (let y = ar.ilk.yil; y <= ar.son.yil; y++)
    yil.append(el("option", { value:y, metin:y, selected:donem.yil === y }));
  const kaydir = n => { donem = donemKaydir(donem.yil, donem.ay, n); yenile(); };
  k.append(el("div.satir", { stil:{ marginBottom:"16px", alignItems:"center" } },
    el("button.dugme.kucuk", { metin:"‹", onclick:() => kaydir(-1) }), ay, yil,
    el("button.dugme.kucuk", { metin:"›", onclick:() => kaydir(1) })));
}

/* ------------------------------------------------------- KPI kartları */
function son12(sutun) {
  const l = [];
  for (let i = 11; i >= 0; i--) {
    const d = donemKaydir(donem.yil, donem.ay, -i);
    l.push(hucre(sutun, d.yil, d.ay));
  }
  return l;
}

function kart(baslik, deger, birim, { ondalik = 0, gecenYil = null, seri = null,
                                      alt = null, rozet = null, koken = null } = {}) {
  const d = gecenYil !== null && gecenYil !== 0 && Number.isFinite(deger)
    ? (deger / gecenYil - 1) * 100 : null;
  return el("div.kart", { stil:{ flex:"1 1 210px", margin:"0", minWidth:"190px" } },
    el("div.mini.sessiz", { metin:baslik },
      koken ? kokenDugmesi(koken, donem.yil, donem.ay) : null),
    el("div", { stil:{ fontSize:"23px", fontWeight:"600", margin:"5px 0 2px",
                       fontVariantNumeric:"tabular-nums" },
      metin:Number.isFinite(deger) ? say(deger, ondalik) : "—" },
      birim ? el("span", { stil:{ fontSize:"12px", fontWeight:"400", color:"var(--ink-mut)",
        marginLeft:"5px" }, metin:birim }) : null),
    el("div.satir", { stil:{ gap:"8px", alignItems:"center", minHeight:"22px" } },
      d !== null ? el("span.mini", { stil:{ color:Math.abs(d) < 1 ? "var(--ink-mut)" : "" },
        metin:fark(d) + " (geçen yıl)" }) : el("span.mini.sessiz", { metin:alt || "" }),
      rozet),
    seri ? el("div", { stil:{ marginTop:"6px" } }, G.miniGrafik(seri, { en:170, boy:24 })) : null);
}

/** Ana EnPI kartının rozeti: baz çizgi var mı, normalize EnPI ne diyor? */
function bazRozeti() {
  const bz = H.etkinBazCizgi();
  if (!bz) return el("span.rozet.dikkat", {
    title:"Normalize EnPI için baz çizgi gerekir (Ekran 8)", metin:"baz çizgi yok" });
  const n = hucre("NORM_ENPI", donem.yil, donem.ay);
  if (!Number.isFinite(n)) return el("span.rozet", { title:bz.ad, metin:"baz: " + bz.ad });
  return el("span.rozet" + (n > 1.02 ? ".dikkat" : n < 0.98 ? ".iyi" : ""),
    { title:`Normalize EnPI — 1,00 = baz performans · ${bz.ad}`,
      metin:"norm. " + say(n, 3) });
}

function kartlar(k) {
  const gy = donemKaydir(donem.yil, donem.ay, -12);
  const al = s2 => hucre(s2, donem.yil, donem.ay);
  const alGY = s2 => hucre(s2, gy.yil, gy.ay);

  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  const enpiSutun = anaKod ? "ENPI_" + anaKod : null;
  const enpiTanim = V.durum.enpi_tanimlari.find(t => t.kod === anaKod);

  // Ölçüm kapsamı — TEK HESAP KAYNAĞI (İ-2): tanım hesap.js'dedir
  const kap = H.elektrikKapsami(donem.yil, donem.ay);
  const kapsam = kap.oran, sayac = kap.sayac || 0;

  const ges = H.gesKatkisi(donem.yil, donem.ay);

  k.append(el("div", { stil:{ display:"grid", marginBottom:"16px", gap:"12px",
    gridTemplateColumns:"repeat(auto-fit,minmax(210px,1fr))" } },
    kart("Toplam enerji", al("TOPLAM_ENERJI"), "kWh",
      { gecenYil:alGY("TOPLAM_ENERJI"), seri:son12("TOPLAM_ENERJI"), koken:"TOPLAM_ENERJI" }),
    kart("Enerji maliyeti", al("TOPLAM_MALIYET"), "TL",
      { gecenYil:alGY("TOPLAM_MALIYET"), seri:son12("TOPLAM_MALIYET"),
        alt:"net (GES mahsubu sonrası)", koken:"TOPLAM_MALIYET" }),
    enpiSutun ? kart(enpiTanim?.ad || "EnPI", al(enpiSutun), enpiTanim?.birim || "",
      { ondalik:enpiTanim?.ondalik ?? 4, gecenYil:alGY(enpiSutun), seri:son12(enpiSutun),
        koken:enpiSutun, rozet:bazRozeti() }) : null,
    kart("Üretim", H.noktaDeger("TOPLAM_URETIM", donem.yil, donem.ay).deger, "kg",
      { gecenYil:H.noktaDeger("TOPLAM_URETIM", gy.yil, gy.ay).deger,
        seri:son12("TOPLAM_URETIM"), koken:"TOPLAM_URETIM" }),
    kart("Ölçüm kapsamı", kapsam === null ? null : kapsam * 100, "%",
      { ondalik:1, alt:`${sayac} alt sayaç · ${kapsam !== null ? yuzde((1 - kapsam) * 100, 1) : "—"} ölçülmüyor`,
        rozet:kapsam !== null && kapsam < 0.5
          ? el("span.rozet.dikkat", { metin:"⚠ düşük" }) : null }),
    kart("GES katkısı", ges.deger, "TL",
      { alt:ges.deger ? "elektrik faturasından düşülen" : "bu dönem yok" })));
}

/* ----------------------------------------------------------- uyarılar */
function uyarilar(k) {
  const u = [];
  const bosluk = (katman.bosluklar || []).filter(b => b.donem === `${donem.yil}-${String(donem.ay).padStart(2,"0")}`);
  if (bosluk.length) u.push(["dikkat", `Bu dönemde ${bosluk.length} türetilmiş değer üretilemedi: ` +
    bosluk.slice(0, 2).map(b => b.ad).join(", ") + (bosluk.length > 2 ? "…" : "")]);
  if (katman.eksikler.length) u.push(["ciddi",
    `${katman.eksikler.length} değer hesaplanamıyor — dönüşüm katsayısı eksik olabilir.`]);
  const yd = V.yedekDurumu();
  if (yd.uyarmali) u.push(["dikkat", yd.aciklama + " — veriniz yalnızca bu tarayıcıda."]);
  for (const [tur, m] of u) k.append(uyari(tur, m));
}

/* ---------------------------------------------------------- grafikler */
function grafikler(k) {
  const d24 = [], e24 = [], enpi24 = [];
  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  for (let i = 23; i >= 0; i--) {
    const d = donemKaydir(donem.yil, donem.ay, -i);
    d24.push(donemKisa(d.yil, d.ay));
    e24.push(hucre("TOPLAM_ENERJI", d.yil, d.ay));
    enpi24.push(anaKod ? hucre("ENPI_" + anaKod, d.yil, d.ay) : null);
  }

  // G1 — toplam enerji (tek seri → açıklama yok, başlık adlandırır)
  const g1 = el("div.kart", {}, el("h2", { metin:"Son 24 ay · Toplam enerji tüketimi" }));
  k.append(g1);
  G.sutun(g1, { seriler:[{ ad:"Toplam enerji", degerler:e24 }], etiketler:d24,
                birim:"kWh", boy:250 });

  // G2 — EnPI: AYRI GRAFİK (çift eksen yasak, 5.7.2)
  const t = V.durum.enpi_tanimlari.find(x => x.kod === anaKod);
  if (t) {
    const g2 = el("div.kart", {}, el("h2", { metin:`Son 24 ay · ${t.ad}` }),
      el("p.mini.sessiz", { metin:
        "Tüketimle aynı grafikte gösterilmez: iki ölçeğin hizası keyfî olur ve " +
        "veride olmayan bir ilişki uydurur (5.7.2)." }));
    k.append(g2);
    G.cizgi(g2, { seriler:[{ ad:t.ad, degerler:enpi24 }], etiketler:d24,
                  birim:t.birim || "", boy:230, ondalik:t.ondalik ?? 4 });
  }

  // G3 — enerji türü dağılımı (yığılmış, kategorik)
  const d12 = [], elk = [], dg = [], mot = [];
  for (let i = 11; i >= 0; i--) {
    const d = donemKaydir(donem.yil, donem.ay, -i);
    d12.push(donemKisa(d.yil, d.ay));
    elk.push(V.deger("SEBEKE_ELK", d.yil, d.ay));
    const g = ["IST1_DG_KWH","IST2_DG_KWH","IST3_DG_KWH"]
      .map(c => V.deger(c, d.yil, d.ay)).filter(x => x !== null);
    dg.push(g.length ? g.reduce((a, b) => a + b, 0) : null);
    mot.push(hucre("MOTORIN_KWH", d.yil, d.ay));
  }
  const seriler = [{ ad:"Şebeke elektriği", degerler:elk }, { ad:"Doğalgaz", degerler:dg }];
  if (mot.some(Number.isFinite)) seriler.push({ ad:"Motorin", degerler:mot });
  const g3 = el("div.kart", {}, el("h2", { metin:"Son 12 ay · Enerji türü dağılımı" }));
  k.append(g3);
  G.sutun(g3, { seriler, etiketler:d12, birim:"kWh", yigili:true, boy:250 });
}

/* -------------------------------------------------------- yıllık özet */
function yillikOzet(k) {
  const yillar = [...new Set(katman.satirlar.map(r => r.yil))].sort((a, b) => b - a).slice(0, 5);
  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  const satirlar = yillar.map(y => {
    const r = katman.satirlar.filter(x => x.yil === y);
    const t = (s2) => { const v = r.map(x => x[s2]).filter(Number.isFinite);
      return v.length ? v.reduce((a, b) => a + b, 0) : null; };
    const enerji = t("TOPLAM_ENERJI");
    const uretim = r.map(x => H.noktaDeger("TOPLAM_URETIM", x.yil, x.ay).deger)
      .filter(Number.isFinite).reduce((a, b) => a + b, 0) || null;
    const eksikAy = r.filter(x => !Number.isFinite(
      H.noktaDeger("TOPLAM_URETIM", x.yil, x.ay).deger)).length;
    return { yil:y, ay:r.length, enerji, uretim,
      enpi:enerji && uretim ? enerji / uretim : null,
      maliyet:t("TOPLAM_MALIYET"), eksikAy };
  });

  const kart2 = el("div.kart", {}, el("h2", { metin:"Yıllık özet" }));
  kart2.append(tablo([
    { ad:"Yıl", deger:r => el("span", {}, String(r.yil),
        r.eksikAy ? el("span.rozet.dikkat", { stil:{ marginLeft:"6px" },
          title:"Bu yılın bazı aylarında üretim değeri üretilemedi",
          metin:`${r.eksikAy} ay eksik` }) : null) },
    { ad:"Ay", sayi:true, anahtar:"ay" },
    { ad:"Enerji (kWh)", sayi:true, anahtar:"enerji" },
    { ad:"Üretim (kg)", sayi:true, anahtar:"uretim" },
    { ad:"EnPI (kWh/kg)", sayi:true, ondalik:4, anahtar:"enpi" },
    { ad:"Maliyet (TL)", sayi:true, anahtar:"maliyet" },
  ], satirlar));
  k.append(kart2);
}
