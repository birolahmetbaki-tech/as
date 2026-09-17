/* uygulama.js — kabuk: menü, üst şerit, yönlendirme
   El Kitabı: 9.0 (ekran ilkeleri), 9.1 (navigasyon haritası), 5.2 (yedek uyarısı) */

import { el, $, bosalt, bosDurum, uyari, bildir, donemAd, bugun } from "./ortak.js";
import * as V from "./veri.js";
import { otomatikUret, katman, katmanDinle } from "./hesaplanan.js";
import BASLANGIC from "./baslangic.js";

import { ekranTanimlar } from "./ekranlar/tanimlar.js";
import { ekranAyarlar }  from "./ekranlar/ayarlar.js";

/* ------------------------------------------------ ekran kayıtları (9.1) */
const YAKINDA = (no, ad, faz, aciklama) => ({
  no, ad, hazir:false, ciz: k => k.append(
    bosDurum(`${ad} — Faz ${faz}'te geliyor`, aciklama,
      el("p.kucuk.sessiz", { metin:"El Kitabı Bölüm 12 · Geliştirme yol haritası" }))),
});

export const EKRANLAR = [
  { grup:"ÖZET" },
  YAKINDA(1,"Gösterge Paneli",3,"Durumunuzu tek ekranda özetler: KPI kartları, 24 aylık enerji ve EnPI trendi, CUSUM, yıllık özet ve açık aksiyonlar."),
  { grup:"VERİ" },
  YAKINDA(2,"Veri Girişi",2,"Aylık verilerin girildiği ana ekran. Dört giriş yöntemi, geçen ay ve geçen yıl karşılaştırması, canlı özet şeridi."),
  YAKINDA(3,"Veri Aktarma",2,"Excel dosyanızı sürükleyip bırakarak içe aktarma; önizleme, ya hep ya hiç kuralı ve güvenlik yedeği."),
  YAKINDA(4,"Veri Denetimi",2,"Bütün veri setinin sağlığı: eksik veri haritası, şüpheli değerler, tutarsızlıklar."),
  YAKINDA(5,"Hesaplanan Değerler",2,"Hesap motorunun camdan kutusu: dönem × hesaplanan değer tablosu, her sütunun formülü ve iki sayfalı Excel çıktısı."),
  { grup:"ANALİZ" },
  YAKINDA(6,"Enerji Dengesi",3,"Enerji nereye gidiyor? Sankey akış diyagramı ve ölçüm kapsamı ağacı."),
  YAKINDA(7,"Tüketim Analizi",3,"Trend, ısı haritası, Pareto ve dönem karşılaştırması."),
  YAKINDA(8,"Performans (EnPI)",4,"Platformun kalbi: baz çizgi, normalize EnPI ve CUSUM. İyileştik mi, ne zaman, ne kadar?"),
  YAKINDA(9,"Dönüşüm Verimliliği",4,"Kojenerasyon ve kazanların yakıtı ne verimle faydalı enerjiye çevirdiği."),
  YAKINDA(10,"Maliyet",4,"Maliyet artışının ne kadarı fiyattan, ne kadarı tüketimden? Fiyat/hacim ayrıştırması."),
  YAKINDA(11,"GES",4,"Yozgat ve Adana santrallerinin üretimi ve mali katkısı."),
  { grup:"YÖNETİM" },
  YAKINDA(12,"Hedefler ve Aksiyonlar",5,"Dört hedef türü ve tespitlerin sahibi ile termini olan aksiyonlar."),
  YAKINDA(13,"Raporlar",5,"Aylık enerji raporu, yönetim gözden geçirme raporu ve serbest rapor oluşturucu."),
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
    el("span", { metin:"Faz 1 · Çekirdek" })));
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
  durumu.ekran = h ? +h[1] : 14;
  if (!EKRANLAR.some(e => e.no === durumu.ekran)) durumu.ekran = 14;

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
