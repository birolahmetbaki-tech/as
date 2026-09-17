/* koken.js — İZLENEBİLİRLİK (E-4)
   "Bu sayı nereden geliyor?"
   Her türetilmiş sayının yanında bir `?` durur; tıklanınca o sayının hangi
   ölçüm noktalarından, hangi ham değerlerden ve hangi katsayılarla üretildiği
   gösterilir. ISO 50001 denetiminde sorulan ilk sorunun cevabıdır. */

import { el, say, donemAd, goster } from "./ortak.js";
import { nokta, varlik } from "./model.js";
import * as H from "./hesap.js";
import { sutunKokeni, katman } from "./hesaplanan.js";

const KALITE_AD = { girildi:"girildi", duzeltildi:"düzeltildi", tahmin:"TAHMİN" };

/** Her ekranın bir sayının yanına koyabileceği `?` düğmesi */
export function kokenDugmesi(sutunKod, yil, ay, { etiket = "?" } = {}) {
  return el("button.koken", {
    type:"button", title:"Bu sayı nereden geliyor? (E-4)",
    "aria-label":"Bu sayının kaynağını göster",
    metin:etiket,
    onclick:ev => { ev.stopPropagation(); kokenGoster(sutunKod, yil, ay); },
  });
}

/** Ölçüm noktası için `?` düğmesi (sütun değil, doğrudan nokta) */
export function noktaKokenDugmesi(kod, yil, ay, { etiket = "?" } = {}) {
  return el("button.koken", {
    type:"button", title:"Bu sayı nereden geliyor? (E-4)", metin:etiket,
    onclick:ev => { ev.stopPropagation(); noktaKokenGoster(kod, yil, ay); },
  });
}

/* ------------------------------------------------------------ pencere */
export function kokenGoster(sutunKod, yil, ay) {
  const k = sutunKokeni(sutunKod, yil, ay);
  if (!k) return;
  const s = k.sutun;
  const g = el("div");

  g.append(baslik(s.ad, k.deger, s.birim, s.ondalik, yil, ay));
  g.append(kutu("Formül", el("code", { metin:s.formul || "—" })));
  if (s.kural) g.append(kutu("Kural", el("span.mini", { metin:s.kural })));

  if (k.eksik)
    g.append(el("div.uyari.ciddi", {}, el("span.ikon", { metin:"⚠" }),
      el("div", {}, el("b", { metin:"Bu sayı üretilemedi. " }), k.eksik,
        el("div.mini", { stil:{ marginTop:"4px" },
          metin:"Veri var ama hesaplanamıyor — eksik olan tanım tamamlanmalı (İ-3)." }))));
  else if (k.bosluk)
    g.append(el("div.uyari.bilgi", {}, el("span.ikon", { metin:"ℹ" }),
      el("div", {}, el("b", { metin:"Ham veri boş. " }), k.bosluk,
        el("div.mini", { stil:{ marginTop:"4px" },
          metin:"Bu bir hata değil; o dönem için değer girilmemiş (İ-4)." }))));

  if (k.ozelKaynaklar.length)
    g.append(kutu("Özel toplamlar", el("span.mini",
      { metin:k.ozelKaynaklar.join(" · ") })));

  g.append(el("h4", { stil:{ margin:"14px 0 6px" },
    metin:`Katkıda bulunan ölçüm noktaları (${k.agac.length})` }));
  g.append(agacCiz(k.agac, yil, ay));
  g.append(altNot());

  goster(`Bu sayı nereden geliyor? · ${donemAd(yil, ay)}`, g);
}

export function noktaKokenGoster(kod, yil, ay) {
  const n = nokta(kod);
  if (!n) return;
  const agac = H.noktaKokeni(kod, yil, ay);
  const g = el("div");
  g.append(baslik(n.ad, agac.deger, n.birim, 0, yil, ay));
  g.append(agacCiz([agac], yil, ay));
  g.append(altNot());
  goster(`Bu sayı nereden geliyor? · ${donemAd(yil, ay)}`, g);
}

/* ------------------------------------------------------------ parçalar */
function baslik(ad, deger, birim, ondalik, yil, ay) {
  return el("div", { stil:{ marginBottom:"10px" } },
    el("div.mini.sessiz", { metin:`${ad} · ${donemAd(yil, ay)}` }),
    el("div", { stil:{ fontSize:"24px", fontWeight:"600",
      fontVariantNumeric:"tabular-nums" } },
      deger === null || deger === undefined ? "—" : say(deger, ondalik || 0),
      el("span", { stil:{ fontSize:"13px", fontWeight:"400",
        color:"var(--ink-mut)", marginLeft:"6px" }, metin:birim || "" })));
}

function kutu(etiket, icerik) {
  return el("div", { stil:{ margin:"6px 0" } },
    el("span.mini.sessiz", { stil:{ marginRight:"7px" }, metin:etiket + ":" }), icerik);
}

function altNot() {
  return el("p.mini.sessiz", { stil:{ marginTop:"12px", borderTop:"1px solid var(--kilavuz)",
    paddingTop:"8px" }, metin:
    "Bu sayı veri dosyasında saklanmaz; her açılışta ham veriden yeniden üretilir " +
    "(İ-1, K-23). Yukarıdaki ham değerler ise kullanıcının girdiği tek doğruluk " +
    "kaynağıdır. TAHMİN işaretli bir değer, ölçülmüş değildir (İ-4)." });
}

/* --------------------------------------------------------- köken ağacı */
function agacCiz(dugumler, yil, ay, seviye = 0) {
  const liste = el("div", { stil:{ marginLeft: seviye ? "16px" : "0",
    borderLeft: seviye ? "1px solid var(--kilavuz)" : "none",
    paddingLeft: seviye ? "10px" : "0" } });
  if (!dugumler.length)
    return liste.append(el("p.mini.sessiz", { metin:"Kaynak nokta bulunamadı." })), liste;

  for (const d of dugumler) {
    const v = varlik(d.varlik);
    const satir = el("div", { stil:{ padding:"5px 0",
      borderTop: seviye ? "none" : "1px solid var(--kilavuz)" } });

    satir.append(el("div.satir", { stil:{ justifyContent:"space-between", gap:"10px",
        alignItems:"baseline" } },
      el("span", {}, el("code", { metin:d.kod }),
        el("span", { stil:{ marginLeft:"7px" }, metin:d.ad || "" }),
        v ? el("span.mini.sessiz", { stil:{ marginLeft:"6px" }, metin:"· " + v.ad }) : null),
      el("span.sayi", { stil:{ whiteSpace:"nowrap" },
        metin: d.deger === null || d.deger === undefined
          ? "—" : `${say(d.deger, d.birim === "TL" ? 0 : 0)} ${d.birim || ""}` })));

    const etiketler = el("div", { stil:{ marginTop:"2px" } });
    const rozet = (metin, tur = "") => el("span.rozet" + tur,
      { stil:{ marginRight:"5px" }, metin });

    if (d.kaynakTipi === "ham") {
      etiketler.append(rozet("ham veri"));
      if (d.kalite && d.kalite !== "girildi")
        etiketler.append(rozet(KALITE_AD[d.kalite] || d.kalite,
          d.kalite === "tahmin" ? ".dikkat" : ""));
      if (d.deger === null) etiketler.append(rozet("girilmemiş", ".dikkat"));
    } else if (d.kaynakTipi === "dagitim") {
      etiketler.append(rozet("dağıtılmış — ölçüm değil", ".dikkat"));
    } else {
      etiketler.append(rozet("hesaplanan"));
    }
    if (d.eksik) etiketler.append(rozet("üretilemedi", ".dikkat"));
    satir.append(etiketler);

    if (d.formul)
      satir.append(el("div.mini.sessiz", { stil:{ marginTop:"2px" } },
        el("code", { metin:d.formul })));
    if (d.not)
      satir.append(el("div.mini.sessiz", { stil:{ marginTop:"2px" }, metin:"Not: " + d.not }));

    for (const k of d.katsayilar) {
      const kay = k.kayit;
      satir.append(el("div.mini", { stil:{ marginTop:"3px",
        color: kay ? "var(--ink-2)" : "var(--ciddi)" },
        metin: kay
          ? `katsayı: ${k.tur} ${k.kaynak} → ${k.hedef} = ${say(kay.katsayi, 6)} ` +
            `(${kay.gecerli_baslangic} tarihinden geçerli${kay.kaynak ? " · " + kay.kaynak : ""})`
          : `katsayı TANIMSIZ: ${k.tur} ${k.kaynak} → ${k.hedef} — bu yüzden sonuç üretilemiyor` }));
    }
    if (d.kesildi)
      satir.append(el("div.mini.sessiz", { metin:"… daha derine inilmedi (döngü veya derinlik sınırı)" }));
    if (d.cocuklar?.length) satir.append(agacCiz(d.cocuklar, yil, ay, seviye + 1));
    liste.append(satir);
  }
  return liste;
}
