/* ekranlar/performans.js — Ekran 8: Performans (EnPI ve Baz Çizgi)
   El Kitabı 9.9 · PLATFORMUN KALBİ.
   "Ne kadar enerji harcadık?"tan "enerji performansımız iyileşti mi,
    ne zaman, ne kadar?"a geçiş burada olur. */

import { el, $, bosalt, say, kisa, yuzde, fark, uyari, bildir, onayla, bosDurum,
         tablo, donemAd, donemKisa, donemAraligi, donemKaydir, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { nokta } from "../model.js";
import * as H from "../hesap.js";
import { katman, hucre, sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";
import { aksiyonAc } from "./hedefler.js";
import { kokenDugmesi } from "../koken.js";
import { OZEL } from "../hesap.js";

let ar2 = null;

export function ekranPerformans(k) {
  const ar = V.veriAraligi();
  if (!ar) { k.append(el("div.sayfa-basi", {}, el("h1", { metin:"Performans (EnPI)" })));
    k.append(bosDurum("Henüz veri yok", "Önce Veri ekranının Aktar sekmesinden verinizi alın.",
      el("button.dugme.ana", { metin:"Veri ekranına git", onclick:() => { location.hash = "e2"; } })));
    return; }
  if (!ar2) { const son = sonEnerjiDonemi() || ar.son;
    ar2 = { bas:{ yil:son.yil, ay:1 }, son:{ yil:son.yil, ay:son.ay } }; }

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Performans (EnPI ve Baz Çizgi)" }),
    el("p", { metin:"Enerji performansındaki gerçek değişimi, üretim dalgalanmasından arındırarak ölçer ve değişimin tarihini bulur." })));

  bazCizgiSecici(k, ar);
  const bz = H.etkinBazCizgi();
  if (!bz) { ilkKurulum(k, ar); return; }

  donemSecici(k, ar);
  bolum1Model(k, bz);
  bolum2BeklenenGercek(k, bz);
  bolum3Enpi(k, bz);
  bolum4Cusum(k, bz);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranPerformans(k); };

/* ------------------------------------------------------ baz çizgi seçici */
function bazCizgiSecici(k, ar) {
  const kart = el("div.kart", { stil:{ padding:"12px 16px" } });
  const satir = el("div.satir", { stil:{ alignItems:"flex-end" } });
  if (V.durum.baz_cizgiler.length) {
    const sec = el("select", { onchange:e => {
      V.durum.ayarlar.varsayilan_baz = e.target.value; V.degisti("baz"); yenile(); } });
    for (const b of V.durum.baz_cizgiler)
      sec.append(el("option", { value:b.kod, metin:b.ad,
        selected:(V.durum.ayarlar?.varsayilan_baz || V.durum.baz_cizgiler[0].kod) === b.kod }));
    satir.append(el("div.alan", { stil:{ margin:"0", minWidth:"240px" } },
      el("label", { metin:"Etkin baz çizgi" }), sec));
  }
  satir.append(el("button.dugme.kucuk" + (V.durum.baz_cizgiler.length ? "" : ".ana"),
    { metin:"+ Baz çizgi kur", onclick:() => bazCizgiKur(null, ar) }));
  if (V.durum.baz_cizgiler.length) {
    const bz = H.etkinBazCizgi();
    satir.append(el("button.dugme.kucuk", { metin:"Düzenle", onclick:() => bazCizgiKur(bz.kod, ar) }));
    satir.append(el("button.dugme.kucuk.tehlike", { metin:"Sil", onclick:async () => {
      if (!await onayla("Baz çizgiyi sil", `"${bz.ad}" silinecek. Ham veri etkilenmez.`, "Sil", true)) return;
      V.durum.baz_cizgiler = V.durum.baz_cizgiler.filter(x => x.kod !== bz.kod);
      if (V.durum.ayarlar.varsayilan_baz === bz.kod)
        V.durum.ayarlar.varsayilan_baz = V.durum.baz_cizgiler[0]?.kod || null;
      V.degisti("baz"); yenile(); } }));
  }
  kart.append(satir);
  k.append(kart);
}

function ilkKurulum(k, ar) {
  k.append(bosDurum("Henüz baz çizgi yok",
    "Baz çizgi, enerji performansındaki gerçek değişimi ölçmenin referansıdır ve ISO 50001'in " +
    "zorunlu parçasıdır (madde 6.5). Bir referans dönem seçin; sistem beklenen tüketim modelini kursun.",
    el("button.dugme.ana", { metin:"Baz çizgi kur", onclick:() => bazCizgiKur(null, ar) })));
}

/* ---------------------------------------------------------- kurulum */
function bazCizgiKur(kod, ar) {
  const mevcut = kod ? V.durum.baz_cizgiler.find(b => b.kod === kod) : null;
  const son = sonEnerjiDonemi() || ar.son;
  const b = mevcut ? { ...mevcut } : {
    kod:"BAZ" + (V.durum.baz_cizgiler.length + 1), ad:"", enerji:"@TOPLAM_ENERJI_KWH",
    baglam:"TOPLAM_URETIM", model_tipi:"regresyon",
    bas:{ yil:Math.max(ar.ilk.yil, son.yil - 3), ay:1 },
    son:{ yil:son.yil - 1, ay:12 }, not:"" };

  const f = el("div");
  const gAd = el("input", { type:"text", value:b.ad, placeholder:"örn. 2022–2024 referansı" });
  const secenekler = [...Object.entries(OZEL).map(([k2, v]) => [k2, "★ " + v.ad]),
    ...V.durum.olcum_noktalari.map(n => [n.kod, `${n.ad} (${n.birim})`])];
  const mk = (etiket, deger, ipucu) => { const s2 = el("select");
    for (const [d, a] of secenekler) s2.append(el("option", { value:d, metin:a, selected:deger === d }));
    f.append(el("div.alan", {}, el("label", { metin:etiket }), s2,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null)); return s2; };
  f.append(el("div.alan", {}, el("label", { metin:"Ad" }), gAd));
  const gEnerji = mk("Ölçülen enerji", b.enerji);
  const gModel = el("select");
  for (const [d, a] of [["regresyon","Regresyonlu (beklenen = a × bağlam + b)"],
                        ["sabit","Sabit (referans dönem ortalaması)"]])
    gModel.append(el("option", { value:d, metin:a, selected:b.model_tipi === d }));
  f.append(el("div.alan", {}, el("label", { metin:"Model" }), gModel,
    el("div.mini.sessiz", { metin:"Regresyon en az 12 veri noktası ister; yoksa sabit model önerilir." })));
  const gBaglam = mk("Bağlam değişkeni", b.baglam,
    "Enerjiyi sürükleyen değişken — genellikle üretim miktarı. Sabit modelde kullanılmaz.");

  const donem = (etiket, hedef) => {
    const ay = el("select"); AYLAR.forEach((a, i) =>
      ay.append(el("option", { value:i + 1, metin:a.slice(0, 3), selected:b[hedef].ay === i + 1 })));
    const yil = el("input", { type:"number", value:b[hedef].yil, min:ar.ilk.yil, max:ar.son.yil,
      stil:{ width:"90px" } });
    f.append(el("div.alan", {}, el("label", { metin:etiket }),
      el("div.satir", { stil:{ gap:"5px" } }, ay, yil)));
    return { ay, yil };
  };
  const gBas = donem("Referans dönem başlangıcı", "bas");
  const gSon = donem("Referans dönem bitişi", "son");

  onayla(mevcut ? "Baz çizgiyi düzenle" : "Baz çizgi kur", f, "Kur ve kaydet").then(ok => {
    if (!ok) return;
    const tanim = { kod:b.kod, ad:gAd.value.trim() || "Baz çizgi",
      enerji:gEnerji.value, baglam:gBaglam.value, model_tipi:gModel.value,
      bas:{ yil:+gBas.yil.value, ay:+gBas.ay.value },
      son:{ yil:+gSon.yil.value, ay:+gSon.ay.value }, not:b.not };
    const r = H.bazCizgiKur(tanim);
    if (r.hata) { bildir(r.hata, "kritik"); return; }
    const yeni = { ...tanim, ...r, ciftler:undefined, kurulma:new Date().toISOString() };
    delete yeni.ciftler;
    if (mevcut) Object.assign(mevcut, yeni);
    else V.durum.baz_cizgiler.push(yeni);
    V.durum.ayarlar.varsayilan_baz = yeni.kod;
    V.degisti("baz"); yenile();
    bildir(yeni.model_tipi === "sabit"
      ? `Sabit baz çizgi kuruldu (${yeni.n} ay)`
      : `Regresyon kuruldu — R² = ${say(yeni.r2, 2)}`);
  });
}

/* ------------------------------------------------------ dönem seçici */
function donemSecici(k, ar) {
  const sec = (etiket, hedef) => {
    const ay = el("select", { onchange:e => { ar2[hedef].ay = +e.target.value; yenile(); } });
    AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a.slice(0, 3),
      selected:ar2[hedef].ay === i + 1 })));
    const yil = el("select", { onchange:e => { ar2[hedef].yil = +e.target.value; yenile(); } });
    for (let y = ar.ilk.yil; y <= ar.son.yil; y++)
      yil.append(el("option", { value:y, metin:y, selected:ar2[hedef].yil === y }));
    return el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:etiket }),
      el("div.satir", { stil:{ gap:"4px" } }, ay, yil));
  };
  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      el("strong", { stil:{ marginRight:"8px" }, metin:"Değerlendirme dönemi" }),
      sec("Başlangıç","bas"), sec("Bitiş","son"))));
}

const donemler = () => donemAraligi(ar2.bas.yil, ar2.bas.ay, ar2.son.yil, ar2.son.ay);
const adi = x => OZEL[x]?.ad || nokta(x)?.ad || x;

/* --------------------------------------------------- 1 · baz çizgi modeli */
function bolum1Model(k, bz) {
  const kart = el("div.kart", {}, el("h2", { metin:"1 · Baz çizgi modeli" }));
  const kutu = el("pre", { stil:{ background:"var(--yuzey-2)", padding:"12px 14px",
    borderRadius:"8px", fontSize:"13px", overflow:"auto", margin:"0 0 10px" } });

  if (bz.model_tipi === "sabit") {
    kutu.textContent =
      `Beklenen enerji = ${say(bz.ortalama, 0)} kWh/ay  (sabit)\n` +
      `Referans: ${donemAd(bz.bas.yil, bz.bas.ay)} – ${donemAd(bz.son.yil, bz.son.ay)} · ${bz.n} ay`;
    kart.append(kutu);
  } else {
    const bazYukPay = bz.ortalama ? bz.b / bz.ortalama : null;
    kutu.textContent =
      `Beklenen enerji = ${say(bz.a, 4)} × ${adi(bz.baglam)} + ${say(bz.b, 0)}        R² = ${say(bz.r2, 2)}\n` +
      `Değişken enerji : ${say(bz.a, 4)} kWh/birim\n` +
      `Sabit / baz yük : ${say(bz.b, 0)} kWh/ay` +
      (bazYukPay ? `   (ortalama tüketimin %${say(bazYukPay * 100, 1)}'i)` : "") + "\n" +
      `Referans        : ${donemAd(bz.bas.yil, bz.bas.ay)} – ${donemAd(bz.son.yil, bz.son.ay)} · n = ${bz.n}`;
    kart.append(kutu);

    // R² UYARISI GİZLENMEZ, SONUCUN YANINDA DURUR (8.3, İ-4)
    if (bz.r2 < 0.5)
      kart.append(uyari("ciddi",
        el("b", { metin:`⚠ R² = ${say(bz.r2, 2)} — model tüketimin yalnızca %${say(bz.r2 * 100, 0)}'ini açıklıyor. ` }),
        `Tüketimi belirleyen asıl şey ${adi(bz.baglam)} değil. Bu bulgunun kendisi değerlidir: ` +
        "başka bir sürükleyici (mevsim, ürün karması, ekipman durumu) baskındır. " +
        "Aşağıdaki sayılar İŞARETTİR, kanıt değildir.",
        el("div.kucuk", { stil:{ marginTop:"6px" }, metin:
          "Aynı belirsizlik sabit yük tahminini de kapsar: düşük R²'de kesişim noktasının " +
          "güven aralığı geniştir." })));
    if (bz.a < 0)
      kart.append(uyari("ciddi", el("b", { metin:"⚠ Eğim negatif. " }),
        `${adi(bz.baglam)} arttıkça enerji azalıyor — fiziksel olarak şüphelidir.`));
    if (bz.b > 0 && bz.ortalama && bz.b / bz.ortalama > 0.5)
      kart.append(uyari("bilgi", el("b", { metin:"Sabit yük baskın. " }),
        `Tüketimin yaklaşık %${say(bz.b / bz.ortalama * 100, 0)}'i üretimden bağımsız. ` +
        "Tasarruf potansiyeli üretim hattında değil, SÜREKLİ ÇALIŞAN SİSTEMLERDEDİR."));

    // dağılım grafiği
    const r = H.bazCizgiKur({ ...bz });
    if (r.ciftler?.length) {
      const bazKume = new Set(r.ciftler.map(p => p.etiket));
      const deg = donemler().map(d => {
        const e = H.terimDeger(bz.enerji, d.yil, d.ay);
        const x = H.terimDeger(bz.baglam, d.yil, d.ay);
        return Number.isFinite(e) && Number.isFinite(x)
          ? { x, y:e, etiket:donemKisa(d.yil, d.ay), anahtar:`${d.ay}/${d.yil}` } : null;
      }).filter(Boolean).filter(p => !bazKume.has(p.anahtar));
      G.dagilim(kart, {
        seriler:[{ ad:"Baz dönem", noktalar:r.ciftler },
                 ...(deg.length ? [{ ad:"Değerlendirme dönemi", noktalar:deg }] : [])],
        dogru:bz, xAd:adi(bz.baglam), yAd:"Enerji (kWh)", boy:320 });
    }
  }
  kart.append(el("p.mini.sessiz", { metin:
    `Kurulma: ${bz.kurulma ? new Date(bz.kurulma).toLocaleString("tr-TR") : "—"} · ` +
    "Regresyon katsayıları SAKLANIR (bir karardır); sapma ve CUSUM saklanmaz, her seferinde hesaplanır (İ-1)." }));
  k.append(kart);
}

/* ------------------------------------------------ 2 · beklenen vs gerçek */
function bolum2BeklenenGercek(k, bz) {
  const d = donemler();
  const et = d.map(x => donemKisa(x.yil, x.ay));
  const gercek = [], beklenen = [];
  for (const x of d) {
    const r = H.bazCizgiDegerlendir(bz, x.yil, x.ay);
    gercek.push(r ? r.gercek : null); beklenen.push(r ? r.beklenen : null);
  }
  const kart = el("div.kart", {}, el("h2", { metin:"2 · Beklenen ile gerçek" }));
  k.append(kart);
  G.cizgi(kart, { seriler:[{ ad:"Gerçek", degerler:gercek },
                           { ad:"Beklenen", degerler:beklenen }],
                  etiketler:et, birim:"kWh", boy:280 });

  const g = gercek.filter(Number.isFinite).reduce((a, b) => a + b, 0);
  const b2 = beklenen.filter(Number.isFinite).reduce((a, b) => a + b, 0);
  if (b2) {
    const s2 = g - b2, o = (g / b2 - 1) * 100;
    kart.append(el("div.satir", { stil:{ gap:"24px", marginTop:"10px", fontSize:"13px" } },
      el("span", {}, el("span.sessiz", { metin:"Gerçek: " }), el("b.sayi", { metin:say(g, 0) + " kWh" })),
      el("span", {}, el("span.sessiz", { metin:"Beklenen: " }), el("b.sayi", { metin:say(b2, 0) + " kWh" })),
      el("span", {}, el("span.sessiz", { metin:"Sapma: " }),
        el("b.sayi", { stil:`color:${s2 > 0 ? "var(--kritik)" : "var(--iyi-ink)"}`,
          metin:(s2 > 0 ? "+" : "−") + say(Math.abs(s2), 0) + " kWh" })),
      el("span", {}, el("span.sessiz", { metin:"Normalize EnPI: " }),
        el("b.sayi", { metin:say(g / b2, 3) }),
        el("span.mini.sessiz", { metin:`  (${fark(o)})` }))));
  }
}

/* ------------------------------------------------------------ 3 · EnPI */
function bolum3Enpi(k, bz) {
  const d = donemler();
  const et = d.map(x => donemKisa(x.yil, x.ay));
  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  const t = V.durum.enpi_tanimlari.find(x => x.kod === anaKod);
  const ham = d.map(x => anaKod ? hucre("ENPI_" + anaKod, x.yil, x.ay) : null);
  const norm = d.map(x => { const r = H.bazCizgiDegerlendir(bz, x.yil, x.ay);
    return r ? r.normalize : null; });

  const kart = el("div.kart", {}, el("h2", { metin:"3 · Ham EnPI ile normalize EnPI" }),
    el("p.kucuk.sessiz", { metin:
      "İkisi YAN YANA gösterilir, biri diğerinin yerine geçmez. Ham EnPI üretim düştüğünde " +
      "sabit yük yüzünden kendiliğinden kötüleşir — bu verimsizlik değildir. Normalize EnPI " +
      "üretim dalgalanmasından arındırılmıştır: 1,00 = baz performans. " +
      "Farklı ölçekte oldukları için AYRI grafiklerde gösterilirler (çift eksen yasak)." }));
  k.append(kart);

  const iki = el("div", { stil:{ display:"grid", gap:"16px",
    gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))" } });
  kart.append(iki);
  const sol = el("div", {}, el("h3", { metin:t?.ad || "Ham EnPI" }));
  const sag = el("div", {}, el("h3", { metin:"Normalize EnPI" }));
  iki.append(sol, sag);
  if (t) G.cizgi(sol, { seriler:[{ ad:t.ad, degerler:ham }], etiketler:et,
    birim:t.birim || "", boy:220, ondalik:t.ondalik ?? 4 });
  G.cizgi(sag, { seriler:[{ ad:"Normalize EnPI", degerler:norm, renk:"var(--s3)" }],
    etiketler:et, birim:"", boy:220, ondalik:3,
    referans:{ deger:1, ad:"1,00 = baz performans" } });
}

/* ----------------------------------------------------------- 4 · CUSUM */
function bolum4Cusum(k, bz) {
  const d = donemler();
  const et = d.map(x => donemKisa(x.yil, x.ay));
  const sapmalar = d.map(x => { const r = H.bazCizgiDegerlendir(bz, x.yil, x.ay);
    return r ? r.sapma : null; });
  const kum = H.cusum(sapmalar.map(v => Number.isFinite(v) ? v : 0));
  const gecerli = sapmalar.map((v, i) => Number.isFinite(v) ? kum[i] : null);

  // eğim kırılımı: ardışık 3 ayın ortalama eğimi işaret değiştirince
  const isaretler = [];
  const egim = i => (gecerli[i] !== null && gecerli[i - 1] !== null) ? gecerli[i] - gecerli[i - 1] : null;
  for (let i = 3; i < gecerli.length - 2; i++) {
    const once = [egim(i - 2), egim(i - 1)].filter(Number.isFinite);
    const sonra = [egim(i + 1), egim(i + 2)].filter(Number.isFinite);
    if (once.length < 2 || sonra.length < 2) continue;
    const o = once.reduce((a, b) => a + b, 0) / once.length;
    const s2 = sonra.reduce((a, b) => a + b, 0) / sonra.length;
    if (Math.sign(o) !== Math.sign(s2) && Math.abs(s2 - o) > Math.abs(o) * 1.5 + 1)
      { isaretler.push({ indeks:i, ad:et[i] }); i += 5; }
  }

  const kart = el("div.kart", {}, el("h2", { metin:"4 · CUSUM — kümülatif sapma" }),
    el("p.kucuk.sessiz", { metin:
      "Tek kural: EĞİM önemlidir, seviye değil. Yatay = baz çizgiyle uyumlu · " +
      "aşağı = kalıcı tasarruf · yukarı = kalıcı kayıp. Eğimin başladığı ay, " +
      "değişimin gerçekten devreye girdiği aydır — CUSUM'un asıl değeri budur: TARİHİ verir." }));
  k.append(kart);
  G.cusum(kart, { degerler:gecerli, etiketler:et, birim:"kWh", boy:300, isaretler });

  const son = gecerli.filter(v => v !== null).pop();
  if (Number.isFinite(son)) {
    const bf = V.durum.ayarlar?.para_birimi || "TL";
    const fiyat = hucre("BIRIM_FIYAT_ELK", ar2.son.yil, ar2.son.ay);
    kart.append(el("div.satir", { stil:{ gap:"24px", marginTop:"10px", fontSize:"13px" } },
      el("span", {}, el("span.sessiz", { metin:"Dönem sonu birikim: " }),
        el("b.sayi", { stil:`color:${son > 0 ? "var(--kritik)" : "var(--iyi-ink)"}`,
          metin:(son > 0 ? "+" : "−") + say(Math.abs(son), 0) + " kWh" })),
      Number.isFinite(fiyat) ? el("span", {},
        el("span.sessiz", { metin:"parasal karşılığı ≈ " }),
        el("b.sayi", { metin:say(Math.abs(son) * fiyat, 0) + " " + bf }),
        el("span.mini.sessiz", { metin:" (son dönem birim fiyatıyla)" })) : null));
  }
  if (isaretler.length)
    kart.append(uyari("dikkat",
      el("b", { metin:`${isaretler.length} eğim kırılımı bulundu: ` }),
      isaretler.map(i => i.ad).join(", ") + ". ",
      "Bu tarihlerde ne olduğunu araştırın — ekipman değişikliği, arıza veya işletme kararı."));

  // Analizden eyleme köprüsü (9.13): kırılım bulunmasa bile, dönem sonu
  // birikimi anlamlıysa tespit bir aksiyona dönüştürülebilir.
  if (Number.isFinite(son) && Math.abs(son) > 0) {
    const fiyat2 = hucre("BIRIM_FIYAT_ELK", ar2.son.yil, ar2.son.ay);
    kart.append(el("div", { stil:{ marginTop:"10px" } },
      el("button.dugme.kucuk", {
        metin: son > 0 ? "→ Bu kayıptan aksiyon aç" : "→ Bu tasarrufu aksiyon olarak kaydet",
        onclick:() => aksiyonAc({
          baslik: son > 0
            ? `Baz çizgiye göre kalıcı sapma (${ar2.bas.yil}-${ar2.son.yil})`
            : `Baz çizgiye göre kalıcı iyileşme (${ar2.bas.yil}-${ar2.son.yil})`,
          aciklama:
            `Baz çizgi "${bz.ad}" üzerinden kümülatif sapma dönem sonunda ` +
            `${son > 0 ? "+" : "−"}${say(Math.abs(son), 0)} kWh` +
            (Number.isFinite(fiyat2) ? ` ≈ ${say(Math.abs(son) * fiyat2, 0)} TL` : "") + ". " +
            (isaretler.length
              ? `Eğim kırılımı: ${isaretler.map(i => i.ad).join(", ")}. Bu tarihlerde yapılan ` +
                "ekipman, işletme veya bakım değişikliği araştırılmalı."
              : "Eğim dönem boyunca aynı yönde; tek bir olaydan değil, kalıcı bir " +
                "işletme durumundan kaynaklanıyor."),
          baglam:{ kaynak:`Ekran 8 · CUSUM (${ar2.bas.yil}-${ar2.son.yil})`,
                   donem:`${ar2.bas.yil}-${ar2.son.yil}` },
          beklenen: (son > 0 && Number.isFinite(fiyat2)) ? Math.abs(son) * fiyat2 : null,
        }) })));
  }
}
