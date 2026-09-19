#!/usr/bin/env python3
"""izgara.py — Birlesik Veri ekranini ve veri izgarasini sinar (9.3, K-30).

Satir = donem, sutun = olcum noktasi, hucre = deger. Yeni satir/sutun acma,
hucre duzenleme, sorunlu hucrenin renklenmesi ve acilir pencere."""
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

def main():
    global gecti,kaldi
    hata=[]
    with sync_playwright() as pw:
        t=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium",args=["--no-sandbox"])
        s=t.new_page(viewport={"width":1500,"height":1050})
        s.on("pageerror",lambda e:hata.append("PAGEERROR: "+str(e)))
        s.on("console",lambda m:hata.append("CONSOLE: "+m.text) if m.type=="error" else None)
        s.goto(D.as_uri()); s.wait_for_timeout(1000)

        print("=== EKRAN LİSTESİ (K-30: 15 → 13 ekran) ===")
        menu=s.evaluate("""()=>[...document.querySelectorAll("#menu .menu-og")]
          .map(b=>b.innerText.replace(/\\n/g," "))""")
        ok("13 ekran var", len(menu)==13, f"{len(menu)} ekran")
        ok("2. ekran 'Veri'", menu[1].endswith("Veri"), menu[1])
        ok("Ayrı Giriş/Aktarma/Denetim ekranı kalmadı",
           not any("Veri Girişi" in m or "Veri Aktarma" in m or "Veri Denetimi" in m for m in menu))

        print("\n=== DÖRT SEKME TEK EKRANDA ===")
        s.evaluate('location.hash="e2"'); s.wait_for_timeout(900)
        sek=s.evaluate("""()=>[...document.querySelectorAll("#icerik .sekme")].map(b=>b.textContent.trim())""")
        ok("Tablo · Aylık form · Aktar · Denetim",
           [x.split(" (")[0] for x in sek]==["Tablo","Aylık form","Aktar","Denetim"], " | ".join(sek))
        ok("Boş durum iki yolu da anlatıyor",
           "Excel dosyamı aktar" in s.evaluate('document.querySelector("#icerik").innerText'))

        print("\n=== ELLE BAŞLAMA: + DÖNEM ===")
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik .bos button")]
          .find(b=>b.textContent.includes("elle başla")).click();}""")
        s.wait_for_timeout(1200)
        r=s.evaluate("""()=>({satir:document.querySelectorAll("table.izgara tbody tr").length,
          hucre:document.querySelectorAll("table.izgara td.hucre").length})""")
        ok("Boş satır açıldı ve hücreleri var", r["satir"]==1 and r["hucre"]>50,
           f'{r["satir"]} satır · {r["hucre"]} hücre')

        print("\n=== VERİ AKTARIMI (Aktar sekmesi) ===")
        s.evaluate('location.hash="e2/aktar"'); s.wait_for_timeout(800)
        s.evaluate("""async (b)=>{const h=Uint8Array.from(atob(b),c=>c.charCodeAt(0));
          const dt=new DataTransfer(); dt.items.add(new File([h],"veri.xlsx"));
          const g=document.querySelector('#icerik input[type=file][accept=".xlsx"]');
          g.files=dt.files; g.dispatchEvent(new Event("change",{bubbles:true}));}""",
          base64.b64encode(XLSX.read_bytes()).decode())
        s.wait_for_timeout(2800); s.get_by_role("button",name="Önizle →").click(); s.wait_for_timeout(2800)
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik button.dugme.ana")]
          .find(b=>b.textContent.includes("geçerli değeri aktar")).click();}""")
        s.wait_for_timeout(900)
        s.evaluate("""()=>{const b=[...document.querySelectorAll(".modal button.dugme.ana")].pop(); b&&b.click();}""")
        s.wait_for_timeout(5000)
        n=s.evaluate('__req("js/veri.js").durum.degerler.length')
        ok("Başlık satırı 1'de olsa da doğru okundu", n==5097, f"{n:,} değer")

        print("\n=== IZGARA ===")
        s.evaluate('location.hash="e2/tablo"'); s.wait_for_timeout(1500)
        s.evaluate("""()=>{const sel=document.querySelectorAll("#icerik select")[0];
          sel.value=""; sel.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(2600)
        r=s.evaluate("""()=>({satir:document.querySelectorAll("table.izgara tbody tr").length,
          sutun:document.querySelectorAll("table.izgara thead tr:nth-child(2) th").length-2,
          hucre:document.querySelectorAll("table.izgara td.hucre").length,
          grup:document.querySelectorAll("table.izgara thead tr:nth-child(1) th.grup").length,
          uyar:document.querySelectorAll("table.izgara td.uyar").length,
          yil:document.querySelector("table.izgara tbody th.d1").innerText,
          ay:document.querySelector("table.izgara tbody th.d2").innerText})""")
        # 99 dönem dosyadan + 1 dönem elle açıldı (yukarıdaki "+ Dönem" adımı)
        ok("100 dönem satırı (99 dosyadan + 1 elle açılan)", r["satir"]==100, str(r["satir"]))
        ok("57 ölçüm noktası sütunu", r["sutun"]==57, str(r["sutun"]))
        ok("Sütunlar varlığa göre gruplanmış", r["grup"]>5, f'{r["grup"]} grup')
        ok("İlk satır 2018 Ocak", r["yil"]=="2018" and r["ay"]=="Ocak", f'{r["yil"]} {r["ay"]}')
        ok("Sorunlu hücreler renklendirildi", r["uyar"]>100, f'{r["uyar"]} uyarı hücresi')
        s.screenshot(path=str(SS/"iz-1-tablo.png"))

        print("\n=== AÇILIR PENCERE (her zaman en üstte) ===")
        s.evaluate("""()=>{const sel=document.querySelectorAll("#icerik select")[0];
          sel.value="2025"; sel.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(1500)
        kutu=s.evaluate("""()=>{const td=document.querySelector("table.izgara td.uyar");
          td.scrollIntoView({block:"center"});
          const r=td.getBoundingClientRect(); return {x:r.x+r.width/2, y:r.y+r.height/2};}""")
        s.mouse.move(kutu["x"], kutu["y"]); s.wait_for_timeout(300)
        s.mouse.move(kutu["x"]+2, kutu["y"]+1); s.wait_for_timeout(500)
        ip=s.evaluate("""()=>{const d=document.querySelector(".ipucu");
          return {gorunur:d&&getComputedStyle(d).display!=="none",
                  z:+getComputedStyle(d).zIndex, metin:d?d.innerText:""};}""")
        ok("Fare üstüne gelince pencere açılıyor", ip["gorunur"])
        ok("Pencere en üstte (z-index modalden büyük)", ip["z"]>=9999, str(ip["z"]))
        ok("Pencerede bulgunun nedeni yazılı",
           "UYARI" in ip["metin"] and len(ip["metin"])>40, ip["metin"].replace("\n"," | ")[:90])
        s.screenshot(path=str(SS/"iz-2-ipucu.png"))
        s.mouse.move(5,5); s.wait_for_timeout(300)
        ok("Fare çekilince pencere kapanıyor",
           not s.evaluate("""()=>{const d=document.querySelector(".ipucu");
             return d&&getComputedStyle(d).display!=="none";}"""))

        print("\n=== HÜCRE DÜZENLEME ===")
        d=s.evaluate("""()=>{const td=[...document.querySelectorAll("table.izgara td.hucre")]
            .find(x=>x.dataset.kod==="SEBEKE_ELK");
          return {kod:td.dataset.kod, don:td.dataset.d};}""")
        onceki=s.evaluate(f"""()=>{{const V=__req("js/veri.js");
          const [y,a]="{d['don']}".split("-").map(Number); return V.deger("{d['kod']}",y,a);}}""")
        s.locator(f'td.hucre[data-kod="{d["kod"]}"][data-d="{d["don"]}"]').click()
        s.wait_for_timeout(400)
        ok("Tıklayınca düzenleme kutusu açılıyor",
           s.evaluate('!!document.querySelector("table.izgara input.duzen")'))
        s.locator("table.izgara input.duzen").fill("1.234.567,5")
        s.keyboard.press("Enter"); s.wait_for_timeout(1200)
        yeni=s.evaluate(f"""()=>{{const V=__req("js/veri.js");
          const [y,a]="{d['don']}".split("-").map(Number); return V.deger("{d['kod']}",y,a);}}""")
        ok("Türkçe biçimli değer doğru yazıldı", yeni==1234567.5, str(yeni))
        ok("Enter bir alt satıra geçiyor",
           s.evaluate("""()=>document.activeElement.dataset.d""")=="2025-02",
           s.evaluate("""()=>document.activeElement.dataset.d"""))
        # geri al
        s.evaluate(f"""()=>{{const V=__req("js/veri.js");
          const [y,a]="{d['don']}".split("-").map(Number);
          V.degerYaz("{d['kod']}",y,a,{onceki},{{k:"girildi"}});}}""")
        s.wait_for_timeout(900)

        print("\n=== KURAL DIŞI DEĞER YAZILAMAZ (6.8) ===")
        s.locator(f'td.hucre[data-kod="{d["kod"]}"][data-d="{d["don"]}"]').click()
        s.wait_for_timeout(400)
        s.locator("table.izgara input.duzen").fill("-500")
        s.keyboard.press("Enter"); s.wait_for_timeout(900)
        v2=s.evaluate(f"""()=>{{const V=__req("js/veri.js");
          const [y,a]="{d['don']}".split("-").map(Number); return V.deger("{d['kod']}",y,a);}}""")
        ok("Negatif değer hücreye yazılmadı", v2==onceki, str(v2))
        s.keyboard.press("Escape"); s.wait_for_timeout(600)

        print("\n=== YENİ SÜTUN (ölçüm noktası) ===")
        once=s.evaluate('__req("js/veri.js").durum.olcum_noktalari.length')
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik button")]
          .find(b=>b.textContent.includes("+ Ölçüm noktası")).click();}""")
        s.wait_for_timeout(700)
        ok("Ölçüm noktası formu açılıyor",
           s.evaluate("""()=>document.querySelector(".modal h2")?.innerText""")=="Yeni ölçüm noktası")
        s.evaluate("""()=>{const m=document.querySelector(".modal");
          m.querySelector("#n_kod").value="IZGARA_TEST";
          m.querySelector("#n_ad").value="Izgara Deneme";
          [...m.querySelectorAll("button")].find(b=>b.textContent.trim()==="Kaydet").click();}""")
        s.wait_for_timeout(1600)
        ok("Yeni nokta tanımlandı",
           s.evaluate('__req("js/veri.js").durum.olcum_noktalari.length')==once+1)
        ok("Yeni sütun tabloda göründü",
           s.evaluate("""()=>[...document.querySelectorAll("table.izgara th.nokta")]
             .some(th=>th.innerText.includes("Izgara Deneme"))"""))

        print("\n=== YENİ SATIR (dönem) ===")
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik button")]
          .find(b=>b.textContent.includes("+ Dönem")).click();}""")
        s.wait_for_timeout(600)
        s.evaluate("""()=>{const m=document.querySelector(".modal");
          const sel=m.querySelector("select"); sel.value="6";
          sel.dispatchEvent(new Event("change",{bubbles:true}));
          const inp=m.querySelector("input[type=number]"); inp.value="2030";
          inp.dispatchEvent(new Event("input",{bubbles:true}));
          [...m.querySelectorAll("button")].find(b=>b.textContent.trim()==="Ekle").click();}""")
        s.wait_for_timeout(1400)
        ek=s.evaluate('__req("js/veri.js").durum.ayarlar.ek_donemler||[]')
        ok("Dönem kaydedildi (boş satır kalıcı)", "2030-06" in ek, str(ek))
        ok("Yeni satır tabloda", s.evaluate("""()=>[...document.querySelectorAll("table.izgara tbody th.d1")]
          .some(th=>th.innerText==="2030")"""))
        s.screenshot(path=str(SS/"iz-3-yeni.png"))

        print("\n=== BOŞ YIL SÜZGECİ: ÇIKIŞ YOLU ===")
        # verisi olmayan bir yıl seçiliymiş gibi davran, sonra yeniden çizdir
        s.evaluate('__req("js/ekranlar/izgara.js").durum.yil=2029')
        s.evaluate('location.hash="e2/denetim"'); s.wait_for_timeout(900)
        s.evaluate('location.hash="e2/tablo"'); s.wait_for_timeout(1400)
        bos=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Veri olmayan yılda çıkış yolu gösteriliyor",
           "Bütün yılları göster" in bos and "Başka yıllarda veri var" in bos,
           [l for l in bos.split("\n") if "kayıt yok" in l][:1])
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik button")]
          .find(b=>b.textContent==="Bütün yılları göster")?.click();}""")
        s.wait_for_timeout(2000)
        ok("Düğme bütün yılları geri getiriyor",
           s.evaluate('document.querySelectorAll("table.izgara tbody tr").length')>50)

        print("\n=== HESAPLANAN SÜTUNLAR (salt okunur) ===")
        s.evaluate("""()=>{const sel=document.querySelectorAll("#icerik select")[1];
          sel.value="tumu"; sel.dispatchEvent(new Event("change",{bubbles:true}));}""")
        s.wait_for_timeout(2000)
        tu=s.evaluate("""()=>({turetilmis:document.querySelectorAll("table.izgara td.turetilmis").length,
          sutun:document.querySelectorAll("table.izgara thead tr:nth-child(2) th").length-2})""")
        ok("Hesaplanan sütunlar da gösteriliyor", tu["sutun"]>60, f'{tu["sutun"]} sütun')
        ok("Hesaplanan hücreler ayrı biçimde ve salt okunur", tu["turetilmis"]>0,
           f'{tu["turetilmis"]} hücre')
        kutu=s.evaluate("""()=>{const td=document.querySelector("table.izgara td.turetilmis");
          td.scrollIntoView({block:"center",inline:"center"});
          const r=td.getBoundingClientRect(); return {x:r.x+r.width/2, y:r.y+r.height/2};}""")
        s.mouse.move(kutu["x"], kutu["y"]); s.wait_for_timeout(300)
        s.mouse.move(kutu["x"]+2, kutu["y"]+1); s.wait_for_timeout(500)
        ok("Hesaplanan hücrenin penceresinde açıklaması yazıyor",
           "hesaplanır" in (s.evaluate('()=>{const d=document.querySelector(".ipucu"); return d?d.innerText:"";}') or ""))

        print("\n=== DENETİM SEKMESİ AYNI EKRANDA ===")
        s.evaluate('location.hash="e2/denetim"'); s.wait_for_timeout(2500)
        m=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Denetim gövdesi birleşik ekranda", "Doğrulama bulguları" in m)
        ok("Bulgu türü gruplaması duruyor", "Faydalı enerji yakıttan büyük" in m)
        ok("Başlık hâlâ tek: Veri", s.evaluate('document.querySelector("#icerik h1").innerText')=="Veri")
        t.close()

    print("\n"+"="*52)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} hata" if hata else ""))
    for h in hata[:8]: print("   !",h[:170])
    return 1 if (kaldi or hata) else 0
sys.exit(main())
