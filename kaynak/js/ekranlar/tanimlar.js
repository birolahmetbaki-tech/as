/* ekranlar/tanimlar.js — Ekran 14: Tanımlar (El Kitabı 9.15)
   Altı sekme. Tanımlar SİLİNMEZ, pasife alınır (İ-5). */

import { el, $, bosalt, tablo, uyari, bildir, onayla, say, sayiOku, bosDurum } from "../ortak.js";
import { durum, degisti } from "../veri.js";
import { agac, varlik, nokta, ROLLER, VERI_TIPLERI, varlikNoktalari,
         ENERJI_BIRIMLERI, enerjiTuru } from "../model.js";
import { OZEL } from "../hesap.js";

let sekme = "agac", secili = null;

const SEKMELER = [
  ["agac",   "Varlık Ağacı"],
  ["nokta",  "Ölçüm Noktaları"],
  ["tur",    "Enerji Türleri"],
  ["kats",   "Dönüşüm Katsayıları"],
  ["enpi",   "EnPI Tanımları"],
  ["baz",    "Baz Çizgiler"],
];

export function ekranTanimlar(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Tanımlar" }),
    el("p", { metin:"Sistemin iskeleti. Tanımlar silinmez, pasife alınır — böylece geçmiş veriler her zaman anlamlı kalır." })));

  const s = el("div.sekmeler", {});
  for (const [kod, ad] of SEKMELER)
    s.append(el("button.sekme", { "aria-selected": sekme === kod ? "true" : "false",
      metin:ad, onclick:() => { sekme = kod; secili = null; yenile(); } }));
  k.append(s);

  const govde = el("div", { id:"tanim-govde" });
  k.append(govde);
  cizGovde(govde);
}

function yenile() {
  const k = bosalt($("#icerik"));
  ekranTanimlar(k);
}

function cizGovde(g) {
  bosalt(g);
  ({ agac:cizAgac, nokta:cizNoktalar, tur:cizTurler,
     kats:cizKatsayilar, enpi:cizEnpi, baz:cizBaz }[sekme])(g);
}

/* ============================================================ 1 · AĞAÇ */
function cizAgac(g) {
  g.append(uyari("bilgi",
    el("b", { metin:"Hiyerarşiyi değiştirmek hiçbir veriyi bozmaz (İ-7). " }),
    "Varlık ağacı ile veri seti birbirinden bağımsızdır; bir varlığı başka bir yere taşıdığınızda ölçüm noktaları ve bütün geçmiş değerler yerinde kalır."));

  const sol = el("div.kart", { stil:{ flex:"1 1 320px", minWidth:"300px" } },
    el("div.satir", { stil:{ justifyContent:"space-between", marginBottom:"10px" } },
      el("h2", { metin:`Varlık ağacı (${durum.varliklar.length})` }),
      el("button.dugme.kucuk.ana", { metin:"+ Varlık", onclick:() => varlikDuzenle(null) })),
    agacListesi(agac()));

  const sag = el("div.kart", { stil:{ flex:"1 1 320px", minWidth:"300px" } });
  varlikDetay(sag);

  g.append(el("div.satir", { stil:{ alignItems:"flex-start" } }, sol, sag));
}

function agacListesi(dugumler) {
  const ul = el("ul.agac");
  for (const d of dugumler) {
    const pasif = d.aktif === false || d.devreden_cikis;
    ul.append(el("li", {},
      el("div.dugum" + (secili === d.kod ? ".secili" : "") + (pasif ? ".pasif" : ""), {
        onclick:() => { secili = d.kod; cizGovde($("#tanim-govde")); } },
        el("span", { metin:d.ad }),
        el("span.tip", { metin:d.tip || "" }),
        d.devreden_cikis ? el("span.rozet.dikkat", { metin:"⚠ " + d.devreden_cikis }) : null),
      d.cocuklar.length ? agacListesi(d.cocuklar) : null));
  }
  return ul;
}

function varlikDetay(k) {
  if (!secili) { k.append(bosDurum("Varlık seçilmedi",
    "Soldaki ağaçtan bir varlık seçin; ayrıntıları ve ona bağlı ölçüm noktaları burada görünür.")); return; }
  const v = varlik(secili);
  if (!v) return;
  const nk = varlikNoktalari(v.kod);

  k.append(el("div.satir", { stil:{ justifyContent:"space-between" } },
    el("h2", { metin:v.ad }),
    el("button.dugme.kucuk", { metin:"Düzenle", onclick:() => varlikDuzenle(v.kod) })));

  const bilgi = [
    ["Kod", v.kod], ["Tip", v.tip || "—"],
    ["Üst varlık", v.ust ? (varlik(v.ust)?.ad || v.ust) : "— (kök)"],
    ["Devreye giriş", v.devreye_giris || "—"],
    ["Devreden çıkış", v.devreden_cikis || "—"],
    ["Durum", v.aktif === false ? "Pasif" : "Aktif"],
  ];
  const dl = el("table");
  for (const [a, b] of bilgi)
    dl.append(el("tr", {}, el("td.sessiz", { metin:a }), el("td", { metin:String(b) })));
  k.append(el("div.tablo-sar", { stil:{ maxHeight:"none", marginBottom:"12px" } }, dl));

  if (v.not) k.append(uyari("dikkat", v.not));

  k.append(el("h3", { metin:`Ölçüm noktaları (${nk.length})` }));
  if (!nk.length) k.append(el("p.sessiz.kucuk", { metin:"Bu varlığa bağlı ölçüm noktası yok." }));
  else k.append(tablo([
    { ad:"Ad", anahtar:"ad" },
    { ad:"Birim", anahtar:"birim" },
    { ad:"Rol", deger:n => ROLLER[n.rol]?.ad || n.rol },
    { ad:"Tip", deger:n => VERI_TIPLERI[n.veri_tipi] || n.veri_tipi },
    { ad:"Toplama", deger:n => n.toplama_dahil ? "✓" : "" },
  ], nk));
}

function varlikDuzenle(kod) {
  const v = kod ? { ...varlik(kod) } : { kod:"", ad:"", tip:"ekipman", ust:null, sira:999, aktif:true };
  const yeni = !kod;
  const f = el("div");
  const g = (etiket, alan, tip = "text", secenekler = null) => {
    const id = "f_" + alan;
    let giris;
    if (secenekler) {
      giris = el("select", { id });
      for (const [d, a] of secenekler)
        giris.append(el("option", { value:d ?? "", metin:a, selected: (v[alan] ?? "") === (d ?? "") }));
    } else giris = el("input", { id, type:tip, value: v[alan] ?? "" });
    f.append(el("div.alan", {}, el("label", { for:id, metin:etiket }), giris));
    return giris;
  };
  const gKod = g("Kod (benzersiz, değişmez)", "kod");
  if (!yeni) gKod.disabled = true;
  const gAd  = g("Ad", "ad");
  const gTip = g("Tip", "tip", "text", [["tesis","Tesis"],["grup","Grup"],["bolum","Bölüm"],
      ["istasyon","İstasyon"],["ekipman","Ekipman"],["hat","Hat"],["proses","Proses"],
      ["santral","Santral"],["giris_noktasi","Giriş noktası"]]);
  const gUst = g("Üst varlık", "ust", "text",
    [[null,"— (kök)"], ...durum.varliklar.filter(x => x.kod !== kod).map(x => [x.kod, x.ad])]);
  const gGir = g("Devreye giriş (YYYY-AA)", "devreye_giris");
  const gCik = g("Devreden çıkış (YYYY-AA)", "devreden_cikis");
  const gNot = g("Not", "not");

  onayla(yeni ? "Yeni varlık" : "Varlığı düzenle", f, "Kaydet").then(ok => {
    if (!ok) return;
    const k2 = gKod.value.trim().toUpperCase();
    if (!k2 || !gAd.value.trim()) return bildir("Kod ve ad zorunlu", "kritik");
    if (yeni && durum.varliklar.some(x => x.kod === k2)) return bildir("Bu kod zaten var", "kritik");
    const nesne = { kod:k2, ad:gAd.value.trim(), tip:gTip.value, ust:gUst.value || null,
      devreye_giris:gGir.value.trim() || null, devreden_cikis:gCik.value.trim() || null,
      not:gNot.value.trim(), aktif:v.aktif !== false, sira:v.sira ?? 999 };
    if (yeni) durum.varliklar.push(nesne);
    else Object.assign(varlik(kod), nesne);
    secili = k2; degisti("varlik"); yenile(); bildir("Kaydedildi");
  });
}

/* ==================================================== 2 · ÖLÇÜM NOKTALARI */
function cizNoktalar(g) {
  g.append(uyari("bilgi",
    el("b", { metin:"Yeni bir makine eklemek burada tek satır eklemektir. " }),
    "Excel'de bu, yeni sütun açıp bütün formülleri güncellemek demekti (S1)."));

  let sup = "";
  const ust = el("div.satir", { stil:{ marginBottom:"12px" } },
    el("input", { type:"text", placeholder:"Ara: ad, kod, varlık…", stil:{ minWidth:"260px" },
      oninput:e => { sup = e.target.value.toLowerCase(); ciz(); } }),
    el("span.bosluk", { stil:{ flex:"1" } }),
    el("button.dugme.kucuk.ana", { metin:"+ Ölçüm noktası", onclick:() => noktaDuzenle(null) }));
  g.append(ust);
  const sar = el("div"); g.append(sar);

  function ciz() {
    bosalt(sar);
    const l = durum.olcum_noktalari.filter(n => !sup ||
      (n.ad + n.kod + (varlik(n.varlik)?.ad || "")).toLowerCase().includes(sup));
    sar.append(el("p.kucuk.sessiz", { metin:`${l.length} / ${durum.olcum_noktalari.length} nokta` }));
    sar.append(tablo([
      { ad:"Kod", deger:n => el("code", { metin:n.kod }) },
      { ad:"Ad", anahtar:"ad" },
      { ad:"Varlık", deger:n => varlik(n.varlik)?.ad || n.varlik },
      { ad:"Birim", anahtar:"birim" },
      { ad:"Rol", deger:n => ROLLER[n.rol]?.ad || n.rol },
      { ad:"Tip", deger:n => VERI_TIPLERI[n.veri_tipi] || n.veri_tipi },
      { ad:"Toplama", deger:n => n.toplama_dahil ? "✓" : "" },
      { ad:"", deger:n => el("button.dugme.kucuk", { metin:"Düzenle",
          onclick:() => noktaDuzenle(n.kod) }) },
    ], l, { satirOzellik:n => ({ title:n.not || "", style:n.aktif === false ? "opacity:.5" : "" }) }));
  }
  ciz();
}

/** Ölçüm noktası formu — Veri ızgarası "yeni sütun" için ödünç alır (tek tanım yeri) */
export function noktaFormu(sonra = null) { noktaDuzenle(null, sonra); }

function noktaDuzenle(kod, sonra = null) {
  const n = kod ? { ...nokta(kod) } : { kod:"", ad:"", varlik:durum.varliklar[0]?.kod,
    enerji_turu:null, birim:"kWh", rol:"satin_alinan", toplama_dahil:false,
    veri_tipi:"olculen", formul:"", aktif:true, not:"" };
  const yeni = !kod;
  const f = el("div");
  const mk = (etiket, alan, secenekler = null, ipucu = null) => {
    const id = "n_" + alan; let giris;
    if (secenekler) {
      giris = el("select", { id });
      for (const [d, a] of secenekler)
        giris.append(el("option", { value:d ?? "", metin:a, selected:(n[alan] ?? "") === (d ?? "") }));
    } else giris = el("input", { id, type:"text", value:n[alan] ?? "" });
    f.append(el("div.alan", {}, el("label", { for:id, metin:etiket }), giris,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null));
    return giris;
  };
  const gKod = mk("Kod (benzersiz)", "kod"); if (!yeni) gKod.disabled = true;
  const gAd  = mk("Ad", "ad");
  const gVar = mk("Bağlı varlık", "varlik", durum.varliklar.map(v => [v.kod, v.ad]),
                  "Değiştirilebilir — geçmiş veri yerinde kalır (İ-7)");
  const gTur = mk("Enerji türü", "enerji_turu",
                  [[null,"— (enerji değil)"], ...durum.enerji_turleri.map(t => [t.kod, t.ad])]);
  const gBir = mk("Birim", "birim", [...ENERJI_BIRIMLERI, "m³","kg","TL","adet"].map(b => [b,b]));
  const gRol = mk("Rol", "rol", Object.entries(ROLLER).map(([k, r]) => [k, r.ad]));
  const gTip = mk("Veri tipi", "veri_tipi", Object.entries(VERI_TIPLERI));
  const gFor = mk("Formül (hesaplanan/dağıtılmış ise)", "formul", null,
                  "Örnek: KAKAO_YAG + KAKAO_TOZ  ·  CEKIRDEK_KG * 0.34  ·  BUH_KG * KATSAYI(BUH,kg,kWh)");
  const gDah = el("input", { type:"checkbox", id:"n_dahil" }); gDah.checked = !!n.toplama_dahil;
  f.append(el("div.alan", {}, el("label", { for:"n_dahil", metin:"Fabrika toplamına dahil" }), gDah,
    el("div.mini.sessiz", { metin:"Yalnız üst seviye giriş noktaları işaretlenir. Alt kırılımlar (GM-1 doğalgazı gibi) işaretlenmez — çift sayım olur (6.7)." })));
  const gFat = el("input", { id:"n_fatura_tuketim", type:"text",
    value:(n.fatura_tuketim || []).join(", ") });
  f.append(el("div.alan", {}, el("label", { for:"n_fatura_tuketim",
      metin:"Faturalandırdığı tüketim (yalnız maliyet rolünde)" }), gFat,
    el("div.mini.sessiz", { metin:"Virgülle ayrılmış ölçüm noktası kodları. " +
      "Ortalama birim fiyat ve fiyat/hacim ayrıştırması buradan hesaplanır (K-12, 8.7). " +
      "Boş bırakılırsa tutar toplanır ama birim fiyat üretilmez." })));
  const gNot = mk("Not", "not");

  onayla(yeni ? "Yeni ölçüm noktası" : "Ölçüm noktasını düzenle", f, "Kaydet").then(ok => {
    if (!ok) return;
    const k2 = gKod.value.trim().toUpperCase();
    if (!k2 || !gAd.value.trim()) return bildir("Kod ve ad zorunlu", "kritik");
    if (yeni && durum.olcum_noktalari.some(x => x.kod === k2)) return bildir("Bu kod zaten var", "kritik");
    const eski = kod ? nokta(kod) : null;
    const turDegisti = eski && (eski.enerji_turu !== (gTur.value || null) || eski.birim !== gBir.value);
    const uygula = () => {
      const nesne = { kod:k2, ad:gAd.value.trim(), varlik:gVar.value,
        enerji_turu:gTur.value || null, birim:gBir.value, rol:gRol.value,
        veri_tipi:gTip.value, formul:gFor.value.trim() || null,
        toplama_dahil:gDah.checked, aktif:eski ? eski.aktif !== false : true,
        fatura_tuketim:gFat.value.split(",").map(x => x.trim().toUpperCase()).filter(Boolean),
        excel_sutun:eski ? eski.excel_sutun ?? null : null,
        not:gNot.value.trim() };
      if (yeni) durum.olcum_noktalari.push(nesne); else Object.assign(eski, nesne);
      degisti("nokta");
      if (sonra) sonra(nesne); else yenile();
      bildir("Kaydedildi");
    };
    const veriVar = kod && durum.degerler.some(d => d.n === kod);
    if (turDegisti && veriVar)
      onayla("Dikkat — geçmiş verinin anlamı değişecek",
        "Bu noktaya girilmiş veriler var. Enerji türünü veya birimini değiştirmek geçmiş dönemlerin anlamını değiştirir (İ-5). Devam edilsin mi?",
        "Yine de değiştir", true).then(o => { if (o) uygula(); });
    else uygula();
  });
}

/* ========================================================= 3 · TÜRLER */
function cizTurler(g) {
  g.append(el("div.satir", { stil:{ justifyContent:"space-between", marginBottom:"10px" } },
    el("h2", { metin:`Enerji türleri (${durum.enerji_turleri.length})` }),
    el("button.dugme.kucuk.ana", { metin:"+ Enerji türü", onclick:() => turDuzenle(null) })));
  g.append(tablo([
    { ad:"Kod", deger:t => el("code", { metin:t.kod }) },
    { ad:"Ad", anahtar:"ad" },
    { ad:"Ana birim", anahtar:"ana_birim" },
    { ad:"Nokta", sayi:true, deger:t => durum.olcum_noktalari.filter(n => n.enerji_turu === t.kod).length },
    { ad:"", deger:t => el("button.dugme.kucuk", { metin:"Düzenle", onclick:() => turDuzenle(t.kod) }) },
  ], durum.enerji_turleri));
}

function turDuzenle(kod) {
  const t = kod ? { ...enerjiTuru(kod) } : { kod:"", ad:"", ana_birim:"kWh", aktif:true };
  const f = el("div");
  const gk = el("input", { type:"text", value:t.kod }); if (kod) gk.disabled = true;
  const ga = el("input", { type:"text", value:t.ad });
  const gb = el("select"); for (const b of [...ENERJI_BIRIMLERI, "m³","kg"])
    gb.append(el("option", { value:b, metin:b, selected:t.ana_birim === b }));
  f.append(el("div.alan", {}, el("label", { metin:"Kod" }), gk),
           el("div.alan", {}, el("label", { metin:"Ad" }), ga),
           el("div.alan", {}, el("label", { metin:"Ana birim" }), gb));
  onayla(kod ? "Enerji türünü düzenle" : "Yeni enerji türü", f, "Kaydet").then(ok => {
    if (!ok || !gk.value.trim() || !ga.value.trim()) return;
    const n = { kod:gk.value.trim().toUpperCase(), ad:ga.value.trim(), ana_birim:gb.value, aktif:true };
    if (kod) Object.assign(enerjiTuru(kod), n); else durum.enerji_turleri.push(n);
    degisti("tur"); yenile(); bildir("Kaydedildi");
  });
}

/* ==================================================== 4 · KATSAYILAR */
function cizKatsayilar(g) {
  g.append(uyari("bilgi",
    el("b", { metin:"Sistem katsayı varsaymaz (İ-3). " }),
    "Katsayı tanımlı değilse dönüştürülmüş değer üretilmez ve nedeni ekranda yazılır. Katsayılar tarihlidir: bir dönem için geçerlilik başlangıcı o dönemden küçük veya eşit olan EN YENİ katsayı kullanılır."));
  g.append(el("div.satir", { stil:{ justifyContent:"space-between", marginBottom:"10px" } },
    el("h2", { metin:`Dönüşüm katsayıları (${durum.donusum_katsayilari.length})` }),
    el("button.dugme.kucuk.ana", { metin:"+ Katsayı", onclick:() => katsDuzenle(null) })));
  g.append(tablo([
    { ad:"Enerji türü", deger:k => enerjiTuru(k.enerji_turu)?.ad || k.enerji_turu },
    { ad:"Dönüşüm", deger:k => `1 ${k.kaynak_birim} = ? ${k.hedef_birim}` },
    { ad:"Katsayı", sayi:true, ondalik:6, anahtar:"katsayi" },
    { ad:"Geçerli", anahtar:"gecerli_baslangic" },
    { ad:"Kaynak", anahtar:"kaynak" },
    { ad:"", deger:(k,i) => el("button.dugme.kucuk", { metin:"Düzenle",
        onclick:() => katsDuzenle(durum.donusum_katsayilari.indexOf(k)) }) },
  ], durum.donusum_katsayilari, { satirOzellik:k => ({ title:k.not || "" }) }));

  const eksik = durum.olcum_noktalari.filter(n =>
    n.enerji_turu && ["m³","kg"].includes(n.birim) && n.rol === "satin_alinan");
  const olmayan = eksik.filter(n => !durum.donusum_katsayilari.some(k =>
    k.enerji_turu === n.enerji_turu && k.kaynak_birim === n.birim));
  if (olmayan.length)
    g.append(uyari("dikkat", el("b", { metin:"Katsayısı tanımlı olmayan noktalar: " }),
      olmayan.map(n => `${n.ad} (${n.birim})`).join(", "),
      el("div.kucuk", { metin:"Bu noktalara sıfırdan farklı bir değer girilirse toplam enerji üretilemez (6.6)." })));
}

function katsDuzenle(i) {
  const k = i !== null ? { ...durum.donusum_katsayilari[i] }
    : { enerji_turu:durum.enerji_turleri[0]?.kod, kaynak_birim:"m³", hedef_birim:"kWh",
        katsayi:null, gecerli_baslangic:"2018-01", kaynak:"", not:"" };
  const f = el("div");
  const gt = el("select"); for (const t of durum.enerji_turleri)
    gt.append(el("option", { value:t.kod, metin:t.ad, selected:k.enerji_turu === t.kod }));
  const gk = el("input", { type:"text", value:k.kaynak_birim });
  const gh = el("input", { type:"text", value:k.hedef_birim });
  const gv = el("input", { type:"text", value:k.katsayi != null ? say(k.katsayi, 6) : "" });
  const gb = el("input", { type:"text", value:k.gecerli_baslangic || "" });
  const gs = el("input", { type:"text", value:k.kaynak || "" });
  const gn = el("input", { type:"text", value:k.not || "" });
  f.append(
    el("div.alan", {}, el("label", { metin:"Enerji türü" }), gt),
    el("div.satir", {}, el("div.alan", {}, el("label", { metin:"Kaynak birim" }), gk),
                        el("div.alan", {}, el("label", { metin:"Hedef birim" }), gh)),
    el("div.alan", {}, el("label", { metin:"Katsayı (1 kaynak = ? hedef)" }), gv),
    el("div.alan", {}, el("label", { metin:"Geçerlilik başlangıcı (YYYY-AA)" }), gb),
    el("div.alan", {}, el("label", { metin:"Kaynak" }), gs,
       el("div.mini.sessiz", { metin:"Katsayının nereden geldiği. Denetimde sorulur." })),
    el("div.alan", {}, el("label", { metin:"Not" }), gn));

  onayla(i !== null ? "Katsayıyı düzenle" : "Yeni katsayı", f, "Kaydet").then(ok => {
    if (!ok) return;
    const s = sayiOku(gv.value);
    if (s.hata) return bildir("Katsayı: " + s.hata, "kritik");
    if (s.deger === null) return bildir("Katsayı zorunlu", "kritik");
    const n = { enerji_turu:gt.value, kaynak_birim:gk.value.trim(), hedef_birim:gh.value.trim(),
      katsayi:s.deger, gecerli_baslangic:gb.value.trim() || null,
      kaynak:gs.value.trim(), not:gn.value.trim() };
    if (i !== null) durum.donusum_katsayilari[i] = n; else durum.donusum_katsayilari.push(n);
    degisti("katsayi"); yenile(); bildir("Kaydedildi");
  });
}

/* ========================================================== 5 · EnPI */
function cizEnpi(g) {
  g.append(uyari("bilgi",
    el("b", { metin:"Sistem gösterge dayatmaz (K-06). " }),
    "Pay ve paydayı siz seçersiniz; istediğiniz kadar EnPI tanımlayabilirsiniz. Ham EnPI üretim düştüğünde kendiliğinden kötüleşir — bu verimsizlik değildir; Faz 4'te yanına normalize EnPI gelecek."));
  g.append(el("div.satir", { stil:{ justifyContent:"space-between", marginBottom:"10px" } },
    el("h2", { metin:`EnPI tanımları (${durum.enpi_tanimlari.length})` }),
    el("button.dugme.kucuk.ana", { metin:"+ EnPI", onclick:() => enpiDuzenle(null) })));
  const ad = x => OZEL[x]?.ad || nokta(x)?.ad || x;
  g.append(tablo([
    { ad:"Ad", anahtar:"ad" },
    { ad:"Pay", deger:t => ad(t.pay) },
    { ad:"Payda", deger:t => ad(t.payda) },
    { ad:"Birim", anahtar:"birim" },
    { ad:"Ana", deger:t => t.ana ? "✓" : "" },
    { ad:"", deger:t => el("button.dugme.kucuk", { metin:"Düzenle", onclick:() => enpiDuzenle(t.kod) }) },
  ], durum.enpi_tanimlari));
}

function enpiDuzenle(kod) {
  const t = kod ? { ...durum.enpi_tanimlari.find(x => x.kod === kod) }
    : { kod:"", ad:"", pay:"@TOPLAM_ENERJI_KWH", payda:"", birim:"kWh/kg", ondalik:4, ana:false };
  const secenekler = [
    ...Object.entries(OZEL).map(([k, v]) => [k, "★ " + v.ad]),
    ...durum.olcum_noktalari.map(n => [n.kod, `${n.ad} (${n.birim})`]),
  ];
  const f = el("div");
  const mkSec = (etiket, deger) => { const s = el("select");
    for (const [d, a] of secenekler) s.append(el("option", { value:d, metin:a, selected:deger === d }));
    f.append(el("div.alan", {}, el("label", { metin:etiket }), s)); return s; };
  const gk = el("input", { type:"text", value:t.kod }); if (kod) gk.disabled = true;
  const ga = el("input", { type:"text", value:t.ad });
  f.append(el("div.alan", {}, el("label", { metin:"Kod" }), gk),
           el("div.alan", {}, el("label", { metin:"Ad" }), ga));
  const gp = mkSec("Pay (bölünen)", t.pay);
  const gq = mkSec("Payda (bölen)", t.payda);
  const gb = el("input", { type:"text", value:t.birim || "" });
  const gd = el("input", { type:"number", value:t.ondalik ?? 4, min:0, max:6 });
  const gn = el("input", { type:"checkbox" }); gn.checked = !!t.ana;
  f.append(el("div.satir", {}, el("div.alan", {}, el("label", { metin:"Birim" }), gb),
                               el("div.alan", {}, el("label", { metin:"Ondalık" }), gd)),
           el("div.alan", {}, el("label", { metin:"Ana gösterge" }), gn));

  onayla(kod ? "EnPI'yi düzenle" : "Yeni EnPI", f, "Kaydet").then(ok => {
    if (!ok || !gk.value.trim() || !ga.value.trim()) return;
    const n = { kod:gk.value.trim().toUpperCase(), ad:ga.value.trim(), pay:gp.value,
      payda:gq.value, birim:gb.value.trim(), ondalik:+gd.value, ana:gn.checked };
    if (n.ana) durum.enpi_tanimlari.forEach(x => { if (x.kod !== n.kod) x.ana = false; });
    if (kod) Object.assign(durum.enpi_tanimlari.find(x => x.kod === kod), n);
    else durum.enpi_tanimlari.push(n);
    degisti("enpi"); yenile(); bildir("Kaydedildi");
  });
}

/* ==================================================== 6 · BAZ ÇİZGİLER */
function cizBaz(g) {
  g.append(uyari("bilgi",
    el("b", { metin:"Baz çizgi Faz 4'te kurulacak (K-19). " }),
    "Burada birden çok baz çizgi tanımlayabilecek ve aralarında geçiş yapabileceksiniz: sabit (referans dönem ortalaması) ve regresyonlu (beklenen = a × üretim + b). Regresyon için en az 12 veri noktası gerekir; R² 0,50'nin altındaysa sistem açık uyarı gösterir."));
  if (!durum.baz_cizgiler.length)
    g.append(bosDurum("Henüz baz çizgi tanımlanmadı",
      "Baz çizgi, enerji performansındaki gerçek değişimi ölçmenin referansıdır. ISO 50001'in zorunlu parçasıdır (madde 6.5). Faz 4'te veri üzerinden kurulacak."));
  else g.append(tablo([
    { ad:"Ad", anahtar:"ad" }, { ad:"Referans dönem", anahtar:"donem" },
    { ad:"Model", anahtar:"model_tipi" },
    { ad:"a", sayi:true, ondalik:4, anahtar:"a" },
    { ad:"b", sayi:true, anahtar:"b" },
    { ad:"R²", sayi:true, ondalik:2, anahtar:"r2" },
  ], durum.baz_cizgiler));
}
