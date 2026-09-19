#!/usr/bin/env python3
"""sina.py — derlenmis tek dosyayi gercek tarayicida sinar."""
import sys, pathlib, json
from playwright.sync_api import sync_playwright

KOK = pathlib.Path(__file__).resolve().parent.parent
DOSYA = KOK / "cikti" / "enerji-yonetim.html"
SS = pathlib.Path("/tmp/claude-0/-home-user-as/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/scratchpad/ss")
SS.mkdir(parents=True, exist_ok=True)

hatalar, uyarilar = [], []

def main():
    with sync_playwright() as pw:
        t = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        s = t.new_page(viewport={"width":1400,"height":900})
        s.on("console", lambda m: (hatalar if m.type=="error" else uyarilar).append(m.text))
        s.on("pageerror", lambda e: hatalar.append("PAGEERROR: "+str(e)))
        s.goto(DOSYA.as_uri())
        s.wait_for_timeout(1200)

        print("=== 1. ACILIS ===")
        print("  baslik   :", s.title())
        menu = s.locator("#menu .menu-og").count()
        print("  menu ogesi:", menu, "(beklenen 15)")
        hazir = s.locator('#menu .menu-og[data-hazir="1"]').count()
        print("  hazir ekran:", hazir, "(beklenen 2)")

        print("\n=== 2. VERI KATMANI ===")
        d = s.evaluate("""() => {
          const k = __req("js/veri.js"), h = __req("js/hesaplanan.js");
          return { varlik:k.durum.varliklar.length,
                   nokta:k.durum.olcum_noktalari.length,
                   katsayi:k.durum.donusum_katsayilari.length,
                   enpi:k.durum.enpi_tanimlari.length,
                   deger:k.durum.degerler.length,
                   sutun:h.katman.sutunlar.length,
                   satir:h.katman.satirlar.length,
                   sure:h.katman.sure };
        }""")
        for a,b in d.items(): print(f"  {a:9}: {b}")

        print("\n=== 3. HESAP MOTORU (bos veriyle) ===")
        r = s.evaluate("""() => {
          const H = __req("js/hesap.js"), M = __req("js/model.js");
          const out = {};
          out.toplamBos = H.toplamEnerji(2024, 6, "kWh");
          // birim donusumu: 1000 kWh -> GJ (sabit)
          out.kwh2gj = M.cevir(1000, "kWh", "GJ", "ELK", 2024, 6);
          // 1 TEP kac kWh?
          out.tep = M.cevir(1, "TEP", "kWh", "ELK", 2024, 6);
          // dogalgaz m3 -> kWh (tarihli katsayi)
          out.m3 = M.cevir(1000, "m³", "kWh", "DG", 2024, 6);
          // buhar kg -> kWh
          out.buhar = M.cevir(1000, "kg", "kWh", "BUH", 2024, 6);
          // motorin: katsayi TANIMSIZ olmali (A-12)
          out.motorinSifir = M.cevir(0, "kg", "kWh", "MOT", 2024, 6);
          out.motorinDolu  = M.cevir(100, "kg", "kWh", "MOT", 2024, 6);
          return out;
        }""")
        print(json.dumps(r, ensure_ascii=False, indent=2))

        print("\n=== 4. EKRAN GECISLERI ===")
        for no, ad in [(12,"tanimlar"),(13,"ayarlar"),(1,"panel-yakinda")]:
            s.evaluate(f'__req("js/uygulama.js").git({no})')
            s.wait_for_timeout(400)
            b = s.locator("#icerik h1, #icerik h3").first.inner_text()
            print(f"  Ekran {no:2} -> {b}")
            s.screenshot(path=str(SS/f"{no:02d}-{ad}.png"), full_page=False)

        print("\n=== 5. SEKMELER (Ekran 14) ===")
        s.evaluate('__req("js/uygulama.js").git(12)'); s.wait_for_timeout(300)
        for i, ad in enumerate(["agac","nokta","tur","kats","enpi","baz"]):
            s.locator("#icerik .sekme").nth(i).click(); s.wait_for_timeout(300)
            sec = s.locator('#icerik .sekme[aria-selected="true"]').inner_text()
            print(f"  {i+1}. {sec}")
            s.screenshot(path=str(SS/f"14{chr(97+i)}-{ad}.png"))

        print("\n=== 6. KOYU TEMA ===")
        s.evaluate('document.documentElement.dataset.tema="koyu"')
        s.evaluate('__req("js/uygulama.js").git(13)'); s.wait_for_timeout(400)
        s.screenshot(path=str(SS/"15-koyu.png"))
        print("  ekran goruntusu alindi")

        t.close()

    print("\n=== SONUC ===")
    if hatalar:
        print(f"  ✗ {len(hatalar)} KONSOL HATASI:")
        for h in hatalar[:12]: print("     ", h[:200])
        return 1
    print("  ✓ konsol hatasi YOK")
    if uyarilar: print(f"  · {len(uyarilar)} uyari")
    return 0

sys.exit(main())
