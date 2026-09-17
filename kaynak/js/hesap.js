/* hesap.js — HESAP ÇEKİRDEĞİ. Tek hesap kaynağı (İ-2).
   Hiçbir ekran kendi hesabını yapmaz; hepsi buradan okur.
   El Kitabı: 7.1, 8.1-8.7, K-24 (rol filtresi), İ-1, İ-3 */

import { durum, deger } from "./veri.js";
import { nokta, varlik, altAgac, varlikNoktalari, cevir, formulCoz,
         ROLLER, enerjiBirimiMi } from "./model.js";

/** Özel toplam kodları — EnPI tanımlarında @ ile kullanılır */
export const OZEL = {
  "@TOPLAM_ENERJI_KWH": { ad:"Toplam Enerji (kWh)",       birim:"kWh" },
  "@TOPLAM_MALIYET_TL": { ad:"Toplam Enerji Maliyeti",    birim:"TL"  },
  "@NET_ODENEN_TL":     { ad:"Net Ödenen Elektrik",       birim:"TL"  },
};

/* --------------------------------------------------------- nokta değeri */
/**
 * Ham veya türetilmiş değer. Türetilmiş SAKLANMAZ, burada üretilir (İ-1).
 * Hesaplanan bir nokta başka bir hesaplanan noktaya inebilir; `ziyaret`
 * kümesi döngüsel formülü yakalar.
 */
export function noktaDeger(kod, yil, ay, ziyaret = null) {
  const n = nokta(kod);
  if (!n) return { eksik: `${kod} tanımlı değil` };
  if (n.veri_tipi === "olculen" || n.veri_tipi === "tahmini") {
    const v = deger(kod, yil, ay);
    return v === null ? { deger: null } : { deger: v };
  }
  const z = ziyaret || new Set();
  if (z.has(kod)) return { eksik: `Döngüsel formül: ${kod}` };
  z.add(kod);
  const r = formulCoz(n.formul, yil, ay, (k, y, a) => noktaDeger(k, y, a, z));
  z.delete(kod);
  return r;   // {deger} | {deger:null, veriYok, sebep} | {eksik}
}

/* ------------------------------------------------- toplam enerji (K-24) */
/**
 * SABİT LİSTE DEĞİL, ROL FİLTRESİ:
 * rolü `satin_alinan` ve toplama_dahil olan bütün noktaların ortak birimdeki toplamı.
 * Yeni bir yakıt tanımlandığında hiçbir formül değişmeden toplama girer.
 */
export function toplamEnerji(yil, ay, birim = "kWh") {
  let toplam = 0, katkida = 0;
  const eksikler = [], kalemler = [];
  for (const n of durum.olcum_noktalari) {
    if (!n.aktif || n.rol !== "satin_alinan" || !n.toplama_dahil) continue;
    const d = noktaDeger(n.kod, yil, ay);
    if (d.eksik) { eksikler.push(`${n.ad}: ${d.eksik}`); continue; }
    if (d.deger === null) continue;
    const c = cevir(d.deger, n.birim, birim, n.enerji_turu, yil, ay);
    if (c.eksik) { eksikler.push(c.eksik); continue; }
    if (c.deger === null) continue;
    toplam += c.deger; katkida++;
    kalemler.push({ kod:n.kod, ad:n.ad, ham:d.deger, birim:n.birim, cevrilen:c.deger });
  }
  // İ-3: eksik katsayı varsa sonuç ÜRETİLMEZ
  if (eksikler.length) return { eksik: eksikler[0], eksikler, kalemler };
  if (!katkida) return { deger: null, kalemler };
  return { deger: toplam, kalemler, birim };
}

/* ------------------------------------------------------- maliyet (6.5) */
function rolToplami(rol, yil, ay, yalnizDahil = true) {
  let t = 0, n_ = 0; const kalemler = [];
  for (const n of durum.olcum_noktalari) {
    if (!n.aktif || n.rol !== rol) continue;
    if (yalnizDahil && !n.toplama_dahil) continue;
    const d = noktaDeger(n.kod, yil, ay);
    if (d.eksik || d.deger === null) continue;
    t += d.deger; n_++;
    kalemler.push({ kod:n.kod, ad:n.ad, deger:d.deger });
  }
  return n_ ? { deger: t, kalemler } : { deger: null, kalemler };
}

/** GES mahsubu + satış (K-13, A-11: tek kalem de olabilir) */
export function gesKatkisi(yil, ay) {
  return rolToplami("gelir", yil, ay, false);
}

export function netOdenenElektrik(yil, ay) {
  const f = noktaDeger("ELK_FATURA_TL", yil, ay);
  const g = gesKatkisi(yil, ay);
  if (f.eksik || f.deger === null) return { deger: null };
  return { deger: f.deger - (g.deger || 0), brut: f.deger, mahsup: g.deger || 0 };
}

/** Toplam maliyet = rolü `maliyet` olan bütün noktalar − GES mahsubu (K-24) */
export function toplamMaliyet(yil, ay) {
  const m = rolToplami("maliyet", yil, ay);
  if (m.deger === null) return { deger: null, kalemler: m.kalemler };
  const g = gesKatkisi(yil, ay);
  return { deger: m.deger - (g.deger || 0), brut: m.deger,
           mahsup: g.deger || 0, kalemler: m.kalemler };
}

/** Ortalama birim fiyat — hesaplanır, girilmez (K-12) */
export function birimFiyat(faturaKod, tuketimKod, yil, ay) {
  const f = noktaDeger(faturaKod, yil, ay), t = noktaDeger(tuketimKod, yil, ay);
  if (f.deger === null || t.deger === null || !t.deger) return { deger: null };
  return { deger: f.deger / t.deger };
}

/* -------------------------------------------------- hiyerarşi toplamı */
/** Bir varlığın altındaki bütün noktaların toplamı (6.6a) */
export function varlikToplami(varlikKod, yil, ay, { rol = null, birim = "kWh" } = {}) {
  let t = 0, say = 0; const eksikler = [];
  for (const v of altAgac(varlikKod)) {
    for (const n of varlikNoktalari(v.kod)) {
      if (!n.aktif) continue;
      if (rol && n.rol !== rol) continue;
      if (!ROLLER[n.rol]?.enerji) continue;
      const d = noktaDeger(n.kod, yil, ay);
      if (d.eksik || d.deger === null) continue;
      const c = cevir(d.deger, n.birim, birim, n.enerji_turu, yil, ay);
      if (c.eksik) { eksikler.push(c.eksik); continue; }
      t += c.deger; say++;
    }
  }
  return say ? { deger: t, say, eksikler } : { deger: null, say: 0, eksikler };
}

/* --------------------------------------------------- ölçüm kapsamı (6.7) */
/**
 * Üst toplam, ölçülen alt toplam ve ölçülmeyen fark.
 * Satırların toplamı HER ZAMAN üst toplama eşittir; üzerine eklenmez.
 */
export function olcumKapsami(ustNoktaKod, altNoktaKodlari, yil, ay, birim = "kWh") {
  const u = noktaDeger(ustNoktaKod, yil, ay);
  if (u.eksik || u.deger === null) return { ust: null };
  const un = nokta(ustNoktaKod);
  const uc = cevir(u.deger, un.birim, birim, un.enerji_turu, yil, ay);
  if (uc.eksik) return { ust: null, eksik: uc.eksik };

  let olculen = 0, say = 0;
  for (const k of altNoktaKodlari) {
    const n = nokta(k); if (!n || !n.aktif) continue;
    const d = noktaDeger(k, yil, ay);
    if (d.eksik || d.deger === null) continue;
    const c = cevir(d.deger, n.birim, birim, n.enerji_turu, yil, ay);
    if (c.eksik) continue;
    olculen += c.deger; say++;
  }
  const fark = uc.deger - olculen;
  return {
    ust: uc.deger, olculen, olcumeyen: fark, say, birim,
    oran: uc.deger ? olculen / uc.deger : null,
    tutarsiz: fark < 0,       // S3: alt toplam üstü aştı
  };
}

/* ------------------------------------------------------------ EnPI (8.2) */
function enpiTerimi(ifade, yil, ay, birim = "kWh") {
  if (ifade === "@TOPLAM_ENERJI_KWH") return toplamEnerji(yil, ay, birim);
  if (ifade === "@TOPLAM_MALIYET_TL") return toplamMaliyet(yil, ay);
  if (ifade === "@NET_ODENEN_TL")     return netOdenenElektrik(yil, ay);
  return noktaDeger(ifade, yil, ay);
}

export function enpi(tanimKod, yil, ay) {
  const t = durum.enpi_tanimlari.find(x => x.kod === tanimKod);
  if (!t) return { eksik: "EnPI tanımı bulunamadı" };
  const p = enpiTerimi(t.pay, yil, ay), q = enpiTerimi(t.payda, yil, ay);
  if (p.eksik) return { eksik: `Pay: ${p.eksik}` };
  if (q.eksik) return { eksik: `Payda: ${q.eksik}` };
  if (p.veriYok) return { deger: null, veriYok: true, sebep: `Pay: ${p.sebep}` };
  if (q.veriYok) return { deger: null, veriYok: true, sebep: `Payda: ${q.sebep}` };
  if (p.deger === null || q.deger === null) return { deger: null };
  if (!q.deger) return { eksik: "Payda sıfır" };
  return { deger: p.deger / q.deger, pay: p.deger, payda: q.deger, tanim: t };
}

/* -------------------------------------------- dönüşüm verimliliği (8.6) */
export function donusumVerimi(varlikKod, yil, ay) {
  const nk = varlikNoktalari(varlikKod);
  const bul = (rol, tur, birim) => nk.find(n =>
    n.rol === rol && (!tur || n.enerji_turu === tur) && (!birim || n.birim === birim));

  const yakit = nk.find(n => n.rol === "satin_alinan" && n.birim === "kWh");
  if (!yakit) return null;
  const y = noktaDeger(yakit.kod, yil, ay);
  if (y.eksik || !y.deger) return null;

  const elk = bul("tesis_ici_uretim", "ELK", "kWh");
  const buh = nk.find(n => n.rol === "ara_enerji" && n.enerji_turu === "BUH" && n.birim === "kWh");
  const ssu = nk.find(n => n.rol === "ara_enerji" && n.enerji_turu === "SSU");

  const al = k => { if (!k) return 0; const d = noktaDeger(k.kod, yil, ay);
                    return (d.eksik || d.deger === null) ? 0 : d.deger; };
  const e = al(elk), b = al(buh), s = al(ssu);
  if (!e && !b && !s) return null;
  return {
    yakit: y.deger, elektrik: e, buhar: b, sicakSu: s,
    elektrikVerimi: e ? e / y.deger : null,
    toplamVerim: (e + b + s) / y.deger,
    kayip: 1 - (e + b + s) / y.deger,
  };
}

/* ------------------------------------- fiyat / hacim ayrıştırması (8.7) */
export function fiyatHacim(fiyat1, tuketim1, fiyat2, tuketim2) {
  if ([fiyat1, tuketim1, fiyat2, tuketim2].some(x => x === null || x === undefined))
    return null;
  const fiyatEtkisi   = (fiyat2 - fiyat1) * tuketim1;
  const hacimEtkisi   = (tuketim2 - tuketim1) * fiyat1;
  const bilesikEtki   = (fiyat2 - fiyat1) * (tuketim2 - tuketim1);
  return { fiyatEtkisi, hacimEtkisi, bilesikEtki,
           toplam: fiyatEtkisi + hacimEtkisi + bilesikEtki };
}

/* ------------------------------------------------ baz çizgi (8.3, 8.4) */
/** En küçük kareler. En az 12 nokta yoksa regresyon KURULMAZ (8.3). */
export function regresyon(ciftler) {
  const g = ciftler.filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
  if (g.length < 12) return { yetersiz: true, n: g.length };
  const n = g.length;
  const sx = g.reduce((t, p) => t + p.x, 0), sy = g.reduce((t, p) => t + p.y, 0);
  const sxx = g.reduce((t, p) => t + p.x * p.x, 0);
  const sxy = g.reduce((t, p) => t + p.x * p.y, 0);
  const payda = n * sxx - sx * sx;
  if (!payda) return { yetersiz: true, n, sebep: "Bağlam değişkeni hiç değişmiyor" };
  const a = (n * sxy - sx * sy) / payda;
  const b = (sy - a * sx) / n;
  const ort = sy / n;
  const sst = g.reduce((t, p) => t + (p.y - ort) ** 2, 0);
  const sse = g.reduce((t, p) => t + (p.y - (a * p.x + b)) ** 2, 0);
  const r2 = sst ? 1 - sse / sst : 0;
  return { a, b, r2, n,
    zayif: r2 < 0.5,                          // 8.3: açık uyarı gerektirir
    supheli: a < 0 };                          // üretim arttıkça enerji azalıyor
}

export function beklenen(bazCizgi, baglamDegeri) {
  if (!bazCizgi) return null;
  if (bazCizgi.model_tipi === "sabit") return bazCizgi.ortalama ?? null;
  if (baglamDegeri === null || baglamDegeri === undefined) return null;
  if (bazCizgi.a === undefined || bazCizgi.b === undefined) return null;
  return bazCizgi.a * baglamDegeri + bazCizgi.b;
}

/** CUSUM — kümülatif sapma (8.5) */
export function cusum(sapmalar) {
  let t = 0;
  return sapmalar.map(s => { t += (s ?? 0); return t; });
}
