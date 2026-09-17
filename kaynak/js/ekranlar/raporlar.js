/* ekranlar/raporlar.js — Ekran 13: Raporlar (El Kitabı 9.14, K-20)
   Ekranda görüleni kâğıda ve toplantıya taşır.
   Üç rapor: aylık enerji · yönetim gözden geçirme (ISO 50001 md. 9.3) · serbest.

   ZORUNLU DAVRANIŞLAR (9.14):
     · yazdırma dostu tek sütun
     · her rapor VERİ KALİTESİ NOTU taşır (İ-4)
     · her sayının kaynağına inilebilir (E-4) */

import { el, $, bosalt, say, yuzde, fark, uyari, bosDurum, tablo,
         donemAd, donemKisa, donemAraligi, donemKaydir, bugunISO, tarihKisa,
         AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { nokta, varlik, cevir } from "../model.js";
import * as H from "../hesap.js";
import { katman, hucre, satir, sonEnerjiDonemi } from "../hesaplanan.js";
import { kokenDugmesi } from "../koken.js";
import * as G from "../grafik.js";

const RAPORLAR = [
  { kod:"aylik",  ad:"Aylık Enerji Raporu",
    aciklama:"Tek sayfa: ayın tüketimi, maliyeti, EnPI'si, hedef durumu ve açık aksiyonlar." },
  { kod:"yonetim", ad:"Yönetim Gözden Geçirme Raporu",
    aciklama:"ISO 50001 md. 9.3 girdileri: dönem performansı, EnPI'ler, SEU, hedefler, aksiyonlar." },
  { kod:"serbest", ad:"Serbest Rapor",
    aciklama:"Tarih aralığı, kırılım ve birim seçilerek oluşturulan rapor." },
];

let secim = { rapor:"aylik", donem:null, bas:null, son:null,
              kirilim:"enerji_turu", birim:"kWh" };

export function ekranRaporlar(k) {
  const ar = V.veriAraligi();
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Raporlar" }),
    el("p", { metin:"Ekranda görüleni kâğıda taşır. Her rapor yazdırılabilir ve veri kalitesi notu taşır." })));

  if (!ar) return k.append(bosDurum("Henüz veri yok",
    "Rapor, girdiğiniz veriden üretilir. Önce Veri Aktarma ekranından verinizi alın.",
    el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));

  const se = sonEnerjiDonemi() || ar.son;
  if (!secim.donem) secim.donem = { yil:se.yil, ay:se.ay };
  if (!secim.bas) secim.bas = { yil:se.yil, ay:1 };
  if (!secim.son) secim.son = { yil:se.yil, ay:se.ay };

  secici(k, ar);
  const govde = el("div.rapor");
  k.append(govde);
  if (secim.rapor === "aylik")   aylikRapor(govde);
  if (secim.rapor === "yonetim") yonetimRaporu(govde);
  if (secim.rapor === "serbest") serbestRapor(govde);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranRaporlar(k); };

/* ------------------------------------------------------------ seçici */
function secici(k, ar) {
  const kart = el("div.kart", { stil:{ padding:"12px 16px" } });
  const satirEl = el("div.satir", { stil:{ alignItems:"flex-end" } });

  const rs = el("select", { onchange:e => { secim.rapor = e.target.value; yenile(); } });
  for (const r of RAPORLAR)
    rs.append(el("option", { value:r.kod, metin:r.ad, selected:secim.rapor === r.kod }));
  satirEl.append(el("div.alan", { stil:{ margin:"0", minWidth:"260px" } },
    el("label", { metin:"Rapor" }), rs));

  const donemSec = (etiket, hedef) => {
    const ay = el("select", { onchange:e => { secim[hedef].ay = +e.target.value; yenile(); } });
    AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a.slice(0, 3),
      selected:secim[hedef].ay === i + 1 })));
    const yil = el("select", { onchange:e => { secim[hedef].yil = +e.target.value; yenile(); } });
    for (let y = ar.ilk.yil; y <= ar.son.yil; y++)
      yil.append(el("option", { value:y, metin:y, selected:secim[hedef].yil === y }));
    return el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:etiket }),
      el("div.satir", { stil:{ gap:"4px" } }, ay, yil));
  };

  if (secim.rapor === "aylik") satirEl.append(donemSec("Ay", "donem"));
  else { satirEl.append(donemSec("Başlangıç", "bas"), donemSec("Bitiş", "son")); }

  if (secim.rapor === "serbest") {
    const kr = el("select", { onchange:e => { secim.kirilim = e.target.value; yenile(); } });
    for (const [v, a] of [["enerji_turu","Enerji türü"], ["varlik","Varlık"],
                          ["nokta","Ölçüm noktası"]])
      kr.append(el("option", { value:v, metin:a, selected:secim.kirilim === v }));
    satirEl.append(el("div.alan", { stil:{ margin:"0" } },
      el("label", { metin:"Kırılım" }), kr));
    const br = el("select", { onchange:e => { secim.birim = e.target.value; yenile(); } });
    for (const b of ["kWh","GJ","TEP"])
      br.append(el("option", { value:b, metin:b, selected:secim.birim === b }));
    satirEl.append(el("div.alan", { stil:{ margin:"0" } },
      el("label", { metin:"Birim" }), br));
  }

  satirEl.append(el("button.dugme.ana", { metin:"Yazdır", onclick:() => window.print() }));
  kart.append(satirEl);
  kart.append(el("p.mini.sessiz", { stil:{ margin:"8px 0 0" },
    metin:RAPORLAR.find(r => r.kod === secim.rapor)?.aciklama || "" }));
  k.append(kart);
}

/* ------------------------------------------------- ortak rapor parçaları */
function raporBasligi(k, ad, altBaslik) {
  k.append(el("div", { stil:{ borderBottom:"2px solid var(--taban)", paddingBottom:"10px",
      marginBottom:"14px" } },
    el("h2", { stil:{ margin:"0" }, metin:ad }),
    el("div.mini.sessiz", { metin:
      `${V.durum.ayarlar?.fabrika_adi || "Fabrika"} · ${altBaslik} · ` +
      `rapor tarihi ${tarihKisa(bugunISO())}` })));
}

/** Her rapor bunu taşımak ZORUNDADIR (9.14, İ-4) */
function kaliteNotu(k, donemler) {
  const kk = H.veriKalitesi(donemler);
  const kod = new Set(donemler.map(d => `${d.yil}-${String(d.ay).padStart(2, "0")}`));
  const eksik = katman.eksikler.filter(e => kod.has(e.donem));
  const bosluk = katman.bosluklar.filter(e => kod.has(e.donem));

  const parcalar = [`${say(kk.toplam, 0)} ham değer`];
  if (kk.tahmin) parcalar.push(`${kk.tahmin} TAHMİN`);
  if (kk.duzeltildi) parcalar.push(`${kk.duzeltildi} düzeltildi`);

  k.append(uyari(kk.tahmin || eksik.length ? "dikkat" : "bilgi",
    el("b", { metin:"Veri kalitesi: " }),
    parcalar.join(" · ") + ". " +
    (kk.tahmin
      ? `Bu raporda ${kk.tahmin} değer ölçülmemiş, tahmin edilmiştir (İ-4). `
      : "Raporda tahmin edilmiş değer yok. ") +
    (eksik.length ? `${eksik.length} hesap üretilemedi (eksik tanım). ` : "") +
    (bosluk.length ? `${bosluk.length} hesap ham veri boş olduğu için üretilmedi.` : "")));
}

function satirKutusu(kalemler) {
  const g = el("div", { stil:{ maxWidth:"560px" } });
  for (const [ad, deger, birim, tip, koken, d] of kalemler) {
    g.append(el("div.satir", { stil:{ justifyContent:"space-between", gap:"14px",
        padding:"5px 0", fontSize:"14px",
        borderTop: tip === "toplam" ? "1.5px solid var(--taban)" : "1px solid var(--kilavuz)",
        fontWeight: tip === "toplam" ? "600" : "400" } },
      el("span", {}, ad, koken ? kokenDugmesi(koken, d.yil, d.ay) : null),
      el("span.sayi", { metin: deger === null || deger === undefined
        ? "—" : `${say(deger, tip === "oran" ? 4 : 0)} ${birim || ""}` })));
  }
  return g;
}

/* ================================================ 1 · AYLIK ENERJİ RAPORU */
function aylikRapor(k) {
  const { yil, ay } = secim.donem;
  const d = [{ yil, ay }];
  const gy = donemKaydir(yil, ay, -12);
  raporBasligi(k, "Aylık Enerji Raporu", donemAd(yil, ay));

  const s = satir(yil, ay);
  if (!s) { k.append(bosDurum("Bu ay için veri yok",
    "Seçilen ayda hiç kayıt bulunmuyor. Yukarıdan başka bir ay seçin.")); return; }

  kaliteNotu(k, d);

  // --- tüketim ve maliyet
  const kart1 = el("div.kart", {}, el("h2", { metin:"Tüketim ve maliyet" }));
  const te = hucre("TOPLAM_ENERJI", yil, ay), teGY = hucre("TOPLAM_ENERJI", gy.yil, gy.ay);
  const tm = hucre("TOPLAM_MALIYET", yil, ay), tmGY = hucre("TOPLAM_MALIYET", gy.yil, gy.ay);
  const kalemler = [];
  const t = H.toplamEnerji(yil, ay, "kWh");
  for (const x of (t.kalemler || []))
    kalemler.push([x.ad, x.cevrilen, "kWh", "", null, { yil, ay }]);
  kalemler.push(["Toplam enerji", te, "kWh", "toplam", "TOPLAM_ENERJI", { yil, ay }]);
  kalemler.push(["Toplam enerji maliyeti (net)", tm, "TL", "toplam", "TOPLAM_MALIYET", { yil, ay }]);
  kart1.append(satirKutusu(kalemler));
  kart1.append(el("p.mini.sessiz", { stil:{ marginTop:"8px" }, metin:
    `Geçen yılın aynı ayına göre enerji ${teGY ? fark((te / teGY - 1) * 100) : "—"}, ` +
    `maliyet ${tmGY ? fark((tm / tmGY - 1) * 100) : "—"}.` }));
  k.append(kart1);

  // --- performans
  const anaKod = V.durum.ayarlar?.ana_enpi || V.durum.enpi_tanimlari[0]?.kod;
  const kart2 = el("div.kart", {}, el("h2", { metin:"Enerji performansı" }));
  const perf = [];
  for (const t2 of V.durum.enpi_tanimlari) {
    const v = hucre("ENPI_" + t2.kod, yil, ay);
    const vg = hucre("ENPI_" + t2.kod, gy.yil, gy.ay);
    perf.push({ ad:t2.ad + (t2.kod === anaKod ? " (ana gösterge)" : ""),
      deger:v, gecen:vg, birim:t2.birim, ondalik:t2.ondalik ?? 4, kod:"ENPI_" + t2.kod });
  }
  const norm = hucre("NORM_ENPI", yil, ay);
  kart2.append(tablo([
    { ad:"Gösterge", deger:r => el("span", {}, r.ad,
        kokenDugmesi(r.kod, yil, ay)) },
    { ad:"Bu ay", deger:r => Number.isFinite(r.deger) ? say(r.deger, r.ondalik) : "—" },
    { ad:"Geçen yıl aynı ay", deger:r => Number.isFinite(r.gecen) ? say(r.gecen, r.ondalik) : "—" },
    { ad:"Değişim", deger:r => (Number.isFinite(r.deger) && r.gecen)
        ? el("span", { stil:{ color:r.deger > r.gecen ? "var(--ciddi)" : "var(--iyi-ink)" },
            metin:fark((r.deger / r.gecen - 1) * 100) }) : "—" },
  ], perf));
  if (Number.isFinite(norm)) {
    const bz = H.etkinBazCizgi();
    kart2.append(el("p", { stil:{ marginTop:"10px" } },
      el("b", { metin:"Normalize EnPI: " }), say(norm, 3),
      kokenDugmesi("NORM_ENPI", yil, ay),
      el("span.mini.sessiz", { metin:
        ` — 1,00 = baz performans (${bz?.ad || "baz çizgi"}). ` +
        (norm > 1 ? `Üretimden arındırıldığında ${yuzde((norm - 1) * 100, 1)} daha fazla enerji harcandı.`
                  : `Üretimden arındırıldığında ${yuzde((1 - norm) * 100, 1)} tasarruf sağlandı.`) })));
  } else {
    kart2.append(el("p.mini.sessiz", { stil:{ marginTop:"10px" }, metin:
      "Normalize EnPI üretilemedi — etkin bir baz çizgi tanımlı değil (Ekran 8)." }));
  }
  k.append(kart2);

  hedefBolumu(k, d);
  aksiyonBolumu(k);
}

/* ================================== 2 · YÖNETİM GÖZDEN GEÇİRME RAPORU (9.3) */
function yonetimRaporu(k) {
  const d = donemAraligi(secim.bas.yil, secim.bas.ay, secim.son.yil, secim.son.ay);
  raporBasligi(k, "Yönetim Gözden Geçirme Raporu",
    `${donemAd(secim.bas.yil, secim.bas.ay)} – ${donemAd(secim.son.yil, secim.son.ay)}`);
  k.append(uyari("bilgi",
    el("b", { metin:"ISO 50001 madde 9.3 girdileri. " }),
    "Bu rapor, yönetimin gözden geçirmesinde sunulacak kanıtları tek yerde toplar: " +
    "dönem performansı, EnPI'ler ve baz çizgiye göre durum, önemli enerji kullanımları, " +
    "hedeflerin ve aksiyonların durumu, iyileştirme fırsatları."));
  kaliteNotu(k, d);

  // --- 1 dönem performansı
  const kart1 = el("div.kart", {}, el("h2", { metin:"1 · Dönem performans özeti" }));
  const topla = kod => d.reduce((t, x) => { const v = hucre(kod, x.yil, x.ay);
    return Number.isFinite(v) ? t + v : t; }, 0);
  const enerji = topla("TOPLAM_ENERJI"), maliyet = topla("TOPLAM_MALIYET");
  const uretim = H.donemToplami("TOPLAM_URETIM", d);
  kart1.append(satirKutusu([
    ["Toplam enerji", enerji, "kWh", "toplam", null, d[0]],
    ["Toplam enerji maliyeti (net)", maliyet, "TL", "toplam", null, d[0]],
    ["Toplam üretim", uretim, "kg", "", null, d[0]],
    ["Dönem EnPI'si", (uretim ? enerji / uretim : null), "kWh/kg", "oran", null, d[0]],
  ]));
  kart1.append(el("p.mini.sessiz", { stil:{ marginTop:"8px" }, metin:
    `${d.length} ay · dönem EnPI'si, aylık EnPI'lerin ortalaması değil, ` +
    "dönem toplam enerjisinin dönem toplam üretimine bölümüdür." }));
  k.append(kart1);

  // --- 2 EnPI ve baz çizgi
  const kart2 = el("div.kart", {}, el("h2", { metin:"2 · EnPI'ler ve baz çizgiye göre durum" }));
  const bz = H.etkinBazCizgi();
  if (!bz) kart2.append(uyari("dikkat",
    el("b", { metin:"Etkin baz çizgi yok. " }),
    "ISO 50001 madde 6.5 enerji baz çizgisi kurulmasını zorunlu tutar. " +
    "Ekran 8'den bir referans dönem seçilerek kurulur."));
  else {
    let g = 0, b = 0, n = 0;
    for (const x of d) { const r = H.bazCizgiDegerlendir(bz, x.yil, x.ay);
      if (r) { g += r.gercek; b += r.beklenen; n++; } }
    kart2.append(satirKutusu([
      ["Beklenen enerji (baz çizgi)", b || null, "kWh", "", null, d[0]],
      ["Gerçekleşen enerji", g || null, "kWh", "", null, d[0]],
      ["Sapma", (n ? g - b : null), "kWh", "toplam", null, d[0]],
      ["Normalize EnPI", (b ? g / b : null), "", "oran", null, d[0]],
    ]));
    kart2.append(el("p.mini.sessiz", { metin:
      `Baz çizgi: ${bz.ad} · ${bz.model_tipi === "sabit" ? "sabit model"
        : `regresyon, R² = ${say(bz.r2 ?? 0, 2)}`} · ${n}/${d.length} ay değerlendirildi.` +
      (bz.model_tipi !== "sabit" && (bz.r2 ?? 1) < 0.5
        ? " ⚠ R² 0,50'nin altında: model tüketimin azını açıklıyor, sonuç işaret niteliğindedir (8.3)."
        : "") }));
  }
  const enpiSatir = V.durum.enpi_tanimlari.map(t2 => {
    let pay = 0, payda = 0, var2 = false;
    for (const x of d) { const r = H.enpi(t2.kod, x.yil, x.ay);
      if (Number.isFinite(r.pay) && Number.isFinite(r.payda)) {
        pay += r.pay; payda += r.payda; var2 = true; } }
    return { ad:t2.ad, deger:(var2 && payda) ? pay / payda : null,
             birim:t2.birim, ondalik:t2.ondalik ?? 4 };
  });
  kart2.append(tablo([
    { ad:"EnPI", anahtar:"ad" },
    { ad:"Dönem değeri", deger:r => Number.isFinite(r.deger)
        ? `${say(r.deger, r.ondalik)} ${r.birim || ""}` : "—" },
  ], enpiSatir));
  k.append(kart2);

  // --- 3 SEU
  const kart3 = el("div.kart", {}, el("h2", { metin:"3 · Önemli enerji kullanımları (SEU)" }),
    el("p.mini.sessiz", { metin:
      "Toplam enerjinin %80'ini oluşturan kalemler. Kümülatif yüzde tablo sütunundadır; " +
      "çift eksenli Pareto çizilmez (5.7.2)." }));
  const kalemler = [];
  for (const n2 of V.durum.olcum_noktalari) {
    if (!n2.aktif || n2.rol !== "satin_alinan" || !n2.toplama_dahil) continue;
    let t = 0, var2 = false;
    for (const x of d) {
      const r = H.noktaDeger(n2.kod, x.yil, x.ay);
      if (!Number.isFinite(r.deger)) continue;
      const c = cevirGuvenli(r.deger, n2, "kWh", x);   // çevrilemiyorsa sayılmaz (İ-3)
      if (c === null) continue;
      t += c; var2 = true;
    }
    if (var2 && t > 0) kalemler.push({ ad:n2.ad, deger:t });
  }
  if (kalemler.length) G.pareto(kart3, { kalemler, birim:"kWh" });
  else kart3.append(el("p.sessiz", { metin:"Kırılacak kalem yok." }));
  k.append(kart3);

  // --- 4 dönüşüm verimliliği
  const kart4 = el("div.kart", {}, el("h2", { metin:"4 · Dönüşüm verimliliği" }));
  const ver = H.donusumVarliklari().map(x => {
    const s = H.donusumVerimiAralik(x.varlik.kod, d);
    return { ad:x.varlik.ad, s };
  }).filter(r => r.s);
  if (ver.length) {
    kart4.append(tablo([
      { ad:"Ekipman", anahtar:"ad" },
      { ad:"Yakıt (kWh)", sayi:true, deger:r => r.s.yakit },
      { ad:"Faydalı (kWh)", sayi:true, deger:r => r.s.faydali },
      { ad:"Toplam verim", deger:r => r.s.toplamVerim === null ? "—"
          : el("span", { stil:{ color:r.s.imkansiz ? "var(--ciddi)" : "" } },
              yuzde(r.s.toplamVerim * 100, 1), r.s.imkansiz ? " ⚠" : "") },
    ], ver));
    if (ver.some(r => r.s.imkansiz))
      kart4.append(uyari("ciddi",
        el("b", { metin:"⚠ işaretli ekipmanlarda faydalı enerji yakıttan büyük. " }),
        "Verim %100'ü aşamaz; bu sayılar performans olarak okunamaz, veri sorununu " +
        "gösterir (K-25). Ayrıntı Ekran 9'dadır."));
  } else kart4.append(el("p.sessiz", { metin:"Dönem içinde çalışan dönüşüm ekipmanı yok." }));
  k.append(kart4);

  hedefBolumu(k, d);
  aksiyonBolumu(k);

  // --- 7 iyileştirme fırsatları
  const kart7 = el("div.kart", {}, el("h2", { metin:"7 · İyileştirme fırsatları" }));
  const firsatlar = [];
  const kap = H.elektrikKapsami(d[d.length - 1].yil, d[d.length - 1].ay);
  if (kap.oran !== null && kap.oran < 0.6)
    firsatlar.push(`Elektrikte ölçüm kapsamı %${say(kap.oran * 100, 1)}. ` +
      `${say(kap.olcumeyen, 0)} kWh'nin nereye gittiği bilinmiyor — alt sayaç yatırımı ` +
      "buradaki en yüksek getirili adımdır (6.7).");
  for (const a of H.atanmamisYakit(d))
    if (a.oran !== null && Math.abs(a.oran) > 0.05)
      firsatlar.push(`Satın alınan yakıtın %${say(Math.abs(a.oran) * 100, 1)}'i ` +
        "hiçbir dönüşüm ekipmanına atanmamış; ekipman verimleri bu yüzden güvenilmez (A-05).");
  for (const r of ver) {
    if (r.s.imkansiz || r.s.toplamVerim === null) continue;
    if (r.s.kayipKwh > 0 && r.s.toplamVerim < 0.6)
      firsatlar.push(`${r.ad} toplam verimi %${say(r.s.toplamVerim * 100, 1)}; ` +
        `dönemde ${say(r.s.kayipKwh, 0)} kWh kayıp. Yük dağıtımı ve bakım durumu incelenmeli.`);
  }
  if (!firsatlar.length)
    kart7.append(el("p.sessiz", { metin:
      "Program bu dönemde otomatik bir fırsat işareti üretmedi. Bu, fırsat yok demek değildir." }));
  else kart7.append(el("ul", {}, firsatlar.map(f => el("li", { metin:f }))));
  k.append(kart7);
}

/* ================================================== 3 · SERBEST RAPOR */
function serbestRapor(k) {
  const d = donemAraligi(secim.bas.yil, secim.bas.ay, secim.son.yil, secim.son.ay);
  raporBasligi(k, "Serbest Rapor",
    `${donemAd(secim.bas.yil, secim.bas.ay)} – ${donemAd(secim.son.yil, secim.son.ay)} · ` +
    `${secim.kirilim === "enerji_turu" ? "enerji türü" : secim.kirilim === "varlik" ? "varlık" : "ölçüm noktası"} kırılımı · ${secim.birim}`);
  kaliteNotu(k, d);

  const gruplar = new Map();
  for (const n of V.durum.olcum_noktalari) {
    if (!n.aktif || n.rol !== "satin_alinan") continue;
    let t = 0, var2 = false;
    for (const x of d) {
      const r = H.noktaDeger(n.kod, x.yil, x.ay);
      if (!Number.isFinite(r.deger)) continue;
      const c = cevirGuvenli(r.deger, n, secim.birim, x);
      if (c === null) continue;
      t += c; var2 = true;
    }
    if (!var2 || t <= 0) continue;
    const anahtar = secim.kirilim === "enerji_turu"
      ? (V.durum.enerji_turleri.find(e => e.kod === n.enerji_turu)?.ad || n.enerji_turu || "—")
      : secim.kirilim === "varlik" ? (varlik(n.varlik)?.ad || n.varlik) : n.ad;
    // Alt kırılımlar üst ölçümün tekrarıdır; yalnız toplama dahil olanlar sayılır (6.7)
    if (secim.kirilim === "enerji_turu" && !n.toplama_dahil) continue;
    gruplar.set(anahtar, (gruplar.get(anahtar) || 0) + t);
  }

  const kalemler = [...gruplar.entries()].map(([ad, deger]) => ({ ad, deger }))
    .sort((a, b) => b.deger - a.deger);
  const kart = el("div.kart", {}, el("h2", { metin:"Dönem toplamları" }));
  k.append(kart);
  if (!kalemler.length) {
    kart.append(el("p.sessiz", { metin:"Seçilen aralıkta gösterilecek kalem yok." }));
    return;
  }
  G.sutun(kart, { seriler:[{ ad:"Dönem toplamı", degerler:kalemler.map(x => x.deger) }],
                  etiketler:kalemler.map(x => x.ad), birim:secim.birim, boy:300 });
  const toplam = kalemler.reduce((t, x) => t + x.deger, 0);
  kart.append(tablo([
    { ad:"Kalem", anahtar:"ad" },
    { ad:secim.birim, sayi:true, ondalik:secim.birim === "kWh" ? 0 : 2, anahtar:"deger" },
    { ad:"Pay", deger:r => yuzde(r.deger / toplam * 100, 1) },
  ], [...kalemler, { ad:"TOPLAM", deger:toplam }]));

  if (secim.kirilim !== "enerji_turu")
    kart.append(el("p.mini.sessiz", { metin:
      "Varlık ve ölçüm noktası kırılımında alt sayaçlar da listelenir; bunlar üst " +
      "ölçümün içindedir, toplamı fabrika toplam enerjisi değildir (6.7)." }));

  // aylık seyir
  const kart2 = el("div.kart", {}, el("h2", { metin:"Aylık seyir" }));
  k.append(kart2);
  const ilk5 = kalemler.slice(0, 5).map(x => x.ad);
  const seriler = ilk5.map(ad => ({ ad, degerler:d.map(x => {
    let t = 0, var2 = false;
    for (const n of V.durum.olcum_noktalari) {
      if (!n.aktif || n.rol !== "satin_alinan") continue;
      if (secim.kirilim === "enerji_turu" && !n.toplama_dahil) continue;
      const anahtar = secim.kirilim === "enerji_turu"
        ? (V.durum.enerji_turleri.find(e => e.kod === n.enerji_turu)?.ad || n.enerji_turu || "—")
        : secim.kirilim === "varlik" ? (varlik(n.varlik)?.ad || n.varlik) : n.ad;
      if (anahtar !== ad) continue;
      const r = H.noktaDeger(n.kod, x.yil, x.ay);
      if (!Number.isFinite(r.deger)) continue;
      const c = cevirGuvenli(r.deger, n, secim.birim, x);
      if (c === null) continue;
      t += c; var2 = true;
    }
    return var2 ? t : null;
  }) }));
  G.cizgi(kart2, { seriler, etiketler:d.map(x => donemKisa(x.yil, x.ay)),
                   birim:secim.birim, ondalik:secim.birim === "kWh" ? 0 : 2, boy:300 });
  if (kalemler.length > 5)
    kart2.append(el("p.mini.sessiz", { metin:
      `En büyük 5 kalem çizildi; kalan ${kalemler.length - 5} kalem yukarıdaki tablodadır.` }));
}

/** Çevrilemiyorsa null döner — sistem katsayı UYDURMAZ (İ-3) */
function cevirGuvenli(v, n, birim, donem) {
  const c = cevir(v, n.birim, birim, n.enerji_turu, donem.yil, donem.ay);
  return (c.eksik || c.deger === null) ? null : c.deger;
}

/* ------------------------------------------- ortak: hedefler ve aksiyonlar */
function hedefBolumu(k, d) {
  const kart = el("div.kart", {}, el("h2", { metin:"Hedeflerin durumu" }));
  k.append(kart);
  if (!V.durum.hedefler.length) {
    kart.append(el("p.sessiz", { metin:
      "Tanımlı hedef yok. ISO 50001 madde 6.2 enerji hedefleri belirlenmesini " +
      "zorunlu tutar; Ekran 12'den tanımlanır." }));
    return;
  }
  const satirlar = V.durum.hedefler.map(h => {
    const s = H.hedefDurumu(h);
    const tur = H.HEDEF_TURLERI[h.tur];
    return { ad:h.ad, tur:tur?.ad || h.tur, hedef:h.deger, gercek:s.gercek,
             tuttu:s.tuttu, sorumlu:h.sorumlu,
             ondalik:h.tur === "enpi" ? 4 : h.tur === "tasarruf" ? 1 : 0,
             birim:tur?.birim || "",
             donem:`${donemAd(h.bas.yil, h.bas.ay)} – ${donemAd(h.son.yil, h.son.ay)}` };
  });
  kart.append(tablo([
    { ad:"", deger:r => r.gercek === null ? el("span.sessiz", { metin:"–" })
        : el("span", { stil:{ color:r.tuttu ? "var(--iyi-ink)" : "var(--ciddi)" },
            metin:r.tuttu ? "✓" : "✕" }) },
    { ad:"Hedef", deger:r => el("span", {}, el("b", { metin:r.ad }),
        el("div.mini.sessiz", { metin:`${r.tur} · ${r.donem}` })) },
    { ad:"Hedef değer", deger:r => `${say(r.hedef, r.ondalik)} ${r.birim}` },
    { ad:"Gerçekleşen", deger:r => r.gercek === null ? "—"
        : `${say(r.gercek, r.ondalik)} ${r.birim}` },
    { ad:"Sorumlu", deger:r => r.sorumlu || "—" },
  ], satirlar));
}

function aksiyonBolumu(k) {
  const bg = bugunISO();
  const o = H.aksiyonOzeti(bg);
  const kart = el("div.kart", {}, el("h2", { metin:"Aksiyonlar" }));
  k.append(kart);
  if (!o.toplam) {
    kart.append(el("p.sessiz", { metin:
      "Tanımlı aksiyon yok. Tespitlerin sahibi ve termini olmadan kapanması izlenemez " +
      "(ISO 50001 md. 6.2.2)." }));
    return;
  }
  kart.append(el("p", { metin:
    `${o.acik} açık · ${o.geciken} gecikmiş · ${o.kapanan} kapanmış aksiyon. ` +
    `Beklenen tasarruf ${say(o.beklenenTL, 0)} TL, gerçekleşen ${say(o.gerceklesenTL, 0)} TL.` }));
  const acikListe = V.durum.aksiyonlar.filter(a => H.AKSIYON_DURUMLARI[a.durum]?.acikMi);
  if (acikListe.length) kart.append(tablo([
    { ad:"", deger:a => el("span", { stil:{ color:H.aksiyonGecikti(a, bg) ? "var(--ciddi)" : "" },
        metin:H.AKSIYON_DURUMLARI[a.durum]?.ikon || "○" }) },
    { ad:"Aksiyon", deger:a => el("span", {}, el("b", { metin:a.baslik }),
        a.baglam?.kaynak ? el("div.mini.sessiz", { metin:a.baglam.kaynak }) : null) },
    { ad:"Sorumlu", deger:a => a.sorumlu || "—" },
    { ad:"Termin", deger:a => el("span", {}, tarihKisa(a.termin),
        H.aksiyonGecikti(a, bg) ? el("span.rozet.dikkat",
          { stil:{ marginLeft:"6px" }, metin:"GECİKTİ" }) : null) },
    { ad:"Durum", deger:a => H.AKSIYON_DURUMLARI[a.durum]?.ad || a.durum },
  ], acikListe));
}
