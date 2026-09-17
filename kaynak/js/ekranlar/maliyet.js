/* ekranlar/maliyet.js — Ekran 10: Maliyet (El Kitabı 9.11)
   "Para nereye gidiyor ve maliyet neden arttı?"
   Bu ekranın en değerli parçası fiyat/hacim ayrıştırmasıdır (8.7):
   maliyet artışının ne kadarı piyasadan (fiyat), ne kadarı bizden (hacim). */

import { el, $, bosalt, say, yuzde, uyari, bosDurum, tablo,
         donemAraligi, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import * as H from "../hesap.js";
import { sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";

let secilenYil = null;

export function ekranMaliyet(k) {
  const ar = V.veriAraligi();
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Maliyet" }),
    el("p", { metin:"Maliyet artışının ne kadarı fiyattan, ne kadarı tüketimden geliyor — enerji yönetiminin başarısı yalnızca ikincisiyle ölçülür." })));

  if (!ar) return k.append(bosDurum("Henüz veri yok",
    "Önce Veri Aktarma ekranından verinizi alın.",
    el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));

  const kalemler = H.faturaKalemleri();
  if (!kalemler.length) return k.append(bosDurum("Maliyet noktası tanımlı değil",
    "Bu ekran, rolü `maliyet` olan ölçüm noktalarını kendiliğinden bulur. " +
    "Tanımlar ekranından bir fatura noktası ekleyin ve faturalandırdığı tüketim " +
    "noktalarını yazın; birim fiyat ve ayrıştırma buradan hesaplanır (K-12)."));

  if (secilenYil === null) secilenYil = (sonEnerjiDonemi() || ar.son).yil;
  yilSecici(k, ar);

  const d  = donemAraligi(secilenYil, 1, secilenYil, 12);
  const dO = donemAraligi(secilenYil - 1, 1, secilenYil - 1, 12);
  const dokum = H.maliyetDokumu(d);
  if (!dokum.brut && !dokum.mahsup)
    return k.append(bosDurum(`${secilenYil} yılında maliyet verisi yok`,
      "Bu yılda hiçbir fatura kaydı bulunmuyor. Yukarıdan başka bir yıl seçin."));

  ozet(k, dokum, d);
  ayristirma(k, kalemler, dO, d);
  aylikMaliyet(k, kalemler, d);
  birimFiyatTrendi(k, kalemler, ar);
  gesKatkisi(k, dokum, d);
  dokumTablosu(k, dokum, kalemler, dO, d);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranMaliyet(k); };

function yilSecici(k, ar) {
  const s = el("select", { onchange:e => { secilenYil = +e.target.value; yenile(); } });
  for (let y = ar.son.yil; y >= ar.ilk.yil; y--)
    s.append(el("option", { value:y, metin:y, selected:secilenYil === y }));
  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Yıl" }), s),
      el("p.mini.sessiz", { stil:{ margin:"0 0 6px" },
        metin:`Ayrıştırma dönemi: ${secilenYil - 1} → ${secilenYil}` }))));
}

/* ------------------------------------------------------------- özet */
function ozet(k, dokum, d) {
  const kart = el("div.kart", {}, el("h2", { metin:`Maliyet özeti · ${secilenYil}` }));
  const satir = (ad, v, tip) => el("div.satir", { stil:{ justifyContent:"space-between",
      gap:"14px", padding:"5px 0", fontSize:"14px",
      borderTop: tip === "toplam" ? "1.5px solid var(--taban)" : "1px solid var(--kilavuz)",
      fontWeight: tip === "toplam" ? "600" : "400" } },
    el("span", { stil:{ color:tip === "eksi" ? "var(--s1)" : "" }, metin:ad }),
    el("span.sayi", { stil:{ color:tip === "eksi" ? "var(--s1)" : "" },
      metin:`${tip === "eksi" ? "−" : ""}${say(Math.abs(v), 0)} TL` }));

  const g = el("div", { stil:{ maxWidth:"520px" } });
  for (const kl of dokum.kalemler) {
    if (!Number.isFinite(kl.tutar)) continue;
    g.append(satir(kl.fatura.ad + " (brüt)", kl.tutar));
  }
  if (dokum.mahsup) {
    g.append(satir("GES mahsubu + satışı", dokum.mahsup, "eksi"));
    g.append(el("p.mini.sessiz", { stil:{ margin:"2px 0 0" },
      metin:"GES geliri elektrik faturasından düşülür; fabrikanın kWh dengesine girmez (K-03, K-13)." }));
  }
  g.append(satir("Toplam enerji maliyeti", dokum.net, "toplam"));
  kart.append(g);

  const te = d.reduce((t, x) => { const r = H.toplamEnerji(x.yil, x.ay, "kWh");
    return Number.isFinite(r.deger) ? t + r.deger : t; }, 0);
  if (te) kart.append(el("p.mini.sessiz", { stil:{ marginTop:"10px" },
    metin:`Toplam enerji ${say(te, 0)} kWh · ortalama ${say(dokum.net / te, 4)} TL/kWh ` +
          "(mahsup sonrası net maliyet ÷ satın alınan enerji)" }));
  k.append(kart);
}

/* --------------------------------------- fiyat / hacim ayrıştırması (8.7) */
function ayristirma(k, kalemler, dO, d) {
  const kart = el("div.kart", {}, el("h2", { metin:`Fiyat / hacim ayrıştırması · ${secilenYil - 1} → ${secilenYil}` }),
    el("p.mini.sessiz", { metin:
      "Ayrıştırma her faturanın kendi biriminde yapılır (elektrik kWh, doğalgaz m³); " +
      "çevrim yapılsa katsayı hatası etkilere karışırdı. " +
      "Fiyat etkisi piyasadır, hacim etkisi bizim kontrolümüzdedir." }));
  k.append(kart);

  let hicBiri = true;
  for (const kalem of kalemler) {
    const r = H.kalemFiyatHacim(kalem, dO, d);
    if (!r) {
      const o = H.faturaOzeti(kalem, d);
      if (Number.isFinite(o.tutar) && o.tutar)
        kart.append(uyari("bilgi", el("b", { metin:kalem.fatura.ad + ": " }),
          kalem.tuketimKodlari.length
            ? `${secilenYil - 1} veya ${secilenYil} için birim fiyat üretilemedi (tüketim ya da tutar eksik) — ayrıştırma yapılamaz.`
            : "faturalandırdığı tüketim noktası tanımlı değil. Tanımlar ekranından " +
              "`Faturalandırdığı tüketim` alanını doldurun; ayrıştırma ancak o zaman yapılabilir."));
      continue;
    }
    hicBiri = false;
    const alt = el("div", { stil:{ marginTop:"16px" } });
    alt.append(el("div.satir", { stil:{ justifyContent:"space-between", alignItems:"baseline" } },
      el("h3", { stil:{ margin:"0" }, metin:kalem.fatura.ad }),
      el("span.sayi", { stil:{ fontWeight:"600",
        color:r.toplam > 0 ? "var(--ciddi)" : "var(--iyi)" },
        metin:`maliyet farkı ${r.toplam > 0 ? "+" : "−"}${say(Math.abs(r.toplam), 0)} TL` })));
    alt.append(el("p.mini.sessiz", { metin:
      `Birim fiyat: ${say(r.onceki.birimFiyat, 4)} → ${say(r.simdiki.birimFiyat, 4)} TL/${r.simdiki.birim} ` +
      `(${r.fiyatDegisim > 0 ? "+" : "−"}${yuzde(Math.abs(r.fiyatDegisim) * 100, 1)}) · ` +
      `miktar: ${say(r.onceki.miktar, 0)} → ${say(r.simdiki.miktar, 0)} ${r.simdiki.birim}` +
      (r.hacimDegisim === null ? "" : ` (${r.hacimDegisim > 0 ? "+" : "−"}${yuzde(Math.abs(r.hacimDegisim) * 100, 1)})`) }));
    kart.append(alt);

    // Üç etkinin toplamı maliyet farkına EŞİTTİR; ayrı bir "toplam" sütunu
    // çizilmez, çünkü şelalenin son kümülatif noktası zaten odur.
    G.selale(alt, { kalemler:[
      { ad:"Fiyat etkisi (piyasa)", deger:r.fiyatEtkisi },
      { ad:"Hacim etkisi (bizde)",  deger:r.hacimEtkisi },
      { ad:"Bileşik etki",          deger:r.bilesikEtki },
    ], birim:"TL", boy:260 });
    alt.append(el("p.mini.sessiz", { metin:
      `Üç etkinin toplamı = ${r.toplam > 0 ? "+" : "−"}${say(Math.abs(r.toplam), 0)} TL, ` +
      "yani maliyet farkının tamamı. Bileşik etki, fiyat ve miktarın aynı yönde " +
      "değişmesinden doğan ve ikisine de tek başına yazılamayan artıktır." }));

    const yorum = r.hacimEtkisi < 0
      ? el("div", {}, el("b", { metin:"Hacim etkisi negatif: tüketim düştü. " }),
          `${say(Math.abs(r.hacimEtkisi), 0)} TL tasarruf sağlandı. Fatura yine de ` +
          `${r.toplam > 0 ? "arttı" : "düştü"} çünkü birim fiyat ` +
          `${yuzde(Math.abs(r.fiyatDegisim) * 100, 1)} ${r.fiyatDegisim > 0 ? "yükseldi" : "geriledi"} — ` +
          "bu, enerji yönetiminin değil piyasanın sonucudur.")
      : el("div", {}, el("b", { metin:"Hacim etkisi pozitif: tüketim arttı. " }),
          `${say(r.hacimEtkisi, 0)} TL'lik artış gerçek tüketim artışıdır ve enerji ` +
          "yönetiminin sorumluluğundadır. Nedenini Performans ve Dönüşüm Verimliliği ekranlarında arayın.");
    alt.append(uyari(r.hacimEtkisi < 0 ? "iyi" : "dikkat", yorum));
  }
  if (hicBiri) kart.append(el("p.sessiz", { metin:
    "Hiçbir kalem için ayrıştırma yapılamadı — iki dönemde de birim fiyat gerekiyor." }));
}

/* -------------------------------------------------- G1 aylık maliyet */
function aylikMaliyet(k, kalemler, d) {
  const seriler = kalemler.map(kl => ({ ad:kl.fatura.ad,
    degerler:d.map(x => { const r = H.noktaDeger(kl.fatura.kod, x.yil, x.ay);
      return Number.isFinite(r.deger) ? r.deger : null; }) }))
    .filter(s => s.degerler.some(v => v));
  const gelirler = H.gelirNoktalari();
  if (!seriler.length) return;
  const kart = el("div.kart", {}, el("h2", { metin:`Aylık maliyet · ${secilenYil}` }),
    el("p.mini.sessiz", { metin:"Brüt fatura tutarları — GES mahsubu düşülmemiştir (K-13)." }));
  k.append(kart);
  G.sutun(kart, { seriler, etiketler:d.map(x => AYLAR[x.ay - 1].slice(0, 3)),
                  birim:"TL", yigili:true, boy:300 });
  if (gelirler.length) {
    const net = d.map(x => { const r = H.toplamMaliyet(x.yil, x.ay);
      return Number.isFinite(r.deger) ? r.deger : null; });
    kart.append(el("p.mini.sessiz", { stil:{ marginTop:"8px" }, metin:
      `Mahsup sonrası net yıllık toplam: ${say(net.reduce((t, v) => t + (v || 0), 0), 0)} TL` }));
  }
}

/* ------------------------------------------- G2 ortalama birim fiyat trendi */
function birimFiyatTrendi(k, kalemler, ar) {
  const yillar = [];
  for (let y = ar.ilk.yil; y <= ar.son.yil; y++) yillar.push(y);
  const seriler = [], tabloSatir = [];
  for (const kalem of kalemler) {
    const deg = yillar.map(y => H.birimFiyatKwh(kalem, donemAraligi(y, 1, y, 12)));
    if (!deg.some(v => v !== null)) continue;
    seriler.push({ ad:kalem.fatura.ad, degerler:deg });
    const ilk = deg.find(v => v !== null), son = [...deg].reverse().find(v => v !== null);
    tabloSatir.push({ ad:kalem.fatura.ad, ilk, son, kat: ilk ? son / ilk : null,
      birim:kalem.tuketimBirim });
  }
  if (!seriler.length) return;
  const kart = el("div.kart", {}, el("h2", { metin:"Ortalama birim fiyat trendi" }),
    el("p.mini.sessiz", { metin:
      "Fiyatlar kıyaslanabilmesi için TL/kWh cinsine çevrilmiştir (doğalgaz m³ fiyatı " +
      "dönüşüm katsayısıyla bölünür). Maliyet grafiğiyle aynı grafikte gösterilmez — " +
      "iki farklı ölçeğin tek eksende hizalanması keyfî olurdu (5.7.2)." }));
  k.append(kart);
  G.cizgi(kart, { seriler, etiketler:yillar.map(String), birim:"TL/kWh", ondalik:4, boy:300 });
  kart.append(tablo([
    { ad:"Kalem", anahtar:"ad" },
    { ad:"İlk yıl (TL/kWh)", deger:r => r.ilk === null ? "—" : say(r.ilk, 4) },
    { ad:"Son yıl (TL/kWh)", deger:r => r.son === null ? "—" : say(r.son, 4) },
    { ad:"Kat", deger:r => r.kat === null ? "—" : say(r.kat, 1) + "×" },
  ], tabloSatir));
}

/* ----------------------------------------------- G4 GES mali katkısı */
function gesKatkisi(k, dokum, d) {
  const gelirler = H.gelirNoktalari();
  if (!gelirler.length || !dokum.mahsup) return;
  const deg = d.map(x => { const r = H.gesKatkisi(x.yil, x.ay);
    return Number.isFinite(r.deger) ? r.deger : null; });
  const kart = el("div.kart", {}, el("h2", { metin:`GES mali katkısı · ${secilenYil}` }));
  const elkKalem = H.faturaKalemleri().find(kl => kl.enerjiTuru === "ELK");
  const elk = elkKalem ? H.faturaOzeti(elkKalem, d).tutar : null;
  kart.append(el("p.mini.sessiz", { metin:
    `Yıl toplamı ${say(dokum.mahsup, 0)} TL` +
    (elk ? ` — brüt elektrik faturasının %${say(dokum.mahsup / elk * 100, 1)}'ini karşıladı.` : ".") +
    " Mahsup ve satış tek kalemde girildiği için ayrı gösterilemiyor (A-11)." }));
  k.append(kart);
  G.sutun(kart, { seriler:[{ ad:"Mahsup + satış", degerler:deg, renk:G.renk(2) }],
                  etiketler:d.map(x => AYLAR[x.ay - 1].slice(0, 3)), birim:"TL", boy:260 });
}

/* -------------------------------------------------- T1 maliyet dökümü */
function dokumTablosu(k, dokum, kalemler, dO, d) {
  const satirlar = dokum.kalemler.filter(kl => Number.isFinite(kl.tutar)).map(kl => {
    const o = H.faturaOzeti(kl, dO);
    return { ad:kl.fatura.ad, tutar:kl.tutar, pay:dokum.brut ? kl.tutar / dokum.brut : null,
             miktar:kl.miktar, birim:kl.birim, bf:kl.birimFiyat,
             onceki:o.tutar, degisim: (Number.isFinite(o.tutar) && o.tutar)
               ? (kl.tutar - o.tutar) / o.tutar : null };
  });
  const kart = el("div.kart", {}, el("h2", { metin:"Maliyet dökümü" }));
  kart.append(tablo([
    { ad:"Kalem", anahtar:"ad" },
    { ad:`${secilenYil} (TL)`, sayi:true, anahtar:"tutar" },
    { ad:"Pay", deger:r => r.pay === null ? "—"
        : el("div.satir", { stil:{ gap:"8px", alignItems:"center" } },
            G.oranCubugu(r.pay, { en:70 }), el("span.sayi.mini", { metin:yuzde(r.pay * 100, 1) })) },
    { ad:"Miktar", deger:r => r.miktar === null ? "—" : `${say(r.miktar, 0)} ${r.birim}` },
    { ad:"Birim fiyat", deger:r => r.bf === null ? "—" : `${say(r.bf, 4)} TL/${r.birim}` },
    { ad:`${secilenYil - 1} (TL)`, sayi:true, anahtar:"onceki" },
    { ad:"Değişim", deger:r => r.degisim === null ? "—"
        : el("span", { stil:{ color:r.degisim > 0 ? "var(--ciddi)" : "var(--iyi)" },
            metin:(r.degisim > 0 ? "+" : "−") + yuzde(Math.abs(r.degisim) * 100, 1) }) },
  ], satirlar));
  kart.append(el("p.mini.sessiz", { metin:
    "Tutarlar brüttür. GES mahsubu tek tek kalemlere değil, elektrik faturasının " +
    "tamamına uygulanır ve yalnız özet kısmında düşülür (7.2)." }));
  k.append(kart);
}
