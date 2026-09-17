#!/usr/bin/env python3
"""faz3.py — grafik ekranlarini gercek veriyle sinar."""
import base64, json, pathlib, sys
from playwright.sync_api import sync_playwright
KOK=pathlib.Path(__file__).resolve().parent.parent
D=KOK/"cikti"/"enerji-yonetim.html"
XLSX=pathlib.Path("/root/.claude/uploads/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/77d1f4e3-veri.xlsx")
SS=pathlib.Path("/tmp/claude-0/-home-user-as/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/scratchpad/ss")
SS.mkdir(parents=True,exist_ok=True)
gecti=kaldi=0
def ok(ad,kosul,ek=""):
    global gecti,kaldi
    print(f"  {'✓' if kosul else '✗'} {ad}" + (f"  {ek}" if ek else ""))
    if kosul: gecti+=1
    else: kaldi+=1

def main():
    global gecti,kaldi
    hata=[]
    with sync_playwright() as pw:
        t=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium",args=["--no-sandbox"])
        s=t.new_page(viewport={"width":1500,"height":1050})
        s.on("pageerror",lambda e:hata.append("PAGEERROR: "+str(e)))
        s.on("console",lambda m:hata.append("CONSOLE: "+m.text) if m.type=="error" else None)
        s.goto(D.as_uri()); s.wait_for_timeout(900)

        print("=== BOŞ DURUM (veri yokken) ===")
        b=s.evaluate("""()=>{const u=__req("js/uygulama.js"); u.git(1);
          return document.querySelector("#icerik .bos h3")?.innerText||"";}""")
        ok("Panel boş durumu öğretici", "Henüz veri yok" in b, b)
        s.screenshot(path=str(SS/"f3-00-bos.png"))

        print("\n=== VERİ AKTARIMI ===")
        s.evaluate('__req("js/uygulama.js").git(3)'); s.wait_for_timeout(400)
        s.evaluate("""async (b)=>{const h=Uint8Array.from(atob(b),c=>c.charCodeAt(0));
          const dt=new DataTransfer(); dt.items.add(new File([h],"veri.xlsx"));
          const g=document.querySelector('#icerik input[type=file][accept=".xlsx"]');
          g.files=dt.files; g.dispatchEvent(new Event("change",{bubbles:true}));}""",
          base64.b64encode(XLSX.read_bytes()).decode())
        s.wait_for_timeout(2400); s.get_by_role("button",name="Önizle →").click(); s.wait_for_timeout(2400)
        s.locator("#icerik button.dugme.ana").filter(has_text="geçerli değeri aktar").click()
        s.wait_for_timeout(600); s.locator(".modal button.dugme.ana").click(); s.wait_for_timeout(4000)
        n=s.evaluate('__req("js/veri.js").durum.degerler.length')
        ok("Veri aktarıldı", n>4000, f"{n:,} değer")

        for no,ad,bekle in [(1,"panel","Gösterge Paneli"),(7,"tuketim","Tüketim Analizi"),
                            (6,"denge","Enerji Dengesi")]:
            print(f"\n=== EKRAN {no} · {bekle} ===")
            s.evaluate(f'__req("js/uygulama.js").git({no})'); s.wait_for_timeout(1600)
            baslik=s.locator("#icerik h1").first.inner_text()
            ok("başlık", baslik==bekle, baslik)
            svg=s.locator("#icerik svg").count()
            ok("SVG grafik çizildi", svg>0, f"{svg} svg")
            s.screenshot(path=str(SS/f"f3-{no:02d}-{ad}.png"), full_page=True)

        print("\n=== PANEL SAYILARI ===")
        p=s.evaluate("""()=>{
          const HL=__req("js/hesaplanan.js"), H=__req("js/hesap.js");
          return { enerji:HL.hucre("TOPLAM_ENERJI",2025,12),
                   maliyet:HL.hucre("TOPLAM_MALIYET",2025,12),
                   enpi:HL.hucre("ENPI_ENPI_ANA",2025,12),
                   kart:document.querySelectorAll("#icerik .kart").length };}""")
        s.evaluate('__req("js/uygulama.js").git(1)'); s.wait_for_timeout(1200)
        ok("Aralık 2025 toplam enerji", abs(p["enerji"]-11798400)<2, f"{p['enerji']:,.0f} kWh")
        ok("EnPI üretiliyor", p["enpi"] is not None, f"{p['enpi']}")

        print("\n=== GRAFİK KURALLARI (5.7.2) ===")
        r=s.evaluate("""()=>{
          const svgler=[...document.querySelectorAll("#icerik svg")];
          const kesikli=svgler.some(v=>[...v.querySelectorAll("*")]
            .some(e=>e.getAttribute("stroke-dasharray")));
          const tabloDugmesi=[...document.querySelectorAll("#icerik button")]
            .filter(b=>b.textContent.includes("Tablo olarak göster")).length;
          return { kesikli, tabloDugmesi, svg:svgler.length };}""")
        ok("Kesikli kılavuz/eksen YOK", not r["kesikli"])
        ok("Her grafikte 'Tablo olarak göster'", r["tabloDugmesi"]>=2, f"{r['tabloDugmesi']} düğme")

        print("\n=== TABLO GÖRÜNÜMÜ ===")
        s.evaluate("""()=>{const b=[...document.querySelectorAll("#icerik button")]
          .find(x=>x.textContent.includes("Tablo olarak göster")); b&&b.click();}""")
        s.wait_for_timeout(500)
        tsay=s.evaluate('document.querySelectorAll("#icerik table tbody tr").length')
        ok("Tabloya çevrilebiliyor", tsay>0, f"{tsay} satır")
        s.screenshot(path=str(SS/"f3-01b-tablo.png"))

        print("\n=== KOYU TEMA ===")
        s.evaluate('document.documentElement.dataset.tema="koyu"')
        s.evaluate('__req("js/uygulama.js").git(6)'); s.wait_for_timeout(1500)
        s.screenshot(path=str(SS/"f3-06b-koyu.png"), full_page=True)
        ok("Koyu temada çiziliyor", s.locator("#icerik svg").count()>0)
        t.close()

    print("\n"+"="*52)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} hata" if hata else ""))
    for h in hata[:6]: print("   !",h[:170])
    return 1 if (kaldi or hata) else 0
sys.exit(main())
