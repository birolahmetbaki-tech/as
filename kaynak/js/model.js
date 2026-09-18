/* model.js — veri modeli sorguları, birim dönüşümü ve doğrulama
   El Kitabı: 6.2 (üç katman), 6.4 (roller), 6.8 (veri kalitesi), İ-3, İ-5 */

import { durum, deger, noktaDonemleri } from "./veri.js";
import { donemKod, donemKaydir } from "./ortak.js";

/* ----------------------------------------------------------- roller (6.4) */
export const ROLLER = {
  satin_alinan:      { ad:"Satın alınan enerji",   enerji:true,  toplam:true  },
  tesis_ici_uretim:  { ad:"Tesis içi üretim",      enerji:true,  toplam:false },
  ara_enerji:        { ad:"Ara enerji taşıyıcısı", enerji:true,  toplam:false },
  ayri_tesis_uretim: { ad:"Ayrı tesis üretimi",    enerji:true,  toplam:false },
  sebekeye_satilan:  { ad:"Şebekeye satılan",      enerji:true,  toplam:false },
  uretim_miktari:    { ad:"Üretim miktarı",        enerji:false, toplam:false },
  girdi_miktari:     { ad:"Girdi miktarı",         enerji:false, toplam:false },
  maliyet:           { ad:"Maliyet (TL)",          enerji:false, toplam:true  },
  gelir:             { ad:"Gelir (TL)",            enerji:false, toplam:false },
};
export const VERI_TIPLERI = {
  olculen:    "Ölçülen",     hesaplanan: "Hesaplanan",
  dagitilmis: "Dağıtılmış",  tahmini:    "Tahmini",
};

/* ----------------------------------------------------------- varlık ağacı */
export const varlik  = kod => durum.varliklar.find(v => v.kod === kod) || null;
export const nokta   = kod => durum.olcum_noktalari.find(n => n.kod === kod) || null;
export const enerjiTuru = kod => durum.enerji_turleri.find(t => t.kod === kod) || null;

export function agac() {
  const cocuk = new Map();
  for (const v of durum.varliklar) {
    if (!cocuk.has(v.ust)) cocuk.set(v.ust, []);
    cocuk.get(v.ust).push(v);
  }
  for (const l of cocuk.values()) l.sort((a, b) => (a.sira ?? 0) - (b.sira ?? 0));
  const kur = ust => (cocuk.get(ust) || []).map(v => ({ ...v, cocuklar: kur(v.kod) }));
  return kur(null);
}

export function varlikYolu(kod) {
  const yol = []; let v = varlik(kod); let guvenlik = 0;
  while (v && guvenlik++ < 50) { yol.unshift(v); v = v.ust ? varlik(v.ust) : null; }
  return yol;
}

/** Bir varlığın kendisi + bütün alt varlıkları */
export function altAgac(kod) {
  const sonuc = [], sira = [kod];
  while (sira.length) {
    const k = sira.shift(); const v = varlik(k);
    if (!v) continue;
    sonuc.push(v);
    for (const c of durum.varliklar) if (c.ust === k) sira.push(c.kod);
  }
  return sonuc;
}

export const varlikNoktalari = kod =>
  durum.olcum_noktalari.filter(n => n.varlik === kod);

/** Varlık o dönemde devrede mi? (İ-5, S6) */
export function devrede(varlikKod, yil, ay) {
  const v = varlik(varlikKod);
  if (!v) return true;
  const d = donemKod(yil, ay);
  if (v.devreye_giris  && d < v.devreye_giris)  return false;
  if (v.devreden_cikis && d > v.devreden_cikis) return false;
  return v.aktif !== false;
}

/* ------------------------------------------------- birim dönüşümü (8.1) */
/* Matematiksel dönüşüm SABİTTİR; referans birim GJ.
   1 TEP = 41,868 GJ = 11.630 kWh (El Kitabı 8.1) */
const GJ_KARSILIGI = { kWh: 0.0036, MJ: 0.001, GJ: 1, TEP: 41.868 };
export const ENERJI_BIRIMLERI = Object.keys(GJ_KARSILIGI);
export const enerjiBirimiMi = b => b in GJ_KARSILIGI;

/** Tarihli enerji içeriği katsayısı (İ-5). Sistem katsayı VARSAYMAZ (İ-3). */
export function katsayi(turKod, kaynakBirim, hedefBirim, yil, ay) {
  const d = donemKod(yil, ay);
  const uygun = durum.donusum_katsayilari
    .filter(k => k.enerji_turu === turKod &&
                 k.kaynak_birim === kaynakBirim && k.hedef_birim === hedefBirim &&
                 (!k.gecerli_baslangic || k.gecerli_baslangic <= d))
    .sort((a, b) => String(a.gecerli_baslangic).localeCompare(String(b.gecerli_baslangic)));
  return uygun.length ? uygun[uygun.length - 1] : null;
}

/**
 * Değeri hedef enerji birimine çevirir.
 * @returns {{deger:number, katsayi?:object}} veya {eksik:"açıklama"}
 * KURAL (6.6): değer yok veya 0 ise katsayı olmasa da sonuç üretilir.
 */
export function cevir(v, kaynakBirim, hedefBirim, turKod, yil, ay) {
  if (v === null || v === undefined) return { deger: null };
  if (kaynakBirim === hedefBirim) return { deger: v };
  if (v === 0) return { deger: 0 };                       // 6.6 kenar durumu

  if (enerjiBirimiMi(kaynakBirim) && enerjiBirimiMi(hedefBirim))
    return { deger: v * GJ_KARSILIGI[kaynakBirim] / GJ_KARSILIGI[hedefBirim] };

  // Enerji içeriği katsayısı gerekiyor (m³→kWh, kg→kWh)
  const k = katsayi(turKod, kaynakBirim, hedefBirim, yil, ay);
  if (k) return { deger: v * k.katsayi, katsayi: k };

  // kaynak → kWh → hedef
  const ara = katsayi(turKod, kaynakBirim, "kWh", yil, ay);
  if (ara && enerjiBirimiMi(hedefBirim)) {
    const kwh = v * ara.katsayi;
    return { deger: kwh * GJ_KARSILIGI.kWh / GJ_KARSILIGI[hedefBirim], katsayi: ara };
  }
  const t = enerjiTuru(turKod);
  // Değer VAR ama çevrilemiyor — bu gerçek bir sorundur (6.6 kenar durumu)
  return { eksik: `${t ? t.ad : turKod} için ${kaynakBirim} → ${hedefBirim} dönüşüm katsayısı tanımlı değil` };
}

/* ----------------------------------------------------- doğrulama (6.8) */
export const ENGEL = "engel", UYAR = "uyar";

/** Bulgu türleri — denetim ekranı bunlara göre gruplar (6.8) */
export const BULGU_TURLERI = {
  negatif:       "Negatif değer",
  gelecek:       "Gelecek dönem",
  devrede_degil: "Varlık devrede değil",
  sicrama:       "Ani sıçrama",
  dusuk:         "Ani düşüş",
  atlanan:       "Atlanmış dönem",
  oran:          "kWh/m³ oranı sapmış",
  denge:         "Faydalı enerji yakıttan büyük",
};

/* Ek doğrulama kuralları (6.8).
   Hesap çekirdeğini gerektiren kurallar buraya KAYIT OLUR; model.js hesap.js'e
   bağımlı olmaz, döngüsel içe aktarma doğmaz. */
const ekKurallar = [];
export function kuralEkle(fn) { ekKurallar.push(fn); }

function medyan(liste) {
  if (!liste.length) return null;
  const s = [...liste].sort((a, b) => a - b), o = s.length >> 1;
  return s.length % 2 ? s[o] : (s[o - 1] + s[o]) / 2;
}

/** Bir değerin son 12 dönemdeki medyanı (kendisi hariç) */
function gecmisMedyan(noktaKod, yil, ay) {
  const v = [];
  for (let i = 1; i <= 12; i++) {
    const { yil: y, ay: a } = donemKaydir(yil, ay, -i);
    const d = deger(noktaKod, y, a);
    if (d !== null && d !== 0) v.push(d);
  }
  return v.length >= 4 ? medyan(v) : null;
}

/**
 * Giriş anında çalışan denetimler. Sistem asla sessizce düzeltmez (İ-3, İ-4).
 * @returns [{seviye:"engel"|"uyar", mesaj:string}]
 */
export function dogrula(noktaKod, yil, ay, v) {
  const bulgular = [];
  const n = nokta(noktaKod);
  if (!n) return [{ seviye: ENGEL, mesaj: "Ölçüm noktası tanımlı değil" }];
  if (v === null || v === undefined || v === "") return bulgular;

  if (v < 0) bulgular.push({ seviye: ENGEL, mesaj: "Negatif değer girilemez" , tur: "negatif" });

  const bug = new Date();
  if (yil * 12 + ay > bug.getFullYear() * 12 + bug.getMonth() + 1)
    bulgular.push({ seviye: UYAR, mesaj: "Bu dönem gelecekte" , tur: "gelecek" });

  if (!devrede(n.varlik, yil, ay)) {
    const va = varlik(n.varlik);
    bulgular.push({ seviye: UYAR, tur: "devrede_degil",
      mesaj: `${va?.ad || n.varlik} bu dönemde devrede görünmüyor${va?.devreden_cikis ? ` (${va.devreden_cikis} sonrası)` : ""}` });
  }

  const m = gecmisMedyan(noktaKod, yil, ay);
  if (m !== null && v > 0) {
    if (v > m * 3)
      bulgular.push({ seviye: UYAR, tur: "sicrama", mesaj: `Son 12 ayın medyanının 3 katından büyük (medyan ${Math.round(m).toLocaleString("tr-TR")})` });
    else if (v < m / 3)
      bulgular.push({ seviye: UYAR, tur: "dusuk", mesaj: `Son 12 ayın medyanının üçte birinden küçük (medyan ${Math.round(m).toLocaleString("tr-TR")})` });
  }

  // Atlanan ay: bir önceki dönem boş ama daha öncesi dolu
  const o = donemKaydir(yil, ay, -1);
  if (deger(noktaKod, o.yil, o.ay) === null) {
    const oo = donemKaydir(yil, ay, -2);
    if (deger(noktaKod, oo.yil, oo.ay) !== null)
      bulgular.push({ seviye: UYAR, tur: "atlanan", mesaj: "Bir önceki dönem boş — atlanmış olabilir" });
  }

  // Doğalgaz kWh ↔ m³ tutarlılığı (K-04)
  const es = esBirimNoktasi(n);
  if (es) {
    const ev = deger(es.kod, yil, ay);
    if (ev !== null && ev !== 0 && v !== 0) {
      const kwh = n.birim === "kWh" ? v : ev;
      const m3  = n.birim === "m³"  ? v : ev;
      const oran = kwh / m3;
      const k = katsayi(n.enerji_turu, "m³", "kWh", yil, ay);
      const bek = k ? k.katsayi : 10.92;
      if (Math.abs(oran - bek) / bek > 0.05)
        bulgular.push({ seviye: UYAR, tur: "oran",
          mesaj: `kWh/m³ oranı ${oran.toFixed(2)} — beklenen ${bek.toFixed(2)} (%5'ten fazla sapma)` });
    }
  }

  for (const fn of ekKurallar) {
    let b = null;
    try { b = fn(noktaKod, yil, ay, v); } catch (e) { b = null; }
    if (b) bulgular.push(...(Array.isArray(b) ? b : [b]));
  }
  return bulgular;
}

/** Aynı varlık + aynı enerji türü, farklı birim (doğalgaz kWh ↔ m³) */
function esBirimNoktasi(n) {
  if (!n.enerji_turu || !["kWh", "m³"].includes(n.birim)) return null;
  const hedef = n.birim === "kWh" ? "m³" : "kWh";
  return durum.olcum_noktalari.find(x =>
    x.kod !== n.kod && x.varlik === n.varlik &&
    x.enerji_turu === n.enerji_turu && x.birim === hedef) || null;
}

/* ----------------------------------------------------- formül çözümleme */
/**
 * "A + B - C * 0.34" ve "KATSAYI(TUR,kaynak,hedef)" destekler.
 *
 * @param cozucu  (kod, yil, ay) => {deger}|{eksik}
 *   Verilmezse yalnız HAM değer okunur. hesap.js kendi çözücüsünü geçirir;
 *   böylece hesaplanan bir nokta başka bir hesaplanan noktaya inebilir
 *   (TOPLAM_URETIM -> TOPLAM_KAKAO -> ham değerler).
 */
export function formulCoz(formul, yil, ay, cozucu = null) {
  if (!formul) return { eksik: "Formül tanımlı değil" };

  // İKİ AYRI DURUM (İ-3 gürültü yapmasın diye):
  //   veriYok  → o dönemde ham veri hiç girilmemiş. NORMALDİR, sessizce null döner.
  //   eksikler → veri VAR ama hesaplanamıyor (katsayı yok vb.). Bu bir SORUNDUR.
  const veriYok = [], eksikler = [];
  let ifade = String(formul);

  // 1) KATSAYI(...) çağrılarını yer tutucuya al.
  //    Aksi halde argümanlarındaki büyük harfli tür kodu (BUH gibi) bir sonraki
  //    adımda ölçüm noktası sanılır.
  const katsayiCagrilari = [];
  ifade = ifade.replace(/KATSAYI\(\s*([A-Za-z_]+)\s*,\s*([^,)]+)\s*,\s*([^)]+)\s*\)/g,
    (_, tur, kay, hed) => {
      katsayiCagrilari.push({ tur: tur.trim(), kay: kay.trim(), hed: hed.trim() });
      return `\u0001k${katsayiCagrilari.length - 1}\u0001`;   // küçük harf: tanımlayıcı taramasına yakalanmasın
    });

  // 2) Ölçüm noktası kodlarını değerleriyle değiştir
  ifade = ifade.replace(/\b([A-Z][A-Z0-9_]*)\b/g, (tam) => {
    if (tam === "NaN") return tam;
    const r = cozucu ? cozucu(tam, yil, ay)
                     : (v => v === null ? { deger: null } : { deger: v })(deger(tam, yil, ay));
    if (r.veriYok)        { veriYok.push(r.sebep || `${tam} değeri yok`); return "NaN"; }
    if (r.eksik)          { eksikler.push(`${tam}: ${r.eksik}`); return "NaN"; }
    if (r.deger === null) { veriYok.push(`${tam} değeri yok`); return "NaN"; }
    return String(r.deger);
  });

  // 3) Ham veri hiç yoksa katsayı aramanın anlamı yok — sessizce çık
  if (veriYok.length) return { deger: null, veriYok: true, sebep: veriYok[0] };

  // 4) Katsayıları çöz
  ifade = ifade.replace(/\u0001k(\d+)\u0001/g, (_, i) => {
    const c = katsayiCagrilari[+i];
    const k = katsayi(c.tur, c.kay, c.hed, yil, ay);
    if (!k) { eksikler.push(`${c.tur} için ${c.kay} → ${c.hed} katsayısı tanımlı değil`); return "NaN"; }
    return String(k.katsayi);
  });

  if (!/^[\d+\-*/().\sNa]+$/.test(ifade))
    return { eksik: eksikler[0] || "Formül çözümlenemedi" };
  let s;
  try { s = Function(`"use strict";return (${ifade});`)(); }
  catch { return { eksik: "Formül hesaplanamadı" }; }
  if (!Number.isFinite(s)) return { eksik: eksikler[0] || "Sonuç üretilemedi", eksikler };
  return { deger: s };
}

