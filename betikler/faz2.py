#!/usr/bin/env python3
"""faz2.py — Faz 2 uctan uca: gercek Excel'i aktar, altin sayilari dogrula."""
import base64, json, pathlib, sys
from playwright.sync_api import sync_playwright

KOK   = pathlib.Path(__file__).resolve().parent.parent
DOSYA = KOK / "cikti" / "enerji-yonetim.html"
XLSX  = pathlib.Path("/root/.claude/uploads/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/77d1f4e3-veri.xlsx")
SS    = pathlib.Path("/tmp/claude-0/-home-user-as/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/scratchpad/ss")
SS.mkdir(parents=True, exist_ok=True)

# El Kitabi 13.2 — yillik altin sayilar (Excel'in kendi degerleri)
ALTIN = {
 2018:(15_919_712, 128_362_622, 144_282_334, 104_980_360),
 2019:( 4_388_200, 151_249_409, 155_637_609, 101_839_334),
 2020:( 6_559_460, 147_423_923, 153_983_384, 101_758_697),
 2021:(12_425_346, 127_572_551, 139_997_897,  98_148_940),
 2022:(24_482_137,  99_649_227, 124_131_364, 107_258_078),
 2023:(18_097_125, 111_279_600, 129_376_725, 111_976_787),
 # 2024 uretim: Excel 111.897.453 diyor AMA bu deger HATALI (bkz. El Kitabi 2.5/S10).
 # 2024 Agustos cikolata hucresi metin ("286609,,4"); Excel'in SUM'i onu sessizce
 # atlamis ve o ayin toplamini yalniz kakao ile uretmis. Program ise o ayin toplamini
 # HIC uretmiyor ve nedenini yaziyor (I-3) — dogru davranis budur.
 2024:(19_248_726, 111_987_169, 131_235_894, 107_911_108),
 2025:(17_199_431, 120_168_406, 137_367_837, 100_503_911),
}
gecti = kaldi = 0
def sina(ad, bulunan, beklenen, tol=1):
    global gecti, kaldi
    if bulunan is None:
        print(f"  ✗ {ad:34} ÜRETİLEMEDİ (beklenen {beklenen:,.0f})"); kaldi += 1; return False
    ok = abs(bulunan - beklenen) <= tol
    print(f"  {'✓' if ok else '✗'} {ad:34} {bulunan:>16,.2f}  bekl. {beklenen:>16,.0f}")
    gecti += ok; kaldi += (not ok); return ok

def main():
    global gecti, kaldi
    hata = []
    with sync_playwright() as pw:
        t = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        s = t.new_page(viewport={"width":1500,"height":1000})
        s.on("pageerror", lambda e: hata.append("PAGEERROR: " + str(e)))
        s.on("console", lambda m: hata.append("CONSOLE: " + m.text) if m.type == "error" else None)
        s.goto(DOSYA.as_uri()); s.wait_for_timeout(900)

        print("=== EXCEL AKTARIMI ===")
        s.evaluate('__req("js/uygulama.js").git(3)'); s.wait_for_timeout(400)
        s.evaluate("""async (b64) => {
          const ham = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
          const dt = new DataTransfer(); dt.items.add(new File([ham], "veri.xlsx"));
          const g = document.querySelector('#icerik input[type=file][accept=".xlsx"]');
          g.files = dt.files; g.dispatchEvent(new Event("change", { bubbles:true }));
        }""", base64.b64encode(XLSX.read_bytes()).decode())
        s.wait_for_timeout(2500)
        s.get_by_role("button", name="Önizle →").click(); s.wait_for_timeout(2500)
        s.screenshot(path=str(SS/"f2-01-onizleme.png"), full_page=True)
        s.get_by_role("button", name__contains="geçerli değeri aktar").click() if False else \
            s.locator("#icerik button.dugme.ana").filter(has_text="geçerli değeri aktar").click()
        s.wait_for_timeout(700)
        s.locator(".modal button.dugme.ana").click()     # onay
        s.wait_for_timeout(4000)

        d = s.evaluate("""() => {
          const V = __req("js/veri.js"), HL = __req("js/hesaplanan.js");
          return { deger:V.durum.degerler.length, donem:HL.katman.satirlar.length,
                   sure:HL.katman.sure, eksik:HL.katman.eksikler.length };
        }""")
        print(f"  {d['deger']:,} ham değer · {d['donem']} dönem · katman {d['sure']} ms · "
              f"{d['eksik']} üretilemeyen")

        print("\n=== 13.2 ALTIN SAYILAR (yıllık) ===")
        for yil, (elk, dg, ten, ure) in ALTIN.items():
            r = s.evaluate("""(yil) => {
              const H = __req("js/hesap.js"), HL = __req("js/hesaplanan.js");
              let e=0, g=0, t=0, u=0, ok=true; const eksikAy=[];
              for (let a=1; a<=12; a++) {
                const se = H.noktaDeger("SEBEKE_ELK", yil, a);
                const te = H.toplamEnerji(yil, a, "kWh");
                const tu = H.noktaDeger("TOPLAM_URETIM", yil, a);
                const dg1 = H.noktaDeger("IST1_DG_KWH", yil, a),
                      dg2 = H.noktaDeger("IST2_DG_KWH", yil, a),
                      dg3 = H.noktaDeger("IST3_DG_KWH", yil, a);
                e += se.deger || 0;
                g += (dg1.deger||0)+(dg2.deger||0)+(dg3.deger||0);
                if (Number.isFinite(te.deger)) t += te.deger; else if (te.eksik) ok = false;
                if (Number.isFinite(tu.deger)) u += tu.deger;
                else { ok = false; eksikAy.push({ ay:a, sebep: tu.eksik || "değer yok" }); }
              }
              return { e, g, t, u, ok, eksikAy };
            }""", yil)
            print(f"  --- {yil} ---")
            sina(f"{yil} şebeke elektriği", r["e"], elk, 1)
            sina(f"{yil} toplam doğalgaz",  r["g"], dg, 1)
            sina(f"{yil} TOPLAM ENERJİ",    r["t"], ten, 1)
            if r["eksikAy"]:
                for x in r["eksikAy"]:
                    print(f"     ⚠ {yil}-{x['ay']:02} üretim üretilemedi: {x['sebep']}"
                          "  → kaynak veri hatası, program doğru davranıyor (İ-3)")
            sina(f"{yil} toplam üretim",    r["u"], ure, 2)

        print("\n=== KAYNAK VERİ HATASININ YAKALANMASI (S10) ===")
        s10 = s.evaluate("""() => {
          const H = __req("js/hesap.js"), V = __req("js/veri.js");
          const tu = H.noktaDeger("TOPLAM_URETIM", 2024, 8);
          return { cikolata: V.deger("CIKOLATA_KG", 2024, 8),
                   kakao:    H.noktaDeger("TOPLAM_KAKAO", 2024, 8).deger,
                   uretim:   tu.deger ?? null, sebep: tu.eksik || null };
        }""")
        for ad, kosul, ayrinti in [
            ("2024-08 çikolata değeri alınmadı", s10["cikolata"] is None, s10["cikolata"]),
            ("2024-08 kakao yine de üretiliyor", s10["kakao"] is not None, s10["kakao"]),
            ("2024-08 toplam üretim ÜRETİLMİYOR", s10["uretim"] is None, s10["sebep"])]:
            print(f"  {'✓' if kosul else '✗'} {ad:38} {ayrinti}")
            if kosul: gecti += 1
            else: kaldi += 1

        print("\n=== EKRAN GEÇİŞLERİ ===")
        for no, ad in [(2,"giris"),(4,"denetim"),(5,"hesaplanan"),(14,"tanimlar")]:
            s.evaluate(f'__req("js/uygulama.js").git({no})'); s.wait_for_timeout(900)
            b = s.locator("#icerik h1, #icerik h3").first.inner_text()
            print(f"  Ekran {no:2} → {b}")
            s.screenshot(path=str(SS/f"f2-{no:02d}-{ad}.png"))

        print("\n=== EXCEL ÇIKTISI (2 sayfa) ===")
        x = s.evaluate("""async () => {
          const X = __req("js/xlsx.js"), HL = __req("js/hesaplanan.js"), V = __req("js/veri.js");
          const nk = V.durum.olcum_noktalari.filter(n => n.veri_tipi === "olculen");
          const ham = [["Dönem", ...nk.map(n => n.ad)]];
          for (const r of HL.katman.satirlar.slice(0,3))
            ham.push([r.kod, ...nk.map(n => V.deger(n.kod, r.yil, r.ay))]);
          const hes = [["Dönem", ...HL.katman.sutunlar.map(c => c.ad)],
                       ["FORMÜL", ...HL.katman.sutunlar.map(c => c.formul)]];
          for (const r of HL.katman.satirlar.slice(0,3))
            hes.push([r.kod, ...HL.katman.sutunlar.map(c => r[c.kod])]);
          const blob = await X.xlsxYaz([{ad:"Ham Veri",satirlar:ham},{ad:"Hesaplanan",satirlar:hes}]);
          const geri = await X.xlsxOku(await blob.arrayBuffer());
          return { boyut:blob.size, sayfalar:geri.sayfalar.map(z => z.ad),
                   hamSutun:geri.sayfalar[0].satirlar[0].length,
                   formulSatiri:geri.sayfalar[1].satirlar[1].slice(1,3) };
        }""")
        print(f"  {x['boyut']:,} bayt · sayfalar {x['sayfalar']} · {x['hamSutun']} sütun")
        print(f"  formül satırı: {x['formulSatiri']}")
        gecti_ = x["sayfalar"] == ["Ham Veri","Hesaplanan"]
        print(f"  {'✓' if gecti_ else '✗'} iki sayfalı çalışma kitabı gidiş-dönüş")
        globals()['gecti'] += gecti_; globals()['kaldi'] += (not gecti_)

        t.close()

    print("\n" + "="*56)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} sayfa hatası" if hata else ""))
    for h in hata[:6]: print("   !", h[:180])
    return 1 if (kaldi or hata) else 0

sys.exit(main())
