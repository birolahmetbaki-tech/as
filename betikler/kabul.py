#!/usr/bin/env python3
"""kabul.py — El Kitabi Bolum 13 kabul kriterleri testi.
Gercek 2024 Haziran verisiyle programin altin sayilari uretip uretmedigini sinar."""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

KOK = pathlib.Path(__file__).resolve().parent.parent
DOSYA = KOK / "cikti" / "enerji-yonetim.html"
VERI = json.loads(pathlib.Path("/tmp/2024h.json").read_text())

BEKLENEN = {          # El Kitabi 13.3
    "toplam_enerji": 10_800_103,
    "toplam_uretim":  8_868_323,
    "enpi":               1.2178,
    "turbin_verim":      58.9,
}
gecti = basarisiz = 0

def sina(ad, bulunan, beklenen, tolerans=0.5):
    global gecti, basarisiz
    if bulunan is None:
        print(f"  ✗ {ad:28} ÜRETİLEMEDİ (beklenen {beklenen:,.4f})"); basarisiz += 1; return
    ok = abs(bulunan - beklenen) <= tolerans
    isaret = "✓" if ok else "✗"
    print(f"  {isaret} {ad:28} {bulunan:>16,.4f}   beklenen {beklenen:>16,.4f}")
    if ok: gecti += 1
    else: basarisiz += 1

def main():
    global gecti, basarisiz
    hatalar = []
    with sync_playwright() as pw:
        t = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        s = t.new_page(viewport={"width":1400,"height":900})
        s.on("pageerror", lambda e: hatalar.append(str(e)))
        s.goto(DOSYA.as_uri()); s.wait_for_timeout(900)

        print("=== 13.3 NOKTA KONTROLÜ · 2024 Haziran ===")
        r = s.evaluate("""(veri) => {
          const V = __req("js/veri.js"), H = __req("js/hesap.js"),
                HL = __req("js/hesaplanan.js");
          for (const [kod, v] of Object.entries(veri)) V.degerYaz(kod, 2024, 6, v);
          HL.uret();
          const te = H.toplamEnerji(2024, 6, "kWh");
          const tu = H.noktaDeger("TOPLAM_URETIM", 2024, 6);
          const ep = H.enpi("ENPI_ANA", 2024, 6);
          const dv = H.donusumVerimi("TURBIN", 2024, 6);
          return {
            toplam_enerji: te.deger, toplam_enerji_eksik: te.eksik || null,
            toplam_uretim: tu.deger, enpi: ep.deger,
            turbin_verim: dv ? dv.toplamVerim * 100 : null,
            katman_satir: HL.katman.satirlar.length,
            katman_sure: HL.katman.sure,
            katman_toplam: HL.hucre("TOPLAM_ENERJI", 2024, 6),
            kalem: te.kalemler ? te.kalemler.length : 0,
          };
        }""", VERI)

        sina("Toplam enerji (kWh)", r["toplam_enerji"], BEKLENEN["toplam_enerji"], 1)
        sina("Toplam üretim (kg)",  r["toplam_uretim"],  BEKLENEN["toplam_uretim"], 1)
        sina("EnPI (kWh/kg)",       r["enpi"],           BEKLENEN["enpi"], 0.0001)
        sina("Türbin toplam verim %", r["turbin_verim"], BEKLENEN["turbin_verim"], 0.1)

        print(f"\n  toplam enerjiye giren kalem : {r['kalem']} (şebeke + 3 istasyon)")
        if r["toplam_enerji_eksik"]: print("  ! eksik:", r["toplam_enerji_eksik"])

        print("\n=== K-23 · HESAP KATMANI ===")
        sina("Katmandaki toplam enerji", r["katman_toplam"], BEKLENEN["toplam_enerji"], 1)
        print(f"  katman: {r['katman_satir']} dönem · {r['katman_sure']} ms")

        print("\n=== K-23 · DEĞİŞİMDE YENİDEN ÜRETİM ===")
        r2 = s.evaluate("""() => {
          const V = __req("js/veri.js"), HL = __req("js/hesaplanan.js");
          const once = HL.hucre("TOPLAM_ENERJI", 2024, 6);
          V.degerYaz("SEBEKE_ELK", 2024, 6, 2000000);   // değeri değiştir
          const sonra = HL.hucre("TOPLAM_ENERJI", 2024, 6);
          V.degerYaz("SEBEKE_ELK", 2024, 6, 1789175.52); // geri al
          return { once, sonra, geri: HL.hucre("TOPLAM_ENERJI", 2024, 6) };
        }""")
        d = r2["sonra"] - r2["once"]
        ok = abs(d - (2000000 - 1789175.52)) < 1
        print(f"  {'✓' if ok else '✗'} değer değişti → katman anında güncellendi (fark {d:,.0f} kWh)")
        gecti += ok; basarisiz += (not ok)
        ok2 = abs(r2["geri"] - BEKLENEN["toplam_enerji"]) < 1
        print(f"  {'✓' if ok2 else '✗'} geri alındı → eski değere döndü")
        gecti += ok2; basarisiz += (not ok2)

        print("\n=== 13.5 · DAVRANIŞ KONTROLLERİ ===")
        b = s.evaluate("""() => {
          const M = __req("js/model.js"), V = __req("js/veri.js"), H = __req("js/hesap.js");
          const o = {};
          o.negatif = M.dogrula("SEBEKE_ELK", 2024, 7, -5).some(x => x.seviye === "engel");
          // Medyan kurali en az 4 gecmis deger ister; once gecmis yazilir
          for (let a = 1; a <= 5; a++) V.degerYaz("SEBEKE_ELK", 2024, a, 1800000);
          o.gecmisYok = !M.dogrula("SEBEKE_ELK", 2024, 7, 999999999).length; // gecmis varken bos olmamali
          o.spike   = M.dogrula("SEBEKE_ELK", 2024, 7, 999999999).some(x => x.seviye === "uyar");
          o.dusuk   = M.dogrula("SEBEKE_ELK", 2024, 7, 100).some(x => x.seviye === "uyar");
          for (let a = 1; a <= 5; a++) V.degerYaz("SEBEKE_ELK", 2024, a, null);
          // A-12 sonrasi: motorin katsayisi 11,9 kWh/kg tanimli.
          // 500 kg -> 5.950 kWh olarak toplama GIRER (K-24).
          const teBos = H.toplamEnerji(2024, 6, "kWh").deger;
          V.degerYaz("MOTORIN_KG", 2024, 6, 500);
          const te = H.toplamEnerji(2024, 6, "kWh");
          o.motorinGirdi = !te.eksik && Math.abs((te.deger - teBos) - 5950) < 0.5;
          o.motorinSebep = `+${Math.round(te.deger - teBos)} kWh (500 kg × 11,9)`;
          // Katsayi KALDIRILINCA I-3 kurali geri gelir: toplam URETILMEZ
          const kat = V.durum.donusum_katsayilari;
          const i = kat.findIndex(x => x.enerji_turu === "MOT");
          const yedek = kat.splice(i, 1)[0];
          const teYok = H.toplamEnerji(2024, 6, "kWh");
          o.motorinEngel = !!teYok.eksik;
          kat.splice(i, 0, yedek);
          V.degerYaz("MOTORIN_KG", 2024, 6, 0);         // sifir -> toplam URETILIR
          const te0 = H.toplamEnerji(2024, 6, "kWh");
          o.motorinSifirOk = te0.deger !== null && !te0.eksik;
          V.degerYaz("MOTORIN_KG", 2024, 6, null);
          return o;
        }""")
        for ad, deger, bek in [
            ("Negatif değer engellenir", b["negatif"], True),
            ("Aşırı sıçrama uyarır (medyanın 3 katı)", b["spike"], True),
            ("Aşırı düşük uyarır (medyanın 1/3'ü)",    b["dusuk"], True),
            ("Motorin≠0 + katsayı var → toplama girer (A-12, K-24)", b["motorinGirdi"], True),
            ("Katsayı kaldırılınca toplam üretilmez (İ-3)",           b["motorinEngel"], True),
            ("Motorin=0 → toplam üretilir",                           b["motorinSifirOk"], True)]:
            isaret = "✓" if deger == bek else "✗"
            print(f"  {isaret} {ad}")
            if deger == bek: gecti += 1
            else: basarisiz += 1
        print("    ↳", b["motorinSebep"])

        print("\n=== K-10 · YEDEK GİDİŞ-DÖNÜŞ ===")
        y = s.evaluate("""() => {
          const V = __req("js/veri.js"), HL = __req("js/hesaplanan.js");
          const yedek = JSON.parse(JSON.stringify(V.disaVer()));
          const oncekiDeger = V.durum.degerler.length;
          const oncekiToplam = HL.hucre("TOPLAM_ENERJI", 2024, 6);
          V.durum.degerler.length = 0; V.degisti("sil");
          const bosToplam = HL.hucre("TOPLAM_ENERJI", 2024, 6);
          V.yedegiUygula(yedek);
          return { oncekiDeger, oncekiToplam, bosToplam,
                   sonraDeger: V.durum.degerler.length,
                   sonraToplam: HL.hucre("TOPLAM_ENERJI", 2024, 6),
                   yedekteHesaplanan: Object.keys(yedek).some(k => /hesapla|katman/i.test(k)) };
        }""")
        for ad, kosul in [
            ("Yedek alındı ve geri yüklendi", y["sonraDeger"] == y["oncekiDeger"]),
            ("Geri yükleme sonrası toplam aynı", y["sonraToplam"] == y["oncekiToplam"]),
            ("Silinince toplam üretilmiyor", y["bosToplam"] is None),
            ("Yedekte hesaplanan değer YOK (K-23)", not y["yedekteHesaplanan"])]:
            print(f"  {'✓' if kosul else '✗'} {ad}")
            if kosul: gecti += 1
            else: basarisiz += 1

        t.close()

    print("\n" + "=" * 52)
    print(f"  {gecti} geçti · {basarisiz} başarısız" + (f" · {len(hatalar)} sayfa hatası" if hatalar else ""))
    for h in hatalar[:5]: print("   !", h[:160])
    return 1 if (basarisiz or hatalar) else 0

sys.exit(main())
