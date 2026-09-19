/* ekranlar/aktarma.js — Ekran 3: Veri Aktarma (El Kitabı 9.4)
   Zorunlu davranışlar: önizleme zorunlu · ya hep ya hiç · önce güvenlik yedeği ·
   bütün doğrulama kuralları burada da çalışır · üzerine yazma açıkça sorulur ·
   eşleşmeyen sütun atlanmaz, sorulur ve cevap HATIRLANIR. */

import { el, $, bosalt, say, sayiOku, uyari, bildir, onayla, tablo, bosDurum,
         donemAd, tarihMetni, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { nokta, dogrula, ENGEL } from "../model.js";
import { xlsxOku, sutunAdi } from "../xlsx.js";

let oturum = null;   // { dosyaAdi, sayfalar, secili, baslikSatiri, esleme, onizleme }

export function ekranAktarma(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Veri Aktarma" }),
    el("p", { metin:"Verinin sisteme giriş ve çıkış kapısı." })));
  aktarmaGovde(k);
}

/** Başlıksız gövde — birleşik Veri ekranı bunu çağırır (9.3) */
export function aktarmaGovde(k) {
  if (!oturum) { iceAktarBaslangic(k); yedekBolumu(k); }
  else if (!oturum.onizleme) eslemeEkrani(k);
  else onizlemeEkrani(k);
}

let yenileFn = null;
/** Birleşik Veri ekranı kendi yeniden çizimini buraya takar (9.3) */
export function yenileyiciKur(fn) { yenileFn = fn; }
const yenile = (...a) => { if (yenileFn) return yenileFn(...a);
  const k = bosalt($("#icerik")); ekranAktarma(k); };

/* ------------------------------------------------------- 1 · dosya seç */
function iceAktarBaslangic(k) {
  const kart = el("div.kart", {}, el("h2", { metin:"Excel içe aktarma" }));

  const kutu = el("div.bos", {
    stil:{ cursor:"pointer", padding:"40px 24px" },
    ondragover:e => { e.preventDefault(); kutu.style.borderColor = "var(--s1)"; },
    ondragleave:() => { kutu.style.borderColor = ""; },
    ondrop:e => { e.preventDefault(); kutu.style.borderColor = "";
                  if (e.dataTransfer.files[0]) dosyaAl(e.dataTransfer.files[0]); },
    onclick:() => giris.click(),
  },
    el("h3", { metin:"Excel dosyasını buraya sürükleyin" }),
    el("p", { metin:"veya tıklayıp seçin — .xlsx" }),
    el("p.mini.sessiz", { metin:"Dosya bilgisayarınızdan çıkmaz; tamamen tarayıcı içinde okunur." }));
  const giris = el("input", { type:"file", accept:".xlsx", stil:{ display:"none" },
    onchange:e => e.target.files[0] && dosyaAl(e.target.files[0]) });
  kart.append(kutu, giris);

  const es = V.durum.ayarlar?.sutun_eslesme;
  if (es && Object.keys(es).length)
    kart.append(el("p.kucuk.sessiz", { stil:{ marginTop:"10px" },
      metin:`Önceki aktarımdan ${Object.keys(es).length} sütun eşlemesi hatırlanıyor — tekrar sorulmayacak.` }));
  k.append(kart);
}

async function dosyaAl(dosya) {
  if (!/\.xlsx$/i.test(dosya.name)) return bildir("Yalnızca .xlsx dosyası okunabilir", "kritik");
  bildir("Okunuyor: " + dosya.name);
  try {
    const kitap = await xlsxOku(await dosya.arrayBuffer());
    if (!kitap.sayfalar.length) throw new Error("Dosyada sayfa yok.");
    oturum = { dosyaAdi:dosya.name, sayfalar:kitap.sayfalar, secili:0,
               baslikSatiri:null, esleme:null, onizleme:null };
    baslikBul();
    eslemeKur();
    yenile();
  } catch (e) { console.error(e); bildir("Okunamadı: " + e.message, "kritik"); }
}

/** Başlık satırı: ilk 6 satırda en çok metin hücresi olan satır */
function baslikBul() {
  const s = oturum.sayfalar[oturum.secili].satirlar;
  let eniyi = 0, enfazla = -1;
  for (let i = 0; i < Math.min(6, s.length); i++) {
    const n = (s[i] || []).filter(h => typeof h === "string" && h.trim()).length;
    if (n > enfazla) { enfazla = n; eniyi = i; }
  }
  oturum.baslikSatiri = eniyi;
}

/* ---------------------------------------------------- 2 · sütun eşleme */
function eslemeKur() {
  const sf = oturum.sayfalar[oturum.secili];
  const basliklar = sf.satirlar[oturum.baslikSatiri] || [];
  const hatirlanan = V.durum.ayarlar?.sutun_eslesme || {};
  const esleme = [];

  // Yıl / Ay sütunları
  let yilS = -1, ayS = -1;
  basliklar.forEach((b, i) => {
    const t = String(b || "").trim().toLocaleUpperCase("tr");
    if (t === "YIL" && yilS < 0) yilS = i;
    if (t === "AY"  && ayS  < 0) ayS  = i;
  });
  oturum.yilSutunu = yilS; oturum.aySutunu = ayS;

  for (let i = 0; i < basliklar.length; i++) {
    if (i === yilS || i === ayS) continue;
    const baslik = String(basliklar[i] ?? "").replace(/\s+/g, " ").trim();
    const harf = sutunAdi(i);
    let kod = null, kaynak = null;

    // 1) tanımlardaki excel_sutun (K-16 — ilk aktarımı otomatikleştirir)
    const t = V.durum.olcum_noktalari.find(n => n.excel_sutun === harf && n.veri_tipi === "olculen");
    if (t) { kod = t.kod; kaynak = "tanım"; }
    // 2) daha önce verilen cevap
    else if (baslik && hatirlanan[baslik] !== undefined) {
      kod = hatirlanan[baslik]; kaynak = "hatırlandı";
    }
    // 3) başlık metniyle birebir eşleşme
    else if (baslik) {
      const a = V.durum.olcum_noktalari.find(n =>
        n.veri_tipi === "olculen" &&
        (n.ad + " " + (n.birim || "")).toLocaleLowerCase("tr").replace(/\s+/g," ").trim()
          === baslik.toLocaleLowerCase("tr"));
      if (a) { kod = a.kod; kaynak = "başlık"; }
    }
    esleme.push({ sutun:i, harf, baslik, kod, kaynak,
                  dolu: sf.satirlar.filter(r => r[i] !== null && r[i] !== undefined && r[i] !== "").length });
  }
  oturum.esleme = esleme;
}

function eslemeEkrani(k) {
  const sf = oturum.sayfalar[oturum.secili];
  const eslesen = oturum.esleme.filter(e => e.kod).length;
  const bos = oturum.esleme.filter(e => !e.kod && e.dolu > 0).length;

  k.append(el("div.satir", { stil:{ marginBottom:"12px" } },
    el("button.dugme", { metin:"← Vazgeç", onclick:() => { oturum = null; yenile(); } }),
    el("strong", { metin:oturum.dosyaAdi })));

  if (oturum.yilSutunu < 0 || oturum.aySutunu < 0)
    k.append(uyari("kritik", el("b", { metin:"Yıl ve Ay sütunu bulunamadı. " }),
      "Başlık satırında 'YIL' ve 'AY' sütunları olmalı."));

  k.append(uyari(bos ? "dikkat" : "iyi",
    el("b", { metin:`${eslesen} sütun eşleşti` }),
    bos ? `, ${bos} sütun eşleşmedi. ` : ". Aktarmaya hazır.",
    bos ? el("div.kucuk", { stil:{ marginTop:"5px" }, metin:
      "Bunların çoğu beklenen: Excel'deki formül sütunları (toplamlar, hat dağılımları) " +
      "aktarılmaz — sistem onları ham veriden yeniden hesaplar (İ-1). Taslak sütunlar da " +
      "aktarılmaz (K-02). Aşağıdan tek tek gözden geçirip gerekirse eşleyebilirsiniz." }) : null));

  // Sayfa ve başlık satırı seçimi
  const ayar = el("div.kart", {}, el("h3", { metin:"Kaynak" }));
  if (oturum.sayfalar.length > 1) {
    const s = el("select", { onchange:e => { oturum.secili = +e.target.value;
      baslikBul(); eslemeKur(); yenile(); } });
    oturum.sayfalar.forEach((x, i) => s.append(el("option", { value:i, metin:x.ad,
      selected:i === oturum.secili })));
    ayar.append(el("div.alan", {}, el("label", { metin:"Sayfa" }), s));
  } else ayar.append(el("p.kucuk.sessiz", { metin:`Sayfa: ${sf.ad} · ${sf.satirlar.length} satır` }));
  const bs = el("input", { type:"number", value:oturum.baslikSatiri + 1, min:1, max:10,
    onchange:e => { oturum.baslikSatiri = Math.max(0, +e.target.value - 1); eslemeKur(); yenile(); } });
  ayar.append(el("div.alan", {}, el("label", { metin:"Başlık satırı" }), bs,
    el("div.mini.sessiz", { metin:"Ölçüm noktası adlarının bulunduğu satır." })));
  k.append(ayar);

  // Eşleme tablosu
  const secenekler = [["", "— aktarma —"],
    ...V.durum.olcum_noktalari.filter(n => n.veri_tipi === "olculen")
      .map(n => [n.kod, `${n.ad} (${n.birim})`])];
  k.append(el("h2", { metin:"Sütun eşlemesi", stil:{ marginTop:"18px" } }));
  k.append(tablo([
    { ad:"Sütun", deger:e => el("code", { metin:e.harf }) },
    { ad:"Excel başlığı", deger:e => e.baslik || el("span.sessiz", { metin:"(boş)" }) },
    { ad:"Dolu", sayi:true, anahtar:"dolu" },
    { ad:"Ölçüm noktası", deger:e => {
        const s = el("select", { onchange:ev => { e.kod = ev.target.value || null;
          e.kaynak = "elle"; eslemeHatirla(e); } });
        for (const [d, a] of secenekler)
          s.append(el("option", { value:d, metin:a, selected:e.kod === d }));
        return s; } },
    { ad:"Kaynak", deger:e => e.kod ? el("span.mini.sessiz", { metin:e.kaynak || "" }) : "" },
  ], oturum.esleme.filter(e => e.dolu > 0 || e.kod)));

  k.append(el("div.satir", { stil:{ marginTop:"16px" } },
    el("button.dugme.ana", { metin:"Önizle →", onclick:onizlemeUret })));
}

function eslemeHatirla(e) {
  if (!e.baslik) return;
  V.durum.ayarlar.sutun_eslesme ||= {};
  V.durum.ayarlar.sutun_eslesme[e.baslik] = e.kod;
  V.kaydet();
}

/* ------------------------------------------------------- 3 · önizleme */
const AY_NO = (() => { const m = new Map();
  AYLAR.forEach((a, i) => m.set(a.toLocaleLowerCase("tr"), i + 1)); return m; })();

function donemCoz(yilH, ayH) {
  const y = typeof yilH === "number" ? yilH : parseInt(String(yilH), 10);
  if (!Number.isFinite(y) || y < 1990 || y > 2100) return null;
  let a = null;
  if (typeof ayH === "number") a = ayH;
  else if (typeof ayH === "string") {
    a = AY_NO.get(ayH.trim().toLocaleLowerCase("tr")) ?? parseInt(ayH, 10);
  }
  return (a >= 1 && a <= 12) ? { yil:y, ay:a } : null;
}

function onizlemeUret() {
  const sf = oturum.sayfalar[oturum.secili];
  const es = oturum.esleme.filter(e => e.kod);
  const kayitlar = [], hatalar = [], uyarilar = [];
  const donemler = new Set();
  let cakisan = 0;

  for (let r = oturum.baslikSatiri + 1; r < sf.satirlar.length; r++) {
    const sat = sf.satirlar[r] || [];
    const d = donemCoz(sat[oturum.yilSutunu], sat[oturum.aySutunu]);
    if (!d) {
      if (sat.some(h => h !== null && h !== undefined && h !== ""))
        hatalar.push({ satir:r + 1, sebep:"Yıl/Ay okunamadı" });
      continue;
    }
    for (const e of es) {
      const ham = sat[e.sutun];
      if (ham === null || ham === undefined || ham === "") continue;
      const v = typeof ham === "number" ? ham : Number(String(ham).replace(/\./g, "").replace(",", "."));
      if (!Number.isFinite(v)) {
        hatalar.push({ satir:r + 1, sebep:`${e.harf}: sayı değil (${ham})`,
                       kod:e.kod, yil:d.yil, ay:d.ay, ham:String(ham) });
        continue;
      }
      const b = dogrula(e.kod, d.yil, d.ay, v);
      const engel = b.find(x => x.seviye === ENGEL);
      if (engel) {
        hatalar.push({ satir:r + 1, sebep:`${nokta(e.kod)?.ad}: ${engel.mesaj}`,
                       kod:e.kod, yil:d.yil, ay:d.ay, ham:String(ham) });
        continue;
      }
      for (const u of b) uyarilar.push({ donem:donemAd(d.yil, d.ay), ad:nokta(e.kod)?.ad, mesaj:u.mesaj });
      if (V.deger(e.kod, d.yil, d.ay) !== null) cakisan++;
      kayitlar.push({ kod:e.kod, yil:d.yil, ay:d.ay, v });
      donemler.add(`${d.yil}-${d.ay}`);
    }
  }
  const sirali = [...donemler].map(x => x.split("-").map(Number)).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  oturum.onizleme = { kayitlar, hatalar, uyarilar, cakisan,
    donem:donemler.size, ilk:sirali[0], son:sirali[sirali.length - 1] };
  yenile();
}

function onizlemeEkrani(k) {
  const o = oturum.onizleme;
  k.append(el("div.satir", { stil:{ marginBottom:"12px" } },
    el("button.dugme", { metin:"← Eşlemeye dön", onclick:() => { oturum.onizleme = null; yenile(); } }),
    el("strong", { metin:oturum.dosyaAdi })));

  const kart = el("div.kart", {}, el("h2", { metin:"Önizleme" }));
  const t = el("table");
  for (const [a, b] of [
    ["Aktarılacak değer", say(o.kayitlar.length)],
    ["Dönem sayısı", say(o.donem)],
    ["Dönem aralığı", o.ilk ? `${donemAd(o.ilk[0], o.ilk[1])} → ${donemAd(o.son[0], o.son[1])}` : "—"],
    ["Üzerine yazılacak", say(o.cakisan)],
    ["Hatalı satır", say(o.hatalar.length)],
    ["Uyarı", say(o.uyarilar.length)],
  ]) t.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td.s", { metin:String(b) })));
  kart.append(el("div.tablo-sar", { stil:{ maxHeight:"none" } }, t));
  k.append(kart);

  if (o.hatalar.length)
    k.append(uyari("ciddi",
      el("b", { metin:`${o.hatalar.length} değer aktarılamıyor ve DIŞARIDA BIRAKILACAK. ` }),
      "Geçerli değerler tek işlemde birlikte yazılır (ya hep ya hiç); aşağıdakiler yazılmaz. " +
      "Kaynak dosyadaki bu hücreleri düzeltip yeniden aktarabilirsiniz.",
      el("ul", { stil:{ margin:"8px 0 0 18px" } },
        o.hatalar.slice(0, 8).map(h => el("li.kucuk", {},
          `Satır ${h.satir}: ${h.sebep}`,
          h.kod ? el("button.dugme.kucuk", { stil:{ marginLeft:"8px" },
            metin: h.duzeltme === undefined ? "Düzelt"
                 : `düzeltildi: ${say(h.duzeltme, 0)}`,
            onclick:() => hucreDuzelt(h) }) : null)),
        o.hatalar.length > 8 ? el("li.kucuk.sessiz", { metin:`…ve ${o.hatalar.length - 8} tane daha` }) : null),
      el("p.kucuk", { stil:{ marginTop:"8px" }, metin:
        "Kaynak dosyadaki hücreyi düzeltip yeniden aktarabilir ya da doğru değeri " +
        "burada girebilirsiniz. Burada girilen değer kalitesi TAHMİN değil " +
        "DÜZELTİLDİ olarak işaretlenir ve kaynağı kayıtta kalır (İ-4)." })));

  if (o.uyarilar.length)
    k.append(uyari("dikkat", el("b", { metin:`${o.uyarilar.length} uyarı. ` }),
      "Bunlar aktarmayı engellemez ama gözden geçirin:",
      el("ul", { stil:{ margin:"8px 0 0 18px" } },
        o.uyarilar.slice(0, 6).map(u => el("li.kucuk", { metin:`${u.donem} · ${u.ad}: ${u.mesaj}` })),
        o.uyarilar.length > 6 ? el("li.kucuk.sessiz", { metin:`…ve ${o.uyarilar.length - 6} tane daha` }) : null)));

  if (o.cakisan)
    k.append(uyari("dikkat", el("b", { metin:`${say(o.cakisan)} dönem-nokta zaten dolu. ` }),
      "Aktarma bu değerlerin ÜZERİNE YAZACAK."));

  k.append(el("div.satir", { stil:{ marginTop:"16px" } },
    el("button.dugme.ana", { metin:`${say(o.kayitlar.length + o.hatalar.filter(h => h.duzeltme !== undefined).length)} geçerli değeri aktar`,
      disabled:!o.kayitlar.length, onclick:aktar }),
    el("button.dugme", { metin:"Vazgeç", onclick:() => { oturum = null; yenile(); } })));

  if (o.hatalar.length)
    k.append(el("p.kucuk.sessiz", { metin:
      `${o.hatalar.length} değer dışarıda kalacak. Bu hücrelerin ait olduğu dönemlerde, ` +
      "onlara bağlı türetilmiş değerler de üretilmez ve nedeni ekranda yazılır — " +
      "eksik veri sıfır sayılmaz (İ-3)." }));
}

/** Reddedilmiş bir hücrenin doğru değerini elle girmek (İ-4).
    Kaynak dosya bozuk kalabilir; düzeltme burada kayda geçer. */
function hucreDuzelt(h) {
  const n = nokta(h.kod);
  const g = el("input", { type:"text",
    value: h.duzeltme === undefined ? "" : String(h.duzeltme).replace(".", ",") });
  const f = el("div", {},
    el("p", {}, el("b", { metin:n?.ad || h.kod }), ` · ${donemAd(h.yil, h.ay)}`),
    el("p.kucuk.sessiz", { metin:`Kaynak dosyadaki değer: "${h.ham}" — ${h.sebep}` }),
    el("div.alan", {}, el("label", { metin:`Doğru değer (${n?.birim || ""})` }), g,
      el("div.mini.sessiz", { metin:"Türkçe biçim: 2.866.094 · Boş bırakılırsa düzeltme kaldırılır." })));
  onayla("Hücreyi düzelt", f, "Kaydet").then(ok => {
    if (!ok) return;
    const metin = g.value.trim();
    if (!metin) { delete h.duzeltme; yenile(); return; }
    const r = sayiOku(metin);
    if (r.hata) return bildir(r.hata, "kritik");
    const b = dogrula(h.kod, h.yil, h.ay, r.deger);
    const engel = b.find(x => x.seviye === ENGEL);
    if (engel) return bildir(engel.mesaj, "kritik");
    h.duzeltme = r.deger;
    bildir("Düzeltme kaydedildi — aktarmaya dahil edilecek");
    yenile();
  });
}

async function aktar() {
  const o = oturum.onizleme;
  const duzeltilen = o.hatalar.filter(h => h.duzeltme !== undefined);
  const ok = await onayla("Aktarmayı onaylayın",
    el("div", {},
      el("p", { metin:`${say(o.kayitlar.length)} değer, ${say(o.donem)} dönem aktarılacak.` }),
      o.cakisan ? el("p", {}, el("b", { metin:`${say(o.cakisan)} mevcut değerin üzerine yazılacak.` })) : null,
      duzeltilen.length ? el("p", {}, el("b", { metin:`${duzeltilen.length} hücre elle düzeltildi` }),
        " ve DÜZELTİLDİ kalitesiyle yazılacak.") : null,
      (o.hatalar.length - duzeltilen.length)
        ? el("p", {}, el("b", { metin:`${o.hatalar.length - duzeltilen.length} değer dışarıda kalacak.` })) : null,
      el("p.kucuk.sessiz", { metin:"Önce mevcut verinizin güvenlik yedeği indirilecek." })),
    "Aktar");
  if (!ok) return;

  V.guvenlikYedegi();
  for (const r of o.kayitlar) V.degerYaz(r.kod, r.yil, r.ay, r.v, { k:"girildi" });
  for (const h of duzeltilen)
    V.degerYaz(h.kod, h.yil, h.ay, h.duzeltme,
      { k:"duzeltildi", not:`Kaynak dosyada "${h.ham}" yazıyordu — elle düzeltildi` });
  V.durum.ayarlar.son_aktarim = { tarih:new Date().toISOString(),
    dosya:oturum.dosyaAdi, deger:o.kayitlar.length };
  V.degisti("aktarim");
  oturum = null;
  yenile();
  bildir(`${say(o.kayitlar.length)} değer aktarıldı`);
}

/* ------------------------------------------------------- yedek bölümü */
function yedekBolumu(k) {
  const y = V.yedekDurumu();
  const kart = el("div.kart", {}, el("h2", { metin:"Yedekleme" }));
  kart.append(uyari(y.uyarmali ? "dikkat" : "iyi", el("b", { metin:y.aciklama }),
    y.tarih ? el("div.kucuk", { metin:y.metin }) : null));
  kart.append(el("div.satir", {},
    el("button.dugme.ana", { metin:"Yedek al (.json)",
      onclick:() => { V.yedekAl(); yenile(); bildir("Yedek indirildi"); } }),
    el("label.dugme", { metin:"Yedekten geri yükle…", stil:{ cursor:"pointer" } },
      el("input", { type:"file", accept:".json", stil:{ display:"none" },
        onchange:e => geriYukle(e.target.files[0]) }))));
  const sa = V.durum.ayarlar?.son_aktarim;
  if (sa) kart.append(el("p.kucuk.sessiz", { stil:{ marginTop:"10px" },
    metin:`Son Excel aktarımı: ${tarihMetni(sa.tarih)} · ${sa.dosya} · ${say(sa.deger)} değer` }));
  k.append(kart);
}

async function geriYukle(dosya) {
  if (!dosya) return;
  let c;
  try { c = await V.yedegiCoz(dosya); } catch (e) { return bildir(e.message, "kritik"); }
  const o = c.ozet;
  const ok = await onayla("Yedeği geri yükle",
    el("div", {},
      el("p", { metin:`Bu yedek ${say(o.deger)} değer içeriyor` +
        (o.ilk ? `, ${donemAd(o.ilk.y, o.ilk.a)} → ${donemAd(o.son.y, o.son.a)}.` : ".") }),
      uyari("kritik", el("b", { metin:"Mevcut veriniz silinecek. " }),
        `Şu an ${say(V.durum.degerler.length)} değer var.`),
      el("p.kucuk.sessiz", { metin:"Önce güvenlik yedeği indirilecek." })),
    "Geri yükle", true);
  if (!ok) return;
  V.guvenlikYedegi(); V.yedegiUygula(c.nesne); yenile();
  bildir(`Geri yüklendi — ${say(o.deger)} değer`);
}
