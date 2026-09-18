/* hesap.js — HESAP ÇEKİRDEĞİ. Tek hesap kaynağı (İ-2).
   Hiçbir ekran kendi hesabını yapmaz; hepsi buradan okur.
   El Kitabı: 7.1, 8.1-8.7, K-24 (rol filtresi), İ-1, İ-3 */

import { durum, deger, degerKayit } from "./veri.js";
import { nokta, varlik, altAgac, varlikNoktalari, cevir, katsayi, formulCoz,
         kuralEkle, UYAR, ROLLER, enerjiBirimiMi } from "./model.js";

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

/* --------------------------------------------- elektrik ölçüm kapsamı (6.7) */
/**
 * TEK TANIM (İ-2). Panel ve Enerji Dengesi aynı sayıyı göstermek ZORUNDA.
 *   toplam elektrik = şebekeden çekilen + tesis içi üretim (kojen)
 *   ölçülen         = alt sayaçlar (toplama dahil OLMAYAN elektrik noktaları)
 */
export function elektrikAltSayaclari() {
  return durum.olcum_noktalari.filter(n =>
    n.aktif !== false && n.rol === "satin_alinan" && !n.toplama_dahil &&
    n.birim === "kWh" && n.enerji_turu === "ELK" && n.veri_tipi === "olculen");
}

export function elektrikKapsami(yil, ay) {
  const sebeke = noktaDeger("SEBEKE_ELK", yil, ay).deger;
  let kojen = 0;
  for (const n of durum.olcum_noktalari) {
    if (n.rol !== "tesis_ici_uretim" || n.enerji_turu !== "ELK" || n.birim !== "kWh") continue;
    if (n.veri_tipi !== "olculen") continue;          // türetilmiş "Üretilen Elektrik" iki kez saymasın
    const d = noktaDeger(n.kod, yil, ay);
    if (Number.isFinite(d.deger)) kojen += d.deger;
  }
  if (!Number.isFinite(sebeke)) return { toplam: null };
  let olculen = 0, sayac = 0;
  for (const n of elektrikAltSayaclari()) {
    const d = noktaDeger(n.kod, yil, ay);
    if (Number.isFinite(d.deger)) { olculen += d.deger; sayac++; }
  }
  const toplam = sebeke + kojen;
  return { toplam, sebeke, kojen, olculen, sayac,
           olcumeyen: toplam - olculen,
           oran: toplam ? olculen / toplam : null };
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

/* ------------------------------------------------ baz çizgi kurulumu */
/**
 * Bir baz çizgi tanımından model parametrelerini üretir (8.3).
 * Sonuç SAKLANIR — çünkü bir KARARDIR, türev değil (İ-1).
 * @param tanim {enerji, baglam, bas:{yil,ay}, son:{yil,ay}, model_tipi}
 */
export function bazCizgiKur(tanim) {
  const ciftler = [], enerjiler = [];
  let y = tanim.bas.yil, a = tanim.bas.ay;
  let guvenlik = 0;
  while ((y < tanim.son.yil || (y === tanim.son.yil && a <= tanim.son.ay)) && guvenlik++ < 600) {
    const e = terimDeger(tanim.enerji, y, a);
    const x = terimDeger(tanim.baglam, y, a);
    if (Number.isFinite(e)) {
      enerjiler.push(e);
      if (Number.isFinite(x)) ciftler.push({ x, y: e, etiket: `${a}/${y}` });
    }
    const t = y * 12 + (a - 1) + 1; y = Math.floor(t / 12); a = (t % 12) + 1;
  }
  if (!enerjiler.length) return { hata: "Referans dönemde enerji verisi yok" };

  const ortalama = enerjiler.reduce((t2, v) => t2 + v, 0) / enerjiler.length;
  if (tanim.model_tipi === "sabit")
    return { ortalama, n: enerjiler.length, ciftler };

  const r = regresyon(ciftler);
  if (r.yetersiz)
    return { hata: r.sebep || `Regresyon için en az 12 veri noktası gerekir (şu an ${r.n}). Sabit baz çizgi kullanın.`,
             n: r.n, ortalama, ciftler };
  return { ...r, ortalama, ciftler };
}

/** Özel toplam veya ölçüm noktası — tek sayı döndürür */
export function terimDeger(ifade, yil, ay) {
  const r = ifade === "@TOPLAM_ENERJI_KWH" ? toplamEnerji(yil, ay, "kWh")
          : ifade === "@TOPLAM_MALIYET_TL" ? toplamMaliyet(yil, ay)
          : ifade === "@NET_ODENEN_TL"     ? netOdenenElektrik(yil, ay)
          : noktaDeger(ifade, yil, ay);
  return Number.isFinite(r?.deger) ? r.deger : null;
}

/** Bir dönemi baz çizgiye göre değerlendirir (8.4) */
export function bazCizgiDegerlendir(bz, yil, ay) {
  if (!bz) return null;
  const gercek = terimDeger(bz.enerji, yil, ay);
  if (!Number.isFinite(gercek)) return null;
  let bek;
  if (bz.model_tipi === "sabit") bek = bz.ortalama;
  else {
    const x = terimDeger(bz.baglam, yil, ay);
    if (!Number.isFinite(x) || !Number.isFinite(bz.a)) return null;
    bek = bz.a * x + bz.b;
  }
  if (!Number.isFinite(bek) || !bek) return null;
  return { gercek, beklenen: bek, sapma: gercek - bek, normalize: gercek / bek };
}

/** Etkin baz çizgi (ayarlardan) */
export function etkinBazCizgi() {
  const k = durum.ayarlar?.varsayilan_baz;
  return durum.baz_cizgiler.find(b => b.kod === k) || durum.baz_cizgiler[0] || null;
}

/** CUSUM — kümülatif sapma (8.5) */
export function cusum(sapmalar) {
  let t = 0;
  return sapmalar.map(s => { t += (s ?? 0); return t; });
}

/* ===================================================================
   FAZ 4 — dönüşüm, maliyet ve ayrı tesis toplamları
   Ekran 9/10/11 kendi hesabını yapmaz; hepsi buradan okur (İ-2).
   =================================================================== */

/** Bir dönem aralığında bir noktanın toplamı. Hiç veri yoksa null (İ-3). */
export function donemToplami(kod, donemler) {
  let t = 0, varMi = false;
  for (const d of donemler) {
    const r = noktaDeger(kod, d.yil, d.ay);
    if (Number.isFinite(r.deger)) { t += r.deger; varMi = true; }
  }
  return varMi ? t : null;
}

/* ------------------------------------------------- dönüşüm varlıkları */
/**
 * Bir varlığın dönüşüm noktaları. SABİT LİSTE DEĞİL: roller taranır,
 * yeni bir kazan tanımlandığında ekran kendiliğinden onu da gösterir.
 */
export function donusumNoktalari(varlikKod) {
  const nk = varlikNoktalari(varlikKod).filter(n => n.aktif !== false);
  return {
    yakit: nk.find(n => n.rol === "satin_alinan" && n.birim === "kWh") || null,
    elk:   nk.find(n => n.rol === "tesis_ici_uretim" && n.enerji_turu === "ELK" && n.birim === "kWh") || null,
    buhar: nk.find(n => n.rol === "ara_enerji" && n.enerji_turu === "BUH" && n.birim === "kWh") || null,
    ssu:   nk.find(n => n.rol === "ara_enerji" && n.enerji_turu === "SSU" && n.birim === "kWh") || null,
  };
}

/** Yakıtı faydalı enerjiye çeviren bütün varlıklar (rol taramasıyla) */
export function donusumVarliklari() {
  const liste = [];
  for (const v of durum.varliklar) {
    if (v.aktif === false) continue;
    const n = donusumNoktalari(v.kod);
    if (!n.yakit) continue;
    if (!n.elk && !n.buhar && !n.ssu) continue;
    liste.push({ varlik: v, noktalar: n });
  }
  return liste;
}

/**
 * Bir dönem aralığında toplanmış dönüşüm verimi (8.6).
 * Verim, AYLIK ORANLARIN ORTALAMASI DEĞİL, toplamların oranıdır —
 * aksi halde az yakıt yakılan ay, çok yakılan ayla aynı ağırlığı alır.
 */
export function donusumVerimiAralik(varlikKod, donemler) {
  const n = donusumNoktalari(varlikKod);
  if (!n.yakit) return null;
  const yakit = donemToplami(n.yakit.kod, donemler);
  const elektrik = n.elk   ? (donemToplami(n.elk.kod, donemler)   || 0) : 0;
  const buhar    = n.buhar ? (donemToplami(n.buhar.kod, donemler) || 0) : 0;
  const sicakSu  = n.ssu   ? (donemToplami(n.ssu.kod, donemler)   || 0) : 0;
  const faydali  = elektrik + buhar + sicakSu;
  if (!Number.isFinite(yakit) || !yakit) {
    // yakıt yok ama üretim varsa bu bir veri tutarsızlığıdır, sessizce geçilmez
    return faydali ? { yakit:yakit || 0, elektrik, buhar, sicakSu, faydali,
                       tutarsiz:true, elektrikVerimi:null, isiVerimi:null,
                       toplamVerim:null, kayip:null } : null;
  }
  return {
    yakit, elektrik, buhar, sicakSu, faydali,
    elektrikVerimi: elektrik / yakit,
    isiVerimi: (buhar + sicakSu) / yakit,
    toplamVerim: faydali / yakit,
    kayip: 1 - faydali / yakit,
    kayipKwh: yakit - faydali,
    // Faydalı enerji yakıttan büyük olamaz. Olduğunda bu bir PERFORMANS
    // değil VERİ sorunudur; sonuç gizlenmez ama performans gibi de
    // sunulmaz (İ-3, 6.8). Yüzde 2 pay yuvarlama içindir.
    imkansiz: faydali > yakit * 1.02,
    calisan: donemler.filter(d => Number.isFinite(noktaDeger(n.yakit.kod, d.yil, d.ay).deger)
                                  && noktaDeger(n.yakit.kod, d.yil, d.ay).deger > 0).length,
  };
}

/* ------------------------------------------------------ fatura kalemleri */
/**
 * Maliyet noktaları ve faturalandırdıkları tüketim.
 * `fatura_tuketim` alanı hangi ölçüm noktalarının o faturayı oluşturduğunu
 * söyler; boşsa birim fiyat hesaplanamaz ama tutar yine toplanır (İ-3).
 */
export function faturaKalemleri() {
  return durum.olcum_noktalari
    .filter(n => n.aktif !== false && n.rol === "maliyet")
    .map(n => {
      const kodlar = (n.fatura_tuketim || []).filter(k => nokta(k));
      const ilk = kodlar.length ? nokta(kodlar[0]) : null;
      return { fatura:n, tuketimKodlari:kodlar,
               tuketimBirim: ilk ? ilk.birim : null,
               enerjiTuru: ilk ? ilk.enerji_turu : null };
    });
}

/** Bir fatura kaleminin bir aralıktaki tutarı, miktarı ve birim fiyatı (K-12) */
export function faturaOzeti(kalem, donemler) {
  const tutar = donemToplami(kalem.fatura.kod, donemler);
  let miktar = null;
  for (const k of kalem.tuketimKodlari) {
    const t = donemToplami(k, donemler);
    if (Number.isFinite(t)) miktar = (miktar || 0) + t;
  }
  return { tutar, miktar, birim:kalem.tuketimBirim,
           birimFiyat: (Number.isFinite(tutar) && Number.isFinite(miktar) && miktar)
                        ? tutar / miktar : null };
}

/** Birim fiyatı kWh cinsine çevirir — farklı yakıtlar ancak böyle kıyaslanır */
export function birimFiyatKwh(kalem, donemler) {
  const o = faturaOzeti(kalem, donemler);
  if (o.birimFiyat === null) return null;
  if (o.birim === "kWh") return o.birimFiyat;
  const son = donemler[donemler.length - 1];
  const c = cevir(1, o.birim, "kWh", kalem.enerjiTuru, son.yil, son.ay);
  if (c.eksik || !c.deger) return null;
  return o.birimFiyat / c.deger;
}

/**
 * Bir fatura kaleminin iki dönem arası fiyat/hacim ayrıştırması (8.7).
 * Ayrıştırma faturanın KENDİ biriminde yapılır (elektrik kWh, doğalgaz m³);
 * çevrim yapılırsa katsayı hatası etkilere karışır.
 */
export function kalemFiyatHacim(kalem, oncekiDonemler, simdikiDonemler) {
  const a = faturaOzeti(kalem, oncekiDonemler);
  const b = faturaOzeti(kalem, simdikiDonemler);
  if (a.birimFiyat === null || b.birimFiyat === null) return null;
  const d = fiyatHacim(a.birimFiyat, a.miktar, b.birimFiyat, b.miktar);
  if (!d) return null;
  return { ...d, onceki:a, simdiki:b,
           fiyatDegisim:(b.birimFiyat - a.birimFiyat) / a.birimFiyat,
           hacimDegisim: a.miktar ? (b.miktar - a.miktar) / a.miktar : null };
}

/** Bir aralıktaki maliyet dökümü: kalemler, GES mahsubu ve net toplam */
export function maliyetDokumu(donemler) {
  const kalemler = faturaKalemleri().map(k => ({ ...k, ...faturaOzeti(k, donemler) }));
  const brut = kalemler.reduce((t, k) => t + (k.tutar || 0), 0);
  const mahsup = donemToplami0(gelirNoktalari(), donemler);
  return { kalemler, brut, mahsup, net: brut - mahsup };
}

/** Rolü `gelir` olan noktalar — GES mahsubu ve satışı (K-13) */
export function gelirNoktalari() {
  return durum.olcum_noktalari.filter(n => n.aktif !== false && n.rol === "gelir");
}

function donemToplami0(noktalar, donemler) {
  let t = 0;
  for (const n of noktalar) t += donemToplami(n.kod, donemler) || 0;
  return t;
}

/* ------------------------------------------------- ayrı tesis (GES, K-03) */
/**
 * Ayrı tesisler: üretimi fabrikanın kWh dengesine GİRMEZ, yalnızca
 * mali dengeye mahsup olarak girer (7.1, 7.2).
 */
export function ayriTesisler() {
  const liste = [];
  for (const v of durum.varliklar) {
    if (v.aktif === false) continue;
    const nk = varlikNoktalari(v.kod).filter(n => n.aktif !== false);
    const uretim = nk.find(n => n.rol === "ayri_tesis_uretim");
    if (!uretim) continue;
    liste.push({ varlik:v, uretim, gelirler:nk.filter(n => n.rol === "gelir") });
  }
  return liste;
}

export function ayriTesisOzeti(tesis, donemler) {
  const uretim = donemToplami(tesis.uretim.kod, donemler);
  let gelir = null;
  for (const g of tesis.gelirler) {
    const t = donemToplami(g.kod, donemler);
    if (Number.isFinite(t)) gelir = (gelir || 0) + t;
  }
  const dolu = donemler.filter(d =>
    Number.isFinite(noktaDeger(tesis.uretim.kod, d.yil, d.ay).deger));
  return { uretim, gelir, ay:dolu.length,
           birimDeger: (Number.isFinite(gelir) && Number.isFinite(uretim) && uretim)
                        ? gelir / uretim : null,
           ilk: dolu[0] || null, son: dolu[dolu.length - 1] || null };
}

/* ---------------------------------------- katsayı değişimi uyarısı (İ-5) */
/**
 * İki dönemde aynı çevrim katsayısı mı kullanılıyor?
 * Katsayı değiştiyse iki dönem arasındaki farkın bir kısmı FİZİK DEĞİL,
 * VARSAYIM değişimidir. Bu asla sessizce geçilmez (İ-5, 6.6).
 */
export function katsayiKarsilastir(turKod, kaynakBirim, hedefBirim, donemA, donemB) {
  const a = katsayi(turKod, kaynakBirim, hedefBirim, donemA.yil, donemA.ay);
  const b = katsayi(turKod, kaynakBirim, hedefBirim, donemB.yil, donemB.ay);
  if (!a || !b) return { a, b, ayni:true, bilinmiyor:true };
  return { a, b, ayni: a.katsayi === b.katsayi,
           oran: a.katsayi ? b.katsayi / a.katsayi : null };
}

/**
 * Bir dönüşüm veriminin, ısı katsayısı eski dönemdekiyle aynı olsaydı
 * ne olacağı. Verim düşüşünün ne kadarı varsayım değişimi, ne kadarı
 * gerçek performanstır sorusunu ayırır.
 */
export function verimKatsayiDuzeltmesi(s, oran) {
  if (!s || !Number.isFinite(oran) || !oran || !s.yakit) return null;
  const isi = (s.buhar + s.sicakSu) / oran;        // eski katsayıya geri çevir
  const faydali = s.elektrik + isi;
  return { toplamVerim: faydali / s.yakit, faydali, isi };
}

/* ------------------------------- ekipmana atanmamış yakıt (6.7, A-05) */
/**
 * Satın alınan yakıt ile dönüşüm ekipmanlarına atanmış yakıt arasındaki fark.
 * Fark büyükse ekipman verimleri güvenilmezdir — hatta %100'ü aşabilir.
 * Enerji türü başına ayrı hesaplanır; sabit bir yakıt listesi yoktur (K-24).
 */
export function atanmamisYakit(donemler) {
  const satin = new Map();          // enerji_turu -> kWh
  for (const n of durum.olcum_noktalari) {
    if (n.aktif === false || n.rol !== "satin_alinan" || !n.toplama_dahil) continue;
    if (n.birim !== "kWh" || n.enerji_turu === "ELK") continue;
    const t = donemToplami(n.kod, donemler);
    if (Number.isFinite(t)) satin.set(n.enerji_turu, (satin.get(n.enerji_turu) || 0) + t);
  }
  const ekip = new Map();
  for (const x of donusumVarliklari()) {
    const y = x.noktalar.yakit;
    if (!y || y.birim !== "kWh") continue;
    const t = donemToplami(y.kod, donemler);
    if (Number.isFinite(t)) ekip.set(y.enerji_turu, (ekip.get(y.enerji_turu) || 0) + t);
  }
  const sonuc = [];
  for (const [tur, s] of satin) {
    const e = ekip.get(tur) || 0;
    sonuc.push({ enerji_turu:tur, satinAlinan:s, ekipman:e,
                 atanmamis:s - e, oran: s ? (s - e) / s : null,
                 olcumsuz: olcumsuzTuketiciler() });
  }
  return sonuc;
}

/**
 * Sayacı olmayan ama bir istasyondan beslendiği BİLİNEN tüketiciler (A-05).
 * Atanmamış yakıtın nereye gittiği sorusunun cevabı burada adlandırılır:
 * "bilinmiyor" demekle "sayacı yok" demek aynı şey değildir.
 */
export function olcumsuzTuketiciler(istasyonKod = null) {
  return durum.varliklar
    .filter(v => v.aktif !== false && v.olcumsuz_besleyen &&
                 (!istasyonKod || v.olcumsuz_besleyen === istasyonKod))
    .map(v => ({ kod:v.kod, ad:v.ad, besleyen:v.olcumsuz_besleyen,
                 besleyenAd: varlik(v.olcumsuz_besleyen)?.ad || v.olcumsuz_besleyen }));
}

/* ===================================================================
   FAZ 5 — İZLENEBİLİRLİK (E-4)
   "Bu sayı nereden geliyor?" sorusunun tek tıkla cevabı.
   =================================================================== */

/** Bir formüldeki ölçüm noktası kodları ve KATSAYI() çağrıları */
export function formulBilesenleri(formul) {
  const metin = String(formul || "");
  const katsayilar = [];
  const temiz = metin.replace(/KATSAYI\(\s*([A-Za-z_]+)\s*,\s*([^,)]+)\s*,\s*([^)]+)\s*\)/g,
    (_, tur, kay, hed) => {
      katsayilar.push({ tur:tur.trim(), kaynak:kay.trim(), hedef:hed.trim() });
      return " ";
    });
  const kodlar = [...new Set((temiz.match(/\b[A-Z][A-Z0-9_]*\b/g) || [])
    .filter(k => nokta(k)))];
  return { kodlar, katsayilar };
}

/**
 * Bir ölçüm noktasının bir dönemdeki KÖKEN AĞACI.
 * Ölçülen nokta yaprak olur (değer + kalite + not);
 * hesaplanan nokta formülüyle birlikte çocuklarına iner.
 * `derinlik` sonsuz döngüye karşı sınırdır.
 */
export function noktaKokeni(kod, yil, ay, derinlik = 4, ziyaret = null) {
  const n = nokta(kod);
  if (!n) return { kod, eksik:`${kod} tanımlı değil` };
  const r = noktaDeger(kod, yil, ay);
  const dugum = {
    kod, ad:n.ad, birim:n.birim, veri_tipi:n.veri_tipi, rol:n.rol,
    varlik:n.varlik, deger:r.deger ?? null,
    eksik:r.eksik || null, veriYok:!!r.veriYok, sebep:r.sebep || null,
    cocuklar:[], katsayilar:[],
  };
  if (n.veri_tipi === "olculen" || n.veri_tipi === "tahmini") {
    const k = degerKayit(kod, yil, ay);
    dugum.kalite = k?.k || (k ? "girildi" : null);
    dugum.not = k?.not || null;
    dugum.kaynakTipi = "ham";
    return dugum;
  }
  dugum.kaynakTipi = n.veri_tipi === "dagitilmis" ? "dagitim" : "formul";
  dugum.formul = n.formul || null;
  const z = ziyaret || new Set();
  if (z.has(kod) || derinlik <= 0) { dugum.kesildi = true; return dugum; }
  z.add(kod);
  const b = formulBilesenleri(n.formul);
  for (const c of b.kodlar) dugum.cocuklar.push(noktaKokeni(c, yil, ay, derinlik - 1, z));
  for (const kt of b.katsayilar) {
    const k = katsayi(kt.tur, kt.kaynak, kt.hedef, yil, ay);
    dugum.katsayilar.push({ ...kt, kayit:k || null });
  }
  z.delete(kod);
  return dugum;
}

/** Ortak birime çevrilirken kullanılan katsayı (toplamların kökeni için) */
export function noktaCevrimKatsayisi(kod, hedefBirim, yil, ay) {
  const n = nokta(kod);
  if (!n || n.birim === hedefBirim) return null;
  return katsayi(n.enerji_turu, n.birim, hedefBirim, yil, ay);
}

/* ===================================================================
   FAZ 5 — HEDEFLER VE AKSİYONLAR (9.13, K-21)
   Dört hedef türü de aynı motordan beslenir.
   =================================================================== */

export const HEDEF_TURLERI = {
  enpi:     { ad:"EnPI hedefi",     birim:"", yon:"azalt",
              aciklama:"Üretim dalgalanmasından arındırılmış performans" },
  tuketim:  { ad:"Tüketim hedefi",  birim:"kWh", yon:"azalt",
              aciklama:"Mutlak kWh — üretim düşerse kendiliğinden tutar" },
  maliyet:  { ad:"Maliyet hedefi",  birim:"TL", yon:"azalt",
              aciklama:"TL — fiyat piyasadan gelir, hepsi bizim başarımız değildir" },
  tasarruf: { ad:"Tasarruf hedefi", birim:"%", yon:"artir",
              aciklama:"Baz çizgiye göre iyileşme yüzdesi" },
};

/**
 * Bir hedefin dönem dönem gerçekleşmesi ve durumu.
 * Oranlar (EnPI, tasarruf) TOPLANMAZ; dönemin tamamı için yeniden hesaplanır.
 */
export function hedefDurumu(h) {
  const d = [];
  let y = h.bas.yil, a = h.bas.ay, guvenlik = 0;
  while ((y < h.son.yil || (y === h.son.yil && a <= h.son.ay)) && guvenlik++ < 600) {
    d.push({ yil:y, ay:a });
    const t = y * 12 + a; y = Math.floor(t / 12); a = (t % 12) + 1;
  }
  if (!d.length) return { hata:"Hedef dönemi boş" };

  const seri = d.map(x => ({ ...x, deger: hedefOlcumu(h, [x]) }));
  const gercek = hedefOlcumu(h, d);
  const tur = HEDEF_TURLERI[h.tur];
  const yon = h.yon || tur?.yon || "azalt";
  if (!Number.isFinite(gercek)) return { seri, donemler:d, gercek:null, yon };

  const fark = yon === "azalt" ? h.deger - gercek : gercek - h.deger;
  return {
    seri, donemler:d, gercek, yon,
    tuttu: fark >= 0,
    kalan: Math.abs(fark),
    // hedefe ne kadar yaklaşıldı: 1,00 = hedef tam tutuyor
    oran: h.deger ? (yon === "azalt" ? h.deger / gercek : gercek / h.deger) : null,
    doluAy: seri.filter(s => Number.isFinite(s.deger)).length,
  };
}

/** Bir hedefin ölçüsünü verilen dönemler için üretir */
export function hedefOlcumu(h, donemler) {
  if (h.tur === "tuketim" || h.tur === "maliyet") {
    let t = 0, varMi = false;
    for (const x of donemler) {
      const r = h.tur === "maliyet"
        ? (h.ifade && h.ifade !== "@TOPLAM_MALIYET_TL"
            ? noktaDeger(h.ifade, x.yil, x.ay) : toplamMaliyet(x.yil, x.ay))
        : (h.ifade && h.ifade !== "@TOPLAM_ENERJI_KWH"
            ? noktaDeger(h.ifade, x.yil, x.ay) : toplamEnerji(x.yil, x.ay, "kWh"));
      if (Number.isFinite(r?.deger)) { t += r.deger; varMi = true; }
    }
    return varMi ? t : null;
  }
  if (h.tur === "enpi") {
    // Dönem EnPI'si = dönem payı ÷ dönem paydası (aylık oranların ortalaması DEĞİL)
    const t = durum.enpi_tanimlari.find(x => x.kod === h.ifade);
    if (!t) return null;
    let pay = 0, payda = 0, varMi = false;
    for (const x of donemler) {
      const p = enpiTerimi(t.pay, x.yil, x.ay), q = enpiTerimi(t.payda, x.yil, x.ay);
      if (Number.isFinite(p?.deger) && Number.isFinite(q?.deger)) {
        pay += p.deger; payda += q.deger; varMi = true;
      }
    }
    return varMi && payda ? pay / payda : null;
  }
  if (h.tur === "tasarruf") {
    // Baz çizgiye göre iyileşme: (1 − gerçek/beklenen) × 100
    const bz = durum.baz_cizgiler.find(b => b.kod === h.ifade) || etkinBazCizgi();
    if (!bz) return null;
    let g = 0, b = 0, varMi = false;
    for (const x of donemler) {
      const r = bazCizgiDegerlendir(bz, x.yil, x.ay);
      if (r) { g += r.gercek; b += r.beklenen; varMi = true; }
    }
    return varMi && b ? (1 - g / b) * 100 : null;
  }
  return null;
}

/** Aksiyon durumları ve gecikme (9.13) */
export const AKSIYON_DURUMLARI = {
  acik:    { ad:"Açık",    ikon:"○", acikMi:true },
  devam:   { ad:"Devam",   ikon:"◐", acikMi:true },
  kapandi: { ad:"Kapandı", ikon:"●", acikMi:false },
  iptal:   { ad:"İptal",   ikon:"×", acikMi:false },
};

export function aksiyonGecikti(a, bugunISO) {
  if (!AKSIYON_DURUMLARI[a.durum]?.acikMi || !a.termin) return false;
  return a.termin < bugunISO;
}

export function aksiyonOzeti(bugunISO) {
  const hepsi = durum.aksiyonlar;
  const acik = hepsi.filter(a => AKSIYON_DURUMLARI[a.durum]?.acikMi);
  const geciken = acik.filter(a => aksiyonGecikti(a, bugunISO));
  const kapanan = hepsi.filter(a => a.durum === "kapandi");
  const topla = (liste, alan) => liste.reduce((t, a) =>
    Number.isFinite(a[alan]?.deger) ? t + a[alan].deger : t, 0);
  return {
    toplam:hepsi.length, acik:acik.length, geciken:geciken.length,
    kapanan:kapanan.length, gecikenler:geciken,
    beklenenTL: topla(hepsi.filter(a => a.durum !== "iptal"), "beklenen"),
    gerceklesenTL: topla(kapanan, "gerceklesen"),
  };
}

/* --------------------------------------------- veri kalitesi notu (İ-4) */
/**
 * Bir dönem aralığında kaç değer tahmin edilmiş, kaç değer boş.
 * Her rapor bu notu taşımak ZORUNDADIR (9.14).
 */
export function veriKalitesi(donemler) {
  const kod = new Set(donemler.map(d => `${d.yil}-${String(d.ay).padStart(2, "0")}`));
  let girildi = 0, duzeltildi = 0, tahmin = 0;
  for (const v of durum.degerler) {
    if (!kod.has(`${v.y}-${String(v.a).padStart(2, "0")}`)) continue;
    if (v.k === "tahmin") tahmin++;
    else if (v.k === "duzeltildi") duzeltildi++;
    else girildi++;
  }
  return { girildi, duzeltildi, tahmin, toplam:girildi + duzeltildi + tahmin };
}


/* ============================================================ 6.8 kuralı
   ENERJİ DENGESİ: bir dönüşüm ekipmanının faydalı enerjisi yakıtından
   büyük olamaz. Bu, S13'te gerçek veride görüldü (2025 buhar kilogramları
   fazla yazılmış). Kural giriş anında da, içe aktarmada da çalışır ki
   aynı hata bir daha sessizce girmesin.
   `engel` DEĞİL `uyar` seviyesindedir: yakıt ile üretim farklı sırayla
   girilebilir, yarı dolu bir dönem geçici olarak dengesiz görünür.       */
kuralEkle((noktaKod, yil, ay, v) => {
  const n = nokta(noktaKod);
  if (!n) return null;
  const cikti = n.rol === "ara_enerji" || n.rol === "tesis_ici_uretim";
  const yakitMi = n.rol === "satin_alinan";
  if (!cikti && !yakitMi) return null;

  const nk = donusumNoktalari(n.varlik);
  if (!nk.yakit) return null;

  const kwh = p => { if (!p) return 0;
    const d = noktaDeger(p.kod, yil, ay);
    return Number.isFinite(d.deger) ? d.deger : 0; };

  // Doğrulanan değerin kWh karşılığı (kg girilmişse katsayıyla çevrilir)
  const c = cevir(v, n.birim, "kWh", n.enerji_turu, yil, ay);
  if (c.eksik || !Number.isFinite(c.deger)) return null;
  const vKwh = c.deger;

  // Bu nokta hangi kalemin kaynağı? (kg noktası, kWh noktasının formülünde geçer)
  const kaynagiMi = p => p && (p.kod === noktaKod ||
    formulBilesenleri(p.formul).kodlar.includes(noktaKod));

  let yakit = yakitMi && (nk.yakit.kod === noktaKod) ? vKwh : kwh(nk.yakit);
  const faydali =
      (kaynagiMi(nk.elk)   ? vKwh : kwh(nk.elk)) +
      (kaynagiMi(nk.buhar) ? vKwh : kwh(nk.buhar)) +
      (kaynagiMi(nk.ssu)   ? vKwh : kwh(nk.ssu));

  if (!yakit || !faydali) return null;
  if (faydali <= yakit * 1.02) return null;
  const va = varlik(n.varlik);
  return { seviye: UYAR, tur: "denge",
    mesaj: `${va?.ad || n.varlik}: faydalı enerji yakıttan büyük ` +
      `(${Math.round(faydali).toLocaleString("tr-TR")} > ` +
      `${Math.round(yakit).toLocaleString("tr-TR")} kWh, verim %` +
      `${(faydali / yakit * 100).toFixed(0)}). Verim %100'ü aşamaz — ` +
      "ölçümlerden biri hatalı (6.8, K-25)." };
});
