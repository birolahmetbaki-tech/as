/* ekranlar/denge.js — Ekran 6: Enerji Dengesi (El Kitabı 9.7)
   "Enerji nereye gidiyor?" — ve ölçülmeyen payı DÜRÜSTÇE göster (6.7, S2). */

import { el, $, bosalt, say, kisa, yuzde, uyari, bosDurum, tablo,
         donemAd, donemAraligi, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { varlik, nokta, agac, altAgac, varlikNoktalari } from "../model.js";
import * as H from "../hesap.js";
import { sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";

let ar2 = null;

export function ekranDenge(k) {
  const ar = V.veriAraligi();
  if (!ar) { k.append(el("div.sayfa-basi", {}, el("h1", { metin:"Enerji Dengesi" })));
    k.append(bosDurum("Henüz veri yok", "Önce Veri Aktarma ekranından verinizi alın.",
      el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));
    return; }
  if (!ar2) {
    const son = sonEnerjiDonemi() || ar.son;          // GES'e değil, enerji verisine göre
    ar2 = { bas:{ yil:son.yil, ay:1 }, son:{ yil:son.yil, ay:son.ay } };
  }

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Enerji Dengesi" }),
    el("p", { metin:"Satın alınan enerjinin tesise girişinden tüketildiği yere kadar izi — ve ölçülmeyen pay." })));

  donemSecici(k, ar);
  const b = hesapla();
  if (!b) {
    const se = sonEnerjiDonemi();
    k.append(bosDurum("Seçilen aralıkta enerji verisi yok",
      se ? `Bu dönemlerde şebeke elektriği ve doğalgaz kaydı bulunmuyor. Enerji verisi ${donemAd(se.yil, se.ay)} tarihine kadar var — yukarıdan başka bir aralık seçin.`
         : "Önce veri aktarın."));
    return;
  }

  ozet(k, b);
  sankeyCiz(k, b);
  kapsamAgaci(k, b);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranDenge(k); };

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
    el("div.satir", { stil:{ alignItems:"flex-end" } }, sec("Başlangıç","bas"), sec("Bitiş","son"))));
}

/* ------------------------------------------------------------ hesap */
function hesapla() {
  const d = donemAraligi(ar2.bas.yil, ar2.bas.ay, ar2.son.yil, ar2.son.ay);
  const T = kod => { let t = 0, v = false;
    for (const x of d) { const r = H.noktaDeger(kod, x.yil, x.ay);
      if (Number.isFinite(r.deger)) { t += r.deger; v = true; } }
    return v ? t : 0; };

  const sebeke = T("SEBEKE_ELK");
  const ist = { IST1:T("IST1_DG_KWH"), IST2:T("IST2_DG_KWH"), IST3:T("IST3_DG_KWH") };
  const dogalgaz = ist.IST1 + ist.IST2 + ist.IST3;
  if (!sebeke && !dogalgaz) return null;

  // Dönüşüm ekipmanları — hangi istasyondan beslendiği
  const EKIP = [
    ["TURBIN","IST3"], ["GM1","IST1"], ["GM2","IST1"], ["GM3","IST1"],
    ["KAZAN1","IST2"], ["KAZAN2","IST2"],
  ];
  let kojenElk = 0, buhar = 0, sicakSu = 0;
  const ekipman = [];
  for (const [kod, istKod] of EKIP) {
    const yakit = T(`${kod}_DG_KWH`);
    const elk = T(`${kod}_EL`), bh = T(`${kod}_BUH_KWH`), ss = T(`${kod}_SSU`);
    if (!yakit && !elk && !bh && !ss) continue;
    kojenElk += elk; buhar += bh; sicakSu += ss;
    ekipman.push({ kod, ad:varlik(kod)?.ad || kod, ist:istKod, yakit,
      elk, buhar:bh, sicakSu:ss, faydali:elk + bh + ss,
      verim:yakit ? (elk + bh + ss) / yakit : null });
  }
  const olculenYakit = ekipman.reduce((t, e) => t + e.yakit, 0);
  const donusumKaybi = Math.max(0, olculenYakit - (kojenElk + buhar + sicakSu));
  const olculmeyenYakit = Math.max(0, dogalgaz - olculenYakit);

  // Elektrik tüketicileri — alt sayaç tanımı hesap.js'den (İ-2)
  const tuketici = [];
  for (const n of H.elektrikAltSayaclari()) {
    const t = T(n.kod);
    if (t > 0) tuketici.push({ kod:n.kod, ad:n.ad, varlik:n.varlik, deger:t });
  }
  // Kapsamın paydası hesap.js'deki elektrikKapsami() ile AYNI: şebeke + kojen
  const elkToplam = sebeke + kojenElk;
  const olculenElk = tuketici.reduce((t, x) => t + x.deger, 0);
  const olculmeyenElk = elkToplam - olculenElk;

  return { d, sebeke, dogalgaz, ist, ekipman, kojenElk, buhar, sicakSu,
           donusumKaybi, olculenYakit, olculmeyenYakit,
           tuketici, elkToplam, olculenElk, olculmeyenElk,
           kapsam:elkToplam ? olculenElk / elkToplam : null,
           toplamEnerji:sebeke + dogalgaz };
}

/* ------------------------------------------------------------- özet */
function ozet(k, b) {
  const kutu = (ad, v, birim, alt) => el("div.kart", { stil:{ flex:"1 1 200px", margin:"0" } },
    el("div.mini.sessiz", { metin:ad }),
    el("div", { stil:{ fontSize:"21px", fontWeight:"600", margin:"4px 0 2px",
      fontVariantNumeric:"tabular-nums" } }, say(v, 0),
      el("span", { stil:{ fontSize:"12px", fontWeight:"400", color:"var(--ink-mut)",
        marginLeft:"5px" }, metin:birim })),
    alt ? el("div.mini.sessiz", { metin:alt }) : null);

  k.append(el("div.satir", { stil:{ marginBottom:"14px" } },
    kutu("Satın alınan enerji", b.toplamEnerji, "kWh",
      `${say(b.d.length)} ay · elektrik + doğalgaz`),
    kutu("Şebeke elektriği", b.sebeke, "kWh", yuzde(b.sebeke / b.toplamEnerji * 100, 1)),
    kutu("Doğalgaz", b.dogalgaz, "kWh", yuzde(b.dogalgaz / b.toplamEnerji * 100, 1)),
    kutu("Kojenerasyon elektriği", b.kojenElk, "kWh", "toplam enerjiye GİRMEZ")));

  if (b.kapsam !== null)
    k.append(uyari(b.kapsam < 0.5 ? "dikkat" : "iyi",
      el("b", { metin:`Elektrikte ölçüm kapsamı: ${yuzde(b.kapsam * 100, 1)}. ` }),
      `${say(b.olculmeyenElk, 0)} kWh (${yuzde((1 - b.kapsam) * 100, 1)}) nereye gittiğini bilmiyorsunuz. ` +
      "Bu, alt sayaç yatırımının nereye yapılacağını söyleyen sayıdır."));

  k.append(uyari("bilgi",
    el("b", { metin:"Kojenerasyon elektriği ve buhar toplam enerjiye eklenmez. " }),
    "Onları üreten doğalgaz zaten sayılmıştır; eklenirse çift sayım olur (7.1). " +
    "GES üretimi de girmez — fabrikada fiziksel olarak hiç bulunmamıştır (K-03)."));
}

/* ----------------------------------------------------------- Sankey */
function sankeyCiz(k, b) {
  const dugumler = [
    { kod:"SEBEKE",   ad:"Şebeke Elektriği", katman:0, renk:"var(--s1)" },
    { kod:"DOGALGAZ", ad:"Doğalgaz",         katman:0, renk:"var(--s2)" },
  ];
  const akislar = [];

  for (const [kod, ad] of [["IST1","İstasyon 1"],["IST2","İstasyon 2"],["IST3","İstasyon 3"]]) {
    if (!b.ist[kod]) continue;
    dugumler.push({ kod, ad, katman:1, renk:"var(--s2)" });
    akislar.push({ kaynak:"DOGALGAZ", hedef:kod, deger:b.ist[kod], slot:1 });
  }
  if (b.olculmeyenYakit > 0) {
    dugumler.push({ kod:"DG_OLCULMEYEN", ad:"Ölçülmeyen gaz", katman:2, renk:"var(--ink-mut)" });
    // istasyon altında ölçülmeyen: en büyük istasyondan akıt
    const enb = Object.entries(b.ist).sort((a, c) => c[1] - a[1])[0];
    if (enb && enb[1]) akislar.push({ kaynak:enb[0], hedef:"DG_OLCULMEYEN",
      deger:b.olculmeyenYakit, slot:7 });
  }

  const cikti = [["KOJEN","Kojen Elektriği", b.kojenElk, "var(--s1)", 0],
                 ["BUHAR","Buhar",           b.buhar,    "var(--s3)", 2],
                 ["SSU","Sıcak Su",          b.sicakSu,  "var(--s4)", 3],
                 ["KAYIP","Dönüşüm Kaybı",   b.donusumKaybi, "var(--ink-mut)", 7]];
  for (const [kod, ad, deger, renk, slot] of cikti) {
    if (deger <= 0) continue;
    dugumler.push({ kod, ad, katman:2, renk });
    // ekipmanların bağlı olduğu istasyonlardan payla
    const toplamYakit = b.ekipman.reduce((t, e) => t + e.yakit, 0) || 1;
    for (const istKod of ["IST1","IST2","IST3"]) {
      const pay = b.ekipman.filter(e => e.ist === istKod).reduce((t, e) => t + e.yakit, 0);
      if (pay > 0 && b.ist[istKod])
        akislar.push({ kaynak:istKod, hedef:kod, deger:deger * pay / toplamYakit, slot });
    }
  }

  dugumler.push({ kod:"ELK", ad:"Elektrik", katman:3, renk:"var(--s1)" });
  if (b.sebeke) akislar.push({ kaynak:"SEBEKE", hedef:"ELK", deger:b.sebeke, slot:0 });
  if (b.kojenElk) akislar.push({ kaynak:"KOJEN", hedef:"ELK", deger:b.kojenElk, slot:0 });

  // Tüketiciler: üst varlığa göre grupla, en fazla 6 + Diğer (≤8 renk kuralı)
  const grup = new Map();
  for (const t of b.tuketici) {
    const v = varlik(t.varlik);
    const ust = v?.ust ? (varlik(v.ust)?.ad || v.ad) : (v?.ad || t.ad);
    grup.set(ust, (grup.get(ust) || 0) + t.deger);
  }
  const sirali = [...grup.entries()].sort((a, c) => c[1] - a[1]);
  const ilk = sirali.slice(0, 5), kalan = sirali.slice(5);
  ilk.forEach(([ad, deger], i) => {
    const kod = "T" + i;
    dugumler.push({ kod, ad, katman:4, renk:G.renk(i + 2) });
    akislar.push({ kaynak:"ELK", hedef:kod, deger, slot:i + 2 });
  });
  if (kalan.length) {
    const t = kalan.reduce((s2, [, v]) => s2 + v, 0);
    dugumler.push({ kod:"TDIGER", ad:"Diğer", katman:4, renk:"var(--s6)" });
    akislar.push({ kaynak:"ELK", hedef:"TDIGER", deger:t, slot:5 });
  }
  if (b.olculmeyenElk > 0) {
    dugumler.push({ kod:"OLCULMEYEN", ad:"ÖLÇÜLMEYEN", katman:4, renk:"var(--ciddi)" });
    akislar.push({ kaynak:"ELK", hedef:"OLCULMEYEN", deger:b.olculmeyenElk, renk:"var(--ciddi)" });
  }

  const kart = el("div.kart", {}, el("h2", { metin:"Enerji akışı" }),
    el("p.mini.sessiz", { metin:
      "Kalınlık enerji miktarıyla orantılıdır. En kalın kolun 'ÖLÇÜLMEYEN' olması rahatsız edicidir " +
      "ama doğrudur — ve alt sayaç yatırımının nereye yapılacağını söyler." }));
  k.append(kart);
  G.sankey(kart, { dugumler, akislar, birim:"kWh", boy:400 });
}

/* ----------------------------------------------------- kapsam ağacı */
function kapsamAgaci(k, b) {
  const kart = el("div.kart", {}, el("h2", { metin:"Ölçüm kapsamı" }),
    el("p.mini.sessiz", { metin:
      "Satırların toplamı her zaman üst toplama eşittir; ölçülmeyen pay üzerine eklenmez (6.7)." }));

  const satirlar = [
    { ad:"Elektrik — toplam", deger:b.elkToplam, pay:1, tip:"ust" },
    ...b.tuketici.sort((a, c) => c.deger - a.deger).map(t =>
      ({ ad:"  " + t.ad, deger:t.deger, pay:b.elkToplam ? t.deger / b.elkToplam : null, tip:"alt" })),
    { ad:"  Ölçülmeyen / dağıtılmamış", deger:b.olculmeyenElk,
      pay:b.elkToplam ? b.olculmeyenElk / b.elkToplam : null, tip:"eksik" },
  ];
  kart.append(tablo([
    { ad:"Kalem", deger:r => el("span", { stil:r.tip === "ust" ? "font-weight:600"
        : r.tip === "eksik" ? "color:var(--ciddi);font-weight:600" : "" }, r.ad) },
    { ad:"kWh", sayi:true, anahtar:"deger" },
    { ad:"Pay", deger:r => r.pay === null ? "—"
        : el("div.satir", { stil:{ gap:"8px", alignItems:"center" } },
            G.oranCubugu(r.pay, { en:70, cizgiRenk:r.tip === "eksik" ? "var(--ciddi)" : "var(--s1)" }),
            el("span.sayi.mini", { metin:yuzde(r.pay * 100, 1) })) },
  ], satirlar));

  if (b.ekipman.length) {
    kart.append(el("h3", { metin:"Dönüşüm ekipmanları", stil:{ marginTop:"20px" } }));
    kart.append(el("p.mini.sessiz", { metin:
      "Bu ekipmanlar toplam enerjinin dışındadır; yakıtı faydalı enerjiye ne verimle " +
      "çevirdiklerini gösterir (8.6). Ayrıntı Faz 4'te Dönüşüm Verimliliği ekranında." }));
    kart.append(tablo([
      { ad:"Ekipman", anahtar:"ad" },
      { ad:"Yakıt (kWh)", sayi:true, anahtar:"yakit" },
      { ad:"Elektrik", sayi:true, anahtar:"elk" },
      { ad:"Buhar", sayi:true, anahtar:"buhar" },
      { ad:"Sıcak su", sayi:true, anahtar:"sicakSu" },
      { ad:"Toplam verim", deger:e => e.verim === null ? "—"
          : el("span", { stil:e.verim < 0.55 ? "color:var(--ciddi)" : "" },
              yuzde(e.verim * 100, 1)) },
    ], b.ekipman.filter(e => e.yakit > 0)));
  }
  k.append(kart);
}
