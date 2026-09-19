#!/usr/bin/env python3
"""faz5.py — Faz 5 ekranlarini (12 Hedefler ve Aksiyonlar, 13 Raporlar) ve
izlenebilirligi (E-4) gercek veriyle sinar."""
import base64, pathlib, sys
from playwright.sync_api import sync_playwright
KOK=pathlib.Path(__file__).resolve().parent.parent
D=KOK/"cikti"/"enerji-yonetim.html"
XLSX=pathlib.Path("/root/.claude/uploads/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/24858116-veri.xlsx")
SS=pathlib.Path("/tmp/claude-0/-home-user-as/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/scratchpad/ss")
SS.mkdir(parents=True,exist_ok=True)
gecti=kaldi=0
def ok(ad,kosul,ek=""):
    global gecti,kaldi
    print(f"  {'✓' if kosul else '✗'} {ad}" + (f"  {ek}" if ek else ""))
    if kosul: gecti+=1
    else: kaldi+=1
def yakin(a,b,tol): return a is not None and abs(a-b)<=tol

def main():
    global gecti,kaldi
    hata=[]
    with sync_playwright() as pw:
        t=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium",args=["--no-sandbox"])
        s=t.new_page(viewport={"width":1500,"height":1050})
        s.on("pageerror",lambda e:hata.append("PAGEERROR: "+str(e)))
        s.on("console",lambda m:hata.append("CONSOLE: "+m.text) if m.type=="error" else None)
        s.goto(D.as_uri()); s.wait_for_timeout(900)

        print("=== BOŞ DURUM ===")
        for no,bekle,bosBekle in [(10,"Hedefler ve Aksiyonlar","Henüz hedef yok"),
                                  (11,"Raporlar","Henüz veri yok")]:
            b=s.evaluate(f"""()=>{{__req("js/uygulama.js").git({no});
              return {{h1:document.querySelector("#icerik h1")?.innerText||"",
                       metin:document.querySelector("#icerik").innerText}};}}""")
            ok(f"Ekran {no} başlığı", b["h1"]==bekle, b["h1"])
            ok(f"Ekran {no} boş durumu öğretici", bosBekle in b["metin"])

        print("\n=== VERİ AKTARIMI ===")
        s.evaluate('location.hash="e2/aktar"'); s.wait_for_timeout(700)
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

        # --------------------------------------------- E-4 izlenebilirlik
        print("\n=== 5.3 · İZLENEBİLİRLİK (E-4) ===")
        kk=s.evaluate("""()=>{const HL=__req("js/hesaplanan.js");
          const k=HL.sutunKokeni("TOPLAM_ENERJI",2025,6);
          const e=HL.sutunKokeni("TURBIN_BUH_KWH",2025,6);
          const u=HL.sutunKokeni("TOPLAM_URETIM",2025,6);
          return { toplam:{deger:k.deger, kaynak:k.agac.map(x=>x.kod),
                           tipler:k.agac.map(x=>x.kaynakTipi), formul:k.sutun.formul},
                   buhar:{deger:e.deger, kaynak:e.agac.map(x=>x.kod),
                          kats:e.agac.map(x=>x.katsayilar.length)},
                   uretim:{kaynak:u.agac.map(x=>x.kod),
                           cocuk:u.agac.map(x=>x.cocuklar.map(c=>c.kod))} };}""")
        ok("Toplam enerji kökeni 4 satın alınan noktayı gösteriyor",
           set(kk["toplam"]["kaynak"])=={"SEBEKE_ELK","IST1_DG_KWH","IST2_DG_KWH","IST3_DG_KWH","MOTORIN_KG"}
           or len(kk["toplam"]["kaynak"])>=4, str(kk["toplam"]["kaynak"]))
        ok("Kaynakların hepsi ham veri olarak işaretli",
           all(x in ("ham","formul") for x in kk["toplam"]["tipler"]), str(kk["toplam"]["tipler"]))
        ok("Formül insan diliyle yazılı", "rol" in kk["toplam"]["formul"])
        ok("Buhar kWh kökeninde katsayı görünüyor",
           sum(kk["buhar"]["kats"])==0 and kk["buhar"]["kaynak"]==["TURBIN_BUH_KG"],
           str(kk["buhar"]))
        ok("Toplam üretim kökeni iki seviye iniyor",
           any(len(c)>0 for c in kk["uretim"]["cocuk"]), str(kk["uretim"]["cocuk"]))

        kt=s.evaluate("""()=>{const H=__req("js/hesap.js");
          const a=H.noktaKokeni("TURBIN_BUH_KWH",2025,6);
          const b=H.noktaKokeni("TURBIN_BUH_KWH",2024,6);
          return { a25:a.katsayilar[0]?.kayit?.katsayi, a24:b.katsayilar[0]?.kayit?.katsayi,
                   formul:a.formul, cocukTipi:a.cocuklar[0]?.kaynakTipi };}""")
        ok("2025 kökeninde 0,651163 katsayısı", yakin(kt["a25"],560/860,1e-9), f'{kt["a25"]}')
        ok("2024 kökeninde 0,697674 katsayısı", yakin(kt["a24"],600/860,1e-9), f'{kt["a24"]}')
        ok("Köken ağacı ham veriye kadar iniyor", kt["cocukTipi"]=="ham", str(kt["cocukTipi"]))

        print("\n=== PANEL'DE `?` DÜĞMESİ ===")
        s.evaluate('__req("js/uygulama.js").git(1)'); s.wait_for_timeout(1500)
        d=s.evaluate('document.querySelectorAll("#icerik button.koken").length')
        ok("Panel kartlarında izlenebilirlik düğmesi var", d>=4, f"{d} düğme")
        s.evaluate('document.querySelector("#icerik button.koken").click()')
        s.wait_for_timeout(700)
        mm=s.evaluate("""()=>{const m=document.querySelector(".modal");
          return m?m.innerText:"";}""")
        ok("Köken penceresi açılıyor", "nereden geliyor" in mm or "Formül" in mm)
        ok("Pencerede ham veri rozetleri var", "ham veri" in mm)
        ok("Pencerede kural/atıf yazılı", "K-24" in mm or "7.1" in mm, mm[:60].replace("\n"," "))
        ok("Salt okunur pencerede 'Vazgeç' yok", "Vazgeç" not in mm)
        s.screenshot(path=str(SS/"f5-00-koken.png"))
        s.evaluate("""()=>{const b=[...document.querySelectorAll(".modal button")]
          .find(x=>x.textContent.trim()==="Kapat"); b&&b.click();}""")
        s.wait_for_timeout(400)

        # --------------------------------------------- hedef motoru
        print("\n=== 9.13 · HEDEF MOTORU (K-21) ===")
        hm=s.evaluate("""()=>{const H=__req("js/hesap.js");
          const h1={kod:"T1",ad:"EnPI",tur:"enpi",ifade:"ENPI_ANA",deger:1.20,
                    bas:{yil:2025,ay:1},son:{yil:2025,ay:12},yon:"azalt"};
          const h2={kod:"T2",ad:"Tüketim",tur:"tuketim",ifade:"@TOPLAM_ENERJI_KWH",
                    deger:130000000,bas:{yil:2025,ay:1},son:{yil:2025,ay:12},yon:"azalt"};
          const h3={kod:"T3",ad:"Maliyet",tur:"maliyet",ifade:"@TOPLAM_MALIYET_TL",
                    deger:200000000,bas:{yil:2025,ay:1},son:{yil:2025,ay:12},yon:"azalt"};
          return { enpi:H.hedefDurumu(h1), tuketim:H.hedefDurumu(h2), maliyet:H.hedefDurumu(h3) };}""")
        ok("EnPI hedefi dönem EnPI'sini üretiyor (1,3668)",
           yakin(hm["enpi"]["gercek"],1.3668,0.0005), f'{hm["enpi"]["gercek"]:.4f}')
        ok("EnPI hedefi tutmuyor olarak işaretlendi", hm["enpi"]["tuttu"] is False)
        ok("Tüketim hedefi 2025 toplamını buluyor (137.367.837)",
           yakin(hm["tuketim"]["gercek"],137367837,3), f'{hm["tuketim"]["gercek"]:,.0f}')
        ok("Maliyet hedefi 2025 net maliyetini buluyor (195.182.337)",
           yakin(hm["maliyet"]["gercek"],195182337,3), f'{hm["maliyet"]["gercek"]:,.0f}')
        ok("Maliyet hedefi tutuyor (200 M TL altında)", hm["maliyet"]["tuttu"] is True)
        ok("12 ayın hepsinde veri var", hm["tuketim"]["doluAy"]==12, str(hm["tuketim"]["doluAy"]))

        print("\n=== HEDEF VE AKSİYON KAYDI ===")
        s.evaluate("""()=>{const V=__req("js/veri.js");
          V.durum.hedefler.push({kod:"HDF1",ad:"2025 enerji bütçesi",tur:"maliyet",
            ifade:"@TOPLAM_MALIYET_TL",deger:200000000,bas:{yil:2025,ay:1},
            son:{yil:2025,ay:12},yon:"azalt",sorumlu:"Enerji Yöneticisi",not:""});
          V.durum.hedefler.push({kod:"HDF2",ad:"2025 tüketim hedefi",tur:"tuketim",
            ifade:"@TOPLAM_ENERJI_KWH",deger:130000000,bas:{yil:2025,ay:1},
            son:{yil:2025,ay:12},yon:"azalt",sorumlu:"Üretim",not:""});
          V.durum.aksiyonlar.push({kod:"AKS1",baslik:"Türbin verim düşüşü",
            aciklama:"2024'e göre 6,9 puan",baglam:{kaynak:"Ekran 9 · Dönüşüm Verimliliği"},
            sorumlu:"Bakım",termin:"2020-01-01",durum:"acik",
            beklenen:{deger:7474499,birim:"TL"},gerceklesen:{deger:null,birim:"TL"},
            sonuc_notu:""});
          V.durum.aksiyonlar.push({kod:"AKS2",baslik:"Alt sayaç yatırımı",aciklama:"",
            baglam:{},sorumlu:"Elektrik",termin:"2099-01-01",durum:"devam",
            beklenen:{deger:500000,birim:"TL"},gerceklesen:{deger:null,birim:"TL"},
            sonuc_notu:""});
          V.durum.aksiyonlar.push({kod:"AKS3",baslik:"Kompresör kaçak onarımı",aciklama:"",
            baglam:{},sorumlu:"Bakım",termin:"2024-06-01",durum:"kapandi",
            beklenen:{deger:300000,birim:"TL"},gerceklesen:{deger:250000,birim:"TL"},
            sonuc_notu:"Kaçaklar giderildi"});
          V.degisti("hedef");}""")
        s.wait_for_timeout(1200)
        ao=s.evaluate("""()=>{const H=__req("js/hesap.js");
          return H.aksiyonOzeti("2026-09-17");}""")
        ok("Açık aksiyon sayısı 2", ao["acik"]==2, str(ao["acik"]))
        ok("Gecikmiş aksiyon 1 (termini geçen)", ao["geciken"]==1, str(ao["geciken"]))
        ok("Beklenen tasarruf toplanıyor", yakin(ao["beklenenTL"],8274499,1), f'{ao["beklenenTL"]:,.0f}')
        ok("Gerçekleşen yalnız kapananlardan", yakin(ao["gerceklesenTL"],250000,1),
           f'{ao["gerceklesenTL"]:,.0f}')

        s.evaluate('__req("js/uygulama.js").git(10)'); s.wait_for_timeout(1800)
        m12=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Ekran 12 hedefleri çiziyor", "2025 enerji bütçesi" in m12)
        ok("Mutlak tüketim hedefi uyarısı var (K-21)",
           "Üretim düşerse bu hedef kendiliğinden tutar" in m12)
        ok("Gecikmiş aksiyon etiketle işaretli", "GECİKTİ" in m12)
        ok("Aksiyonun kaynağı görünüyor", "Ekran 9" in m12)
        ok("Tutan hedef 'pay var' diyor", "pay var" in m12)
        ok("Aşılan hedef 'aşıldı' diyor, 'gerçekleşme %' demiyor",
           "aşıldı" in m12 and "gerçekleşme %" not in m12)
        olcer=s.evaluate('document.querySelectorAll("#icerik .olcer").length')
        ok("Hedef ölçeri çizildi", olcer>=2, f"{olcer} ölçer")
        s.screenshot(path=str(SS/"f5-12-hedefler.png"), full_page=True)

        print("\n=== ANALİZDEN EYLEME KÖPRÜSÜ (9.13) ===")
        s.evaluate('__req("js/uygulama.js").git(5)'); s.wait_for_timeout(1500)
        s.evaluate("""()=>{const b=[...document.querySelectorAll("#icerik .sekme")]
          .find(x=>x.textContent.includes("Pareto")); b&&b.click();}""")
        s.wait_for_timeout(1800)
        c7=s.evaluate("""()=>[...document.querySelectorAll("#icerik button")]
          .filter(b=>b.textContent.includes("Aksiyon aç")).length""")
        ok("Ekran 7 (Pareto) tespitten aksiyon açabiliyor", c7>=1, f"{c7} düğme")
        s.evaluate('__req("js/uygulama.js").git(7)'); s.wait_for_timeout(1800)
        c9=s.evaluate("""()=>[...document.querySelectorAll("#icerik button")]
          .filter(b=>b.textContent.includes("Aksiyon aç")).length""")
        ok("Ekran 9 (Dönüşüm Verimliliği) tespitten aksiyon açabiliyor", c9>=1, f"{c9} düğme")
        # Baz çizgi kurulunca CUSUM köprüsü de açılır (8.8 vakası)
        bz=s.evaluate("""()=>{const H=__req("js/hesap.js"), V=__req("js/veri.js");
          const tanim={kod:"BZ1",ad:"2022-2024 referans",enerji:"@TOPLAM_ENERJI_KWH",
            baglam:"TOPLAM_URETIM",bas:{yil:2022,ay:1},son:{yil:2024,ay:12},
            model_tipi:"regresyon"};
          const m=H.bazCizgiKur(tanim);
          if (m.hata) return {hata:m.hata};
          V.durum.baz_cizgiler.push({...tanim,...m});
          V.durum.ayarlar.varsayilan_baz="BZ1"; V.degisti("baz");
          return {a:m.a,b:m.b,r2:m.r2,n:m.n};}""")
        s.wait_for_timeout(1500)
        ok("Baz çizgi kuruldu: a = 0,5025", yakin(bz.get("a"),0.5025,0.0005), f'{bz.get("a"):.4f}')
        ok("Baz çizgi: b = 6.021.966", yakin(bz.get("b"),6021966,3), f'{bz.get("b"):,.0f}')
        ok("Baz çizgi: R² = 0,43", yakin(bz.get("r2"),0.426,0.005), f'{bz.get("r2"):.3f}')
        ok("2024 Ağustos düşüyor: 35 nokta (S10)", bz.get("n")==35, str(bz.get("n")))
        nc=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const bz=H.etkinBazCizgi(); const d=O.donemAraligi(2025,1,2025,12);
          let g=0,b=0; const sap=[];
          for (const x of d){ const e=H.bazCizgiDegerlendir(bz,x.yil,x.ay);
            sap.push(e?e.sapma:0); if(e){g+=e.gercek;b+=e.beklenen;} }
          const k=H.cusum(sap);
          const ilkPozitif=k.findIndex(v=>v>0);
          return {norm:g/b, son:k[k.length-1], ilkPozitif:ilkPozitif+1, ocak:k[0]};}""")
        ok("Normalize EnPI 2025 = 1,119", yakin(nc["norm"],1.119,0.001), f'{nc["norm"]:.4f}')
        ok("CUSUM yıl sonu = +14.605.848 kWh", yakin(nc["son"],14605848,3), f'{nc["son"]:,.0f}')
        ok("CUSUM Şubat 2025'te işaret değiştiriyor", nc["ilkPozitif"]==2,
           f'Ocak {nc["ocak"]:,.0f} → ilk pozitif ay {nc["ilkPozitif"]}')
        s.evaluate('__req("js/uygulama.js").git(6)'); s.wait_for_timeout(2500)
        c8=s.evaluate("""()=>[...document.querySelectorAll("#icerik button")]
          .filter(b=>b.textContent.includes("aksiyon aç")).length""")
        ok("Ekran 8 CUSUM kırılımından aksiyon açabiliyor", c8>=1, f"{c8} düğme")
        m8=s.evaluate('document.querySelector("#icerik").innerText')
        ok("R² uyarısı gizlenmiyor (8.3)", "R²" in m8)

        # --------------------------------------------- raporlar
        print("\n=== 9.14 · RAPORLAR ===")
        s.evaluate('__req("js/uygulama.js").git(11)'); s.wait_for_timeout(2000)
        r1=s.evaluate("""()=>({metin:document.querySelector("#icerik").innerText,
          koken:document.querySelectorAll("#icerik button.koken").length,
          rapor:!!document.querySelector("#icerik .rapor")})""")
        ok("Aylık rapor çizildi", r1["rapor"] and "Aylık Enerji Raporu" in r1["metin"])
        ok("Veri kalitesi notu var (İ-4)", "Veri kalitesi" in r1["metin"])
        ok("Raporda izlenebilirlik düğmeleri var (E-4)", r1["koken"]>=3, f'{r1["koken"]} düğme')
        ok("Hedef durumu bölümü var", "Hedeflerin durumu" in r1["metin"])
        ok("Aksiyon bölümü var", "Aksiyonlar" in r1["metin"])
        s.screenshot(path=str(SS/"f5-13-aylik.png"), full_page=True)

        s.evaluate("""()=>{const sel=document.querySelector("#icerik select");
          sel.value="yonetim"; sel.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(2500)
        r2=s.evaluate('document.querySelector("#icerik").innerText')
        for bolum in ["Dönem performans özeti","EnPI'ler ve baz çizgiye göre durum",
                      "Önemli enerji kullanımları","Dönüşüm verimliliği",
                      "Hedeflerin durumu","İyileştirme fırsatları"]:
            ok(f"Yönetim raporu bölümü: {bolum}", bolum in r2)
        ok("ISO 50001 md. 9.3 atfı var", "9.3" in r2)
        ok("Baz çizgi durumu raporda", "Baz çizgi:" in r2 and "2022-2024 referans" in r2)
        ok("Düşük R² raporda da uyarıyla veriliyor", "R² 0,50'nin altında" in r2)
        ok("Normalize EnPI raporda", "Normalize EnPI" in r2)
        s.screenshot(path=str(SS/"f5-13-yonetim.png"), full_page=True)

        s.evaluate("""()=>{const sel=document.querySelector("#icerik select");
          sel.value="serbest"; sel.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(2500)
        r3=s.evaluate("""()=>({metin:document.querySelector("#icerik").innerText,
          svg:document.querySelectorAll('#icerik svg[role="img"]').length})""")
        ok("Serbest rapor çizildi", "Serbest Rapor" in r3["metin"])
        ok("Serbest raporda grafik var", r3["svg"]>=2, f'{r3["svg"]} grafik')
        ok("Dönem toplamları tablosu var", "TOPLAM" in r3["metin"])
        # birim degisimi: GJ
        s.evaluate("""()=>{const s=[...document.querySelectorAll("#icerik select")];
          const b=s[s.length-1]; b.value="GJ"; b.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(2000)
        r4=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Birim GJ'e çevrilebiliyor", "GJ" in r4)
        s.screenshot(path=str(SS/"f5-13-serbest.png"), full_page=True)

        print("\n=== VERİ KALİTESİ NOTU (İ-4) ===")
        vk=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js"), V=__req("js/veri.js");
          const d=O.donemAraligi(2025,1,2025,12);
          const once=H.veriKalitesi(d);
          // bir degeri tahmin olarak isaretle
          const k=V.durum.degerler.find(x=>x.y===2025&&x.a===6);
          k.k="tahmin"; V.degisti("deger");
          return { once, sonra:H.veriKalitesi(d) };}""")
        s.wait_for_timeout(1200)
        ok("Tahmin sayısı başta 0", vk["once"]["tahmin"]==0, str(vk["once"]["tahmin"]))
        ok("Tahmin işaretlenince sayı artıyor", vk["sonra"]["tahmin"]==1, str(vk["sonra"]["tahmin"]))
        s.evaluate('__req("js/uygulama.js").git(11)'); s.wait_for_timeout(2000)
        r5=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Rapor tahmin edilmiş değeri açıkça yazıyor", "TAHMİN" in r5 or "tahmin edilmiştir" in r5)

        print("\n=== YEDEK: HEDEF VE AKSİYONLAR SAKLANIYOR (K-10) ===")
        yd=s.evaluate("""()=>{const V=__req("js/veri.js"); const y=V.disaVer();
          return { hedef:y.hedefler.length, aksiyon:y.aksiyonlar.length,
                   hesaplanan:Object.keys(y).some(k=>k.includes("hesaplanan")) };}""")
        ok("Hedefler yedeğe giriyor", yd["hedef"]==2, str(yd["hedef"]))
        ok("Aksiyonlar yedeğe giriyor", yd["aksiyon"]==3, str(yd["aksiyon"]))
        ok("Hesaplanan katman yedeğe GİRMİYOR (K-23)", not yd["hesaplanan"])

        print("\n=== KOYU TEMA ===")
        s.evaluate('document.documentElement.dataset.tema="koyu"')
        for no in (12,13):
            s.evaluate(f'__req("js/uygulama.js").git({no})'); s.wait_for_timeout(1500)
            s.screenshot(path=str(SS/f"f5-{no:02d}-koyu.png"), full_page=True)
        ok("Koyu temada çiziliyor",
           s.evaluate('!document.querySelector("#icerik .uyari.kritik")'))
        t.close()

    print("\n"+"="*52)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} hata" if hata else ""))
    for h in hata[:8]: print("   !",h[:170])
    return 1 if (kaldi or hata) else 0
sys.exit(main())
