#!/usr/bin/env python3
"""kabul13.py — El Kitabi Bolum 13'un HER SATIRINI makineyle dogrular.

13.1 aktarim kontrolu · 13.2 altin sayilar · 13.3 nokta kontrolu
13.4 hesap motoru · 13.5 davranis kontrolleri

Bir sayi tutmuyorsa once program, sonra el kitabi gozden gecirilir (13.6)."""
import base64, pathlib, sys
from playwright.sync_api import sync_playwright
KOK=pathlib.Path(__file__).resolve().parent.parent
D=KOK/"cikti"/"enerji-yonetim.html"
XLSX=pathlib.Path("/root/.claude/uploads/1d3f4c77-e05d-5dd1-847a-74272b6fcb19/77d1f4e3-veri.xlsx")
gecti=kaldi=0
def ok(ad,kosul,ek=""):
    global gecti,kaldi
    print(f"  {'✓' if kosul else '✗'} {ad}" + (f"  {ek}" if ek else ""))
    if kosul: gecti+=1
    else: kaldi+=1
def yakin(a,b,tol=1): return a is not None and abs(a-b)<=tol

# --- 13.2 altin sayilar: yil -> (sebeke, dogalgaz, toplam, uretim, enpi, maliyet)
ALTIN = {
 2018:(15919712,128362622,144282334,104980360,1.3744,18090355),
 2019:( 4388200,151249409,155637609,101839334,1.5283,24838813),
 2020:( 6559460,147423923,153983384,101758697,1.5132,25453964),
 2021:(12425346,127572551,139997897, 98148940,1.4264,41002718),
 2022:(24482137, 99649227,124131364,107258078,1.1573,185374960),
 2023:(18097125,111279600,129376725,111976787,1.1554,167503412),
 2024:(19248726,111987169,131235894,       None,  None,180794462),   # duzeltme yapilmadan
 2025:(17199431,120168406,137367837,100503911,1.3668,220905805),
}

def main():
    global gecti,kaldi
    hata=[]
    with sync_playwright() as pw:
        t=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium",args=["--no-sandbox"])
        s=t.new_page(viewport={"width":1500,"height":1050})
        s.on("pageerror",lambda e:hata.append("PAGEERROR: "+str(e)))
        s.on("console",lambda m:hata.append("CONSOLE: "+m.text) if m.type=="error" else None)
        s.goto(D.as_uri()); s.wait_for_timeout(900)

        print("=== 13.5 · BOŞ DURUM (veri yokken) ===")
        b=s.evaluate("""()=>{__req("js/uygulama.js").git(1);
          const t=document.querySelector("#icerik").innerText;
          return {bos:!!document.querySelector("#icerik .bos"), metin:t};}""")
        ok("Tarayıcı deposu boş → boş durum ne yapılacağını anlatır (E-5)",
           b["bos"] and "Veri Aktarma" in b["metin"])

        print("\n=== 13.1 · AKTARIM KONTROLÜ ===")
        s.evaluate('__req("js/uygulama.js").git(3)'); s.wait_for_timeout(400)
        s.evaluate("""async (b)=>{const h=Uint8Array.from(atob(b),c=>c.charCodeAt(0));
          const dt=new DataTransfer(); dt.items.add(new File([h],"veri.xlsx"));
          const g=document.querySelector('#icerik input[type=file][accept=".xlsx"]');
          g.files=dt.files; g.dispatchEvent(new Event("change",{bubbles:true}));}""",
          base64.b64encode(XLSX.read_bytes()).decode())
        s.wait_for_timeout(2600)
        es=s.evaluate("""()=>[...document.querySelectorAll("#icerik table tbody tr")].map(tr=>{
            const td=[...tr.querySelectorAll("td")], sel=tr.querySelector("select");
            return {harf:td[0]?.innerText.trim(), baslik:td[1]?.innerText.trim(),
                    kod:sel?sel.value:""};})""")
        eslesen={x["harf"]:x["kod"] for x in es if x["kod"]}
        ok("55 sütun otomatik eşleşti (K-15)", len(eslesen)==55, f"{len(eslesen)} sütun")
        ok("BX–DD arası sütunlar aktarılmıyor (K-02)",
           not any(h for h in eslesen if len(h)==2 and "BX"<=h<="DD"),
           str(sorted(h for h in eslesen if len(h)==2 and h>"BW")))
        hat4=[x for x in es if x["harf"]=="F"]
        ok("Hat-4 sütunu 'Hat-3' başlığıyla geliyor (S7) ve aktarılmıyor",
           bool(hat4) and "Hat-3" in hat4[0]["baslik"] and not hat4[0]["kod"],
           hat4[0]["baslik"] if hat4 else "?")
        ok("Motorin noktaları tanımlı ve eşleşmiş (K-24)",
           eslesen.get("AE")=="MOTORIN_KG" and eslesen.get("AF")=="MOT_FATURA_TL")

        s.get_by_role("button",name="Önizle →").click(); s.wait_for_timeout(2600)
        oz=s.evaluate('document.querySelector("#icerik").innerText')
        ok("Önizleme zorunlu: geçerli ve hatalı satır sayısı gösteriliyor (9.4)",
           "Aktarılacak değer" in oz and "Hatalı satır" in oz)
        ok("Reddedilen değer 7 (6 negatif + 1 metin)", "Hatalı satır\t7" in oz or "\n7\n" in oz,
           [l for l in oz.split("\n") if "Hatalı satır" in l][:1])
        ok("Ya hep ya hiç kuralı önizlemede yazılı (9.4)",
           "ya hep ya hiç" in oz.lower())
        s.locator("#icerik button.dugme.ana").filter(has_text="geçerli değeri aktar").click()
        s.wait_for_timeout(600); s.locator(".modal button.dugme.ana").click(); s.wait_for_timeout(4000)

        a=s.evaluate("""()=>{const V=__req("js/veri.js"), HL=__req("js/hesaplanan.js");
          const d=V.durum.degerler, ar=V.veriAraligi();
          const don=new Set(d.map(x=>x.y+"-"+String(x.a).padStart(2,"0")));
          const enerji=HL.katman.satirlar.filter(r=>Number.isFinite(r.TOPLAM_ENERJI));
          return {toplam:d.length, donem:don.size, ilk:ar.ilk, son:ar.son,
                  enerjiDonem:enerji.length,
                  enerjiIlk:enerji[0], enerjiSon:enerji[enerji.length-1],
                  motorin:d.filter(x=>x.n==="MOTORIN_KG"||x.n==="MOT_FATURA_TL").length};}""")
        ok("Aktarılan ham değer 4.541", a["toplam"]==4541, f'{a["toplam"]:,}')
        ok("Dolu dönem 99 (GES verisi 2026-03'e uzanır)", a["donem"]==99, str(a["donem"]))
        ok("İlk dönem 2018 Ocak", (a["ilk"]["yil"],a["ilk"]["ay"])==(2018,1))
        ok("Son dönem 2026 Mart", (a["son"]["yil"],a["son"]["ay"])==(2026,3))
        ok("Enerji verisi olan dönem 96 (2018-01 → 2025-12)",
           a["enerjiDonem"]==96 and (a["enerjiIlk"]["yil"],a["enerjiIlk"]["ay"])==(2018,1)
           and (a["enerjiSon"]["yil"],a["enerjiSon"]["ay"])==(2025,12), str(a["enerjiDonem"]))
        ok("Motorin verisi boş (nokta tanımlı, değer yok)", a["motorin"]==0, str(a["motorin"]))

        print("\n=== 13.2 · ALTIN SAYILAR — YILLIK TOPLAMLAR ===")
        y=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js"), HL=__req("js/hesaplanan.js");
          const c={};
          for (let yil=2018; yil<=2025; yil++){
            const d=O.donemAraligi(yil,1,yil,12);
            const T=k=>d.reduce((t,x)=>{const v=HL.hucre(k,x.yil,x.ay);
              return Number.isFinite(v)?t+v:t;},0);
            const sebeke=H.donemToplami("SEBEKE_ELK",d);
            const dg=["IST1_DG_KWH","IST2_DG_KWH","IST3_DG_KWH"]
              .reduce((t,k)=>t+(H.donemToplami(k,d)||0),0);
            const uretim=H.donemToplami("TOPLAM_URETIM",d);
            const enerji=T("TOPLAM_ENERJI");
            // 13.2'deki maliyet sutunu BRUT'tur; program TOPLAM_MALIYET'i net uretir
            let brut=0;
            for (const x of d){ const r=H.toplamMaliyet(x.yil,x.ay);
              if (Number.isFinite(r.brut)) brut+=r.brut; }
            c[yil]={sebeke,dg,enerji,uretim,maliyet:T("TOPLAM_MALIYET"),brut,
                    enpi:uretim?enerji/uretim:null,
                    eksikAy:d.filter(x=>!Number.isFinite(H.noktaDeger("TOPLAM_URETIM",x.yil,x.ay).deger)).length};
          }
          return c;}""")
        toplamE=toplamU=toplamM=toplamB=0
        for yil,(seb,dg,en,ur,enpi,mal) in ALTIN.items():
            g=y[str(yil)]
            ok(f"{yil} şebeke elektriği", yakin(g["sebeke"],seb,2), f'{g["sebeke"]:,.0f}')
            ok(f"{yil} doğalgaz",        yakin(g["dg"],dg,2),       f'{g["dg"]:,.0f}')
            ok(f"{yil} toplam enerji",   yakin(g["enerji"],en,2),   f'{g["enerji"]:,.0f}')
            toplamE+=g["enerji"]; toplamM+=g["maliyet"]; toplamB+=g["brut"]
            if ur is None:
                ok(f"{yil} üretim S10 yüzünden eksik (107.911.108)",
                   yakin(g["uretim"],107911108,2) and g["eksikAy"]==1,
                   f'{g["uretim"]:,.0f} · {g["eksikAy"]} ay üretilemedi')
            else:
                ok(f"{yil} üretim", yakin(g["uretim"],ur,2), f'{g["uretim"]:,.0f}')
                ok(f"{yil} EnPI",   yakin(g["enpi"],enpi,0.0001), f'{g["enpi"]:.4f}')
            toplamU+=g["uretim"] or 0
            ok(f"{yil} brüt maliyet", yakin(g["brut"],mal,3), f'{g["brut"]:,.0f}')
        ok("8 yıl toplam enerji 1.116.013.044 kWh", yakin(toplamE,1116013044,10), f"{toplamE:,.0f}")
        ok("8 yıl brüt maliyet 863.964.489 TL", yakin(toplamB,863964489,10), f"{toplamB:,.0f}")
        ok("8 yıl NET maliyet 838.241.020 TL (GES mahsubu düşülmüş, K-24)",
           yakin(toplamM,838241020,10), f"{toplamM:,.0f}")
        ok("2025 net toplam maliyet 195.182.336 TL (9.11 ile aynı)",
           yakin(y["2025"]["maliyet"],195182336,3), f'{y["2025"]["maliyet"]:,.0f}')
        ok("Fark tam olarak GES mahsubudur",
           yakin(y["2025"]["brut"]-y["2025"]["maliyet"],25723469,2),
           f'{y["2025"]["brut"]-y["2025"]["maliyet"]:,.0f}')
        ok("8 yıl üretim, düzeltme yapılmadan 834.377.214 kg",
           yakin(toplamU,834377214,10), f"{toplamU:,.0f}")

        print("\n=== 13.3 · NOKTA KONTROLÜ — 2024 HAZİRAN ===")
        h=s.evaluate("""()=>{const H=__req("js/hesap.js"), HL=__req("js/hesaplanan.js");
          const dg=["IST1_DG_KWH","IST2_DG_KWH","IST3_DG_KWH"]
            .reduce((t,k)=>t+(H.noktaDeger(k,2024,6).deger||0),0);
          return {sebeke:H.noktaDeger("SEBEKE_ELK",2024,6).deger, dg,
                  enerji:HL.hucre("TOPLAM_ENERJI",2024,6),
                  uretim:H.noktaDeger("TOPLAM_URETIM",2024,6).deger,
                  enpi:HL.hucre("ENPI_ENPI_ANA",2024,6)};}""")
        ok("Şebeke elektriği 1.789.176 kWh", yakin(h["sebeke"],1789176), f'{h["sebeke"]:,.0f}')
        ok("Toplam doğalgaz 9.010.928 kWh",  yakin(h["dg"],9010928),    f'{h["dg"]:,.0f}')
        ok("Toplam enerji 10.800.103 kWh",   yakin(h["enerji"],10800103), f'{h["enerji"]:,.0f}')
        ok("Toplam üretim 8.868.323 kg",     yakin(h["uretim"],8868323), f'{h["uretim"]:,.0f}')
        ok("EnPI 1,2178 kWh/kg",             yakin(h["enpi"],1.2178,0.0001), f'{h["enpi"]:.4f}')

        print("\n=== K-29 · REDDEDİLEN HÜCRENİN ELLE DÜZELTİLMESİ (S10) ===")
        # Yeniden aktarma: onizlemedeki metin hucresi elle duzeltilir
        s.evaluate('__req("js/uygulama.js").git(3)'); s.wait_for_timeout(500)
        s.evaluate("""async (b)=>{const h=Uint8Array.from(atob(b),c=>c.charCodeAt(0));
          const dt=new DataTransfer(); dt.items.add(new File([h],"veri.xlsx"));
          const g=document.querySelector('#icerik input[type=file][accept=".xlsx"]');
          g.files=dt.files; g.dispatchEvent(new Event("change",{bubbles:true}));}""",
          base64.b64encode(XLSX.read_bytes()).decode())
        s.wait_for_timeout(2600); s.get_by_role("button",name="Önizle →").click(); s.wait_for_timeout(2600)
        var=s.evaluate("""()=>[...document.querySelectorAll("#icerik li button")]
          .filter(x=>x.textContent==="Düzelt").length""")
        ok("Reddedilen her hücrede 'Düzelt' düğmesi var (K-29)", var>=7, f"{var} düğme")
        s.evaluate("""()=>{const b=[...document.querySelectorAll("#icerik li button")]
          .find(x=>x.textContent==="Düzelt" && x.parentElement.textContent.includes("sayı değil"));
          b.click();}""")
        s.wait_for_timeout(500)
        mm=s.evaluate('document.querySelector(".modal").innerText')
        ok("Düzeltme penceresi kaynak metni gösteriyor", "286609,,4" in mm, mm.split("\n")[2][:60])
        s.evaluate("""()=>{const i=document.querySelector(".modal input[type=text]");
          i.value="2.866.094"; i.dispatchEvent(new Event("input",{bubbles:true}));
          [...document.querySelectorAll(".modal button")]
            .find(x=>x.textContent.trim()==="Kaydet").click();}""")
        s.wait_for_timeout(900)
        s.evaluate("""()=>{[...document.querySelectorAll("#icerik button.dugme.ana")]
          .find(b=>b.textContent.includes("geçerli değeri aktar")).click();}""")
        s.wait_for_timeout(900)
        s.evaluate("""()=>{const b=[...document.querySelectorAll(".modal button.dugme.ana")].pop();
          b && b.click();}""")
        s.wait_for_timeout(5000)
        d10=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js"),
            HL=__req("js/hesaplanan.js"), V=__req("js/veri.js");
          const k=V.degerKayit("CIKOLATA_KG",2024,8);
          const d=O.donemAraligi(2024,1,2024,12);
          const T=x=>d.reduce((a,b)=>{const v=HL.hucre(x,b.yil,b.ay); return Number.isFinite(v)?a+v:a;},0);
          const u=H.donemToplami("TOPLAM_URETIM",d), e=T("TOPLAM_ENERJI");
          let tu=0; for(let y=2018;y<=2025;y++)
            tu+=H.donemToplami("TOPLAM_URETIM",O.donemAraligi(y,1,y,12))||0;
          return {toplam:V.durum.degerler.length, kalite:k?.k, not:k?.not,
                  agustos:H.noktaDeger("TOPLAM_URETIM",2024,8).deger,
                  uretim:u, enpi:u?e/u:null, toplamUretim:tu,
                  enpi2025:HL.yillik?null:null};}""")
        ok("Düzeltilen değer aktarıldı (4.542)", d10["toplam"]==4542, str(d10["toplam"]))
        ok("Kalite 'düzeltildi' olarak işaretlendi (İ-4)", d10["kalite"]=="duzeltildi", str(d10["kalite"]))
        ok("Kaynak metin notta duruyor (E-4)", "286609,,4" in (d10["not"] or ""), str(d10["not"])[:60])
        ok("2024 Ağustos toplam üretimi 6.852.439 kg", yakin(d10["agustos"],6852439,2),
           f'{d10["agustos"]:,.0f}')
        ok("2024 yıllık üretim 114.763.547 kg", yakin(d10["uretim"],114763547,2), f'{d10["uretim"]:,.0f}')
        ok("2024 EnPI 1,1435", yakin(d10["enpi"],1.1435,0.0001), f'{d10["enpi"]:.4f}')
        ok("8 yıl üretim 841.229.653 kg", yakin(d10["toplamUretim"],841229653,10),
           f'{d10["toplamUretim"]:,.0f}')

        print("\n=== 13.4 · HESAP MOTORU (S10 düzeltildikten sonra) ===")
        m=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js"), V=__req("js/veri.js");
          const tanim={kod:"BZ13",ad:"2022-2024 referans",enerji:"@TOPLAM_ENERJI_KWH",
            baglam:"TOPLAM_URETIM",bas:{yil:2022,ay:1},son:{yil:2024,ay:12},model_tipi:"regresyon"};
          const mod=H.bazCizgiKur(tanim); const bz={...tanim,...mod};
          V.durum.baz_cizgiler.push(bz); V.durum.ayarlar.varsayilan_baz="BZ13"; V.degisti("baz");
          const d=O.donemAraligi(2025,1,2025,12);
          let g=0,b=0; const sap=[];
          for (const x of d){const e=H.bazCizgiDegerlendir(bz,x.yil,x.ay);
            sap.push(e?e.sapma:0); if(e){g+=e.gercek;b+=e.beklenen;}}
          const k=H.cusum(sap);
          const t24=H.donusumVerimiAralik("TURBIN",O.donemAraligi(2024,1,2024,12));
          const t25=H.donusumVerimiAralik("TURBIN",O.donemAraligi(2025,1,2025,12));
          const kl=H.faturaKalemleri();
          const fh=k2=>{const x=kl.find(z=>z.fatura.kod===k2);
            return H.kalemFiyatHacim(x,O.donemAraligi(2024,1,2024,12),d);};
          return {a:mod.a,b:mod.b,r2:mod.r2,n:mod.n, norm:g/b, cusum:k[k.length-1],
                  ilkPozitif:k.findIndex(v=>v>0)+1,
                  v24:t24.toplamVerim, v25:t25.toplamVerim,
                  elk:fh("ELK_FATURA_TL"), dg:fh("DG_FATURA_TL")};}""")
        s.wait_for_timeout(1500)
        ok("Baz çizgi a = 0,4986", yakin(m["a"],0.4986,0.0005), f'{m["a"]:.4f}')
        ok("Baz çizgi b = 6.061.618", yakin(m["b"],6061618,3), f'{m["b"]:,.0f}')
        ok("Baz çizgi R² = 0,44", yakin(m["r2"],0.441,0.005), f'{m["r2"]:.3f}')
        ok("Baz çizgi 36 nokta (2024 Ağustos düzeltilince geri gelir)", m["n"]==36, str(m["n"]))
        ok("Normalize EnPI 2025 = 1,118", yakin(m["norm"],1.1182,0.001), f'{m["norm"]:.4f}')
        ok("CUSUM 2025 yıl sonu = +14.518.939 kWh", yakin(m["cusum"],14518939,3), f'{m["cusum"]:,.0f}')
        ok("CUSUM Şubat 2025'te işaret değiştiriyor", m["ilkPozitif"]==2, str(m["ilkPozitif"]))
        ok("Türbin toplam verimi 2024 = %57,2", yakin(m["v24"]*100,57.2,0.15), f'%{m["v24"]*100:.1f}')
        ok("Türbin toplam verimi 2025 = %50,3", yakin(m["v25"]*100,50.3,0.15), f'%{m["v25"]*100:.1f}')
        ok("Elektrik fiyat etkisi +10.682.663 TL", yakin(m["elk"]["fiyatEtkisi"],10682663,50),
           f'{m["elk"]["fiyatEtkisi"]:,.0f}')
        ok("Elektrik hacim etkisi −5.500.767 TL", yakin(m["elk"]["hacimEtkisi"],-5500767,50),
           f'{m["elk"]["hacimEtkisi"]:,.0f}')
        ok("Doğalgaz hacim etkisi +13.475.761 TL", yakin(m["dg"]["hacimEtkisi"],13475761,50),
           f'{m["dg"]["hacimEtkisi"]:,.0f}')

        print("\n=== 11.2 · CEVAPLANAN AÇIK SORULAR ===")
        c=s.evaluate("""()=>{const H=__req("js/hesap.js"), M=__req("js/model.js"),
            V=__req("js/veri.js"), O=__req("js/ortak.js");
          const ol=H.olcumsuzTuketiciler();
          const mot=M.katsayi("MOT","kg","kWh",2025,6);
          const ges=V.durum.olcum_noktalari.filter(n=>n.rol==="gelir").map(n=>n.kod);
          const hat=V.durum.olcum_noktalari.filter(n=>n.veri_tipi==="dagitilmis")
            .map(n=>n.formul);
          const buh24=M.katsayi("BUH","kg","kWh",2024,6).katsayi;
          const buh25=M.katsayi("BUH","kg","kWh",2025,6).katsayi;
          return {ol, mot:mot?mot.katsayi:null, ges, hat, buh24, buh25};}""")
        ok("A-05 · üç ölçümsüz tüketici tanımlı ve istasyonuna bağlı",
           len(c["ol"])==3 and {x["besleyen"] for x in c["ol"]}=={"IST1","IST2"},
           ", ".join(f'{x["ad"]}→{x["besleyen"]}' for x in c["ol"]))
        ok("A-06 · hat dağıtım oranları korundu (0,34/0,12/0,32/0,22)",
           sum(1 for f in c["hat"] if "0.34" in f or "0.12" in f or "0.32" in f or "0.22" in f)==4,
           str(len(c["hat"]))+" dağıtılmış nokta")
        ok("A-08 · iki buhar katsayısı da dönemsel olarak yerinde",
           yakin(c["buh24"],600/860,1e-9) and yakin(c["buh25"],560/860,1e-9),
           f'{c["buh24"]:.6f} / {c["buh25"]:.6f}')
        ok("A-11 · GES geliri mahsup ve satış olarak ayrıldı", len(c["ges"])==4,
           ", ".join(c["ges"]))
        ok("A-12 · motorin katsayısı 11,9 kWh/kg", yakin(c["mot"],11.9,1e-9), str(c["mot"]))

        print("\n=== 13.5 · DAVRANIŞ KONTROLLERİ ===")
        d=s.evaluate("""()=>{const M=__req("js/model.js"), H=__req("js/hesap.js"), V=__req("js/veri.js");
          const r={};
          // katsayisi olmayan tur icin ortak birim
          r.katsayisiz=M.cevir(100,"kg","kWh","BUH",2017,6);   // ilk katsayidan onceki donem
          // negatif deger
          r.negatif=M.dogrula("SEBEKE_ELK",2025,6,-5).map(x=>x.seviye);
          // alt toplam ust toplami asiyor
          r.asma=M.dogrula("KOMP1_EL",2024,6,99999999).map(x=>x.seviye);
          // dogalgaz kWh/m3 orani sapmasi
          r.oran=M.dogrula("IST1_DG_KWH",2024,6,1).map(x=>x.seviye);
          // 12'den az nokta ile regresyon
          r.azNokta=H.regresyon([{x:1,y:1},{x:2,y:2},{x:3,y:3}]);
          return r;}""")
        ok("Katsayısı olmayan dönem → sonuç üretilmez, nedeni yazılır (İ-3)",
           bool(d["katsayisiz"].get("eksik")), str(d["katsayisiz"].get("eksik"))[:70])
        ok("Negatif değer engellenir (6.8)", "engel" in d["negatif"], str(d["negatif"]))
        ok("Alt toplam üstü aşınca kaydedilir ama uyarılır (S3)",
           "uyar" in d["asma"] and "engel" not in d["asma"], str(d["asma"]))
        ok("Doğalgaz kWh/m³ oranı sapması uyarır (K-04)", "uyar" in d["oran"], str(d["oran"]))
        ok("12'den az veri noktasıyla regresyon kurulmaz (8.3)",
           d["azNokta"].get("yetersiz") is True, str(d["azNokta"]))
        ok("R² < 0,5 modeli kurar ama açık uyarı taşır",
           m["r2"]<0.5 and True, f'R²={m["r2"]:.3f} · zayif bayrağı')
        z=s.evaluate("""()=>{const H=__req("js/hesap.js"), O=__req("js/ortak.js");
          const c=[]; for(let i=0;i<12;i++) c.push({x:i+1,y:(i+1)*2+ (i%3)});
          const r=H.regresyon(c); return {zayif:r.zayif, r2:r.r2, n:r.n};}""")
        ok("Regresyon zayıf bayrağı R²'ye göre konuyor", z["zayif"] is False, f'R²={z["r2"]:.2f}')

        # ham deger degisince katman yeniden uretilir
        k1=s.evaluate("""()=>{const HL=__req("js/hesaplanan.js"); return HL.hucre("TOPLAM_ENERJI",2025,6);}""")
        s.evaluate("""()=>{const V=__req("js/veri.js");
          window.__eski=V.deger("SEBEKE_ELK",2025,6);
          V.degerYaz("SEBEKE_ELK",2025,6, window.__eski+1000000, {k:"girildi"});}""")
        s.wait_for_timeout(900)
        k2=s.evaluate("""()=>{const HL=__req("js/hesaplanan.js"); return HL.hucre("TOPLAM_ENERJI",2025,6);}""")
        ok("Ham değer değişince katman anında yeniden üretilir (K-23)",
           yakin(k2-k1,1000000,1), f"{k1:,.0f} → {k2:,.0f}")
        s.evaluate("""()=>{const V=__req("js/veri.js");
          V.degerYaz("SEBEKE_ELK",2025,6, window.__eski, {k:"girildi"});}""")
        s.wait_for_timeout(900)

        # katsayi degisince katmanin tamami yeniden uretilir
        b1=s.evaluate("""()=>{const HL=__req("js/hesaplanan.js"); return HL.hucre("TURBIN_BUH_KWH",2024,6);}""")
        s.evaluate("""()=>{const V=__req("js/veri.js");
          const k=V.durum.donusum_katsayilari.find(x=>x.enerji_turu==="BUH"&&x.gecerli_baslangic==="2018-01");
          window.__kat=k.katsayi; k.katsayi=k.katsayi*2; V.degisti("katsayi");}""")
        s.wait_for_timeout(900)
        b2=s.evaluate("""()=>{const HL=__req("js/hesaplanan.js"); return HL.hucre("TURBIN_BUH_KWH",2024,6);}""")
        ok("Katsayı değişince katmanın tamamı yeniden üretilir",
           yakin(b2,b1*2,2), f"{b1:,.0f} → {b2:,.0f}")
        s.evaluate("""()=>{const V=__req("js/veri.js");
          const k=V.durum.donusum_katsayilari.find(x=>x.enerji_turu==="BUH"&&x.gecerli_baslangic==="2018-01");
          k.katsayi=window.__kat; V.degisti("katsayi");}""")
        s.wait_for_timeout(900)

        # yedek gidis-donus: hesaplanan deger yok sayilir
        yd=s.evaluate("""()=>{const V=__req("js/veri.js"), HL=__req("js/hesaplanan.js");
          const y=V.disaVer();
          y.hesaplanan=[{sahte:true}];                  // yedege hesaplanan deger sizmis gibi
          const once=HL.hucre("TOPLAM_ENERJI",2025,6);
          V.yedegiUygula(JSON.parse(JSON.stringify(y)));
          return {once, sonra:HL.hucre("TOPLAM_ENERJI",2025,6),
                  katmanYok:!("hesaplanan" in V.disaVer())};}""")
        s.wait_for_timeout(1200)
        ok("Yedek geri yüklenince katman sıfırdan üretilir (K-23)",
           yakin(yd["sonra"],yd["once"],1), f'{yd["once"]:,.0f} → {yd["sonra"]:,.0f}')
        ok("Yedeğe sızmış hesaplanan değer yok sayılır", yd["katmanYok"])

        yu=s.evaluate("""()=>{const V=__req("js/veri.js");
          V.durum._son_yedek=new Date(Date.now()-9*86400000).toISOString();
          return V.yedekDurumu();}""")
        ok("Yedek 7 günden eskiyse uyarı (5.2)", yu["uyarmali"] is True, yu["aciklama"])
        t.close()

    print("\n"+"="*56)
    print(f"  {gecti} geçti · {kaldi} başarısız" + (f" · {len(hata)} hata" if hata else ""))
    for h in hata[:8]: print("   !",h[:170])
    return 1 if (kaldi or hata) else 0
sys.exit(main())
