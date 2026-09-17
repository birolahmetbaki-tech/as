#!/usr/bin/env python3
"""faz4.py — Faz 4 ekranlarini (9 Dönüşüm Verimliliği, 10 Maliyet, 11 GES)
gercek veriyle sinar ve El Kitabi 8.8 / 9.11'deki altin sayilari dogrular."""
import base64, pathlib, sys
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
def yakin(a,b,tol):
    return a is not None and abs(a-b)<=tol

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
        for no,bekle in [(9,"Dönüşüm Verimliliği"),(10,"Maliyet"),(11,"GES")]:
            b=s.evaluate(f"""()=>{{const u=__req("js/uygulama.js"); u.git({no});
              return {{h1:document.querySelector("#icerik h1")?.innerText||"",
                       bos:document.querySelector("#icerik .bos h3")?.innerText||""}};}}""")
            ok(f"Ekran {no} başlığı ve boş durumu", b["h1"]==bekle and "Henüz veri yok" in b["bos"],
               f'{b["h1"]} · {b["bos"]}')

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

        # --------------------------------------------- 8.6 dönüşüm verimi
        print("\n=== 8.8 VAKASI · TÜRBİN VERİM KAYBI (hesap çekirdeği) ===")
        v=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const y=v=>O.donemAraligi(v,1,v,12);
          const g=(k,yil)=>H.donusumVerimiAralik(k,y(yil));
          const t24=g("TURBIN",2024), t25=g("TURBIN",2025);
          return { t24, t25, gm1_25:g("GM1",2025), gm1_24:g("GM1",2024),
                   varlik:H.donusumVarliklari().map(x=>x.varlik.kod) };}""")
        ok("Dönüşüm varlıkları rol taramasıyla bulundu",
           set(v["varlik"])=={"TURBIN","GM1","GM2","GM3","KAZAN1","KAZAN2"}, str(v["varlik"]))
        ok("Türbin toplam verimi 2024 = %57,2",
           yakin(v["t24"]["toplamVerim"]*100,57.2,0.15), f'%{v["t24"]["toplamVerim"]*100:.1f}')
        ok("Türbin toplam verimi 2025 = %50,3",
           yakin(v["t25"]["toplamVerim"]*100,50.3,0.15), f'%{v["t25"]["toplamVerim"]*100:.1f}')
        kayip=(v["t24"]["toplamVerim"]-v["t25"]["toplamVerim"])*v["t25"]["yakit"]
        ok("Verim kaybının karşılığı ≈ 5,6 GWh/yıl", yakin(kayip/1e6,5.6,0.35), f"{kayip:,.0f} kWh")
        ok("Türbin 2025 yakıtı ≈ 80,6 GWh", yakin(v["t25"]["yakit"]/1e6,80.6,0.6),
           f'{v["t25"]["yakit"]:,.0f} kWh')
        ok("GM-1 2025'te durmuş (yakıt verisi yok)", v["gm1_25"] is None,
           "yok" if v["gm1_25"] is None else str(v["gm1_25"]["yakit"]))
        ok("GM-1 2024'te çalışıyordu", v["gm1_24"] is not None and v["gm1_24"]["yakit"]>0)

        # ----------------------------------------------- 9.11 maliyet özeti
        print("\n=== 9.11 MALİYET ÖZETİ · 2025 ===")
        m=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const d=O.donemAraligi(2025,1,2025,12);
          const dk=H.maliyetDokumu(d);
          const kl=H.faturaKalemleri();
          const bul=k=>kl.find(x=>x.fatura.kod===k);
          return { brut:dk.brut, mahsup:dk.mahsup, net:dk.net,
            kalem:dk.kalemler.map(x=>({kod:x.fatura.kod,tutar:x.tutar,miktar:x.miktar,
                                       birim:x.birim,bf:x.birimFiyat})),
            elk:H.faturaOzeti(bul("ELK_FATURA_TL"),d),
            dg:H.faturaOzeti(bul("DG_FATURA_TL"),d) };}""")
        elk=next(x for x in m["kalem"] if x["kod"]=="ELK_FATURA_TL")
        dg =next(x for x in m["kalem"] if x["kod"]=="DG_FATURA_TL")
        ok("Brüt elektrik faturası 55.712.474 TL", yakin(elk["tutar"],55712474,2), f'{elk["tutar"]:,.0f}')
        ok("GES mahsubu + satışı 25.723.468 TL", yakin(m["mahsup"],25723468,2), f'{m["mahsup"]:,.0f}')
        ok("Net ödenen elektrik 29.989.006 TL",
           yakin(elk["tutar"]-m["mahsup"],29989006,3), f'{elk["tutar"]-m["mahsup"]:,.0f}')
        ok("Doğalgaz faturası 165.193.331 TL", yakin(dg["tutar"],165193331,2), f'{dg["tutar"]:,.0f}')
        ok("Toplam enerji maliyeti 195.182.337 TL", yakin(m["net"],195182337,3), f'{m["net"]:,.0f}')
        ok("Elektrik birim fiyatı kWh cinsinden", elk["birim"]=="kWh", elk["birim"])
        ok("Doğalgaz birim fiyatı m³ cinsinden", dg["birim"]=="m³", dg["birim"])
        ok("Elektrik birim fiyatı 2025 = 3,2392 TL/kWh", yakin(elk["bf"],3.2392,0.0002), f'{elk["bf"]:.4f}')
        ok("Doğalgaz birim fiyatı 2025 = 14,6266 TL/m³", yakin(dg["bf"],14.6266,0.0002), f'{dg["bf"]:.4f}')

        # --------------------------------------- 8.7 fiyat/hacim ayrıştırması
        print("\n=== 8.7 FİYAT / HACİM AYRIŞTIRMASI · 2024 → 2025 ===")
        a=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const d24=O.donemAraligi(2024,1,2024,12), d25=O.donemAraligi(2025,1,2025,12);
          const kl=H.faturaKalemleri();
          const al=k=>{const x=kl.find(y=>y.fatura.kod===k);
                       return x?H.kalemFiyatHacim(x,d24,d25):null;};
          return { elk:al("ELK_FATURA_TL"), dg:al("DG_FATURA_TL"), mot:al("MOT_FATURA_TL") };}""")
        e,g=a["elk"],a["dg"]
        ok("Elektrik fiyat etkisi +10.682.663 TL", yakin(e["fiyatEtkisi"],10682663,50), f'{e["fiyatEtkisi"]:,.0f}')
        ok("Elektrik hacim etkisi −5.500.767 TL", yakin(e["hacimEtkisi"],-5500767,50), f'{e["hacimEtkisi"]:,.0f}')
        ok("Elektrik bileşik etkisi −1.137.318 TL", yakin(e["bilesikEtki"],-1137318,50), f'{e["bilesikEtki"]:,.0f}')
        ok("Elektrik maliyet farkı +4.044.578 TL", yakin(e["toplam"],4044578,50), f'{e["toplam"]:,.0f}')
        ok("Elektrik fiyat artışı %20,7", yakin(e["fiyatDegisim"]*100,20.7,0.15), f'%{e["fiyatDegisim"]*100:.1f}')
        ok("Doğalgaz fiyat etkisi +20.456.179 TL", yakin(g["fiyatEtkisi"],20456179,50), f'{g["fiyatEtkisi"]:,.0f}')
        ok("Doğalgaz hacim etkisi +13.475.761 TL", yakin(g["hacimEtkisi"],13475761,50), f'{g["hacimEtkisi"]:,.0f}')
        ok("Doğalgaz maliyet farkı +36.066.765 TL", yakin(g["toplam"],36066765,80), f'{g["toplam"]:,.0f}')
        ok("Doğalgaz fiyat artışı %15,8", yakin(g["fiyatDegisim"]*100,15.8,0.15), f'%{g["fiyatDegisim"]*100:.1f}')
        ok("Üç etkinin toplamı maliyet farkına eşit",
           yakin(e["fiyatEtkisi"]+e["hacimEtkisi"]+e["bilesikEtki"]-e["toplam"],0,0.5))
        ok("Motorin kalemi ayrıştırma üretmiyor (veri yok, uydurmuyor)", a["mot"] is None)

        print("\n=== BİRİM FİYAT TRENDİ (K-12, kWh cinsine çevrilmiş) ===")
        bf=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const kl=H.faturaKalemleri();
          const al=(k,y)=>{const x=kl.find(z=>z.fatura.kod===k);
            return x?H.birimFiyatKwh(x,O.donemAraligi(y,1,y,12)):null;};
          return { e18:al("ELK_FATURA_TL",2018), e25:al("ELK_FATURA_TL",2025),
                   g25:al("DG_FATURA_TL",2025) };}""")
        ok("Elektrik 2018 birim fiyatı 0,2942 TL/kWh", yakin(bf["e18"],0.2942,0.0002), f'{bf["e18"]:.4f}')
        ok("Elektrik 2018 → 2025 artışı 11 kat", yakin(bf["e25"]/bf["e18"],11.0,0.3),
           f'{bf["e25"]/bf["e18"]:.1f}×')
        ok("Doğalgaz m³ fiyatı kWh'e çevrildi (14,6266 ÷ 10,92)",
           yakin(bf["g25"],14.6266/10.92,0.0005), f'{bf["g25"]:.4f} TL/kWh')

        # -------------------------------------------------------- GES (K-03)
        print("\n=== 9.12 GES (K-03) ===")
        ges=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const d=O.donemAraligi(2025,1,2025,12);
          const ts=H.ayriTesisler();
          const o=ts.map(x=>({kod:x.varlik.kod, ...H.ayriTesisOzeti(x,d)}));
          // GES üretimi toplam enerjiye GİRMEMELİ
          const te=H.toplamEnerji(2025,6,"kWh");
          return { tesis:o, kalemler:te.kalemler.map(k=>k.kod) };}""")
        ok("Ayrı tesisler rol taramasıyla bulundu",
           {x["kod"] for x in ges["tesis"]}=={"GES_YOZGAT","GES_ADANA"},
           str([x["kod"] for x in ges["tesis"]]))
        toplamU=sum(x["uretim"] or 0 for x in ges["tesis"])
        toplamG=sum(x["gelir"] or 0 for x in ges["tesis"])
        ok("GES 2025 üretimi > 0", toplamU>0, f"{toplamU:,.0f} kWh")
        ok("GES 2025 mali katkısı = mahsup toplamı", yakin(toplamG,m["mahsup"],2), f"{toplamG:,.0f} TL")
        ok("GES üretimi toplam enerjiye GİRMİYOR (K-03)",
           not any(k.startswith("GES_") for k in ges["kalemler"]), str(ges["kalemler"]))

        # ------------------------------------------------------- ekran çizimi
        print("\n=== EKRANLAR ÇİZİLİYOR ===")
        for no,ad,bekle in [(9,"verimlilik","Dönüşüm Verimliliği"),
                            (10,"maliyet","Maliyet"),(11,"ges","GES")]:
            s.evaluate(f'__req("js/uygulama.js").git({no})'); s.wait_for_timeout(2200)
            r=s.evaluate("""()=>{
              // mini çubuklar aria-hidden; gerçek grafikler role="img"
              const svgler=[...document.querySelectorAll('#icerik svg[role="img"]')];
              return { h1:document.querySelector("#icerik h1")?.innerText||"",
                svg:svgler.length,
                kesikli:svgler.some(v=>[...v.querySelectorAll("*")]
                  .some(e=>e.getAttribute("stroke-dasharray"))),
                tabloDugmesi:[...document.querySelectorAll("#icerik button")]
                  .filter(b=>b.textContent.includes("Tablo olarak göster")).length,
                kart:document.querySelectorAll("#icerik .kart").length,
                bos:!!document.querySelector("#icerik .bos"),
                hataKutusu:!!document.querySelector("#icerik .uyari.kritik") };}""")
            print(f"  — Ekran {no} · {bekle}")
            ok("başlık", r["h1"]==bekle, r["h1"])
            ok("ekran çizildi (hata kutusu yok)", not r["hataKutusu"] and not r["bos"])
            ok("SVG grafik var", r["svg"]>0, f'{r["svg"]} svg · {r["kart"]} kart')
            ok("kesikli çizgi yok (5.7.2)", not r["kesikli"])
            ok("her grafikte 'Tablo olarak göster'", r["tabloDugmesi"]>=r["svg"],
               f'{r["tabloDugmesi"]} düğme / {r["svg"]} grafik')
            s.screenshot(path=str(SS/f"f4-{no:02d}-{ad}.png"), full_page=True)

        print("\n=== S12 · KATSAYI DEĞİŞİMİ DÜRÜSTLÜĞÜ (İ-5) ===")
        kk=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const k=H.katsayiKarsilastir("BUH","kg","kWh",{yil:2024,ay:12},{yil:2025,ay:12});
          const t25=H.donusumVerimiAralik("TURBIN",O.donemAraligi(2025,1,2025,12));
          const duz=H.verimKatsayiDuzeltmesi(t25,k.oran);
          return { ayni:k.ayni, a:k.a.katsayi, b:k.b.katsayi,
                   olculen:t25.toplamVerim, duzeltilmis:duz.toplamVerim };}""")
        ok("2024 buhar katsayısı 0,697674 (600/860)", yakin(kk["a"],600/860,1e-9), f'{kk["a"]:.6f}')
        ok("2025 buhar katsayısı 0,651163 (560/860)", yakin(kk["b"],560/860,1e-9), f'{kk["b"]:.6f}')
        ok("Katsayı değişimi tespit edildi", not kk["ayni"])
        ok("Eski katsayıyla 2025 verimi %52,0 olurdu",
           yakin(kk["duzeltilmis"]*100,52.0,0.15), f'%{kk["duzeltilmis"]*100:.1f}')
        ok("Düşüşün ~1,7 puanı varsayım değişiminden",
           yakin((kk["duzeltilmis"]-kk["olculen"])*100,1.7,0.15),
           f'{(kk["duzeltilmis"]-kk["olculen"])*100:.1f} puan')

        print("\n=== EKRAN 9 · METİNDE VAKANIN ADI GEÇİYOR ===")
        s.evaluate('__req("js/uygulama.js").git(9)'); s.wait_for_timeout(1800)
        m9=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Türbin kartı var", "Türbin" in m9)
        ok("Verim düşüşü uyarısı gösteriliyor", "puan düştü" in m9)
        ok("Ekipman kümesi değişimi uyarısı var (karma toplam kıyaslanmaz)",
           "Ekipman kümesi" in m9 and "Devreden çıkan" in m9)
        ok("Karşılaştırma yalnız aynı ekipmanlar üzerinden",
           "İki yılda da çalışan" in m9 and "verim düştü" in m9)
        ok("Birleşik verim yüzdesinin kıyaslanamazlığı yazılı",
           "birleşik" in m9 and "yıllar arası okunamaz" in m9)
        ok("Kaybın TL karşılığı yazıyor", "TL" in m9)
        ok("Katsayı değişimi ekranda uyarı olarak duruyor",
           "katsayısı" in m9 and "değişti" in m9)

        print("\n=== S13 · İMKÂNSIZ VERİM VE ATANMAMIŞ YAKIT (İ-3, A-05) ===")
        tz=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const d=O.donemAraligi(2025,1,2025,12);
          const g=k=>H.donusumVerimiAralik(k,d);
          return { k1:g("KAZAN1"), k2:g("KAZAN2"), tur:g("TURBIN"),
                   atan:H.atanmamisYakit(d) };}""")
        ok("Kazan-1 2025 verimi imkânsız olarak işaretlendi", tz["k1"]["imkansiz"],
           f'%{tz["k1"]["toplamVerim"]*100:.0f}')
        ok("Kazan-2 2025 verimi imkânsız olarak işaretlendi", tz["k2"]["imkansiz"],
           f'%{tz["k2"]["toplamVerim"]*100:.0f}')
        ok("Türbin verimi tutarlı (işaretlenmedi)", not tz["tur"]["imkansiz"])
        dg=next(a for a in tz["atan"] if a["enerji_turu"]=="DG")
        ok("Doğalgazın ekipmana atanmamış payı hesaplanıyor",
           yakin(dg["atanmamis"],15536149,3), f'{dg["atanmamis"]:,.0f} kWh (%{dg["oran"]*100:.1f})')
        ok("Motorin ekipman yakıtı olarak sayılmıyor (kg, kWh değil)",
           all(a["enerji_turu"]!="ELK" for a in tz["atan"]))
        m9b=s.evaluate("""()=>{__req("js/uygulama.js").git(9); return null;}""")
        s.wait_for_timeout(1800)
        m9c=s.evaluate('document.querySelector("#icerik").innerText')
        ok("İmkânsız verim ekranda ciddi uyarı olarak duruyor",
           "fiziksel olarak imkânsız" in m9c or "yakıttan büyük" in m9c)
        ok("Atanmamış yakıt uyarısı ekranda", "atanmamış" in m9c)
        ok("Tutarsız ekipman karşılaştırmadan çıkarıldı", "verisi tutarlı" in m9c)

        print("\n=== EKRAN 10 · AYRIŞTIRMA METNİ ===")
        s.evaluate('__req("js/uygulama.js").git(10)'); s.wait_for_timeout(1800)
        m10=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Fiyat etkisi gösteriliyor", "Fiyat etkisi" in m10)
        ok("Hacim etkisi gösteriliyor", "Hacim etkisi" in m10)
        ok("Tasarruf yorumu yapılıyor", "tasarruf" in m10.lower())
        ok("GES mahsubu özet içinde", "GES mahsubu" in m10)

        print("\n=== EKRAN 11 · K-03 KURALI EKRANDA YAZILI ===")
        s.evaluate('__req("js/uygulama.js").git(11)'); s.wait_for_timeout(1800)
        m11=s.evaluate('document.querySelector("#icerik").innerText')
        ok("K-03 uyarısı ekranda", "EnPI'sine girmez" in m11 or "girmez" in m11)
        ok("Her iki santral listelendi", "Yozgat" in m11 and "Adana" in m11)

        print("\n=== KOYU TEMA ===")
        s.evaluate('document.documentElement.dataset.tema="koyu"')
        for no in (9,10,11):
            s.evaluate(f'__req("js/uygulama.js").git({no})'); s.wait_for_timeout(1400)
            s.screenshot(path=str(SS/f"f4-{no:02d}-koyu.png"), full_page=True)
        ok("Koyu temada çiziliyor", s.locator("#icerik svg").count()>0)
        t.close()

    print("\n"+"="*52)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} hata" if hata else ""))
    for h in hata[:8]: print("   !",h[:170])
    return 1 if (kaldi or hata) else 0
sys.exit(main())
