/* ekranlar/veri.js — Ekran 2: VERİ (El Kitabı 9.3)
   Veri girişi, aktarma ve denetim TEK EKRANDA (K-30).

   Dört sekme:
     Tablo    — Excel'in kendisi gibi ızgara; asıl giriş yüzeyi
     Aylık form — tek dönem odaklı kategori formu ve toplu yapıştırma
     Aktar    — .xlsx içe aktarma, yedek alma / geri yükleme
     Denetim  — bütün veri setinin sağlığı

   Veriye dokunan her iş burada; kullanıcı ekran değiştirmek zorunda kalmaz. */

import { el, $, bosalt, say, uyari, bosDurum } from "../ortak.js";
import * as V from "../veri.js";
import { izgaraCiz, odakla, sutunEkleyiciKur, durum as izgaraDurum } from "./izgara.js";
import { girisGovde, yenileyiciKur as girisYenileyici } from "./giris.js";
import { aktarmaGovde, yenileyiciKur as aktarmaYenileyici } from "./aktarma.js";
import { denetimGovde, yenileyiciKur as denetimYenileyici } from "./denetim.js";
import { noktaFormu } from "./tanimlar.js";
import { katman } from "../hesaplanan.js";

const SEKMELER = [
  ["tablo",   "Tablo",       "Bütün veri; satır = dönem, sütun = ölçüm noktası"],
  ["form",    "Aylık form",  "Tek bir dönemi kategori kategori doldurmak"],
  ["aktar",   "Aktar",       "Excel içe aktarma · yedek alma ve geri yükleme"],
  ["denetim", "Denetim",     "Bütün veri setinin sağlığı ve doğrulama bulguları"],
];

let sekme = "tablo";
let odakHedefi = null;

export function veriSekmesi(kod) { if (SEKMELER.some(s => s[0] === kod)) sekme = kod; }

export function ekranVeri(k) {
  girisYenileyici(yenile);
  aktarmaYenileyici(yenile);
  denetimYenileyici(yenile);
  sutunEkleyiciKur(sonra => noktaFormu(() => { sekme = "tablo"; yenile(); sonra?.(); }));

  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Veri" }),
    el("p", { metin:"Verinin girildiği, aktarıldığı ve denetlendiği tek yer. Tablo sekmesi kaynak Excel'inizin kendisi gibi çalışır: satır dönem, sütun ölçüm noktası, hücre değer." })));

  const s = el("div.sekmeler", {});
  for (const [kod, ad, ipucu] of SEKMELER)
    s.append(el("button.sekme", { "aria-selected":sekme === kod ? "true" : "false",
      title:ipucu, metin:ad + (kod === "denetim" ? bulguRozeti() : ""),
      onclick:() => { sekme = kod; yenile(); } }));
  k.append(s);

  if (sekme === "tablo")   return tabloSekmesi(k);
  if (sekme === "form")    return girisGovde(k);
  if (sekme === "aktar")   return aktarmaGovde(k);
  if (sekme === "denetim") return denetimGovde(k);
}

function bulguRozeti() {
  const n = (katman.eksikler || []).length;
  return n ? ` (${n})` : "";
}

function tabloSekmesi(k) {
  if (!V.durum.degerler.length && !(V.durum.ayarlar?.ek_donemler || []).length) {
    k.append(bosDurum("Henüz veri yok",
      "İki yol var: Excel dosyanız varsa Aktar sekmesinden alın — 96 aylık geçmiş " +
      "birkaç saniyede içeri girer. Elle başlamak isterseniz '+ Dönem' ile ilk " +
      "satırı açıp hücreleri doldurun.",
      el("div.satir", {},
        el("button.dugme.ana", { metin:"Excel dosyamı aktar",
          onclick:() => { sekme = "aktar"; yenile(); } }),
        el("button.dugme", { metin:"+ Dönem ekleyip elle başla",
          onclick:() => { izgaraCiz; ilkDonem(); } }))));
    return;
  }
  izgaraCiz(k, hedef => { odakHedefi = hedef || null; yenile(); });
  if (odakHedefi) { const h = odakHedefi; odakHedefi = null; setTimeout(() => odakla(h), 0); }
}

function ilkDonem() {
  const b = new Date();
  const kod = `${b.getFullYear()}-${String(b.getMonth() + 1).padStart(2, "0")}`;
  V.durum.ayarlar.ek_donemler ||= [];
  if (!V.durum.ayarlar.ek_donemler.includes(kod)) V.durum.ayarlar.ek_donemler.push(kod);
  izgaraDurum.yil = b.getFullYear();
  V.degisti("donem"); yenile();
}

function yenile(hedef) {
  if (hedef && typeof hedef === "object") odakHedefi = hedef;
  const k = bosalt($("#icerik"));
  ekranVeri(k);
}
