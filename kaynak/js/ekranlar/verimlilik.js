/* ekranlar/verimlilik.js — Ekran 9: Dönüşüm Verimliliği (El Kitabı 9.10)
   "Dönüşüm ekipmanım sağlıklı mı?"
   Excel'de bu hiç hesaplanmıyordu. 2025 vakasında (8.8) bozulmanın
   NEDENİNİ bulan ekran budur. */

import { el, $, bosalt, say, kisa, yuzde, uyari, bildir, onayla, bosDurum, tablo,
         donemAraligi, AYLAR } from "../ortak.js";
import * as V from "../veri.js";
import { varlik } from "../model.js";
import * as H from "../hesap.js";
import { sonEnerjiDonemi } from "../hesaplanan.js";
import * as G from "../grafik.js";

let secilenYil = null;

export function ekranVerimlilik(k) {
  const ar = V.veriAraligi();
  k.append(el("div.sayfa-basi", {},
    el("h1", { metin:"Dönüşüm Verimliliği" }),
    el("p", { metin:"Kojenerasyon ve kazanlar yakıtı ne verimle faydalı enerjiye çeviriyor — ve bu verim değişti mi?" })));

  if (!ar) return k.append(bosDurum("Henüz veri yok",
    "Önce Veri Aktarma ekranından verinizi alın.",
    el("button.dugme.ana", { metin:"Veri Aktarma'ya git", onclick:() => { location.hash = "e3"; } })));

  const varliklar = H.donusumVarliklari();
  if (!varliklar.length) return k.append(bosDurum("Dönüşüm varlığı tanımlı değil",
    "Bu ekran, yakıt tüketen ve karşılığında elektrik, buhar veya sıcak su üreten " +
    "varlıkları kendiliğinden bulur. Tanımlar ekranında bir varlığa hem `satın alınan` " +
    "rolünde kWh yakıt noktası hem de `tesis içi üretim` / `ara enerji` noktası " +
    "tanımlandığında burada görünür."));

  if (secilenYil === null) secilenYil = (sonEnerjiDonemi() || ar.son).yil;
  yilSecici(k, ar);

  const d  = yilDonemleri(secilenYil);
  const dO = yilDonemleri(secilenYil - 1);
  const satirlar = varliklar.map(x => {
    const s  = H.donusumVerimiAralik(x.varlik.kod, d);
    const so = H.donusumVerimiAralik(x.varlik.kod, dO);
    return { ...x, ad:x.varlik.ad, kod:x.varlik.kod, s, so,
             puanFark: (s?.toplamVerim != null && so?.toplamVerim != null)
                        ? (s.toplamVerim - so.toplamVerim) * 100 : null };
  });
  const calisan = satirlar.filter(r => r.s);
  if (!calisan.length) return k.append(bosDurum(`${secilenYil} yılında dönüşüm verisi yok`,
    "Bu yılda hiçbir dönüşüm ekipmanı için yakıt veya üretim kaydı bulunmuyor. Yukarıdan başka bir yıl seçin."));

  ozet(k, calisan, satirlar);
  kartlar(k, satirlar);
  verimTrendi(k, varliklar);
  yakitDagilimi(k, calisan);
  karsilastirma(k, calisan);
  verimTablosu(k, satirlar);
}

const yenile = () => { const k = bosalt($("#icerik")); ekranVerimlilik(k); };
const yilDonemleri = y => donemAraligi(y, 1, y, 12);

function yilSecici(k, ar) {
  const s = el("select", { onchange:e => { secilenYil = +e.target.value; yenile(); } });
  for (let y = ar.son.yil; y >= ar.ilk.yil; y--)
    s.append(el("option", { value:y, metin:y, selected:secilenYil === y }));
  k.append(el("div.kart", { stil:{ padding:"12px 16px" } },
    el("div.satir", { stil:{ alignItems:"flex-end" } },
      el("div.alan", { stil:{ margin:"0" } }, el("label", { metin:"Yıl" }), s),
      el("p.mini.sessiz", { stil:{ margin:"0 0 6px" },
        metin:`Karşılaştırma dönemi: ${secilenYil - 1}. Verim, aylık oranların ortalaması değil, yıl toplamlarının oranıdır.` }))));
}

/* ------------------------------------------------- yakıtın birim fiyatı */
/** Verim kaybının TL karşılığı için yakıtın TL/kWh fiyatı (K-12) */
function yakitFiyatiKwh(enerjiTuru, donemler) {
  for (const kalem of H.faturaKalemleri()) {
    if (kalem.enerjiTuru !== enerjiTuru) continue;
    const f = H.birimFiyatKwh(kalem, donemler);
    if (f !== null) return { fiyat:f, kalem };
  }
  return null;
}

/* ------------------------------------------------------------- özet */
function ozet(k, calisan, hepsi) {
  const yakit = calisan.reduce((t, r) => t + r.s.yakit, 0);
  const faydali = calisan.reduce((t, r) => t + r.s.faydali, 0);
  const verim = yakit ? faydali / yakit : null;

  // BENZER KÜME: iki dönemde de çalışan ekipmanlar. Karşılaştırma yalnız
  // bunlar üzerinden yapılır — yoksa ekipman kümesinin değişmesi, verim
  // değişmiş gibi okunur. 2025'te gaz motorları durdu; karma toplam bu
  // yüzden "iyileşmiş" görünür, oysa çalışan ekipmanın verimi düşmüştür.
  const ortak = hepsi.filter(r => r.s && r.so && r.s.toplamVerim != null && r.so.toplamVerim != null);

  const giren = hepsi.filter(r => r.s && !r.so).map(r => r.ad);
  const cikan = hepsi.filter(r => !r.s && r.so).map(r => r.ad);

  const kutu = (ad, v, birim, alt) => el("div.kart", { stil:{ flex:"1 1 190px", margin:"0" } },
    el("div.mini.sessiz", { metin:ad }),
    el("div", { stil:{ fontSize:"21px", fontWeight:"600", margin:"4px 0 2px",
      fontVariantNumeric:"tabular-nums" } }, v,
      el("span", { stil:{ fontSize:"12px", fontWeight:"400", color:"var(--ink-mut)",
        marginLeft:"5px" }, metin:birim })),
    alt ? el("div.mini.sessiz", { metin:alt }) : null);

  k.append(el("div.satir", { stil:{ marginBottom:"14px" } },
    kutu("Yakıt girdisi", say(yakit, 0), "kWh", `${calisan.length} çalışan ekipman · ${secilenYil}`),
    kutu("Faydalı enerji", say(faydali, 0), "kWh", "elektrik + buhar + sıcak su"),
    kutu("Toplam verim (bu yılın kümesi)", verim === null ? "—" : yuzde(verim * 100, 1), "",
      calisan.some(r => r.s.imkansiz)
        ? "⚠ tutarsız veri içeriyor — aşağıdaki uyarıyı okumadan kullanılamaz"
        : "farklı ekipman tiplerinin karışımı — yıllar arası kıyaslanmaz"),
    kutu("Dönüşüm kaybı", say(yakit - faydali, 0), "kWh",
      verim === null ? "" : yuzde((1 - verim) * 100, 1))));

  // Ekipman kümesi değiştiyse karma toplamın yıllar arası okunması YANLIŞTIR.
  if (giren.length || cikan.length)
    k.append(uyari("dikkat",
      el("b", { metin:`Ekipman kümesi ${secilenYil - 1} ile ${secilenYil} arasında değişti. ` }),
      (cikan.length ? `Devreden çıkan: ${cikan.join(", ")}. ` : "") +
      (giren.length ? `Devreye giren: ${giren.join(", ")}. ` : "") +
      "Kazanın verimi türbinin veriminden yapısal olarak yüksektir; küme değişince " +
      "karma toplam, hiçbir ekipmanın verimi değişmese bile oynar. Bu yüzden yıllar " +
      "arası karşılaştırma aşağıda yalnız iki yılda da çalışan ekipmanlar üzerinden yapılır."));

  // TEK BİR BİRLEŞİK VERİM YÜZDESİ YILLAR ARASI KIYASLANMAZ.
  // Aynı ekipman kümesinde bile yükün ekipmanlar arasında dağılımı değişir:
  // kazanın verimi türbinden yüksek olduğu için yük kazana kaydığında
  // ağırlıklı ortalama YÜKSELİR, her ekipmanın kendi verimi düşse bile.
  // Bu yüzden karşılaştırma ekipman ekipman yapılır ve toplanan şey yüzde
  // değil, KAÇINILABİLİR YAKITTIR (kWh) — bu büyüklük karışımdan bağımsızdır.
  // İMKÂNSIZ VERİM: faydalı enerji yakıttan büyük. Performans olarak
  // okunamaz; karşılaştırmadan çıkarılır ve nedeni açıkça söylenir.
  const imkansiz = hepsi.filter(r => r.s?.imkansiz || r.so?.imkansiz);
  if (imkansiz.length) tutarsizlikUyarisi(k, imkansiz, hepsi);
  atanmamisUyarisi(k);

  const saglam = ortak.filter(r => !r.s.imkansiz && !r.so.imkansiz);
  if (saglam.length) {
    const kotu = saglam.filter(r => r.puanFark < -0.5);
    const iyi  = saglam.filter(r => r.puanFark > 0.5);
    const kacinilabilir = saglam.reduce((t2, r) =>
      t2 + (r.so.toplamVerim - r.s.toplamVerim) * r.s.yakit, 0);
    const fy = yakitFiyatiKwh(saglam[0].noktalar.yakit.enerji_turu, yilDonemleri(secilenYil));
    const tur = kacinilabilir > 0 ? (kotu.length === saglam.length ? "ciddi" : "dikkat")
              : kacinilabilir < 0 ? "iyi" : "bilgi";
    k.append(uyari(tur,
      el("b", { metin: saglam.length === 1
        ? `İki yılda da çalışan ve verisi tutarlı tek ekipman ${saglam[0].ad}: ` +
          `verim ${kotu.length ? "düştü" : iyi.length ? "iyileşti" : "değişmedi"}. `
        : `İki yılda da çalışan ve verisi tutarlı ${saglam.length} ekipmandan ` +
          `${kotu.length} tanesinde verim düştü, ${iyi.length} tanesinde iyileşti. ` }),
      (kacinilabilir > 0
        ? `${secilenYil - 1} verimleri korunsaydı ${say(kacinilabilir, 0)} kWh yakıt ` +
          "yakılmayacaktı"
        : kacinilabilir < 0
        ? `${secilenYil - 1} verimleriyle ${say(Math.abs(kacinilabilir), 0)} kWh daha fazla ` +
          "yakıt gerekecekti"
        : "yakıt karşılığı değişmedi") +
      (fy && kacinilabilir ? ` ≈ ${say(Math.abs(kacinilabilir) * fy.fiyat, 0)} TL` : "") + ". " +
      "Bu sayı her ekipmanın kendi yakıtı üzerinden toplanır. Tek bir birleşik " +
      "verim yüzdesi yıllar arası okunamaz, çünkü yük ekipmanlar arasında yer değiştirdikçe " +
      "hiçbir ekipmanın verimi değişmese bile oynar. Ekipman ekipman fark aşağıdaki kartlarda." +
      (imkansiz.length ? ` Verisi tutarsız ${imkansiz.length} ekipman bu toplama girmedi.` : "")));
  } else {
    k.append(uyari("dikkat",
      el("b", { metin:"Yıllar arası verim karşılaştırması yapılamıyor. " }),
      ortak.length
        ? `${secilenYil - 1} ve ${secilenYil} yıllarında birlikte çalışan ekipmanların ` +
          "hepsinde veri tutarsız (faydalı enerji yakıttan büyük). Karşılaştırma, veri " +
          "düzeltilmeden anlam taşımaz."
        : `${secilenYil - 1} ve ${secilenYil} yıllarında birlikte çalışan hiçbir ekipman yok.`));
  }

  katsayiUyarisi(k, ortak.length ? ortak : calisan);

  k.append(uyari("bilgi",
    el("b", { metin:"Bu ekranın sayıları fabrika toplam enerjisine eklenmez. " }),
    "Dönüşüm ekipmanlarının yakıtı istasyon ölçümünün alt kırılımıdır, ürettikleri " +
    "elektrik ve buhar ise ara enerjidir (7.1). Burada ölçülen tek şey, aynı yakıttan " +
    "ne kadar faydalı enerji çıkarıldığıdır."));
}

/* ----------------------------------------------------------- kartlar */
function kartlar(k, satirlar) {
  const g = el("div", { stil:{ display:"grid", gap:"12px",
    gridTemplateColumns:"repeat(auto-fill, minmax(330px, 1fr))", marginBottom:"14px" } });

  for (const r of satirlar) {
    const kart = el("div.kart", { stil:{ margin:"0" } });
    const v = r.varlik;
    const durumEtiketi = v.devreden_cikis
      ? el("span.rozet.dikkat", { metin:`durduruldu · ${v.devreden_cikis}` })
      : r.s ? el("span.rozet", { metin:`çalışıyor · ${r.s.calisan} ay` })
            : el("span.rozet.dikkat", { metin:"bu yıl veri yok" });
    kart.append(el("div.satir", { stil:{ justifyContent:"space-between", alignItems:"baseline" } },
      el("h3", { stil:{ margin:"0" }, metin:r.ad }), durumEtiketi));
    if (v.devreye_giris)
      kart.append(el("div.mini.sessiz", { metin:`Devreye giriş: ${v.devreye_giris}` }));

    if (!r.s) {
      kart.append(el("p.sessiz.mini", { stil:{ marginTop:"10px" },
        metin:`${secilenYil} yılında bu ekipman için yakıt veya üretim kaydı yok.` }));
      if (v.not) kart.append(el("p.mini.sessiz", { metin:v.not }));
      g.append(kart); continue;
    }
    if (r.s.tutarsiz) {
      kart.append(uyari("ciddi", el("b", { metin:"Yakıt kaydı yok, üretim kaydı var. " }),
        "Verim hesaplanamaz — Veri Denetimi ekranına bakın."));
      g.append(kart); continue;
    }

    const kalem = (ad, v2, birim) => el("div.satir", { stil:{ justifyContent:"space-between",
      gap:"10px", padding:"3px 0", fontSize:"13px" } },
      el("span.sessiz", { metin:ad }),
      el("span.sayi", { metin:`${say(v2, 0)} ${birim}` }));
    kart.append(el("div", { stil:{ marginTop:"8px",
      borderTop:"1px solid var(--kilavuz)", paddingTop:"6px" } },
      kalem("Yakıt girdisi", r.s.yakit, "kWh"),
      r.noktalar.elk   ? kalem("Elektrik üretimi", r.s.elektrik, "kWh") : null,
      r.noktalar.buhar ? kalem("Buhar üretimi", r.s.buhar, "kWh") : null,
      r.noktalar.ssu   ? kalem("Sıcak su üretimi", r.s.sicakSu, "kWh") : null));

    // yukariIyi=false olan satırda (kayıp) artış KÖTÜDÜR; ok yönü ile renk
    // birbirinden ayrılır, yoksa artan kayıp yeşil görünür.
    const oran = (ad, deg, oncekiDeg, yukariIyi = true) => {
      const p = (deg != null && oncekiDeg != null) ? (deg - oncekiDeg) * 100 : null;
      const iyi = p === null ? null : (yukariIyi ? p > 0 : p < 0);
      return el("div.satir", { stil:{ justifyContent:"space-between", gap:"10px",
        padding:"3px 0", fontSize:"13px" } },
        el("span.sessiz", { metin:ad }),
        el("span", {}, el("b.sayi", { metin:deg == null ? "—" : yuzde(deg * 100, 1) }),
          p === null ? null : el("span.mini", {
            stil:{ marginLeft:"7px", color:Math.abs(p) < 0.05 ? "var(--ink-mut)"
              : iyi ? "var(--iyi)" : "var(--ciddi)" },
            metin:`${p < 0 ? "▼" : "▲"} ${say(Math.abs(p), 1)} puan` })));
    };
    kart.append(el("div", { stil:{ marginTop:"6px",
      borderTop:"1px solid var(--kilavuz)", paddingTop:"6px" } },
      r.noktalar.elk ? oran("Elektrik verimi", r.s.elektrikVerimi, r.so?.elektrikVerimi) : null,
      (r.noktalar.buhar || r.noktalar.ssu) ? oran("Isı verimi", r.s.isiVerimi, r.so?.isiVerimi) : null,
      oran("Toplam verim", r.s.toplamVerim, r.so?.toplamVerim),
      oran("Kayıp", r.s.kayip, r.so?.kayip, false)));

    if (r.s.imkansiz) {
      kart.append(uyari("ciddi",
        el("b", { metin:`Toplam verim %${say(r.s.toplamVerim * 100, 1)} — fiziksel olarak imkânsız. ` }),
        `Faydalı enerji (${say(r.s.faydali, 0)} kWh) bu ekipmana atanmış yakıttan ` +
        `(${say(r.s.yakit, 0)} kWh) büyük. Eksik olan ${say(r.s.faydali - r.s.yakit, 0)} kWh ` +
        "en az bu kadar yakıt daha yakıldığı anlamına gelir. Bu bir performans sonucu " +
        "değil, yakıt ölçümünün ekipmana yanlış dağıtıldığının işaretidir (A-05). " +
        "Bu ekipman yıllar arası karşılaştırmaya alınmaz."));
    } else if (r.puanFark !== null && r.puanFark < -0.5 && !r.so?.imkansiz) {
      const kayip = (r.so.toplamVerim - r.s.toplamVerim) * r.s.yakit;
      const fy = yakitFiyatiKwh(r.noktalar.yakit.enerji_turu, yilDonemleri(secilenYil));
      kart.append(uyari(r.puanFark < -3 ? "ciddi" : "dikkat",
        `Verim ${secilenYil - 1}'e göre ${say(Math.abs(r.puanFark), 1)} puan düştü. ` +
        `${kisa(r.s.yakit, 1)} kWh yakıt üzerinden ≈ ${kisa(kayip, 1)} kWh/yıl kayıp` +
        (fy ? ` ≈ ${kisa(kayip * fy.fiyat, 1)} TL` : "") + "."));
    }
    if (v.not) kart.append(el("p.mini.sessiz", { stil:{ marginTop:"8px" }, metin:v.not }));

    kart.append(el("div", { stil:{ marginTop:"8px" } },
      el("button.dugme.kucuk", { metin:v.not ? "Notu düzenle" : "+ Not ekle",
        onclick:() => notDuzenle(v.kod) })));
    g.append(kart);
  }
  k.append(g);
}

function notDuzenle(varlikKod) {
  const v = varlik(varlikKod);
  const a = el("textarea", { rows:4, stil:{ width:"100%" } });
  a.value = v.not || "";
  const f = el("div", {}, el("div.alan", {},
    el("label", { metin:"Not — bakım, arıza, devreden çıkarma gerekçesi" }), a,
    el("div.mini.sessiz", { metin:"Not varlığa yazılır ve raporlarda bu ekipmanın yanında görünür." })));
  onayla(`${v.ad} — not`, f, "Kaydet").then(ok => {
    if (!ok) return;
    v.not = a.value.trim();
    V.degisti("varlik"); yenile(); bildir("Not kaydedildi");
  });
}

/* --------------------------------------------------- G1 verim trendi */
function verimTrendi(k, varliklar) {
  const aylar = yilDonemleri(secilenYil);
  const seriler = [];
  for (const x of varliklar) {
    const deg = aylar.map(a => {
      const r = H.donusumVerimiAralik(x.varlik.kod, [a]);
      return r && r.toplamVerim != null ? r.toplamVerim * 100 : null;
    });
    if (deg.some(v => v !== null)) seriler.push({ ad:x.varlik.ad, degerler:deg });
  }
  if (!seriler.length) return;
  const kart = el("div.kart", {}, el("h2", { metin:`Toplam verim trendi · ${secilenYil}` }),
    el("p.mini.sessiz", { metin:
      "Boşluk, o ay ekipmanın çalışmadığı (yakıt yakmadığı) anlamına gelir — sıfır verim değildir." }));
  k.append(kart);
  // 8'den fazla seri kategorik renk düzenini bozar (5.7.2)
  G.cizgi(kart, { seriler:seriler.slice(0, 8), etiketler:aylar.map(a => AYLAR[a.ay - 1].slice(0, 3)),
                  birim:"%", ondalik:1, boy:300 });
  if (seriler.length > 8)
    kart.append(el("p.mini.sessiz", { metin:`${seriler.length - 8} ekipman grafiğe sığmadı; tabloya bakın.` }));
}

/* ----------------------------------------- G2 yakıt → faydalı dağılımı */
function yakitDagilimi(k, calisan) {
  const et = calisan.map(r => r.ad);
  const seriler = [
    { ad:"Elektrik", degerler:calisan.map(r => r.s.elektrik) },
    { ad:"Buhar",    degerler:calisan.map(r => r.s.buhar) },
    { ad:"Sıcak su", degerler:calisan.map(r => r.s.sicakSu) },
    { ad:"Kayıp",    degerler:calisan.map(r => Math.max(0, r.s.yakit - r.s.faydali)),
      renk:"var(--ink-mut)" },
  ].filter(s => s.degerler.some(v => v > 0));
  const kart = el("div.kart", {}, el("h2", { metin:`Yakıt nereye gitti · ${secilenYil}` }),
    el("p.mini.sessiz", { metin:
      "Her sütunun tamamı o ekipmanın yaktığı yakıttır; kayıp payı üzerine eklenmez, içindedir (6.7)." }));
  k.append(kart);
  G.sutun(kart, { seriler, etiketler:et, birim:"kWh", yigili:true, boy:300 });
}

/* ------------------------------------------- G3 varlık karşılaştırması */
function karsilastirma(k, calisan) {
  const sirali = [...calisan].filter(r => r.s.toplamVerim != null)
    .sort((a, b) => b.s.toplamVerim - a.s.toplamVerim);
  if (!sirali.length) return;
  const kart = el("div.kart", {}, el("h2", { metin:"Aynı işi hangi ekipman daha verimli yapıyor?" }),
    el("p.mini.sessiz", { metin:
      "Yük dağıtım kararının sayısal karşılığı: yakıtı en verimli çeviren ekipmana yük " +
      "kaydırmak, hiç yatırım yapmadan tasarruf demektir (9.10)." }));
  const enb = sirali[0].s.toplamVerim;
  kart.append(tablo([
    { ad:"Ekipman", anahtar:"ad" },
    { ad:"", deger:r => el("div.satir", { stil:{ gap:"8px", alignItems:"center" } },
        G.oranCubugu(r.s.toplamVerim / enb, { en:150 }),
        el("span.sayi.mini", { metin:yuzde(r.s.toplamVerim * 100, 1) })) },
    { ad:"Yakıt (kWh)", sayi:true, deger:r => r.s.yakit },
    { ad:"Faydalı (kWh)", sayi:true, deger:r => r.s.faydali },
    { ad:"Pay", deger:r => yuzde(r.s.yakit / sirali.reduce((t, x) => t + x.s.yakit, 0) * 100, 1) },
  ], sirali));
  k.append(kart);
}

/* --------------------------------------------------- T1 verim tablosu */
function verimTablosu(k, satirlar) {
  const kart = el("div.kart", {}, el("h2", { metin:"Verim tablosu" }),
    el("p.mini.sessiz", { metin:
      "Durum ikonu, mutlak bir verim eşiğine değil önceki yıla göre değişime bakar: " +
      "! verisi tutarsız (faydalı enerji > yakıt) · ✕ 3 puandan fazla düşüş · " +
      "⚠ 0,5–3 puan düşüş · ✓ iyileşme. " +
      "Üretici katalog verisiyle mutlak karşılaştırma ileride eklenecektir (9.10)." }));
  const ikon = r => (r.s?.imkansiz || r.so?.imkansiz) ? "!"
    : r.puanFark === null ? ""
    : r.puanFark < -3 ? "✕" : r.puanFark < -0.5 ? "⚠" : r.puanFark > 0.5 ? "✓" : "–";
  const renkli = (v, ond = 1) => v == null ? "—" : yuzde(v * 100, ond);
  kart.append(tablo([
    { ad:"", baslik:r => (r.s?.imkansiz || r.so?.imkansiz)
        ? "Veri tutarsız: faydalı enerji yakıttan büyük" : "",
      deger:r => el("span", { stil:{ fontWeight:"600",
        color: (r.s?.imkansiz || r.so?.imkansiz) ? "var(--ciddi)"
        : r.puanFark === null ? "var(--ink-mut)"
        : r.puanFark < -0.5 ? "var(--ciddi)" : r.puanFark > 0.5 ? "var(--iyi)" : "var(--ink-mut)" },
        metin:ikon(r) }) },
    { ad:"Ekipman", anahtar:"ad" },
    { ad:`Yakıt ${secilenYil}`, sayi:true, deger:r => r.s?.yakit ?? null },
    { ad:"Elektrik verimi", deger:r => renkli(r.s?.elektrikVerimi) },
    { ad:"Isı verimi", deger:r => renkli(r.s?.isiVerimi) },
    { ad:`Toplam verim ${secilenYil}`, deger:r => renkli(r.s?.toplamVerim) },
    { ad:`Toplam verim ${secilenYil - 1}`, deger:r => renkli(r.so?.toplamVerim) },
    { ad:"Fark (puan)", deger:r => r.puanFark === null ? "—"
        : el("span", { stil:{ color:r.puanFark < 0 ? "var(--ciddi)" : "var(--iyi)" },
            metin:(r.puanFark > 0 ? "+" : "−") + say(Math.abs(r.puanFark), 1) }) },
    { ad:"Kayıp (kWh)", sayi:true, deger:r => r.s?.kayipKwh ?? null },
  ], satirlar));
  k.append(kart);
}

/* ------------------------------------ katsayı değişimi uyarısı (İ-5, S12) */
/**
 * Buhar kg → kWh katsayısı karşılaştırılan iki yılda farklıysa, verim
 * değişiminin bir kısmı fizik değil VARSAYIM değişimidir. Bu ayrım
 * gösterilmezse ekran yanıltır.
 */
function katsayiUyarisi(k, ekipman) {
  const kk = H.katsayiKarsilastir("BUH", "kg", "kWh",
    { yil:secilenYil - 1, ay:12 }, { yil:secilenYil, ay:12 });
  if (kk.bilinmiyor || kk.ayni) return;

  // Etkiyi ekipman bazında ver: kg aynı kalırken raporlanan kWh değişir.
  const etki = ekipman.filter(r => r.s && r.s.buhar > 0 && r.s.yakit)
    .map(r => { const d = H.verimKatsayiDuzeltmesi(r.s, kk.oran);
      return { ad:r.ad, kwh:d.faydali - r.s.faydali,
               puan:(d.toplamVerim - r.s.toplamVerim) * 100 }; })
    .sort((a, b) => b.kwh - a.kwh);
  const toplamKwh = etki.reduce((t2, x) => t2 + x.kwh, 0);

  k.append(uyari("dikkat",
    el("b", { metin:`Buhar kg → kWh katsayısı ${secilenYil - 1} ile ${secilenYil} arasında değişti: ` }),
    `${say(kk.a.katsayi, 6)} → ${say(kk.b.katsayi, 6)} kWh/kg ` +
    `(${say(kk.a.katsayi * 860, 0)} → ${say(kk.b.katsayi * 860, 0)} kcal/kg entalpi varsayımı). ` +
    (etki.length
      ? `Aynı buhar kilogramı ${say(Math.abs(toplamKwh), 0)} kWh daha ` +
        `${toplamKwh > 0 ? "az" : "çok"} raporlanıyor: ` +
        etki.slice(0, 3).map(x => `${x.ad} ${x.puan > 0 ? "−" : "+"}${say(Math.abs(x.puan), 1)} puan`).join(", ") +
        ". Verim düşüşünün bu kadarı fizik değil, VARSAYIM değişimidir. "
      : "") +
    "Hangi entalpinin doğru olduğu ve değişimin gerekçesi teyit bekliyor (A-08). " +
    "Katsayının hangi dönemde ne olduğu Tanımlar › Katsayılar ekranında görülür (6.6, İ-5)."));
}

/* ------------------------- imkânsız verim: veri sorunu, performans değil */
function tutarsizlikUyarisi(k, imkansiz, hepsi) {
  const ad = imkansiz.map(r => {
    const s = r.s?.imkansiz ? r.s : r.so;
    const yil = r.s?.imkansiz ? secilenYil : secilenYil - 1;
    return `${r.ad} (${yil}: %${say(s.toplamVerim * 100, 0)})`;
  }).join(", ");
  const eksik = imkansiz.reduce((t2, r) =>
    t2 + (r.s?.imkansiz ? r.s.faydali - r.s.yakit : 0), 0);
  k.append(uyari("ciddi",
    el("b", { metin:`${imkansiz.length} ekipmanda faydalı enerji yakıttan büyük: ${ad}. ` }),
    (eksik > 0 ? `${secilenYil} yılında en az ${say(eksik, 0)} kWh yakıt ölçülmemiş ya da ` +
      "başka bir ekipmana yazılmış görünüyor. " : "") +
    "Verim %100'ü aşamaz; bu sayılar performans olarak okunamaz. " +
    "En olası neden, istasyon sayacındaki gazın ekipmanlara doğru dağıtılmamış olmasıdır " +
    "(A-05). Veri düzeltilene kadar bu ekipmanların verim değişimi yorumlanmamalıdır."));
}

/* ------------------- hiçbir ekipmana atanmamış yakıt (6.7, A-05) */
function atanmamisUyarisi(k) {
  const d = yilDonemleri(secilenYil);
  for (const a of H.atanmamisYakit(d)) {
    if (!a.satinAlinan || a.oran === null) continue;
    if (Math.abs(a.oran) < 0.02) continue;          // %2 altı ölçüm gürültüsü
    const tur = Math.abs(a.oran) > 0.1 ? "dikkat" : "bilgi";
    k.append(uyari(tur,
      el("b", { metin:a.atanmamis > 0
        ? `Satın alınan yakıtın ${yuzde(a.oran * 100, 1)}'i hiçbir dönüşüm ekipmanına atanmamış. `
        : `Ekipmanlara atanan yakıt, satın alınandan ${yuzde(-a.oran * 100, 1)} fazla. ` }),
      `İstasyon sayaçları ${say(a.satinAlinan, 0)} kWh, ekipman sayaçları ` +
      `${say(a.ekipman, 0)} kWh gösteriyor; fark ${say(Math.abs(a.atanmamis), 0)} kWh. ` +
      (a.atanmamis > 0
        ? "Bu gaz bir yerde yakılıyor ama hangi ekipmanda olduğu bilinmiyor; " +
          "ekipman verimleri bu yüzden olduğundan yüksek görünebilir."
        : "Ekipman ölçümlerinin toplamı istasyon ölçümünü aşıyor — biri hatalı.") +
      " Bu fark, alt sayaç yatırımının nereye yapılacağını söyleyen sayıdır (6.7, A-05)."));
  }
}
