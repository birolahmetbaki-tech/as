/* ekranlar/izgara.js — VERİ IZGARASI (El Kitabı 9.3)
   Kaynak Excel'in kendisi gibi: satır = dönem, sütun = ölçüm noktası,
   değer = hücre. Yeni veri için yeni satır (dönem) veya yeni sütun
   (ölçüm noktası) açılır ve hücreye yazılır.

   SORUNLU HÜCRE RENKLİDİR ve fare üstüne gelince nedenini açılır
   pencerede yazar. Pencere her zaman en üstte durur (z-index 9999). */

import { el, $, bosalt, say, sayiOku, uyari, bildir, onayla, bosDurum,
         donemAd, donemKod, donemKaydir, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { varlik, nokta, dogrula, ENGEL, BULGU_TURLERI, devrede } from "../model.js";
import * as H from "../hesap.js";
import { katman, hucre as katmanHucre } from "../hesaplanan.js";

/* durum — ekran yeniden çizilse de korunur */
export const durum = {
  yil: null,           // null = bütün yıllar
  sutunKumesi: "girilebilir",   // girilebilir | tumu
  ara: "",
};

/* ------------------------------------------------------------ ipucu */
let kutu = null;
function ipucu() {
  if (kutu) return kutu;
  const d = el("div.ipucu");
  document.body.append(d);
  kutu = {
    goster(olay, icerik) {
      bosalt(d); d.append(icerik); d.style.display = "block";
      const k = d.getBoundingClientRect();
      let x = olay.clientX + 16, y = olay.clientY + 16;
      if (x + k.width > innerWidth - 8) x = olay.clientX - k.width - 16;
      if (y + k.height > innerHeight - 8) y = olay.clientY - k.height - 16;
      d.style.left = Math.max(8, x) + "px";
      d.style.top = Math.max(8, y) + "px";
    },
    gizle() { d.style.display = "none"; },
  };
  return kutu;
}

/* ------------------------------------------------------ dönem listesi */
/** Satırlar: veri bulunan dönemler + kullanıcının elle açtığı boş dönemler */
export function donemler() {
  const kume = new Set(V.durum.degerler.map(d => donemKod(d.y, d.a)));
  for (const k of (V.durum.ayarlar?.ek_donemler || [])) kume.add(k);
  const liste = [...kume].map(k => ({ yil:+k.slice(0, 4), ay:+k.slice(5) }))
    .sort((a, b) => a.yil - b.yil || a.ay - b.ay);
  return durum.yil === null ? liste : liste.filter(d => d.yil === durum.yil);
}

/** Sütunlar: ölçüm noktaları, tanım sırasında (Excel sütun düzeni) */
export function sutunlar() {
  const ara = durum.ara.trim().toLocaleLowerCase("tr");
  return V.durum.olcum_noktalari.filter(n => {
    if (n.aktif === false) return false;
    const girilebilir = n.veri_tipi === "olculen" || n.veri_tipi === "tahmini";
    if (durum.sutunKumesi === "girilebilir" && !girilebilir) return false;
    if (!ara) return true;
    const va = varlik(n.varlik)?.ad || "";
    return (n.ad + " " + n.kod + " " + va).toLocaleLowerCase("tr").includes(ara);
  });
}

/* ------------------------------------------------------------- çizim */
export function izgaraCiz(k, yenile) {
  const sut = sutunlar();
  const don = donemler();

  araclar(k, yenile, sut.length, don.length);

  if (!sut.length) {
    k.append(bosDurum("Gösterilecek sütun yok",
      "Arama kutusunu temizleyin ya da sütun kümesini değiştirin."));
    return;
  }
  if (!don.length) {
    // Yıl süzgeci doluyken başka yıllarda veri olabilir; kullanıcı burada
    // sıkışmasın diye çıkış yolu açıkça gösterilir.
    const baskaVarMi = durum.yil !== null &&
      (V.durum.degerler.length > 0 || (V.durum.ayarlar?.ek_donemler || []).length > 0);
    k.append(bosDurum("Gösterilecek dönem yok",
      durum.yil === null
        ? "Henüz hiç veri yok. '+ Dönem' ile ilk satırı açın ya da Aktar sekmesinden Excel dosyanızı alın."
        : `${durum.yil} yılında kayıt yok.` + (baskaVarMi ? " Başka yıllarda veri var." : ""),
      el("div.satir", {},
        baskaVarMi ? el("button.dugme.ana", { metin:"Bütün yılları göster",
          onclick:() => { durum.yil = null; yenile(); } }) : null,
        el("button.dugme" + (baskaVarMi ? "" : ".ana"), { metin:"+ Dönem ekle",
          onclick:() => donemEkle(yenile) }))));
    return;
  }

  const bulgular = bulguHaritasi(don, sut);
  const sar = el("div.izgara-sar");
  const t = el("table.izgara");
  t.append(baslik(sut));
  t.append(govde(don, sut, bulgular, yenile));
  sar.append(t);
  k.append(sar);
  altBilgi(k, bulgular, don, sut);
}

/* ----------------------------------------------------------- araçlar */
function araclar(k, yenile, sutunSay, donemSay) {
  const ar = V.veriAraligi();
  const yillar = new Set(V.durum.degerler.map(d => d.y));
  for (const kod of (V.durum.ayarlar?.ek_donemler || [])) yillar.add(+kod.slice(0, 4));

  const ys = el("select", { onchange:e => {
    durum.yil = e.target.value === "" ? null : +e.target.value; yenile(); } });
  ys.append(el("option", { value:"", metin:"Bütün yıllar", selected:durum.yil === null }));
  for (const y of [...yillar].sort((a, b) => b - a))
    ys.append(el("option", { value:y, metin:y, selected:durum.yil === y }));

  const ks = el("select", { onchange:e => { durum.sutunKumesi = e.target.value; yenile(); } });
  for (const [v, a] of [["girilebilir","Yalnız girilebilir sütunlar"],
                        ["tumu","Bütün sütunlar (hesaplananlar dahil)"]])
    ks.append(el("option", { value:v, metin:a, selected:durum.sutunKumesi === v }));

  const arama = el("input", { type:"search", value:durum.ara, placeholder:"Sütun ara…",
    stil:{ minWidth:"180px" },
    oninput:e => { durum.ara = e.target.value;
      clearTimeout(arama._z); arama._z = setTimeout(yenile, 250); } });

  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Yıl" }), ys),
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Sütunlar" }), ks),
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Ara" }), arama),
      el("button.dugme.kucuk", { metin:"+ Dönem (satır)", onclick:() => donemEkle(yenile) }),
      el("button.dugme.kucuk", { metin:"+ Ölçüm noktası (sütun)",
        onclick:() => sutunEkle(yenile) })),
    el("p.mini.sessiz", { stil:{ margin:"8px 0 0" }, metin:
      `${say(donemSay)} satır × ${say(sutunSay)} sütun. Hücreye tıklayıp yazın; ` +
      "Enter alta, Tab sağa geçer. Renkli hücrelerin üstüne gelince nedeni açılır." })));
}

/* ------------------------------------------------------------ başlık */
function baslik(sut) {
  const th = el("thead");
  // 1. satır: varlık grupları
  const g = el("tr", {}, el("th.d1", { metin:"" }), el("th.d2", { metin:"" }));
  let i = 0;
  while (i < sut.length) {
    const v = sut[i].varlik;
    let n = 1;
    while (i + n < sut.length && sut[i + n].varlik === v) n++;
    const va = varlik(v);
    g.append(el("th.grup", { colspan:n, title:va?.ad || v, metin:va?.ad || v || "—" }));
    i += n;
  }
  th.append(g);
  // 2. satır: nokta adı + birim
  const s = el("tr", {}, el("th.d1", { metin:"Yıl" }), el("th.d2", { metin:"Ay" }));
  for (const n of sut) {
    const hucre = el("th.nokta", {}, n.ad,
      el("div.birim", { metin:`${n.birim}${n.veri_tipi !== "olculen" && n.veri_tipi !== "tahmini" ? " · hesaplanan" : ""}` }));
    hucre.addEventListener("mousemove", ev => ipucu().goster(ev, sutunIpucu(n)));
    hucre.addEventListener("mouseleave", () => ipucu().gizle());
    s.append(hucre);
  }
  th.append(s);
  return th;
}

function sutunIpucu(n) {
  const va = varlik(n.varlik);
  return el("div", {},
    el("b", { metin:n.ad }),
    el("div", {}, el("code", { metin:n.kod })),
    el("div", { metin:`${va?.ad || n.varlik} · ${n.birim} · ${n.rol}` }),
    n.formul ? el("div.satir", {}, "Formül: ", el("code", { metin:n.formul })) : null,
    n.not ? el("div.satir", { metin:n.not }) : null);
}

/* ------------------------------------------------------------- gövde */
function govde(don, sut, bulgular, yenile) {
  const gv = el("tbody");
  for (const d of don) {
    const tr = el("tr", {},
      el("th.d1", { metin:String(d.yil) }),
      el("th.d2", { metin:AYLAR[d.ay - 1] }));
    for (const n of sut) tr.append(hucreCiz(n, d, bulgular, yenile));
    gv.append(tr);
  }
  return gv;
}

function hucreCiz(n, d, bulgular, yenile) {
  const girilebilir = n.veri_tipi === "olculen" || n.veri_tipi === "tahmini";
  const anahtar = `${n.kod}|${donemKod(d.yil, d.ay)}`;
  const b = bulgular.get(anahtar);

  if (!girilebilir) {
    const r = H.noktaDeger(n.kod, d.yil, d.ay);
    const td = el("td.hucre.turetilmis", {},
      Number.isFinite(r.deger) ? say(r.deger, n.birim === "TL" ? 0 : 0) : "—");
    td.addEventListener("mousemove", ev => ipucu().goster(ev,
      turetilmisIpucu(n, d, r)));
    td.addEventListener("mouseleave", () => ipucu().gizle());
    return td;
  }

  const kayit = V.degerKayit(n.kod, d.yil, d.ay);
  const v = kayit ? kayit.v : null;
  const sinif = ["hucre"];
  if (v === null) sinif.push("bos");
  if (b?.engel) sinif.push("engel");
  else if (b?.uyar) sinif.push("uyar");
  if (kayit?.k === "tahmin") sinif.push("tahmin");
  if (kayit?.k === "duzeltildi") sinif.push("duzeltildi");

  const td = el("td." + sinif.join("."), { tabindex:"0" },
    v === null ? "" : say(v, ondalik(n, v)));
  td.dataset.kod = n.kod; td.dataset.d = donemKod(d.yil, d.ay);

  td.addEventListener("mousemove", ev => {
    const ic = hucreIpucu(n, d, kayit, b);
    if (ic) ipucu().goster(ev, ic); else ipucu().gizle();
  });
  td.addEventListener("mouseleave", () => ipucu().gizle());
  td.addEventListener("click", () => duzenle(td, n, d, yenile));
  td.addEventListener("keydown", ev => {
    if (ev.key === "Enter" || ev.key === "F2") { ev.preventDefault(); duzenle(td, n, d, yenile); }
    else if (ev.key.length === 1 && /[\d,.\-]/.test(ev.key)) { duzenle(td, n, d, yenile, ev.key); ev.preventDefault(); }
    else if (ev.key === "Delete" || ev.key === "Backspace") {
      ev.preventDefault();
      if (V.deger(n.kod, d.yil, d.ay) !== null) { V.degerYaz(n.kod, d.yil, d.ay, null); yenile(); }
    } else yonTusu(ev, td);
  });
  return td;
}

const ondalik = (n, v) => (n.birim === "TL" || Math.abs(v) >= 1000) ? 0
  : (Number.isInteger(v) ? 0 : 2);

/* --------------------------------------------------------- düzenleme */
function duzenle(td, n, d, yenile, ilkHarf = null) {
  if (td.querySelector("input")) return;
  const eski = V.deger(n.kod, d.yil, d.ay);
  const g = el("input.duzen", { type:"text",
    value: ilkHarf !== null ? ilkHarf
         : (eski === null ? "" : String(eski).replace(".", ",")) });
  bosalt(td); td.append(g);
  g.focus();
  if (ilkHarf === null) g.select();

  let bitti = false;
  const kaydet = (sonraki = null) => {
    if (bitti) return; bitti = true;
    const metin = g.value.trim();
    let yeniDeger = null, hata = null;
    if (metin !== "") {
      const r = sayiOku(metin);
      if (r.hata) hata = r.hata; else yeniDeger = r.deger;
    }
    if (hata) { bildir(hata, "kritik"); bitti = false; g.focus(); return; }
    const degisti = (eski === null ? metin !== "" : yeniDeger !== eski);
    if (degisti) {
      const b = yeniDeger === null ? [] : dogrula(n.kod, d.yil, d.ay, yeniDeger);
      const engel = b.find(x => x.seviye === ENGEL);
      if (engel) {
        bildir(`${engel.mesaj} — yazılmadı`, "kritik");
        bitti = false; g.focus(); return;
      }
      V.degerYaz(n.kod, d.yil, d.ay, yeniDeger, { k:"girildi" });
    }
    yenile(sonraki || { kod:n.kod, d:donemKod(d.yil, d.ay) });
  };

  g.addEventListener("blur", () => kaydet());
  g.addEventListener("keydown", ev => {
    if (ev.key === "Enter") { ev.preventDefault(); kaydet(komsu(td, 0, 1)); }
    else if (ev.key === "Tab") { ev.preventDefault(); kaydet(komsu(td, ev.shiftKey ? -1 : 1, 0)); }
    else if (ev.key === "Escape") { ev.preventDefault(); bitti = true; yenile({ kod:n.kod, d:donemKod(d.yil, d.ay) }); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); kaydet(komsu(td, 0, -1)); }
    else if (ev.key === "ArrowDown") { ev.preventDefault(); kaydet(komsu(td, 0, 1)); }
  });
}

/** Komşu hücrenin kimliği — yeniden çizimden sonra oraya odaklanılır */
function komsu(td, dx, dy) {
  const tr = td.parentElement;
  const hucreler = [...tr.querySelectorAll("td.hucre")];
  const i = hucreler.indexOf(td);
  if (dx) {
    const h = hucreler[i + dx];
    return h ? { kod:h.dataset.kod, d:h.dataset.d } : null;
  }
  const satirlar = [...tr.parentElement.children];
  const j = satirlar.indexOf(tr) + dy;
  const hedefSatir = satirlar[j];
  if (!hedefSatir) return null;
  const h = [...hedefSatir.querySelectorAll("td.hucre")][i];
  return h ? { kod:h.dataset.kod, d:h.dataset.d } : null;
}

function yonTusu(ev, td) {
  const yon = { ArrowLeft:[-1,0], ArrowRight:[1,0], ArrowUp:[0,-1], ArrowDown:[0,1] }[ev.key];
  if (!yon) return;
  ev.preventDefault();
  const h = komsu(td, yon[0], yon[1]);
  if (h) odakla(h);
}

/** Yeniden çizimden sonra bir hücreye odaklanmak için */
export function odakla(hedef) {
  if (!hedef) return;
  const td = document.querySelector(
    `td.hucre[data-kod="${hedef.kod}"][data-d="${hedef.d}"]`);
  if (td) { td.focus(); td.scrollIntoView({ block:"nearest", inline:"nearest" }); }
}

/* ----------------------------------------------------------- ipuçları */
function hucreIpucu(n, d, kayit, b) {
  if (!b && !kayit?.not && (!kayit || kayit.k === "girildi")) return null;
  const g = el("div", {},
    el("b", { metin:`${n.ad} · ${donemAd(d.yil, d.ay)}` }));
  if (kayit && kayit.k && kayit.k !== "girildi")
    g.append(el("div.satir", {}, el("b", { metin:kayit.k === "tahmin" ? "TAHMİN" : "DÜZELTİLDİ" }),
      kayit.k === "tahmin" ? "Bu değer ölçülmedi, tahmin edildi (İ-4)."
                           : "Bu değer elle düzeltildi."));
  if (kayit?.not) g.append(el("div.satir", { metin:kayit.not }));
  for (const x of (b?.liste || []))
    g.append(el("div.satir", {},
      el("b", { metin:(x.seviye === ENGEL ? "ENGEL" : "UYARI") + " · " +
        (BULGU_TURLERI[x.tur] || "denetim") }), x.mesaj));
  return g;
}

function turetilmisIpucu(n, d, r) {
  const g = el("div", {}, el("b", { metin:`${n.ad} · ${donemAd(d.yil, d.ay)}` }),
    el("div", { metin:"Bu sütun hesaplanır, elle girilmez (İ-1)." }));
  if (n.formul) g.append(el("div.satir", {}, "Formül: ", el("code", { metin:n.formul })));
  if (r.eksik) g.append(el("div.satir", {}, el("b", { metin:"ÜRETİLEMEDİ " }), r.eksik));
  else if (r.veriYok) g.append(el("div.satir", {}, el("b", { metin:"HAM VERİ BOŞ " }), r.sebep || ""));
  return g;
}

/* ------------------------------------------------------ bulgu haritası */
/** Yalnız DOLU hücreler için doğrulama çalıştırılır (boş hücrenin bulgusu olmaz) */
function bulguHaritasi(don, sut) {
  const harita = new Map();
  const kodlar = new Set(sut.filter(n => n.veri_tipi === "olculen" || n.veri_tipi === "tahmini")
    .map(n => n.kod));
  const donKod = new Set(don.map(d => donemKod(d.yil, d.ay)));
  for (const kayit of V.durum.degerler) {
    if (!kodlar.has(kayit.n)) continue;
    const dk = donemKod(kayit.y, kayit.a);
    if (!donKod.has(dk)) continue;
    const b = dogrula(kayit.n, kayit.y, kayit.a, kayit.v);
    if (!b.length) continue;
    harita.set(`${kayit.n}|${dk}`, {
      liste:b, engel:b.some(x => x.seviye === ENGEL), uyar:b.some(x => x.seviye !== ENGEL) });
  }
  return harita;
}

/* --------------------------------------------------------- alt bilgi */
function altBilgi(k, bulgular, don, sut) {
  let engel = 0, uyar = 0;
  const tur = new Map();
  for (const b of bulgular.values()) {
    if (b.engel) engel++; else uyar++;
    for (const x of b.liste) tur.set(x.tur || "diger", (tur.get(x.tur || "diger") || 0) + 1);
  }
  // kayıt alanları n/y/a/v; dönem nesnesi yil/ay — ikisi karıştırılmaz
  const donKod = new Set(don.map(d => donemKod(d.yil, d.ay)));
  const sutunKod = new Set(sut.map(n => n.kod));
  const dolu = V.durum.degerler.filter(x =>
    sutunKod.has(x.n) && donKod.has(donemKod(x.y, x.a))).length;

  k.append(el("div.satir", { stil:{ marginTop:"10px", gap:"18px", fontSize:"12px",
      flexWrap:"wrap", alignItems:"center" } },
    el("span.sessiz", { metin:`${say(dolu)} dolu hücre` }),
    engel ? el("span", {}, el("span.rozet.kritik", { metin:"engel" }), ` ${engel} hücre`) : null,
    uyar ? el("span", {}, el("span.rozet.dikkat", { metin:"uyarı" }), ` ${uyar} hücre`) : null,
    el("span.sessiz", { metin:"⬛ hesaplanan sütun" }),
    el("span.sessiz", { metin:"▌ sol kenar çizgisi: tahmin / düzeltildi" })));

  if (tur.size)
    k.append(el("p.mini.sessiz", { metin:"Bulgu türleri: " +
      [...tur.entries()].sort((a, b) => b[1] - a[1])
        .map(([t, s]) => `${BULGU_TURLERI[t] || t} (${s})`).join(" · ") }));
}

/* ------------------------------------------------- satır / sütun ekleme */
function donemEkle(yenile) {
  const ar = V.veriAraligi();
  const son = ar ? donemKaydir(ar.son.yil, ar.son.ay, 1)
                 : { yil:new Date().getFullYear(), ay:1 };
  const ay = el("select");
  AYLAR.forEach((a, i) => ay.append(el("option", { value:i + 1, metin:a, selected:son.ay === i + 1 })));
  const yil = el("input", { type:"number", value:son.yil, min:1990, max:2100, stil:{ width:"100px" } });
  const f = el("div", {},
    el("p.kucuk.sessiz", { metin:
      "Yeni bir dönem satırı açılır. Satır boş kalsa bile tabloda durur; " +
      "hücrelerine değer girdikçe dolar." }),
    el("div.alan", {}, el("label", { metin:"Dönem" }),
      el("div.satir", { stil:{ gap:"6px" } }, ay, yil)));
  onayla("Dönem (satır) ekle", f, "Ekle").then(ok => {
    if (!ok) return;
    const kod = donemKod(+yil.value, +ay.value);
    V.durum.ayarlar.ek_donemler ||= [];
    if (!V.durum.ayarlar.ek_donemler.includes(kod)) V.durum.ayarlar.ek_donemler.push(kod);
    if (durum.yil !== null) durum.yil = +yil.value;
    V.degisti("donem"); bildir(`${donemAd(+yil.value, +ay.value)} satırı eklendi`);
    yenile();
  });
}

let sutunEkleyici = null;
/** Tanımlar ekranındaki nokta formunu ödünç alır (tek tanım yeri) */
export function sutunEkleyiciKur(fn) { sutunEkleyici = fn; }

function sutunEkle(yenile) {
  if (sutunEkleyici) return sutunEkleyici(() => yenile());
  bildir("Ölçüm noktası formu yüklenemedi", "kritik");
}
