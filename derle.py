#!/usr/bin/env python3
"""derle.py — kaynağı TEK HTML dosyasına gömer (El Kitabı K-09, K-18).

Teslim edilen ürün tek dosyadır; geliştirme tek dosyada yapılmaz.
ES modülleri file:// üzerinden çalışmadığı için küçük bir modül kaydı kurulur:
her modül kendi kapsamında bir fabrika fonksiyonu olur, __req ile çözülür.
"""
import json, re, pathlib, sys, datetime

KOK = pathlib.Path(__file__).resolve().parent
KAYNAK, CIKTI = KOK / "kaynak", KOK / "cikti"
GIRIS = "js/uygulama.js"
SENTETIK = {"js/baslangic.js"}   # baslangic.json'dan uretilir

def normalize(yol: str, kaynak: str) -> str:
    """'../ortak.js' + 'js/ekranlar/x.js' -> 'js/ortak.js'"""
    return str((pathlib.PurePosixPath(kaynak).parent / yol).as_posix()
               ).replace("/./", "/").split("#")[0]

def coz(p: pathlib.PurePosixPath) -> str:
    parca = []
    for k in str(p).split("/"):
        if k == "..":
            if parca: parca.pop()
        elif k not in (".", ""):
            parca.append(k)
    return "/".join(parca)

IMPORT_ADLI  = re.compile(r'^\s*import\s*\{([^}]*)\}\s*from\s*["\']([^"\']+)["\'];?\s*$', re.M)
IMPORT_YILDIZ= re.compile(r'^\s*import\s*\*\s*as\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*from\s*["\']([^"\']+)["\'];?\s*$', re.M)
IMPORT_VARS  = re.compile(r'^\s*import\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*from\s*["\']([^"\']+)["\'];?\s*$', re.M)
AD = r'[A-Za-z_$][A-Za-z0-9_$]*'          # JS tanimlayicisi: $ ve _ dahil
EXPORT_BILDIRIM = re.compile(r'^\s*export\s+(const|let|var|function|class|async function)\s+(' + AD + ')', re.M)
EXPORT_LISTE = re.compile(r'^\s*export\s*\{([^}]*)\};?\s*$', re.M)
EXPORT_VARS  = re.compile(r'^\s*export\s+default\s+', re.M)

def modulu_sar(yol: str, metin: str) -> str:
    bagimli = []
    def adli(m):
        hedef = coz(pathlib.PurePosixPath(normalize(m.group(2), yol)))
        bagimli.append(hedef)
        ic = ", ".join(p.strip().replace(" as ", ": ") for p in m.group(1).split(",") if p.strip())
        return f'const {{ {ic} }} = __req("{hedef}");'
    def yildiz(m):
        hedef = coz(pathlib.PurePosixPath(normalize(m.group(2), yol)))
        bagimli.append(hedef)
        return f'const {m.group(1)} = __req("{hedef}");'
    def varsayilan(m):
        hedef = coz(pathlib.PurePosixPath(normalize(m.group(2), yol)))
        bagimli.append(hedef)
        return f'const {m.group(1)} = __req("{hedef}").default;'

    metin = IMPORT_ADLI.sub(adli, metin)
    metin = IMPORT_YILDIZ.sub(yildiz, metin)
    metin = IMPORT_VARS.sub(varsayilan, metin)

    disa = [m.group(2) for m in EXPORT_BILDIRIM.finditer(metin)]
    for m in EXPORT_LISTE.finditer(metin):
        disa += [p.strip().split(" as ")[-1].strip() for p in m.group(1).split(",") if p.strip()]
    metin = EXPORT_LISTE.sub("", metin)
    metin = EXPORT_VARS.sub("__x.default = ", metin)
    metin = re.sub(r'^\s*export\s+(?=(const|let|var|function|class|async function)\s)', "", metin, flags=re.M)

    atama = "\n".join(f'  __x.{a} = {a};' for a in dict.fromkeys(disa))
    return (f'__f["{yol}"] = function(__x) {{\n{metin}\n{atama}\n}};\n', bagimli)

def topla(giris: str):
    moduller, sira, bekleyen = {}, [], [giris]
    while bekleyen:
        y = bekleyen.pop(0)
        if y in moduller or y in SENTETIK: continue
        d = KAYNAK / y
        if not d.exists(): sys.exit(f"HATA: {y} bulunamadı")
        sarili, bag = modulu_sar(y, d.read_text(encoding="utf-8"))
        moduller[y] = sarili; sira.append(y)
        bekleyen += [b for b in bag if b not in moduller]
    return sira, moduller

def main():
    html = (KAYNAK / "index.html").read_text(encoding="utf-8")
    css  = (KAYNAK / "css" / "stil.css").read_text(encoding="utf-8")

    sira, moduller = topla(GIRIS)

    # baslangic.json -> sentetik modül (K-16: tanımlar gömülü gelir)
    bas = json.loads((KAYNAK / "baslangic.json").read_text(encoding="utf-8"))
    moduller["js/baslangic.js"] = (
        '__f["js/baslangic.js"] = function(__x) {\n  __x.default = '
        + json.dumps(bas, ensure_ascii=False, separators=(",", ":")) + ";\n};\n")
    sira.append("js/baslangic.js")

    kayit = """
/* Modül kaydı — ES modülleri file:// üzerinden çalışmadığı için (K-09, K-18) */
var __f = {}, __c = {};
function __req(y) {
  if (!(y in __c)) {
    if (!(y in __f)) throw new Error("Modül yok: " + y);
    __c[y] = {}; __f[y](__c[y]);
  }
  return __c[y];
}
"""
    govde = kayit + "".join(moduller[y] for y in sira)
    govde += """
__req("js/uygulama.js").baslat().catch(function (e) {
  document.getElementById("icerik").innerHTML =
    '<div class="uyari kritik"><span class="ikon">\\u2715</span><div><b>Başlatılamadı:</b> ' +
    e.message + '</div></div>';
  console.error(e);
});
"""
    # Not: yerine koyma metni ters bolu icerdigi icin lambda kullanilir
    html = re.sub(r'<!--STIL-->.*?<!--/STIL-->',
                  lambda _: "<style>\n" + css + "\n</style>", html, flags=re.S)
    html = re.sub(r'<!--BETIK-->.*?<!--/BETIK-->',
                  lambda _: "<script>\n" + govde + "\n</" + "script>", html, flags=re.S)
    damga = datetime.date.today().isoformat()
    html = html.replace("</head>", f"<!-- Derleme: {damga} · Faz 1 · Çekirdek -->\n</head>")

    CIKTI.mkdir(exist_ok=True)
    hedef = CIKTI / "enerji-yonetim.html"
    hedef.write_text(html, encoding="utf-8")

    kb = len(html.encode("utf-8")) / 1024
    print(f"{hedef}")
    print(f"  modül  : {len(sira)}  ({', '.join(y.split('/')[-1] for y in sira)})")
    print(f"  boyut  : {kb:,.0f} KB")
    print(f"  tanım  : {len(bas['varliklar'])} varlık · {len(bas['olcum_noktalari'])} ölçüm noktası")

if __name__ == "__main__":
    main()
