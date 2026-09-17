#!/usr/bin/env python3
"""Baslangic tanimlarini uretir (K-16).

Excel'in sutun yapisindan varlik agaci ve olcum noktalari cikarilir.
Cikti: kaynak/baslangic.json  -- programa gomulur.

El kitabi atiflari: K-02, K-05, K-07, K-16, K-24, 6.2, 6.4, 6.6
"""
import json, pathlib, re

# ---------------------------------------------------------------- varlik agaci
# K-05: serbest derinlik. Bu yalnizca BASLANGIC onerisidir; kullanici degistirir.
VARLIKLAR = [
    # (kod, ust, ad, tip)
    ("FAB",        None,   "Fabrika",                      "tesis"),
    ("GIRIS",      "FAB",  "Enerji Girişi",                "grup"),
    ("SEBEKE",     "GIRIS","Şebeke Elektrik",              "giris_noktasi"),
    ("IST1",       "GIRIS","İstasyon 1 (Gaz Motoru)",      "istasyon"),
    ("IST2",       "GIRIS","İstasyon 2 (Kazan)",           "istasyon"),
    ("IST3",       "GIRIS","İstasyon 3 (Türbin)",          "istasyon"),
    ("MOTORIN",    "GIRIS","Motorin",                      "giris_noktasi"),

    ("DONUSUM",    "FAB",  "Enerji Dönüşüm",               "grup"),
    ("TURBIN",     "DONUSUM","Türbin",                     "ekipman"),
    ("GM1",        "DONUSUM","GM-1",                       "ekipman"),
    ("GM2",        "DONUSUM","GM-2",                       "ekipman"),
    ("GM3",        "DONUSUM","GM-3",                       "ekipman"),
    ("KAZAN1",     "DONUSUM","Kazan-1",                    "ekipman"),
    ("KAZAN2",     "DONUSUM","Kazan-2",                    "ekipman"),

    ("YARDIMCI",   "FAB",  "Yardımcı Tesisler",            "grup"),
    ("KOMP",       "YARDIMCI","Kompresörler",              "grup"),
    ("KOMP1",      "KOMP", "Kompresör 1",                  "ekipman"),
    ("KOMP2",      "KOMP", "Kompresör 2",                  "ekipman"),
    ("KOMP3",      "KOMP", "Kompresör 3",                  "ekipman"),
    ("KOMP4",      "KOMP", "Kompresör 4",                  "ekipman"),
    ("CHILLER",    "YARDIMCI","Chiller'lar",               "grup"),
    ("CH_KAKAO",   "CHILLER","Kakao Chiller",              "ekipman"),
    ("CH_PULV",    "CHILLER","Pulvarizatör Chiller",       "ekipman"),
    ("CH_BLOK",    "CHILLER","Blok Paketleme Chiller",     "ekipman"),
    ("CH_FINER1",  "CHILLER","Finer-1 Chiller",            "ekipman"),
    ("CH_FINER2",  "CHILLER","Finer-2 Chiller",            "ekipman"),
    ("CH_TREN",    "CHILLER","Tren Chiller",               "ekipman"),

    ("URETIM",     "FAB",  "Üretim",                       "grup"),
    ("KAKAO",      "URETIM","Kakao Prosesi",               "proses"),
    ("CIKOLATA",   "URETIM","Çikolata Prosesi",            "proses"),
    ("HATLAR",     "URETIM","Çekirdek Hatları",            "grup"),
    ("HAT1",       "HATLAR","Hat-1",                       "hat"),
    ("HAT2",       "HATLAR","Hat-2",                       "hat"),
    ("HAT3",       "HATLAR","Hat-3",                       "hat"),
    ("HAT4",       "HATLAR","Hat-4",                       "hat"),   # S7 duzeltmesi

    # K-03: ayri tesis, fabrikanin kWh dengesine girmez
    ("GES",        None,   "Güneş Santralleri",            "tesis"),
    ("GES_YOZGAT", "GES",  "Yozgat GES",                   "santral"),
    ("GES_ADANA",  "GES",  "Adana GES",                    "santral"),
]

# ------------------------------------------------------------- enerji turleri
ENERJI_TURLERI = [
    ("ELK", "Elektrik",  "kWh"),
    ("DG",  "Doğalgaz",  "kWh"),
    ("BUH", "Buhar",     "kg"),
    ("SSU", "Sıcak Su",  "kWh"),
    ("MOT", "Motorin",   "kg"),
]

# ------------------------------------------------------------- olcum noktalari
# (kod, varlik, ad, tur, birim, rol, toplama_dahil, veri_tipi, formul, not)
#
# toplama_dahil KURALI (6.7, K-24):
#   Fabrika toplamina yalniz UST seviye giris noktalari girer. Alt kirilimlar
#   (GM-1 dogalgazi, turbin dogalgazi) ayni gazin alt olcumudur; toplama_dahil
#   = false, aksi halde cift sayim olur.
#   m3 noktalari da false: ayni tuketimin baska birimdeki karsiligi.
N = [
 # --- Satin alinan enerji (toplam enerjiye giren) ---
 ("SEBEKE_ELK",   "SEBEKE","Şebekeden Çekilen Elektrik","ELK","kWh","satin_alinan",True ,"olculen",None,"Excel N"),
 ("IST1_DG_KWH",  "IST1",  "İstasyon 1 Doğalgaz",       "DG", "kWh","satin_alinan",True ,"olculen",None,"Excel V"),
 ("IST2_DG_KWH",  "IST2",  "İstasyon 2 Doğalgaz",       "DG", "kWh","satin_alinan",True ,"olculen",None,"Excel X"),
 ("IST3_DG_KWH",  "IST3",  "İstasyon 3 Doğalgaz",       "DG", "kWh","satin_alinan",True ,"olculen",None,"Excel Z"),
 ("MOTORIN_KG",   "MOTORIN","Motorin Tüketimi",         "MOT","kg", "satin_alinan",True ,"olculen",None,"Excel AE - K-24: toplama dahil"),
 # --- Ayni tuketimin m3 karsiligi (K-04 tutarlilik denetimi icin) ---
 ("IST1_DG_M3",   "IST1",  "İstasyon 1 Doğalgaz",       "DG", "m³", "satin_alinan",False,"olculen",None,"Excel W - kWh ile tutarlilik denetlenir"),
 ("IST2_DG_M3",   "IST2",  "İstasyon 2 Doğalgaz",       "DG", "m³", "satin_alinan",False,"olculen",None,"Excel Y"),
 ("IST3_DG_M3",   "IST3",  "İstasyon 3 Doğalgaz",       "DG", "m³", "satin_alinan",False,"olculen",None,"Excel AA"),
 # --- Maliyet (K-12, K-13, K-24) ---
 ("ELK_FATURA_TL","SEBEKE","Elektrik Faturası",         None, "TL", "maliyet",     True ,"olculen",None,"Excel O - K-13 mahsup oncesi brut"),
 ("DG_FATURA_TL", "GIRIS", "Doğalgaz Faturası",         None, "TL", "maliyet",     True ,"olculen",None,"Excel AD"),
 ("MOT_FATURA_TL","MOTORIN","Motorin Faturası",         None, "TL", "maliyet",     True ,"olculen",None,"Excel AF - K-24"),
 # --- GES (K-03) ---
 ("GES_YOZ_KWH",  "GES_YOZGAT","Yozgat GES Üretimi",    "ELK","kWh","ayri_tesis_uretim",False,"olculen",None,"Excel R"),
 ("GES_YOZ_TL",   "GES_YOZGAT","Yozgat GES Geliri",     None, "TL", "gelir",       False,"olculen",None,"Excel S - A-11: mahsup/satis ayrismamis"),
 ("GES_ADA_KWH",  "GES_ADANA", "Adana GES Üretimi",     "ELK","kWh","ayri_tesis_uretim",False,"olculen",None,"Excel T"),
 ("GES_ADA_TL",   "GES_ADANA", "Adana GES Geliri",      None, "TL", "gelir",       False,"olculen",None,"Excel U"),
 # --- Uretim (bagl. degiskenler) ---
 ("CEKIRDEK_KG",  "URETIM","Toplam Çekirdek Tüketimi",  None, "kg", "girdi_miktari",False,"olculen",None,"Excel G"),
 ("KAKAO_YAG",    "KAKAO", "Kakao Yağı Üretimi",        None, "kg", "uretim_miktari",False,"olculen",None,"Excel H"),
 ("KAKAO_TOZ",    "KAKAO", "Kakao Tozu Üretimi",        None, "kg", "uretim_miktari",False,"olculen",None,"Excel I"),
 ("KAKAO_LIKOR",  "KAKAO", "Kakao Likör Üretimi",       None, "kg", "uretim_miktari",False,"olculen",None,"Excel J"),
 ("CIKOLATA_KG",  "CIKOLATA","Çikolata Üretimi",        None, "kg", "uretim_miktari",False,"olculen",None,"Excel L"),
]

# Donusum ekipmanlari: yakit girdisi + faydali enerji ciktisi
DONUSUM = [
 ("TURBIN","TURBIN","Türbin","AI","AJ","AK","AL",None),
 ("GM1",   "GM1",   "GM-1",  "AN","AO","AP","AQ","AS"),
 ("GM2",   "GM2",   "GM-2",  "AT","AU","AV","AW","AY"),
 ("GM3",   "GM3",   "GM-3",  "AZ","BA","BB","BC","BE"),
]
for kod, varlik, ad, c_kwh, c_m3, c_el, c_buh, c_ssu in DONUSUM:
    N.append((f"{kod}_DG_KWH", varlik, f"{ad} Doğalgaz Tüketimi","DG","kWh","satin_alinan",False,"olculen",None,f"Excel {c_kwh} - istasyon olcumunun alt kirilimi, toplama girmez"))
    N.append((f"{kod}_DG_M3",  varlik, f"{ad} Doğalgaz Tüketimi","DG","m³", "satin_alinan",False,"olculen",None,f"Excel {c_m3}"))
    N.append((f"{kod}_EL",     varlik, f"{ad} Elektrik Üretimi", "ELK","kWh","tesis_ici_uretim",False,"olculen",None,f"Excel {c_el}"))
    N.append((f"{kod}_BUH_KG", varlik, f"{ad} Buhar Üretimi",    "BUH","kg", "ara_enerji",False,"olculen",None,f"Excel {c_buh}"))
    N.append((f"{kod}_BUH_KWH",varlik, f"{ad} Buhar Üretimi",    "BUH","kWh","ara_enerji",False,"hesaplanan",f"{kod}_BUH_KG * KATSAYI(BUH,kg,kWh)","6.6 - tarihli katsayi"))
    if c_ssu:
        N.append((f"{kod}_SSU", varlik, f"{ad} Sıcak Su Üretimi","SSU","kWh","ara_enerji",False,"olculen",None,f"Excel {c_ssu}"))

for kod, varlik, ad, c_kwh, c_m3, c_buh in [
        ("KAZAN1","KAZAN1","Kazan-1","BF","BG","BH"),
        ("KAZAN2","KAZAN2","Kazan-2","BJ","BK","BL")]:
    N.append((f"{kod}_DG_KWH", varlik, f"{ad} Doğalgaz Tüketimi","DG","kWh","satin_alinan",False,"olculen",None,f"Excel {c_kwh} - alt kirilim"))
    N.append((f"{kod}_DG_M3",  varlik, f"{ad} Doğalgaz Tüketimi","DG","m³", "satin_alinan",False,"olculen",None,f"Excel {c_m3}"))
    N.append((f"{kod}_BUH_KG", varlik, f"{ad} Buhar Üretimi",    "BUH","kg", "ara_enerji",False,"olculen",None,f"Excel {c_buh}"))
    N.append((f"{kod}_BUH_KWH",varlik, f"{ad} Buhar Üretimi",    "BUH","kWh","ara_enerji",False,"hesaplanan",f"{kod}_BUH_KG * KATSAYI(BUH,kg,kWh)","6.6"))

# Elektrik alt sayaclari (gercek alt olcum - kapsamin %26'si)
for kod, varlik, ad, sut in [
        ("KOMP1","KOMP1","Kompresör 1","BN"),("KOMP2","KOMP2","Kompresör 2","BO"),
        ("KOMP3","KOMP3","Kompresör 3","BP"),("KOMP4","KOMP4","Kompresör 4","BQ"),
        ("CH_KAKAO","CH_KAKAO","Kakao Chiller","BR"),
        ("CH_PULV","CH_PULV","Pulvarizatör Chiller","BS"),
        ("CH_BLOK","CH_BLOK","Blok Paketleme Chiller","BT"),
        ("CH_FINER1","CH_FINER1","Finer-1 Chiller","BU"),
        ("CH_FINER2","CH_FINER2","Finer-2 Chiller","BV"),
        ("CH_TREN","CH_TREN","Tren Chiller","BW")]:
    N.append((f"{kod}_EL", varlik, f"{ad} Elektrik Tüketimi","ELK","kWh","satin_alinan",False,"olculen",None,f"Excel {sut} - alt sayac, kapsama girer"))

# Hesaplanan noktalar (6.6)
HESAPLANAN = [
 ("HAT1_CEKIRDEK","HAT1","Hat-1 Çekirdek Tüketimi",None,"kg","girdi_miktari",False,"dagitilmis","CEKIRDEK_KG * 0.34","2.2 - olcum degil, sabit oranla dagitim"),
 ("HAT2_CEKIRDEK","HAT2","Hat-2 Çekirdek Tüketimi",None,"kg","girdi_miktari",False,"dagitilmis","CEKIRDEK_KG * 0.12","2.2"),
 ("HAT3_CEKIRDEK","HAT3","Hat-3 Çekirdek Tüketimi",None,"kg","girdi_miktari",False,"dagitilmis","CEKIRDEK_KG * 0.32","2.2"),
 ("HAT4_CEKIRDEK","HAT4","Hat-4 Çekirdek Tüketimi",None,"kg","girdi_miktari",False,"dagitilmis","CEKIRDEK_KG * 0.22","2.2 - S7: Excel'de basligi yanlis"),
 ("TOPLAM_KAKAO","KAKAO","Toplam Kakao Üretimi",None,"kg","uretim_miktari",False,"hesaplanan","KAKAO_YAG + KAKAO_TOZ + KAKAO_LIKOR","6.6"),
 ("TOPLAM_URETIM","URETIM","Toplam Üretim",None,"kg","uretim_miktari",False,"hesaplanan","TOPLAM_KAKAO + CIKOLATA_KG","6.6"),
 ("URETILEN_ELK","DONUSUM","Üretilen Elektrik",  "ELK","kWh","tesis_ici_uretim",False,"hesaplanan","TURBIN_EL + GM1_EL + GM2_EL + GM3_EL","6.6"),
 ("MOTORIN_KWH","MOTORIN","Motorin Enerji Karşılığı","MOT","kWh","satin_alinan",False,"hesaplanan","MOTORIN_KG * KATSAYI(MOT,kg,kWh)","K-24, A-12 - katsayi tanimsiz"),
]
N += HESAPLANAN

# ---------------------------------------------------------------- donusum kats.
KATSAYILAR = [
 {"enerji_turu":"DG","kaynak_birim":"m³","hedef_birim":"kWh","katsayi":10.92,
  "gecerli_baslangic":"2018-01","kaynak":"Excel'deki kWh/m³ oranından türetildi",
  "not":"2018-2025 arası ölçülen oran 10,918-10,919. Dağıtım şirketinin aylık üst ısıl değerine göre güncellenmelidir."},
 {"enerji_turu":"BUH","kaynak_birim":"kg","hedef_birim":"kWh","katsayi":600/860,
  "gecerli_baslangic":"2018-01","kaynak":"Excel formülü: kg × 600 / 860",
  "not":"600 kcal/kg entalpi ÷ 860 kcal/kWh = 0,697674 kWh/kg. A-08: basınca göre değişken mi, teyit bekliyor."},
]

ENPI = [
 {"kod":"ENPI_ANA","ad":"Toplam Enerji / Toplam Üretim","pay":"@TOPLAM_ENERJI_KWH",
  "payda":"TOPLAM_URETIM","birim":"kWh/kg","ondalik":4,"ana":True},
 {"kod":"ENPI_ELK","ad":"Şebeke Elektriği / Toplam Üretim","pay":"SEBEKE_ELK",
  "payda":"TOPLAM_URETIM","birim":"kWh/kg","ondalik":4,"ana":False},
 {"kod":"ENPI_CIK","ad":"Toplam Enerji / Çikolata Üretimi","pay":"@TOPLAM_ENERJI_KWH",
  "payda":"CIKOLATA_KG","birim":"kWh/kg","ondalik":4,"ana":False},
]

def main():
    varliklar=[{"kod":k,"ust":u,"ad":a,"tip":t,"sira":i*10,
                "devreye_giris":None,"devreden_cikis":None,"aktif":True,"not":""}
               for i,(k,u,a,t) in enumerate(VARLIKLAR)]
    # S6: gaz motorlari 2025'te durdu
    for v in varliklar:
        if v["kod"] in ("GM1","GM2","GM3"):
            v["devreden_cikis"]="2024-12"
            v["not"]="S6: 2025 boyunca veri yok, devreden çıkarılmış görünüyor. Teyit edilmeli."
    def sutun(n):
        """Not alanindaki 'Excel AB' bilgisinden sutun harfini cikarir.
        Ilk ice aktarmada otomatik eslestirme icin kullanilir (K-15, 9.4)."""
        m = re.search(r"Excel ([A-Z]{1,2})\b", n or "")
        return m.group(1) if m else None
    noktalar=[{"kod":k,"varlik":v,"ad":ad,"enerji_turu":et,"birim":b,"rol":r,
               "toplama_dahil":td,"veri_tipi":vt,"formul":f,"aktif":True,
               "excel_sutun":sutun(n),"not":n}
              for (k,v,ad,et,b,r,td,vt,f,n) in N]
    kodlar=[x["kod"] for x in noktalar]
    assert len(kodlar)==len(set(kodlar)), "tekrar eden olcum noktasi kodu"
    vk={x["kod"] for x in varliklar}
    for x in noktalar:
        assert x["varlik"] in vk, f"tanimsiz varlik: {x['varlik']}"
    d={"sema_surumu":1,
       "ayarlar":{"fabrika_adi":"","para_birimi":"TL","varsayilan_birim":"kWh",
                  "ana_enpi":"ENPI_ANA","tema":"otomatik","ondalik":2},
       "enerji_turleri":[{"kod":k,"ad":a,"ana_birim":b,"aktif":True} for k,a,b in ENERJI_TURLERI],
       "varliklar":varliklar,"olcum_noktalari":noktalar,
       "donusum_katsayilari":KATSAYILAR,"enpi_tanimlari":ENPI,
       "baz_cizgiler":[],"hedefler":[],"aksiyonlar":[],"degerler":[]}
    p=pathlib.Path(__file__).resolve().parent.parent/"kaynak"/"baslangic.json"
    p.write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding="utf-8")
    print(f"{p}")
    print(f"  varlık        : {len(varliklar)}")
    print(f"  ölçüm noktası : {len(noktalar)}")
    print(f"    ölçülen     : {sum(1 for x in noktalar if x['veri_tipi']=='olculen')}")
    print(f"    hesaplanan  : {sum(1 for x in noktalar if x['veri_tipi']!='olculen')}")
    print(f"    toplama dahil: {sum(1 for x in noktalar if x['toplama_dahil'])}")
    print(f"  katsayı       : {len(KATSAYILAR)}   EnPI: {len(ENPI)}")
    es = sum(1 for x in noktalar if x["excel_sutun"])
    print(f"  Excel eşlemesi: {es} nokta otomatik eşleşecek")

if __name__=="__main__":
    main()
