/* ekranlar/hesaplanan.js — Ekran 5: Hesaplanan Değerler (El Kitabı 9.6, K-23)
   Hesap motorunun CAMDAN KUTUSU. Salt okunur; bir sayıyı değiştirmek için
   onu üreten ham veriye gidilir (E-4). İki sayfalı Excel çıktısı verir. */

import { el, $, bosalt, say, uyari, bildir, bosDurum, donemAd, tarihMetni,
         dosyaIndir } from "../ortak.js";
import * as V from "../veri.js";
import { nokta } from "../model.js";
import { katman, uret } from "../hesaplanan.js";
import { xlsxYaz } from "../xlsx.js";

let secili = null;    // açık sütun formülü

export function ekranHesaplanan(k) {
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Hesaplanan Değerler" }),
    el("p", { metin:"Sistem bu veriden ne üretti? Hesap motorunun camdan kutusu. Her sütunun formülü ve kaynağı, başlığa tıklanınca açılır." })));

  if (!katman.satirlar.length) {
    k.append(bosDurum("Hesaplanacak veri yok",
      "Önce Veri Aktarma veya Veri Girişi ekranından ham veri girin. Bu katman ham veriden otomatik üretilir; kendi başına bir kaydı yoktur.",
      el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));
    return;
  }

  durumKarti(k);
  if (secili) formulKarti(k);
  tabloKarti(k);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranHesaplanan(k); };

/* ------------------------------------------------------- katman durumu */
function durumKarti(k) {
  const kart = el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"center", gap:"18px" } },
      el("span.kucuk", {}, el("span.sessiz", { metin:"Son üretim: " }),
        el("b", { metin:katman.uretim ? tarihMetni(katman.uretim) : "—" })),
      el("span.kucuk", {}, el("span.sessiz", { metin:"" }),
        el("b.sayi", { metin:`${katman.satirlar.length} dönem × ${katman.sutunlar.length} değer = ${say(katman.hucre)} hücre` })),
      el("span.kucuk.sessiz", { metin:katman.sure + " ms" }),
      el("span.bosluk", { stil:{ flex:"1" } }),
      el("button.dugme.kucuk", { metin:"Yeniden üret",
        onclick:() => { uret(); yenile(); bildir(`Yeniden üretildi (${katman.sure} ms)`); } }),
      el("button.dugme.kucuk.ana", { metin:"Excel'e aktar (2 sayfa)", onclick:excelAktar })));

  kart.append(el("p.mini.sessiz", { stil:{ marginTop:"8px", marginBottom:"0" }, metin:
    "Bu katman bir AYNADIR, kayıt değil (K-23): açılışta ve her veri değişiminde baştan üretilir, " +
    "yedek dosyasına yazılmaz. Silinse hiçbir bilgi kaybolmaz — ham veriden yeniden doğar." }));
  k.append(kart);

  if (katman.eksikler.length)
    k.append(uyari("ciddi",
      el("b", { metin:`${say(katman.eksikler.length)} değer HESAPLANAMADI. ` }),
      "Ham veri var ama dönüşüm katsayısı veya formül eksik. Bu bir sorundur — Tanımlar ekranından giderin.",
      el("div.kucuk", { stil:{ marginTop:"5px" },
        metin:katman.eksikler[0].donem + " · " + katman.eksikler[0].ad + ": " + katman.eksikler[0].sebep })));

  if ((katman.bosluklar || []).length)
    k.append(uyari("dikkat",
      el("b", { metin:`${say(katman.bosluklar.length)} değer üretilemedi — ham veri eksik. ` }),
      "Sistem eksik veriyi sıfır saymaz (İ-3); o dönem boş kalır. Bu genellikle normaldir, " +
      "ama beklemediğiniz bir boşluk varsa kaynak veride hata olabilir.",
      el("ul", { stil:{ margin:"6px 0 0 18px" } },
        katman.bosluklar.slice(0, 4).map(b =>
          el("li.kucuk", { metin:`${b.donem} · ${b.ad}: ${b.sebep}` })),
        katman.bosluklar.length > 4
          ? el("li.kucuk.sessiz", { metin:`…ve ${katman.bosluklar.length - 4} tane daha` }) : null)));
}

/* ------------------------------------------------------- formül kartı */
function formulKarti(k) {
  const s = katman.sutunlar.find(x => x.kod === secili);
  if (!s) return;
  const kaynaklar = (typeof s.kaynak === "function" ? s.kaynak() : s.kaynak) || [];
  k.append(el("div.kart", { stil:{ borderColor:"var(--s1)" } },
    el("div.satir", { stil:{ justifyContent:"space-between" } },
      el("h2", { metin:s.ad }),
      el("button.dugme.kucuk", { metin:"Kapat", onclick:() => { secili = null; yenile(); } })),
    el("table", {},
      sat("Birim", s.birim || "—"),
      sat("Formül", el("code", { metin:s.formul })),
      sat("Kural", el("span.kucuk", { metin:s.kural || "—" })),
      sat("Kaynak", kaynaklar.length
        ? el("div", { stil:{ display:"flex", flexWrap:"wrap", gap:"5px" } },
            kaynaklar.map(x => {
              const n = nokta(String(x).split(" ")[0]);
              return el("span.rozet", { title:n ? `${n.ad} · ${n.birim} · ${n.veri_tipi}` : "",
                metin:String(x) });
            }))
        : el("span.sessiz", { metin:"—" })))));
}
const sat = (a, b) => el("tr", {}, el("td.sessiz", { stil:{ width:"110px" }, metin:a }),
                                   el("td", {}, b instanceof Node ? b : String(b)));

/* ------------------------------------------------------------- tablo */
function tabloKarti(k) {
  const t = el("table");
  const bas = el("tr", {}, el("th", { stil:{ minWidth:"110px" }, metin:"Dönem" }));
  for (const s of katman.sutunlar)
    bas.append(el("th.s", { stil:{ cursor:"pointer", whiteSpace:"nowrap" },
      title:s.formul + "\n\n" + (s.kural || ""),
      onclick:() => { secili = secili === s.kod ? null : s.kod; yenile(); } },
      el("span", { stil:secili === s.kod ? "color:var(--s1)" : "" },
        s.ad + (s.birim ? ` (${s.birim})` : "") + " ⓘ")));
  t.append(el("thead", {}, bas));

  const gv = el("tbody");
  for (const r of [...katman.satirlar].reverse()) {
    const tr = el("tr", {}, el("td", { stil:{ whiteSpace:"nowrap" }, metin:donemAd(r.yil, r.ay) }));
    for (const s of katman.sutunlar) {
      const v = r[s.kod];
      const eksik = r["_eksik_" + s.kod], bosluk = r["_bosluk_" + s.kod];
      tr.append(el("td.s", { title:eksik || bosluk || "",
        stil:eksik ? "color:var(--ciddi)" : bosluk ? "color:var(--uyari)" : "" },
        v === null || v === undefined ? (eksik ? "⚠" : bosluk ? "·" : "—") : say(v, s.ondalik ?? 0)));
    }
    gv.append(tr);
  }
  t.append(gv);
  k.append(el("div.tablo-sar", { stil:{ maxHeight:"58vh" } }, t));
  k.append(el("p.mini.sessiz", { metin:
    "Salt okunur. Bir sayıyı değiştirmek için onu üreten ham veriyi değiştirin — " +
    "sütun başlığına tıklayıp kaynağını görebilirsiniz. ⚠ = hesaplanamadı · · = ham veri eksik — üstüne gelin." }));
}

/* ------------------------------------------------- iki sayfalı Excel */
async function excelAktar() {
  bildir("Excel hazırlanıyor…");
  try {
    // 1. sayfa: HAM VERİ (dönem × ölçüm noktası)
    const noktalar = V.durum.olcum_noktalari.filter(n =>
      n.veri_tipi === "olculen" || n.veri_tipi === "tahmini");
    const ham = [
      ["Dönem", ...noktalar.map(n => n.ad)],
      ["", ...noktalar.map(n => n.birim)],
    ];
    for (const r of katman.satirlar)
      ham.push([donemAd(r.yil, r.ay), ...noktalar.map(n => V.deger(n.kod, r.yil, r.ay))]);

    // 2. sayfa: HESAPLANAN (formül satırıyla birlikte)
    const hes = [
      ["Dönem", ...katman.sutunlar.map(s => s.ad)],
      ["", ...katman.sutunlar.map(s => s.birim || "")],
      ["FORMÜL", ...katman.sutunlar.map(s => s.formul)],
    ];
    for (const r of katman.satirlar)
      hes.push([donemAd(r.yil, r.ay), ...katman.sutunlar.map(s => r[s.kod])]);

    const blob = await xlsxYaz([
      { ad:"Ham Veri",   satirlar:ham },
      { ad:"Hesaplanan", satirlar:hes },
    ]);
    const d = new Date(), p = n => String(n).padStart(2, "0");
    dosyaIndir(`enerji-veri-${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}.xlsx`, blob);
    bildir(`İndirildi — ${katman.satirlar.length} dönem, 2 sayfa`);
  } catch (e) { console.error(e); bildir("Excel üretilemedi: " + e.message, "kritik"); }
}
