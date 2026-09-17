/* uygulama.js — kabuk: menü, üst şerit, yönlendirme
   El Kitabı: 9.0 (ekran ilkeleri), 9.1 (navigasyon haritası), 5.2 (yedek uyarısı) */

import { el, $, bosalt, bosDurum, uyari, bildir, donemAd, bugun } from "./ortak.js";
import * as V from "./veri.js";
import { otomatikUret, katman, katmanDinle } from "./hesaplanan.js";
import BASLANGIC from "./baslangic.js";

import { ekranTanimlar } from "./ekranlar/tanimlar.js";
import { ekranAyarlar }  from "./ekranlar/ayarlar.js";
import { ekranAktarma }  from "./ekranlar/aktarma.js";
import { ekranGiris }    from "./ekranlar/giris.js";
import { ekranDenetim }  from "./ekranlar/denetim.js";
import { ekranHesaplanan } from "./ekranlar/hesaplanan.js";
import { ekranPanel }    from "./ekranlar/panel.js";
import { ekranTuketim }  from "./ekranlar/tuketim.js";
import { ekranDenge }    from "./ekranlar/denge.js";
import { ekranPerformans } from "./ekranlar/performans.js";
import { ekranVerimlilik } from "./ekranlar/verimlilik.js";
import { ekranMaliyet }    from "./ekranlar/maliyet.js";
import { ekranGes }        from "./ekranlar/ges.js";
import { ekranHedefler }   from "./ekranlar/hedefler.js";
import { ekranRaporlar }   from "./ekranlar/raporlar.js";

/* ------------------------------------------------ ekran kayıtları (9.1) */
const YAKINDA = (no, ad, faz, aciklama) => ({
  no, ad, hazir:false, ciz: k => k.append(
    bosDurum(`${ad} — Faz ${faz}'te geliyor`, aciklama,
      el("p.kucuk.sessiz", { metin:"El Kitabı Bölüm 12 · Geliştirme yol haritası" }))),
});

export const EKRANLAR = [
  { grup:"ÖZET" },
  { no:1, ad:"Gösterge Paneli", hazir:true, ciz:ekranPanel },
  { grup:"VERİ" },
  { no:2, ad:"Veri Girişi", hazir:true, ciz:ekranGiris },
  { no:3, ad:"Veri Aktarma", hazir:true, ciz:ekranAktarma },
  { no:4, ad:"Veri Denetimi", hazir:true, ciz:ekranDenetim },
  { no:5, ad:"Hesaplanan Değerler", hazir:true, ciz:ekranHesaplanan },
  { grup:"ANALİZ" },
  { no:6, ad:"Enerji Dengesi", hazir:true, ciz:ekranDenge },
  { no:7, ad:"Tüketim Analizi", hazir:true, ciz:ekranTuketim },
  { no:8, ad:"Performans (EnPI)", hazir:true, ciz:ekranPerformans },
  { no:9,  ad:"Dönüşüm Verimliliği", hazir:true, ciz:ekranVerimlilik },
  { no:10, ad:"Maliyet",             hazir:true, ciz:ekranMaliyet },
  { no:11, ad:"GES",                 hazir:true, ciz:ekranGes },
  { grup:"YÖNETİM" },
  { no:12, ad:"Hedefler ve Aksiyonlar", hazir:true, ciz:ekranHedefler },
  { no:13, ad:"Raporlar", hazir:true, ciz:ekranRaporlar },
  { grup:"SİSTEM" },
  { no:14, ad:"Tanımlar",             hazir:true, ciz:ekranTanimlar },
  { no:15, ad:"Ayarlar ve Yedekleme", hazir:true, ciz:ekranAyarlar  },
];

export const durumu = { ekran: 14, donem: bugun() };

/* ------------------------------------------------------------- menü */
function menuCiz() {
  const m = bosalt($("#menu"));
  m.append(el("div.marka", {},
    el("b", { metin:"Enerji Yönetim" }),
    el("span", { metin:"Faz 5 · Yönetme" })));
  for (const e of EKRANLAR) {
    if (e.grup) { m.append(el("div.menu-grup", { metin:e.grup })); continue; }
    m.append(el("button.menu-og", {
      "data-hazir": e.hazir ? "1" : "0",
      "aria-current": durumu.ekran === e.no ? "page" : null,
      title: e.hazir ? e.ad : `${e.ad} — henüz yapılmadı`,
      onclick: () => git(e.no),
    }, el("span.no", { metin:String(e.no) }), el("span", { metin:e.ad })));
  }
}

/* -------------------------------------------------------- üst şerit */
function seritCiz() {
  const s = bosalt($("#serit"));
  const y = V.yedekDurumu();

  s.append(el("strong", { metin: ekran()?.ad || "" }));
  s.append(el("span.bosluk"));

  if (katman.uretim)
    s.append(el("span.mini.sessiz", {
      title:`${katman.hucre} hücre · ${katman.sure} ms · ${katman.satirlar.length} dönem`,
      metin:`hesap katmanı: ${katman.satirlar.length} dönem × ${katman.sutunlar.length} değer` }));

  s.append(el("span.rozet" + (y.uyarmali ? ".dikkat" : ""), {
    title:y.tarih ? y.metin : "Hiç yedek alınmadı",
    metin:(y.uyarmali ? "⚠ " : "") + y.aciklama }));

  s.append(el("button.dugme.kucuk", { metin:"Yedek al", onclick: () => {
    V.yedekAl(); seritCiz(); bildir("Yedek indirildi"); } }));

  const t = document.documentElement.dataset.tema || "otomatik";
  s.append(el("button.dugme.kucuk", {
    title:"Tema: " + t, metin: t === "koyu" ? "☾" : t === "acik" ? "☀" : "◐",
    onclick: () => {
      const sira = ["otomatik","acik","koyu"];
      const y2 = sira[(sira.indexOf(t) + 1) % 3];
      document.documentElement.dataset.tema = y2;
      V.durum.ayarlar.tema = y2; V.kaydet(); seritCiz();
    } }));
  s.append(el("button.dugme.kucuk", { metin:"Yazdır", onclick:() => window.print() }));
}

/* ------------------------------------------------------------- çizim */
const ekran = () => EKRANLAR.find(e => e.no === durumu.ekran);

export function git(no) {
  durumu.ekran = no;
  location.hash = "e" + no;
  menuCiz(); seritCiz(); ciz();
}

export function ciz() {
  const k = bosalt($("#icerik"));
  const e = ekran();
  if (!e) return k.append(bosDurum("Ekran bulunamadı", "Soldaki menüden bir ekran seçin."));

  // Yedek uyarısı — sonucun yanında durur (E-2)
  const y = V.yedekDurumu();
  if (y.uyarmali && V.durum.degerler.length)
    k.append(uyari("dikkat",
      el("b", { metin:y.aciklama + ". " }),
      "Veriniz yalnızca bu tarayıcıda duruyor. Tarayıcı verisi temizlenirse kaybolur — yedek alın.",
      el("div", { stil:{ marginTop:"7px" } },
        el("button.dugme.kucuk", { metin:"Şimdi yedek al",
          onclick:() => { V.yedekAl(); bildir("Yedek indirildi"); ciz(); seritCiz(); } }))));

  try { e.ciz(k); }
  catch (err) { console.error(err); k.append(uyari("kritik", el("b",{metin:"Ekran çizilemedi: "}), err.message)); }
}

/* ------------------------------------------------------------ başlat */
export async function baslat() {
  const s = await V.baslat(BASLANGIC);
  document.documentElement.dataset.tema = V.durum.ayarlar?.tema || "otomatik";

  otomatikUret();                      // K-23: açılışta + her değişimde
  katmanDinle(() => seritCiz());

  const h = /^#e(\d+)$/.exec(location.hash);
  durumu.ekran = h ? +h[1] : 1;
  if (!EKRANLAR.some(e => e.no === durumu.ekran)) durumu.ekran = 1;

  menuCiz(); seritCiz(); ciz();

  window.addEventListener("hashchange", () => {
    const m = /^#e(\d+)$/.exec(location.hash);
    if (m && +m[1] !== durumu.ekran) git(+m[1]);
  });

  // Yedek alınmadan çıkılıyorsa uyar (5.2)
  window.addEventListener("beforeunload", ev => {
    const yd = V.yedekDurumu();
    if (V.durum.degerler.length && yd.uyarmali) { ev.preventDefault(); ev.returnValue = ""; }
  });

  if (s.kaynak === "baslangic")
    bildir("Başlangıç tanımları yüklendi — " + V.durum.olcum_noktalari.length + " ölçüm noktası");
}
