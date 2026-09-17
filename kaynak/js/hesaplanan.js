/* hesaplanan.js — HESAPLANAN DEĞERLER KATMANI (K-23)
   Açılışta ve HER VERİ DEĞİŞİMİNDE baştan üretilir.
   Bütün ekranlar sayıyı buradan çeker (İ-2).
   Bu katman bir AYNADIR, kayıt değil: yedek dosyasına yazılmaz (İ-1, 5.3). */

import { durum, dinle, veriAraligi } from "./veri.js";
import { donemAraligi, donemKod } from "./ortak.js";
import { varlik, nokta } from "./model.js";
import * as H from "./hesap.js";

/** Katmanın son hâli */
export const katman = {
  satirlar: [],        // [{yil, ay, kod, ...değerler}]
  sutunlar: [],        // sütun tanımları (formül + kaynak dahil)
  uretim: null,        // ISO zaman damgası
  sure: 0,             // ms
  hucre: 0,
  eksikler: [],        // HESAPLANAMAYAN: veri var ama katsayı/formül eksik (İ-3) — sorundur
  bosluklar: [],       // VERİ BOŞLUĞU: ham veri girilmemiş — normaldir ama görünür olmalı (İ-4)
};

const dinleyiciler = new Set();
export function katmanDinle(fn) { dinleyiciler.add(fn); return () => dinleyiciler.delete(fn); }

/* ------------------------------------------------------- sütun tanımları */
/** Her sütun: kod, ad, birim, ondalik, formul (insan okur), kaynak, hesapla() */
function sutunlariKur() {
  const s = [];

  s.push({
    kod:"TOPLAM_ENERJI", ad:"Toplam Enerji", birim:"kWh", ondalik:0,
    formul:"rolü `satın alınan` ve toplama dahil olan bütün noktaların kWh toplamı",
    kaynak:() => durum.olcum_noktalari
      .filter(n => n.aktif && n.rol === "satin_alinan" && n.toplama_dahil)
      .map(n => `${n.kod} (${n.ad})`),
    kural:"7.1 · K-24 — sabit liste değil, rol filtresi",
    hesapla:(y,a) => H.toplamEnerji(y,a,"kWh"),
  });

  s.push({
    kod:"TOPLAM_MALIYET", ad:"Toplam Maliyet", birim:"TL", ondalik:0,
    formul:"rolü `maliyet` olan bütün noktalar − GES mahsubu",
    kaynak:() => durum.olcum_noktalari.filter(n => n.aktif && n.rol === "maliyet")
      .map(n => `${n.kod} (${n.ad})`),
    kural:"6.5 · K-13, K-24",
    hesapla:(y,a) => H.toplamMaliyet(y,a),
  });

  s.push({
    kod:"NET_ELEKTRIK", ad:"Net Ödenen Elektrik", birim:"TL", ondalik:0,
    formul:"ELK_FATURA_TL − GES mahsubu",
    kaynak:() => ["ELK_FATURA_TL", ...durum.olcum_noktalari.filter(n=>n.rol==="gelir").map(n=>n.kod)],
    kural:"6.5 · K-13 — fatura mahsup öncesi brüttür",
    hesapla:(y,a) => H.netOdenenElektrik(y,a),
  });

  s.push({
    kod:"BIRIM_FIYAT_ELK", ad:"Elektrik Birim Fiyatı", birim:"TL/kWh", ondalik:4,
    formul:"ELK_FATURA_TL ÷ SEBEKE_ELK",
    kaynak:() => ["ELK_FATURA_TL","SEBEKE_ELK"],
    kural:"K-12 — hesaplanır, girilmez",
    hesapla:(y,a) => H.birimFiyat("ELK_FATURA_TL","SEBEKE_ELK",y,a),
  });

  // Hesaplanan / dağıtılmış ölçüm noktaları (6.6)
  for (const n of durum.olcum_noktalari) {
    if (!n.aktif || (n.veri_tipi !== "hesaplanan" && n.veri_tipi !== "dagitilmis")) continue;
    s.push({
      kod:n.kod, ad:n.ad, birim:n.birim, ondalik:n.birim === "TL" ? 0 : 0,
      formul:n.formul || "—",
      kaynak:() => (n.formul || "").match(/\b[A-Z][A-Z0-9_]*\b/g)?.filter(x=>x!=="KATSAYI") || [],
      kural:n.veri_tipi === "dagitilmis"
        ? "2.2 — ölçüm değil, sabit oranla dağıtım"
        : "6.6 — türetilmiş nokta",
      hesapla:(y,a) => H.noktaDeger(n.kod,y,a),
      noktaMi:true,
    });
  }

  // EnPI'ler (8.2)
  for (const t of durum.enpi_tanimlari) {
    s.push({
      kod:"ENPI_" + t.kod, ad:t.ad, birim:t.birim || "", ondalik:t.ondalik ?? 4,
      formul:`${t.pay} ÷ ${t.payda}`,
      kaynak:() => [t.pay, t.payda],
      kural:"8.2 — kullanıcı tanımlı (K-06)" + (t.ana ? " · ANA GÖSTERGE" : ""),
      hesapla:(y,a) => H.enpi(t.kod,y,a),
      enpi:true,
    });
  }

  // Dönüşüm verimlilikleri (8.6)
  for (const v of durum.varliklar) {
    if (v.tip !== "ekipman") continue;
    const dv = H.donusumVerimi(v.kod, 2024, 1);
    const nk = durum.olcum_noktalari.filter(n => n.varlik === v.kod);
    const yakitli = nk.some(n => n.rol === "satin_alinan" && n.birim === "kWh");
    const ciktili = nk.some(n => n.rol === "tesis_ici_uretim" || n.rol === "ara_enerji");
    if (!yakitli || !ciktili) continue;
    s.push({
      kod:"VERIM_" + v.kod, ad:v.ad + " Toplam Verim", birim:"%", ondalik:1,
      formul:"(elektrik + buhar + sıcak su) ÷ doğalgaz",
      kaynak:() => nk.map(n => n.kod),
      kural:"8.6 — toplam enerjinin dışındadır, ekipman sağlığını ölçer",
      hesapla:(y,a) => { const r = H.donusumVerimi(v.kod,y,a);
        return r ? { deger: r.toplamVerim*100 } : { deger:null }; },
      verim:true,
    });
  }

  return s;
}

/* --------------------------------------------------------------- üretim */
export function uret() {
  const t0 = performance.now();
  const sutunlar = sutunlariKur();
  const ar = veriAraligi();
  const satirlar = [];
  const eksikler = [], bosluklar = [];

  if (ar) {
    for (const { yil, ay } of donemAraligi(ar.ilk.yil, ar.ilk.ay, ar.son.yil, ar.son.ay)) {
      const satir = { yil, ay, kod: donemKod(yil, ay) };
      for (const s of sutunlar) {
        let r;
        try { r = s.hesapla(yil, ay); } catch (e) { r = { eksik: e.message }; }
        if (r?.eksik) {
          satir[s.kod] = null;
          satir["_eksik_" + s.kod] = r.eksik;
          eksikler.push({ donem: satir.kod, sutun: s.kod, ad: s.ad, sebep: r.eksik });
        } else if (r?.veriYok) {
          satir[s.kod] = null;
          satir["_bosluk_" + s.kod] = r.sebep;
          bosluklar.push({ donem: satir.kod, sutun: s.kod, ad: s.ad, sebep: r.sebep });
        } else {
          satir[s.kod] = r?.deger ?? null;
        }
      }
      satirlar.push(satir);
    }
  }

  katman.sutunlar = sutunlar;
  katman.satirlar = satirlar;
  katman.uretim   = new Date().toISOString();
  katman.sure     = Math.round(performance.now() - t0);
  katman.hucre    = satirlar.length * sutunlar.length;
  katman.eksikler = eksikler;
  katman.bosluklar = bosluklar;

  for (const fn of dinleyiciler) { try { fn(katman); } catch (e) { console.error(e); } }
  return katman;
}

/** Tek dönem satırı */
export const satir = (yil, ay) =>
  katman.satirlar.find(s => s.yil === yil && s.ay === ay) || null;

/** Tek hücre */
export function hucre(sutunKod, yil, ay) {
  const s = satir(yil, ay);
  return s ? s[sutunKod] ?? null : null;
}

/** Yıllık toplam (EnPI ve verim gibi oranlar için toplama YAPILMAZ) */
export function yillik(sutunKod, yil) {
  const s = katman.sutunlar.find(x => x.kod === sutunKod);
  const satirlar = katman.satirlar.filter(x => x.yil === yil && x[sutunKod] !== null);
  if (!satirlar.length) return null;
  if (s?.enpi || s?.verim || sutunKod.startsWith("BIRIM_FIYAT")) return null;  // oran: toplanamaz
  return satirlar.reduce((t, x) => t + x[sutunKod], 0);
}

/** Veri her değiştiğinde katman yeniden üretilir (K-23) */
export function otomatikUret() {
  dinle(() => uret());
  uret();
}
