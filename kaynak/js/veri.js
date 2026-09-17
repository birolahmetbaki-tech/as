/* veri.js — depolama katmanı
   El Kitabı: K-09, K-10, K-11, 5.2, 5.3
   Katman 1: IndexedDB, otomatik.  Katman 2: .json yedek dosyası, elle.
   Hesaplanan değerler burada SAKLANMAZ (K-23, İ-1). */

import { tarihMetni, gunFarki, dosyaIndir, donemKod } from "./ortak.js";

const DB_AD = "enerji-yonetim", DB_SURUM = 1, DEPO = "durum", ANAHTAR = "tek";
export const SEMA_SURUMU = 1;
export const YEDEK_UYARI_GUN = 7;

let db = null;
let yazmaZaman = null;
const dinleyiciler = new Set();

/** Bellekteki tek doğruluk kaynağı. Türetilmiş değer İÇERMEZ (İ-1). */
export const durum = {
  sema_surumu: SEMA_SURUMU,
  olusturma: null,
  ayarlar: {},
  enerji_turleri: [], varliklar: [], olcum_noktalari: [],
  donusum_katsayilari: [], enpi_tanimlari: [], baz_cizgiler: [],
  hedefler: [], aksiyonlar: [],
  degerler: [],           // [{n:kod, y:yıl, a:ay, v:değer, k:kalite, not:""}]
  _son_yedek: null,       // ISO
};

/* ----------------------------------------------------------- değer dizini */
/* degerler dizisi doğrudan taranmaz; hızlı erişim için dizin tutulur. */
let dizin = new Map();                       // "kod|yyyy-mm" -> kayıt
const dz = (n, y, a) => `${n}|${donemKod(y, a)}`;

function dizinKur() {
  dizin = new Map();
  for (const d of durum.degerler) dizin.set(dz(d.n, d.y, d.a), d);
}

export const deger    = (n, y, a) => dizin.get(dz(n, y, a))?.v ?? null;
export const degerKayit= (n, y, a) => dizin.get(dz(n, y, a)) ?? null;

/** Değer yazar/siler. null veya "" gönderilirse kayıt silinir (İ-3: 0 değildir). */
export function degerYaz(n, y, a, v, ek = {}) {
  const k = dz(n, y, a);
  const mevcut = dizin.get(k);
  if (v === null || v === undefined || v === "") {
    if (mevcut) {
      durum.degerler.splice(durum.degerler.indexOf(mevcut), 1);
      dizin.delete(k);
      degisti("deger");
    }
    return;
  }
  if (mevcut) Object.assign(mevcut, { v, ...ek });
  else { const yeni = { n, y, a, v, ...ek }; durum.degerler.push(yeni); dizin.set(k, yeni); }
  degisti("deger");
}

/** Bir ölçüm noktasının dolu dönemleri */
export function noktaDonemleri(n) {
  return durum.degerler.filter(d => d.n === n)
    .map(d => ({ yil: d.y, ay: d.a, v: d.v }))
    .sort((x, y2) => x.yil - y2.yil || x.ay - y2.ay);
}

/** Veride bulunan en eski ve en yeni dönem */
export function veriAraligi() {
  if (!durum.degerler.length) return null;
  let min = null, max = null;
  for (const d of durum.degerler) {
    const t = d.y * 12 + d.a;
    if (min === null || t < min.t) min = { t, yil: d.y, ay: d.a };
    if (max === null || t > max.t) max = { t, yil: d.y, ay: d.a };
  }
  return { ilk: min, son: max };
}

/* ----------------------------------------------------------- değişim olayı */
/** Her veri değişiminde hesap katmanı yeniden üretilir (K-23). */
export function dinle(fn) { dinleyiciler.add(fn); return () => dinleyiciler.delete(fn); }

export function degisti(ne = "genel") {
  for (const fn of dinleyiciler) { try { fn(ne); } catch (e) { console.error(e); } }
  kaydet();
}

/* ----------------------------------------------------------- IndexedDB */
function ac() {
  return new Promise((coz, red) => {
    const i = indexedDB.open(DB_AD, DB_SURUM);
    i.onupgradeneeded = () => {
      const d = i.result;
      if (!d.objectStoreNames.contains(DEPO)) d.createObjectStore(DEPO);
    };
    i.onsuccess = () => coz(i.result);
    i.onerror = () => red(i.error);
  });
}

function yaz(nesne) {
  return new Promise((coz, red) => {
    if (!db) return coz();
    const t = db.transaction(DEPO, "readwrite");
    t.objectStore(DEPO).put(nesne, ANAHTAR);
    t.oncomplete = coz; t.onerror = () => red(t.error);
  });
}

function oku() {
  return new Promise((coz, red) => {
    if (!db) return coz(null);
    const t = db.transaction(DEPO, "readonly");
    const i = t.objectStore(DEPO).get(ANAHTAR);
    i.onsuccess = () => coz(i.result || null);
    i.onerror = () => red(i.error);
  });
}

/** Yazma gecikmeli: hızlı ardışık girişlerde diske tek kez yazılır. */
export function kaydet() {
  clearTimeout(yazmaZaman);
  yazmaZaman = setTimeout(async () => {
    try {
      await yaz(disaVer());
      if (dosyaKolu) await dosyayaYaz();      // K-11, isteğe bağlı
    } catch (e) { console.error("Kaydedilemedi:", e); }
  }, 350);
}

/* ----------------------------------------------------------- aç / yükle */
export async function baslat(baslangicTanimlari) {
  try { db = await ac(); } catch { db = null; }      // gizli sekme vb.
  const kayitli = await oku().catch(() => null);
  if (kayitli) { iceYukle(kayitli); return { kaynak: "depo" }; }
  iceYukle({ ...baslangicTanimlari, olusturma: new Date().toISOString() });
  await yaz(disaVer()).catch(() => {});
  return { kaynak: "baslangic" };
}

function iceYukle(nesne) {
  const g = gocEt(nesne);
  for (const k of Object.keys(durum)) if (k in g) durum[k] = g[k];
  durum.degerler ||= [];
  dizinKur();
}

/** Şema göçü. Bir yedek dosyası hiçbir zaman okunamaz hale gelmemelidir (5.3). */
function gocEt(n) {
  const s = n.sema_surumu ?? 1;
  if (s > SEMA_SURUMU)
    throw new Error(`Bu yedek daha yeni bir sürümle oluşturulmuş (şema ${s}). Programı güncelleyin.`);
  // Gelecekte: if (s < 2) { ...dönüştür... }
  return n;
}

/** Kaydedilecek nesne — hesaplanan katman ASLA dahil değil (K-23). */
export function disaVer() {
  return {
    sema_surumu: SEMA_SURUMU,
    olusturma: durum.olusturma,
    guncelleme: new Date().toISOString(),
    ayarlar: durum.ayarlar,
    enerji_turleri: durum.enerji_turleri,
    varliklar: durum.varliklar,
    olcum_noktalari: durum.olcum_noktalari,
    donusum_katsayilari: durum.donusum_katsayilari,
    enpi_tanimlari: durum.enpi_tanimlari,
    baz_cizgiler: durum.baz_cizgiler,
    hedefler: durum.hedefler,
    aksiyonlar: durum.aksiyonlar,
    degerler: durum.degerler,
    _son_yedek: durum._son_yedek,
  };
}

/* ----------------------------------------------------------- yedekleme */
export function yedekAdi() {
  const d = new Date(), p = n => String(n).padStart(2, "0");
  return `enerji-veri-${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}.json`;
}

export function yedekAl(isaretle = true) {
  const nesne = disaVer();
  dosyaIndir(yedekAdi(), JSON.stringify(nesne, null, 1));
  if (isaretle) { durum._son_yedek = new Date().toISOString(); kaydet(); }
  return nesne;
}

/** Güvenlik yedeği: içe aktarma öncesi, "son yedek" damgasını DEĞİŞTİRMEZ. */
export function guvenlikYedegi() {
  if (!durum.degerler.length && !durum.olcum_noktalari.length) return false;
  const d = new Date(), p = n => String(n).padStart(2, "0");
  dosyaIndir(`guvenlik-yedegi-${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}.json`,
             JSON.stringify(disaVer(), null, 1));
  return true;
}

export function yedekDurumu() {
  const g = gunFarki(durum._son_yedek);
  return {
    tarih: durum._son_yedek, metin: tarihMetni(durum._son_yedek), gun: g,
    uyarmali: g === null || g >= YEDEK_UYARI_GUN,
    aciklama: g === null ? "Hiç yedek alınmadı"
            : g === 0   ? "Bugün yedek alındı"
            : `Son yedek ${g} gün önce alındı`,
  };
}

/** Yedek dosyasını okur ve ÖNİZLEME döndürür — henüz uygulamaz. */
export async function yedegiCoz(dosya) {
  const metin = await dosya.text();
  let n;
  try { n = JSON.parse(metin); }
  catch { throw new Error("Dosya geçerli bir JSON değil."); }
  if (!n || typeof n !== "object" || !Array.isArray(n.olcum_noktalari))
    throw new Error("Bu dosya bir enerji yönetim yedeği değil.");
  gocEt(n);
  const dg = n.degerler || [];
  let ilk = null, son = null;
  for (const d of dg) { const t = d.y * 12 + d.a;
    if (ilk === null || t < ilk.t) ilk = { t, y: d.y, a: d.a };
    if (son === null || t > son.t) son = { t, y: d.y, a: d.a }; }
  return { nesne: n, ozet: {
    deger: dg.length, nokta: n.olcum_noktalari.length, varlik: (n.varliklar || []).length,
    ilk, son, olusturma: n.olusturma, guncelleme: n.guncelleme } };
}

/** Önizleme onaylandıktan SONRA uygulanır. */
export function yedegiUygula(nesne) {
  iceYukle(nesne);
  degisti("yukle");
}

/* ------------------------------------------- dosyaya doğrudan yazma (K-11) */
let dosyaKolu = null;
export const dosyaYazmaDestegi = () => "showSaveFilePicker" in window;
export const dosyaYazmaAcik = () => !!dosyaKolu;

export async function dosyaYazmaAc() {
  if (!dosyaYazmaDestegi()) throw new Error("Bu tarayıcı desteklemiyor. Chrome veya Edge kullanın.");
  dosyaKolu = await window.showSaveFilePicker({
    suggestedName: yedekAdi(),
    types: [{ description: "Enerji verisi", accept: { "application/json": [".json"] } }],
  });
  await dosyayaYaz();
  return dosyaKolu.name;
}
export function dosyaYazmaKapat() { dosyaKolu = null; }

async function dosyayaYaz() {
  try {
    const y = await dosyaKolu.createWritable();
    await y.write(JSON.stringify(disaVer(), null, 1));
    await y.close();
    durum._son_yedek = new Date().toISOString();
  } catch (e) { console.error("Dosyaya yazılamadı:", e); dosyaKolu = null; }
}

/* ----------------------------------------------------------- tanılama */
export async function depoKullanimi() {
  if (!navigator.storage?.estimate) return null;
  const { usage, quota } = await navigator.storage.estimate();
  return { kullanim: usage, kota: quota };
}

export async function hepsiniSil() {
  durum.degerler = []; dizinKur();
  await yaz(disaVer()).catch(() => {});
  degisti("sil");
}
