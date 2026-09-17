/* ortak.js — biçimlendirme, ayrıştırma ve DOM yardımcıları
   El Kitabı: 5.7.3 (Türkçe sayı biçimi), İ-3 (sessiz dönüşüm yok) */

export const AYLAR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                      "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"];

/* ---------------------------------------------------------------- sayı */

/** Türkçe biçimde gösterir: 1250.5 -> "1.250,50" */
export function say(v, ondalik = 0) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString("tr-TR", {
    minimumFractionDigits: ondalik, maximumFractionDigits: ondalik });
}

/** Kısa gösterim: 137367837 -> "137,4 M" */
export function kisa(v, ondalik = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const m = Math.abs(v);
  if (m >= 1e9) return say(v / 1e9, ondalik) + " Mr";
  if (m >= 1e6) return say(v / 1e6, ondalik) + " M";
  if (m >= 1e3) return say(v / 1e3, ondalik) + " B";
  return say(v, ondalik);
}

export function yuzde(v, ondalik = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return "%" + say(v, ondalik);
}

/** İşaretli fark: +%4,7 / −%10,2 */
export function fark(v, ondalik = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const i = v > 0 ? "+" : v < 0 ? "−" : "";
  return i + "%" + say(Math.abs(v), ondalik);
}

/**
 * Türkçe sayı ayrıştırır. Tanımsız biçimi SESSİZCE DÖNÜŞTÜRMEZ (İ-3).
 *   "1.250,50" -> 1250.5     "1.000" -> 1000      "1250,5" -> 1250.5
 *   "1.5"      -> HATA (ondalık ayırıcı virgüldür)
 * @returns {{deger:number}|{hata:string}}
 */
export function sayiOku(metin) {
  if (metin === null || metin === undefined) return { hata: "Değer yok" };
  let t = String(metin).trim().replace(/\s/g, "");
  if (t === "") return { deger: null };

  let eksi = false;
  if (/^[-−]/.test(t)) { eksi = true; t = t.slice(1); }

  const nokta = (t.match(/\./g) || []).length;
  const virgul = (t.match(/,/g) || []).length;

  if (virgul > 1) return { hata: "Birden fazla virgül var" };
  if (!/^[\d.,]+$/.test(t)) return { hata: "Sayı olmayan karakter içeriyor" };

  if (virgul === 1) {
    const [tam, kesir] = t.split(",");
    if (nokta > 0 && !/^\d{1,3}(\.\d{3})*$/.test(tam))
      return { hata: "Binlik ayırıcı hatalı. Doğru yazım: 1.250,50" };
    t = tam.replace(/\./g, "") + "." + kesir;
  } else if (nokta > 0) {
    // Yalnız nokta var: binlik ayırıcı mı, ondalık mı?
    if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");   // 1.000 -> 1000
    else return { hata: "Ondalık ayırıcı virgüldür. Örnek: 1250,5" };
  }

  const d = Number(t);
  if (!Number.isFinite(d)) return { hata: "Sayıya çevrilemedi" };
  return { deger: eksi ? -d : d };
}

/* ---------------------------------------------------------------- dönem */

export const donemKod = (y, a) => `${y}-${String(a).padStart(2, "0")}`;
export const donemAd  = (y, a) => `${AYLAR[a - 1]} ${y}`;
export const donemKisa= (y, a) => `${AYLAR[a - 1].slice(0, 3)} ${String(y).slice(2)}`;

export function donemAyri(kod) {
  const m = /^(\d{4})-(\d{2})$/.exec(String(kod || ""));
  return m ? { yil: +m[1], ay: +m[2] } : null;
}
/** Kaç ay ileri/geri */
export function donemKaydir(y, a, n) {
  const t = y * 12 + (a - 1) + n;
  return { yil: Math.floor(t / 12), ay: (t % 12) + 1 };
}
/** Başlangıç–bitiş arası dönem listesi */
export function donemAraligi(by, ba, sy, sa) {
  const l = [];
  let y = by, a = ba;
  while (y < sy || (y === sy && a <= sa)) { l.push({ yil: y, ay: a });
    ({ yil: y, ay: a } = donemKaydir(y, a, 1)); }
  return l;
}
export const bugun = () => { const d = new Date();
  return { yil: d.getFullYear(), ay: d.getMonth() + 1 }; };

/** Yerel takvime göre bugünün ISO tarihi (YYYY-AA-GG) — saat içermez.
    Termin karşılaştırmaları metin olarak yapılır; saat dilimi kaydırmaz. */
export const bugunISO = () => { const d = new Date(), p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; };

/** Yalnız tarih — termin ve tarih alanları için */
export function tarihKisa(iso) {
  if (!iso) return "—";
  const [y, a, g] = String(iso).slice(0, 10).split("-");
  return (y && a && g) ? `${g}.${a}.${y}` : String(iso);
}

export function tarihMetni(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric" })
       + " " + d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}
export function gunFarki(iso) {
  if (!iso) return null;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
}

/* ---------------------------------------------------------------- DOM */

/** el("div.kart", {onclick}, cocuk...) */
export function el(tanim, ozellik = {}, ...cocuklar) {
  const [etiket, ...siniflar] = String(tanim).split(".");
  const d = document.createElement(etiket || "div");
  if (siniflar.length) d.className = siniflar.join(" ");
  for (const [k, v] of Object.entries(ozellik || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "sinif") d.className = [d.className, v].filter(Boolean).join(" ");
    else if (k === "metin") d.textContent = v;
    else if (k === "html") d.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") d.addEventListener(k.slice(2), v);
    else if (k === "stil") {
      if (typeof v === "string") d.style.cssText += v;      // "color:red" biçimi
      else Object.assign(d.style, v);
    }
    else d.setAttribute(k, v === true ? "" : v);
  }
  for (const c of cocuklar.flat()) {
    if (c === null || c === undefined || c === false) continue;
    d.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return d;
}
export const $  = (s, k = document) => k.querySelector(s);
export const $$ = (s, k = document) => [...k.querySelectorAll(s)];
export function bosalt(d) { while (d.firstChild) d.removeChild(d.firstChild); return d; }

/** Basit tablo kurar. sutunlar: [{ad, anahtar|deger(satir), sayi?, ondalik?}] */
export function tablo(sutunlar, satirlar, secenek = {}) {
  const t = el("table");
  const thead = el("thead");
  thead.append(el("tr", {}, sutunlar.map(s =>
    el("th" + (s.sayi ? ".s" : ""), { metin: s.ad }))));
  const tbody = el("tbody");
  for (const sat of satirlar) {
    const tr = el("tr", secenek.satirOzellik ? secenek.satirOzellik(sat) : {});
    for (const s of sutunlar) {
      const ham = s.deger ? s.deger(sat) : sat[s.anahtar];
      const td = el("td" + (s.sayi ? ".s" : ""));
      if (ham instanceof Node) td.append(ham);
      else if (s.sayi) td.textContent = say(ham, s.ondalik ?? 0);
      else td.textContent = ham ?? "—";
      if (s.baslik) td.title = s.baslik(sat) || "";
      tr.append(td);
    }
    tbody.append(tr);
  }
  t.append(thead, tbody);
  return secenek.sarma === false ? t : el("div.tablo-sar", {}, t);
}

export function uyari(tur, ...icerik) {
  const ikon = { bilgi:"ℹ", iyi:"✓", dikkat:"⚠", ciddi:"⚠", kritik:"✕" }[tur] || "ℹ";
  return el("div.uyari." + tur, {}, el("span.ikon", { metin: ikon }), el("div", {}, ...icerik));
}

export function bosDurum(baslik, aciklama, eylem) {
  return el("div.bos", {}, el("h3", { metin: baslik }), el("p", { metin: aciklama }), eylem);
}

/** Onay kutusu. Tehlikeli işlemlerde kullanılır. */
export function onayla(baslik, mesaj, onayMetni = "Onayla", tehlike = false) {
  return new Promise(coz => {
    const kapat = c => { ortu.remove(); coz(c); };
    const ortu = el("div.ortu", { onclick: e => { if (e.target === ortu) kapat(false); } },
      el("div.modal", {},
        el("h2", { metin: baslik }),
        typeof mesaj === "string" ? el("p", { metin: mesaj }) : mesaj,
        el("div.satir", { stil: { marginTop: "18px", justifyContent: "flex-end" } },
          el("button.dugme", { metin: "Vazgeç", onclick: () => kapat(false) }),
          el("button.dugme" + (tehlike ? ".tehlike" : ".ana"),
             { metin: onayMetni, onclick: () => kapat(true) }))));
    document.body.append(ortu);
  });
}

/** Salt okunur pencere — seçim sormaz, tek düğmesi vardır. */
export function goster(baslik, icerik, kapatMetni = "Kapat") {
  return new Promise(coz => {
    const kapat = () => { ortu.remove(); coz(); };
    const ortu = el("div.ortu", { onclick: e => { if (e.target === ortu) kapat(); } },
      el("div.modal", {},
        el("h2", { metin: baslik }),
        typeof icerik === "string" ? el("p", { metin: icerik }) : icerik,
        el("div.satir", { stil: { marginTop: "18px", justifyContent: "flex-end" } },
          el("button.dugme.ana", { metin: kapatMetni, onclick: kapat }))));
    document.body.append(ortu);
  });
}

/** Kısa bildirim */
export function bildir(mesaj, tur = "iyi") {
  const k = el("div", { stil: {
    position:"fixed", bottom:"20px", left:"50%", transform:"translateX(-50%)",
    background:"var(--yuzey)", border:"1px solid var(--cerceve)",
    borderLeft:`3px solid var(--${tur === "iyi" ? "iyi" : tur === "kritik" ? "kritik" : "s1"})`,
    borderRadius:"6px", padding:"10px 16px", zIndex:"60",
    boxShadow:"0 6px 24px rgba(0,0,0,.2)", fontSize:"13px" }, metin: mesaj });
  document.body.append(k);
  setTimeout(() => k.remove(), 3200);
}

export function dosyaIndir(ad, icerik, tip = "application/json") {
  const b = icerik instanceof Blob ? icerik : new Blob([icerik], { type: tip });
  const u = URL.createObjectURL(b);
  const a = el("a", { href: u, download: ad });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}
