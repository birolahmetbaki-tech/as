/* ekranlar/hedefler.js — Ekran 12: Hedefler ve Aksiyonlar (El Kitabı 9.13)
   Analizden EYLEME geçişin köprüsü.
   Tespit edilen her sapmanın bir SAHİBİ ve TERMİNİ olmalıdır (ISO 50001 md. 6.2). */

import { el, $, bosalt, say, yuzde, uyari, bildir, onayla, bosDurum, tablo,
         donemAd, donemKisa, bugun, bugunISO, tarihKisa, sayiOku, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { varlik } from "../model.js";
import * as H from "../hesap.js";
import { sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";

export function ekranHedefler(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Hedefler ve Aksiyonlar" }),
    el("p", { metin:"Hedefin ölçülebilir, sapmanın bir sahibi ve termini olduğu yer." })));

  hedefBolumu(k);
  aksiyonBolumu(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranHedefler(k); };

/* ==================================================== BÖLÜM 1 — HEDEFLER */
function hedefBolumu(k) {
  const kart = el("div.kart", {});
  kart.append(el("div.satir", { stil:{ justifyContent:"space-between", alignItems:"baseline" } },
    el("h2", { stil:{ margin:"0" }, metin:`Hedefler (${V.durum.hedefler.length})` }),
    el("button.dugme.kucuk.ana", { metin:"+ Hedef", onclick:() => hedefDuzenle(null) })));
  k.append(kart);

  if (!V.durum.hedefler.length) {
    kart.append(bosDurum("Henüz hedef yok",
      "Hedef, enerji yönetimini niyetten ölçülebilir bir taahhüde çeviren şeydir ve " +
      "ISO 50001'in zorunlu parçasıdır (md. 6.2). Dört türden birini seçin: EnPI, " +
      "tüketim, maliyet veya baz çizgiye göre tasarruf.",
      el("button.dugme.ana", { metin:"İlk hedefi kur", onclick:() => hedefDuzenle(null) })));
    return;
  }

  for (const h of V.durum.hedefler) hedefKarti(kart, h);
}

function hedefKarti(kap, h) {
  const tur = H.HEDEF_TURLERI[h.tur];
  const d = H.hedefDurumu(h);
  const kutu = el("div", { stil:{ marginTop:"18px", paddingTop:"14px",
    borderTop:"1px solid var(--kilavuz)" } });

  kutu.append(el("div.satir", { stil:{ justifyContent:"space-between", alignItems:"baseline" } },
    el("div", {}, el("h3", { stil:{ margin:"0" }, metin:h.ad }),
      el("div.mini.sessiz", { metin:
        `${tur?.ad || h.tur} · ${donemAd(h.bas.yil, h.bas.ay)} – ${donemAd(h.son.yil, h.son.ay)}` +
        (h.sorumlu ? ` · sorumlu: ${h.sorumlu}` : "") })),
    el("div.satir", { stil:{ gap:"6px" } },
      el("button.dugme.kucuk", { metin:"Düzenle", onclick:() => hedefDuzenle(h.kod) }),
      el("button.dugme.kucuk.tehlike", { metin:"Sil", onclick:async () => {
        if (!await onayla("Hedefi sil", `"${h.ad}" silinecek. Ham veri etkilenmez.`, "Sil", true)) return;
        V.durum.hedefler = V.durum.hedefler.filter(x => x.kod !== h.kod);
        V.degisti("hedef"); yenile(); } }))));

  if (h.tur === "tuketim")
    kutu.append(uyari("dikkat",
      el("b", { metin:"Bu bir mutlak tüketim hedefidir. " }),
      "Üretim düşerse bu hedef kendiliğinden tutar — performans iyileşmese bile. " +
      "Gerçek performans için EnPI veya tasarruf hedefi kullanın (K-21)."));

  if (d.hata || !Number.isFinite(d.gercek)) {
    kutu.append(el("p.sessiz.mini", { stil:{ marginTop:"8px" }, metin:
      d.hata || "Bu dönem için henüz ölçülebilir veri yok; hedef izlenemiyor." }));
    kap.append(kutu); return;
  }

  const ondalik = h.tur === "enpi" ? 4 : h.tur === "tasarruf" ? 1 : 0;
  G.olcer(kutu, { deger:d.gercek, hedef:h.deger, birim:tur?.birim || "",
                  ondalik, yon:d.yon });

  // "Gerçekleşme %94,6" gibi bir oran, aşılmış bir azaltma hedefini başarı gibi
  // okutur. Aşma ve altında kalma ayrı ayrı, kendi diliyle yazılır.
  const asmaYuzde = h.deger ? Math.abs(d.gercek - h.deger) / Math.abs(h.deger) * 100 : null;
  kutu.append(el("p.mini", { stil:{ color:d.tuttu ? "var(--iyi-ink)" : "var(--ciddi)" },
    metin: d.tuttu
      ? `Hedef tutuyor · ${say(d.kalan, ondalik)} ${tur?.birim || ""} pay var` +
        (asmaYuzde !== null ? ` (hedefin ${yuzde(asmaYuzde, 1)} ${d.yon === "azalt" ? "altında" : "üstünde"})` : "") + "."
      : d.yon === "azalt"
        ? `Hedef ${say(d.kalan, ondalik)} ${tur?.birim || ""} aşıldı` +
          (asmaYuzde !== null ? ` (%${say(asmaYuzde, 1)} fazla)` : "") + "."
        : `Hedefin ${say(d.kalan, ondalik)} ${tur?.birim || ""} altında kalındı` +
          (asmaYuzde !== null ? ` (%${say(asmaYuzde, 1)} eksik)` : "") + "." }));
  kutu.append(el("p.mini.sessiz", { metin:
    `${d.doluAy}/${d.donemler.length} ay verisi var. ` +
    (d.doluAy < d.donemler.length
      ? "Eksik aylar hesaba katılmadı; dönem tamamlanmadan sonuç kesin değildir."
      : "Dönem tamamlandı.") }));

  // G1 — hedef referans hattıyla gerçekleşme
  const seri = d.seri.filter(s => Number.isFinite(s.deger));
  if (seri.length > 1) {
    const aylikHedef = (h.tur === "tuketim" || h.tur === "maliyet")
      ? h.deger / d.donemler.length : h.deger;
    G.cizgi(kutu, {
      seriler:[{ ad:h.ad, degerler:d.seri.map(s => s.deger) }],
      etiketler:d.seri.map(s => donemKisa(s.yil, s.ay)),
      birim:tur?.birim || "", ondalik, boy:240,
      referans:{ deger:aylikHedef, ad:(h.tur === "tuketim" || h.tur === "maliyet")
        ? "aylık hedef payı" : "hedef" } });
    if (h.tur === "tuketim" || h.tur === "maliyet")
      kutu.append(el("p.mini.sessiz", { metin:
        "Referans hattı, dönem hedefinin aya bölünmüş payıdır; aylar eşit " +
        "olmadığı için yalnızca kabaca yön gösterir. Hedefin kendisi dönem toplamıdır." }));
  }
  if (h.not) kutu.append(el("p.mini.sessiz", { metin:h.not }));
  kap.append(kutu);
}

/* -------------------------------------------------------- hedef formu */
function hedefDuzenle(kod) {
  const eski = kod ? V.durum.hedefler.find(x => x.kod === kod) : null;
  const son = sonEnerjiDonemi() || { yil:bugun().yil, ay:12 };
  const h = eski ? { ...eski } : { ad:"", tur:"enpi", ifade:"", deger:null,
    bas:{ yil:son.yil + 1, ay:1 }, son:{ yil:son.yil + 1, ay:12 },
    sorumlu:"", not:"" };

  const f = el("div");
  const alan = (etiket, giris, ipucu) => {
    f.append(el("div.alan", {}, el("label", { metin:etiket }), giris,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null));
    return giris;
  };
  const gAd = alan("Hedefin adı", el("input", { type:"text", value:h.ad }));

  const gTur = el("select");
  for (const [t, x] of Object.entries(H.HEDEF_TURLERI))
    gTur.append(el("option", { value:t, metin:x.ad, selected:h.tur === t }));
  alan("Tür", gTur);
  const turNot = el("div.mini.sessiz", { metin:H.HEDEF_TURLERI[h.tur].aciklama });
  f.append(turNot);

  const gIfade = el("select");
  const ifadeKur = () => {
    bosalt(gIfade);
    const t = gTur.value;
    if (t === "enpi")
      for (const x of V.durum.enpi_tanimlari)
        gIfade.append(el("option", { value:x.kod, metin:x.ad, selected:h.ifade === x.kod }));
    else if (t === "tasarruf")
      for (const b of V.durum.baz_cizgiler)
        gIfade.append(el("option", { value:b.kod, metin:b.ad, selected:h.ifade === b.kod }));
    else if (t === "tuketim") {
      gIfade.append(el("option", { value:"@TOPLAM_ENERJI_KWH", metin:"Toplam enerji (kWh)" }));
      for (const n of V.durum.olcum_noktalari.filter(n => n.rol === "satin_alinan" && n.birim === "kWh"))
        gIfade.append(el("option", { value:n.kod, metin:n.ad, selected:h.ifade === n.kod }));
    } else {
      gIfade.append(el("option", { value:"@TOPLAM_MALIYET_TL", metin:"Toplam enerji maliyeti (TL)" }));
      for (const n of V.durum.olcum_noktalari.filter(n => n.rol === "maliyet"))
        gIfade.append(el("option", { value:n.kod, metin:n.ad, selected:h.ifade === n.kod }));
    }
    turNot.textContent = H.HEDEF_TURLERI[gTur.value].aciklama;
  };
  gTur.addEventListener("change", ifadeKur);
  alan("Neyin hedefi", gIfade, "Hedef bu göstergeye göre ölçülür.");
  ifadeKur();

  const gDeger = alan("Hedef değer", el("input", { type:"text",
    value:h.deger === null || h.deger === undefined ? "" : String(h.deger).replace(".", ",") }),
    "Türkçe biçim: 1.250,50 · EnPI için 1,20 gibi · tasarruf için % olarak 3");

  const donemSec = (etiket, nesne) => {
    const ay = el("select");
    AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a,
      selected:nesne.ay === i + 1 })));
    const yil = el("input", { type:"number", value:nesne.yil, stil:{ width:"90px" } });
    f.append(el("div.alan", {}, el("label", { metin:etiket }),
      el("div.satir", { stil:{ gap:"6px" } }, ay, yil)));
    return { ay, yil };
  };
  const gBas = donemSec("Dönem başlangıcı", h.bas);
  const gSon = donemSec("Dönem bitişi", h.son);
  const gSor = alan("Sorumlu", el("input", { type:"text", value:h.sorumlu || "" }));
  const gNot = alan("Not", el("input", { type:"text", value:h.not || "" }));

  onayla(eski ? "Hedefi düzenle" : "Yeni hedef", f, "Kaydet").then(ok => {
    if (!ok) return;
    const d = sayiOku(gDeger.value);
    if (!gAd.value.trim()) return bildir("Hedef adı zorunlu", "kritik");
    if (d.hata || d.deger === null) return bildir("Hedef değer okunamadı: " + (d.hata || ""), "kritik");
    const nesne = {
      kod: eski ? eski.kod : "HDF" + Date.now().toString(36).toUpperCase(),
      ad:gAd.value.trim(), tur:gTur.value, ifade:gIfade.value, deger:d.deger,
      bas:{ yil:+gBas.yil.value, ay:+gBas.ay.value },
      son:{ yil:+gSon.yil.value, ay:+gSon.ay.value },
      yon:H.HEDEF_TURLERI[gTur.value].yon,
      sorumlu:gSor.value.trim(), not:gNot.value.trim(),
      olusturma: eski ? eski.olusturma : new Date().toISOString(),
    };
    if (eski) Object.assign(eski, nesne); else V.durum.hedefler.push(nesne);
    V.degisti("hedef"); yenile(); bildir("Hedef kaydedildi");
  });
}

/* =================================================== BÖLÜM 2 — AKSİYONLAR */
function aksiyonBolumu(k) {
  const bg = bugunISO();
  const o = H.aksiyonOzeti(bg);
  const kart = el("div.kart", {});
  kart.append(el("div.satir", { stil:{ justifyContent:"space-between", alignItems:"baseline" } },
    el("h2", { stil:{ margin:"0" }, metin:`Aksiyonlar (${o.toplam})` }),
    el("button.dugme.kucuk.ana", { metin:"+ Aksiyon", onclick:() => aksiyonDuzenle(null) })));
  k.append(kart);

  if (!o.toplam) {
    kart.append(bosDurum("Henüz aksiyon yok",
      "Aksiyon, bir tespitin eyleme dönüştüğü kayıttır: kim, ne zaman, ne yapacak. " +
      "Performans ekranındaki CUSUM kırılımından, Tüketim Analizi'ndeki Pareto'nun " +
      "ilk sırasından ve Dönüşüm Verimliliği'ndeki verim uyarısından doğrudan " +
      "aksiyon açabilirsiniz.",
      el("button.dugme.ana", { metin:"İlk aksiyonu aç", onclick:() => aksiyonDuzenle(null) })));
    return;
  }

  const kutu = (ad, v, alt) => el("div.kart", { stil:{ flex:"1 1 160px", margin:"0" } },
    el("div.mini.sessiz", { metin:ad }),
    el("div", { stil:{ fontSize:"21px", fontWeight:"600", margin:"4px 0 2px" }, metin:v }),
    alt ? el("div.mini.sessiz", { metin:alt }) : null);
  kart.append(el("div.satir", { stil:{ margin:"12px 0" } },
    kutu("Açık", String(o.acik), `${o.kapanan} kapandı`),
    kutu("Geciken", String(o.geciken), o.geciken ? "termini geçti" : "gecikme yok"),
    kutu("Beklenen tasarruf", say(o.beklenenTL, 0) + " TL", "iptaller hariç"),
    kutu("Gerçekleşen", say(o.gerceklesenTL, 0) + " TL", "kapanan aksiyonlar")));

  if (o.geciken)
    kart.append(uyari("dikkat",
      el("b", { metin:`${o.geciken} aksiyonun termini geçti. ` }),
      o.gecikenler.map(a => a.baslik).join(" · ") +
      ". Gecikmiş aksiyon, yönetim gözden geçirmesinde açıklanması gereken bir kalemdir (md. 9.3)."));

  kart.append(tablo([
    { ad:"", baslik:a => H.aksiyonGecikti(a, bg) ? "Termini geçti" : "",
      deger:a => el("span", { stil:{ color:H.aksiyonGecikti(a, bg) ? "var(--ciddi)"
          : a.durum === "kapandi" ? "var(--iyi-ink)" : "var(--ink-mut)" },
        metin:H.AKSIYON_DURUMLARI[a.durum]?.ikon || "○" }) },
    { ad:"Başlık", deger:a => el("span", {},
        el("b", { metin:a.baslik }),
        a.aciklama ? el("div.mini.sessiz", { metin:a.aciklama }) : null,
        a.baglam?.kaynak ? el("div.mini.sessiz", { metin:"kaynak: " + a.baglam.kaynak }) : null) },
    { ad:"Sorumlu", deger:a => a.sorumlu || "—" },
    { ad:"Termin", deger:a => !a.termin ? "—"
        : el("span", { stil:{ color:H.aksiyonGecikti(a, bg) ? "var(--ciddi)" : "" } },
            tarihKisa(a.termin),
            H.aksiyonGecikti(a, bg) ? el("span.rozet.dikkat",
              { stil:{ marginLeft:"6px" }, metin:"GECİKTİ" }) : null) },
    { ad:"Durum", deger:a => H.AKSIYON_DURUMLARI[a.durum]?.ad || a.durum },
    { ad:"Beklenen", deger:a => Number.isFinite(a.beklenen?.deger)
        ? `${say(a.beklenen.deger, 0)} ${a.beklenen.birim || "TL"}` : "—" },
    { ad:"", deger:a => el("button.dugme.kucuk", { metin:"Düzenle",
        onclick:() => aksiyonDuzenle(a.kod) }) },
  ], V.durum.aksiyonlar));
}

/* ------------------------------------------------------ aksiyon formu */
/** Başka ekranlardan çağrılabilir: G.aksiyonAc({baslik, aciklama, baglam}) */
export function aksiyonAc(onDolgu = {}) {
  aksiyonDuzenle(null, onDolgu);
}

function aksiyonDuzenle(kod, onDolgu = {}) {
  const eski = kod ? V.durum.aksiyonlar.find(x => x.kod === kod) : null;
  const a = eski ? { ...eski } : {
    baslik:onDolgu.baslik || "", aciklama:onDolgu.aciklama || "",
    baglam:onDolgu.baglam || {}, sorumlu:"", termin:"", durum:"acik",
    beklenen:{ deger:Number.isFinite(onDolgu.beklenen) ? Math.round(onDolgu.beklenen) : null,
               birim:"TL" },
    gerceklesen:{ deger:null, birim:"TL" }, sonuc_notu:"" };

  const f = el("div");
  const alan = (etiket, giris, ipucu) => {
    f.append(el("div.alan", {}, el("label", { metin:etiket }), giris,
      ipucu ? el("div.mini.sessiz", { metin:ipucu }) : null));
    return giris;
  };
  const gBas = alan("Başlık", el("input", { type:"text", value:a.baslik }));
  const gAck = el("textarea", { rows:3, stil:{ width:"100%" } }); gAck.value = a.aciklama || "";
  alan("Açıklama — ne yapılacak", gAck);
  if (a.baglam?.kaynak)
    f.append(el("div.uyari.bilgi", {}, el("span.ikon", { metin:"ℹ" }),
      el("div", {}, el("b", { metin:"Bu aksiyon bir tespitten doğdu: " }), a.baglam.kaynak)));

  const gSor = alan("Sorumlu", el("input", { type:"text", value:a.sorumlu || "" }),
    "Sahibi olmayan aksiyon kapanmaz.");
  const gTer = alan("Termin", el("input", { type:"date", value:a.termin || "" }));
  const gDur = el("select");
  for (const [d, x] of Object.entries(H.AKSIYON_DURUMLARI))
    gDur.append(el("option", { value:d, metin:x.ad, selected:a.durum === d }));
  alan("Durum", gDur);
  const gBek = alan("Beklenen tasarruf (TL)", el("input", { type:"text",
    value:Number.isFinite(a.beklenen?.deger) ? String(a.beklenen.deger).replace(".", ",") : "" }));
  const gGer = alan("Gerçekleşen tasarruf (TL)", el("input", { type:"text",
    value:Number.isFinite(a.gerceklesen?.deger) ? String(a.gerceklesen.deger).replace(".", ",") : "" }),
    "Kapanışta doldurulur. Boş bırakılabilir — sistem tahmin yürütmez (İ-3).");
  const gSon = el("textarea", { rows:2, stil:{ width:"100%" } }); gSon.value = a.sonuc_notu || "";
  alan("Sonuç notu", gSon);

  onayla(eski ? "Aksiyonu düzenle" : "Yeni aksiyon", f, "Kaydet").then(ok => {
    if (!ok) return;
    if (!gBas.value.trim()) return bildir("Başlık zorunlu", "kritik");
    const oku = g => { const r = sayiOku(g.value); return r.hata ? null : r.deger; };
    const nesne = {
      kod: eski ? eski.kod : "AKS" + Date.now().toString(36).toUpperCase(),
      baslik:gBas.value.trim(), aciklama:gAck.value.trim(), baglam:a.baglam || {},
      sorumlu:gSor.value.trim(), termin:gTer.value || "", durum:gDur.value,
      beklenen:{ deger:oku(gBek), birim:"TL" },
      gerceklesen:{ deger:oku(gGer), birim:"TL" },
      sonuc_notu:gSon.value.trim(),
      olusturma: eski ? eski.olusturma : new Date().toISOString(),
      kapanis: gDur.value === "kapandi" ? (eski?.kapanis || new Date().toISOString()) : null,
    };
    if (eski) Object.assign(eski, nesne); else V.durum.aksiyonlar.push(nesne);
    V.degisti("aksiyon"); yenile(); bildir("Aksiyon kaydedildi");
  });
}

