/* ekranlar/ges.js — Ekran 11: GES (El Kitabı 9.12)
   "Santraller ne üretti, ne kazandırdı?"
   KRİTİK KURAL (K-03): GES üretimi fabrikanın kWh dengesine GİRMEZ;
   yalnızca mali dengeye mahsup olarak girer. Bu ekran fabrika EnPI'sini
   etkilemez. */

import { el, $, bosalt, say, kisa, yuzde, uyari, bosDurum, tablo,
         donemAd, donemAraligi, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import * as H from "../hesap.js";
import * as G from "../grafik.js";

let secilenYil = undefined;   // undefined = henüz seçilmedi · null = bütün yıllar

export function ekranGes(k) {
  const ar = V.veriAraligi();
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"GES" }),
    el("p", { metin:"Güneş santralleri ayrı tesistir: ürettiği elektrik fabrikada tüketilmez, şebekeye basılır ve faturada mahsup edilir." })));

  if (!ar) return k.append(bosDurum("Henüz veri yok",
    "Önce Veri ekranının Aktar sekmesinden verinizi alın.",
    el("button.dugme.ana", { metin:"Veri ekranına git", onclick:() => { location.hash = "e2"; } })));

  const tesisler = H.ayriTesisler();
  if (!tesisler.length) return k.append(bosDurum("Ayrı tesis tanımlı değil",
    "Bu ekran, rolü `ayrı tesis üretimi` olan ölçüm noktası bulunan varlıkları " +
    "kendiliğinden listeler. Tanımlar ekranından yeni bir santral eklendiğinde " +
    "burada hiçbir formül değişmeden görünür."));

  // İlk açılışta bütün yıllar değil, GES verisi olan SON yıl gösterilir:
  // 99 aylık bir sütun grafiği okunmaz. Kullanıcı isterse tümünü seçer.
  if (secilenYil === undefined) secilenYil = sonGesYili(tesisler, ar) ?? null;
  yilSecici(k, ar);
  const d = secilenYil === null
    ? donemAraligi(ar.ilk.yil, 1, ar.son.yil, 12)
    : donemAraligi(secilenYil, 1, secilenYil, 12);

  const satirlar = tesisler.map(t => ({ ...t, ad:t.varlik.ad,
    o:H.ayriTesisOzeti(t, d) }));
  const dolu = satirlar.filter(r => Number.isFinite(r.o.uretim));
  if (!dolu.length) return k.append(bosDurum("Seçilen dönemde GES verisi yok",
    "Bu dönemde hiçbir santral için üretim kaydı bulunmuyor. Yukarıdan başka bir yıl seçin."));

  kural(k);
  ozet(k, dolu, d);
  kartlar(k, satirlar, d);
  aylikUretim(k, tesisler, d);
  mevsimselProfil(k, tesisler, ar);
  maliKatki(k, tesisler, d);
  ozetTablosu(k, satirlar, d);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranGes(k); };

/** Üretim kaydı bulunan en son yıl */
function sonGesYili(tesisler, ar) {
  for (let y = ar.son.yil; y >= ar.ilk.yil; y--)
    for (const t of tesisler)
      if (Number.isFinite(H.donemToplami(t.uretim.kod, donemAraligi(y, 1, y, 12)))) return y;
  return null;
}

function yilSecici(k, ar) {
  const s = el("select", { onchange:e => {
    secilenYil = e.target.value === "" ? null : +e.target.value; yenile(); } });
  s.append(el("option", { value:"", metin:"Bütün yıllar", selected:secilenYil === null }));
  for (let y = ar.son.yil; y >= ar.ilk.yil; y--)
    s.append(el("option", { value:y, metin:y, selected:secilenYil === y }));
  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Dönem" }), s))));
}

function kural(k) {
  k.append(uyari("bilgi",
    el("b", { metin:"GES üretimi fabrikanın enerji dengesine ve EnPI'sine girmez. " }),
    "Santraller ayrı lokasyondadır ve ürettikleri elektrik fabrikada fiziksel olarak " +
    "hiç bulunmaz; şebekeye basılır. Fabrika elektriğini şebekeden alır, GES üretimi " +
    "ise TL cinsinden mahsup edilir (K-03, 7.1, 7.2). Bu ekrandaki kWh'ler " +
    "toplam enerjiye eklenmez."));
}

/* ------------------------------------------------------------- özet */
function ozet(k, dolu, d) {
  const uretim = dolu.reduce((t, r) => t + r.o.uretim, 0);
  const gelir  = dolu.reduce((t, r) => t + (r.o.gelir || 0), 0);
  const elkKalem = H.faturaKalemleri().find(kl => kl.enerjiTuru === "ELK");
  const elkFatura = elkKalem ? H.faturaOzeti(elkKalem, d).tutar : null;
  const sebeke = H.donemToplami("SEBEKE_ELK", d);

  const kutu = (ad, v, birim, alt) => el("div.kart", { stil:{ flex:"1 1 190px", margin:"0" } },
    el("div.mini.sessiz", { metin:ad }),
    el("div", { stil:{ fontSize:"21px", fontWeight:"600", margin:"4px 0 2px",
      fontVariantNumeric:"tabular-nums" } }, v,
      el("span", { stil:{ fontSize:"12px", fontWeight:"400", color:"var(--ink-mut)",
        marginLeft:"5px" }, metin:birim })),
    alt ? el("div.mini.sessiz", { metin:alt }) : null);

  k.append(el("div.satir", { stil:{ marginBottom:"14px" } },
    kutu("Toplam üretim", say(uretim, 0), "kWh",
      `${dolu.length} santral · ${secilenYil === null ? "bütün yıllar" : secilenYil}`),
    kutu("Mali katkı", say(gelir, 0), "TL", "mahsup + satış"),
    kutu("Ortalama birim değer", uretim ? say(gelir / uretim, 4) : "—", "TL/kWh",
      "mali katkı ÷ üretim"),
    kutu("Elektrik faturasını karşılama",
      elkFatura ? yuzde(gelir / elkFatura * 100, 1) : "—", "",
      elkFatura ? `brüt fatura ${kisa(elkFatura, 1)} TL` : "fatura verisi yok")));

  if (Number.isFinite(sebeke) && sebeke)
    k.append(el("p.mini.sessiz", { metin:
      `Karşılaştırma için: aynı dönemde şebekeden çekilen elektrik ${say(sebeke, 0)} kWh. ` +
      `GES üretimi bunun %${say(uretim / sebeke * 100, 1)}'i kadar — ama bu bir ` +
      "tüketim azalması değildir, ayrı bir gelirdir." }));
}

/* ----------------------------------------------------------- kartlar */
function kartlar(k, satirlar, d) {
  const g = el("div", { stil:{ display:"grid", gap:"12px",
    gridTemplateColumns:"repeat(auto-fill, minmax(300px, 1fr))", marginBottom:"14px" } });
  for (const r of satirlar) {
    const kart = el("div.kart", { stil:{ margin:"0" } });
    kart.append(el("h3", { stil:{ margin:"0" }, metin:r.ad }));
    if (!Number.isFinite(r.o.uretim)) {
      kart.append(el("p.sessiz.mini", { stil:{ marginTop:"8px" },
        metin:"Seçilen dönemde üretim kaydı yok." }));
      g.append(kart); continue;
    }
    kart.append(el("div.mini.sessiz", { metin:
      (r.o.ilk ? `İlk üretim kaydı: ${donemAd(r.o.ilk.yil, r.o.ilk.ay)}` : "") +
      (r.o.ay ? ` · ${r.o.ay} ay veri` : "") }));
    const kalem = (ad, v, birim, ondalik = 0) => el("div.satir",
      { stil:{ justifyContent:"space-between", gap:"10px", padding:"3px 0", fontSize:"13px" } },
      el("span.sessiz", { metin:ad }),
      el("span.sayi", { metin: v === null ? "—" : `${say(v, ondalik)} ${birim}` }));
    kart.append(el("div", { stil:{ marginTop:"8px",
      borderTop:"1px solid var(--kilavuz)", paddingTop:"6px" } },
      kalem("Üretim", r.o.uretim, "kWh"),
      kalem("Mali katkı", r.o.gelir, "TL"),
      kalem("Birim değer", r.o.birimDeger, "TL/kWh", 4),
      kalem("Aylık ortalama", r.o.ay ? r.o.uretim / r.o.ay : null, "kWh")));
    if (r.gelirler.length > 1)
      kart.append(el("p.mini.sessiz", { stil:{ marginTop:"6px" },
        metin:`${r.gelirler.length} gelir kalemi toplandı.` }));
    if (r.varlik.not) kart.append(el("p.mini.sessiz", { stil:{ marginTop:"6px" }, metin:r.varlik.not }));
    g.append(kart);
  }
  k.append(g);
}

/* --------------------------------------------------- G1 aylık üretim */
function aylikUretim(k, tesisler, d) {
  const seriler = tesisler.map(t => ({ ad:t.varlik.ad,
    degerler:d.map(x => { const r = H.noktaDeger(t.uretim.kod, x.yil, x.ay);
      return Number.isFinite(r.deger) ? r.deger : null; }) }))
    .filter(s => s.degerler.some(v => v));
  if (!seriler.length) return;
  const et = secilenYil === null ? d.map(x => `${AYLAR[x.ay - 1].slice(0, 3)} ${String(x.yil).slice(2)}`)
                                 : d.map(x => AYLAR[x.ay - 1].slice(0, 3));
  const kart = el("div.kart", {}, el("h2", { metin:"Aylık üretim" }),
    el("p.mini.sessiz", { metin:"Boş ay, o santralin o dönemde henüz devrede olmadığı anlamına gelir." }));
  k.append(kart);
  G.sutun(kart, { seriler, etiketler:et, birim:"kWh", yigili:true, boy:300 });
}

/* ----------------------------------------- G2 mevsimsel profil (ısı haritası) */
function mevsimselProfil(k, tesisler, ar) {
  const yillar = [];
  for (let y = ar.ilk.yil; y <= ar.son.yil; y++) yillar.push(y);
  const deg = yillar.map(y => AYLAR.map((_, i) => {
    let t = null;
    for (const ts of tesisler) {
      const r = H.noktaDeger(ts.uretim.kod, y, i + 1);
      if (Number.isFinite(r.deger)) t = (t || 0) + r.deger;
    }
    return t;
  }));
  if (!deg.flat().some(v => v !== null)) return;
  const dolu = yillar.map((y, i) => [y, deg[i]]).filter(([, r]) => r.some(v => v !== null));
  const kart = el("div.kart", {}, el("h2", { metin:"Mevsimsel profil — bütün santraller" }),
    el("p.mini.sessiz", { metin:
      "Yaz–kış farkı güneş enerjisinin doğasıdır; aynı ayın yıldan yıla belirgin " +
      "düşmesi ise bozunma (degradation) belirtisi olabilir. Işınım verisiyle " +
      "beklenen üretim karşılaştırması ileride eklenecektir (9.12)." }));
  k.append(kart);
  G.isiHaritasi(kart, { satirAd:dolu.map(([y]) => String(y)),
    sutunAd:AYLAR.map(a => a.slice(0, 3)), degerler:dolu.map(([, r]) => r), birim:"kWh" });
}

/* ------------------------------------------------- G3 mali katkı */
function maliKatki(k, tesisler, d) {
  const seriler = tesisler.map(t => ({ ad:t.varlik.ad,
    degerler:d.map(x => { let s = null;
      for (const g of t.gelirler) { const r = H.noktaDeger(g.kod, x.yil, x.ay);
        if (Number.isFinite(r.deger)) s = (s || 0) + r.deger; }
      return s; }) }))
    .filter(s => s.degerler.some(v => v));
  if (!seriler.length) return;
  const et = secilenYil === null ? d.map(x => `${AYLAR[x.ay - 1].slice(0, 3)} ${String(x.yil).slice(2)}`)
                                 : d.map(x => AYLAR[x.ay - 1].slice(0, 3));
  const kart = el("div.kart", {}, el("h2", { metin:"Mali katkı" }),
    el("p.mini.sessiz", { metin:
      "Mahsup ve satış tek kalemde girildiği için ayrı gösterilemiyor (A-11). " +
      "Ayrılması istenirse Tanımlar ekranından her santral için iki gelir noktası " +
      "tanımlanır; bu ekran ikisini de kendiliğinden gösterir." }));
  k.append(kart);
  G.sutun(kart, { seriler, etiketler:et, birim:"TL", yigili:true, boy:280 });
}

/* ------------------------------------------------- T1 santral özeti */
function ozetTablosu(k, satirlar, d) {
  const yillar = [...new Set(d.map(x => x.yil))];
  const kart = el("div.kart", {}, el("h2", { metin:"Santral özeti" }));
  kart.append(tablo([
    { ad:"Santral", anahtar:"ad" },
    { ad:"Üretim (kWh)", sayi:true, deger:r => r.o.uretim },
    { ad:"Mali katkı (TL)", sayi:true, deger:r => r.o.gelir },
    { ad:"Birim değer", deger:r => r.o.birimDeger === null ? "—"
        : say(r.o.birimDeger, 4) + " TL/kWh" },
    { ad:"Veri", deger:r => r.o.ay ? `${r.o.ay} ay` : "—" },
    { ad:"İlk kayıt", deger:r => r.o.ilk ? donemAd(r.o.ilk.yil, r.o.ilk.ay) : "—" },
  ], satirlar));

  if (yillar.length > 1) {
    kart.append(el("h3", { metin:"Yıldan yıla üretim", stil:{ marginTop:"20px" } }));
    const yr = yillar.map(y => {
      const dy = donemAraligi(y, 1, y, 12);
      const satir = { yil:y };
      let t = 0, varMi = false;
      for (const r of satirlar) {
        const v = H.donemToplami(r.uretim.kod, dy);
        satir[r.varlik.kod] = v;
        if (Number.isFinite(v)) { t += v; varMi = true; }
      }
      satir.toplam = varMi ? t : null;
      return satir;
    }).filter(s => s.toplam !== null);
    yr.forEach((s, i) => { const o = i ? yr[i - 1].toplam : null;
      s.degisim = o ? (s.toplam - o) / o : null; });
    kart.append(tablo([
      { ad:"Yıl", anahtar:"yil" },
      ...satirlar.map(r => ({ ad:r.varlik.ad, sayi:true, anahtar:r.varlik.kod })),
      { ad:"Toplam (kWh)", sayi:true, anahtar:"toplam" },
      { ad:"Değişim", deger:s => s.degisim === null ? "—"
          : el("span", { stil:{ color:s.degisim < 0 ? "var(--ciddi)" : "var(--iyi)" },
              metin:(s.degisim > 0 ? "+" : "−") + yuzde(Math.abs(s.degisim) * 100, 1) }) },
    ], yr));
    kart.append(el("p.mini.sessiz", { metin:
      "Eksik aylı yıllar tam yıllarla kıyaslanamaz — değişim sütununu okumadan önce " +
      "veri ay sayısını kontrol edin." }));
  }
  k.append(kart);
}
