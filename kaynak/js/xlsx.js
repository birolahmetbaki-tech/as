/* xlsx.js — .xlsx okuma ve yazma, SIFIR DIŞ KÜTÜPHANE
   El Kitabı: K-15 (.xlsx doğrudan okunur), K-17 (sıfır bağımlılık ruhu), K-11 (Chrome/Edge)

   Bir .xlsx dosyası, içinde XML barındıran bir ZIP'tir. Tarayıcının kendi
   DecompressionStream/CompressionStream ve DOMParser arayüzleri işi görür;
   ~400 KB'lık bir kütüphane gömmeye gerek yoktur. */

/* ============================================================ ZIP okuma */

const g16 = (d, o) => d.getUint16(o, true);
const g32 = (d, o) => d.getUint32(o, true);

async function sisir(veri, yontem) {
  if (yontem === 0) return veri;                      // STORED
  if (yontem !== 8) throw new Error("Desteklenmeyen sıkıştırma: " + yontem);
  const ds = new DecompressionStream("deflate-raw");
  const y = ds.writable.getWriter(); y.write(veri); y.close();
  return new Uint8Array(await new Response(ds.readable).arrayBuffer());
}

/** ZIP arşivini açar → Map<dosyaAdı, Uint8Array> */
export async function zipAc(arrayBuffer) {
  const u8 = new Uint8Array(arrayBuffer);
  const d = new DataView(arrayBuffer);

  // Merkezî dizin sonu kaydını (EOCD) sondan tarayarak bul
  let eocd = -1;
  for (let i = u8.length - 22; i >= Math.max(0, u8.length - 65557); i--)
    if (g32(d, i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) throw new Error("Bu bir ZIP/xlsx dosyası değil.");

  const adet = g16(d, eocd + 10);
  let p = g32(d, eocd + 16);
  const dosyalar = new Map();

  for (let i = 0; i < adet; i++) {
    if (g32(d, p) !== 0x02014b50) throw new Error("Merkezî dizin bozuk.");
    const yontem  = g16(d, p + 10);
    const sikisBoy= g32(d, p + 20);
    const adBoy   = g16(d, p + 28);
    const ekBoy   = g16(d, p + 30);
    const yorumBoy= g16(d, p + 32);
    const yerel   = g32(d, p + 42);
    const ad = new TextDecoder().decode(u8.subarray(p + 46, p + 46 + adBoy));

    // Yerel başlıktan gerçek veri başlangıcını bul (ek alan boyu farklı olabilir)
    const yAdBoy = g16(d, yerel + 26), yEkBoy = g16(d, yerel + 28);
    const bas = yerel + 30 + yAdBoy + yEkBoy;
    dosyalar.set(ad, { yontem, veri: u8.subarray(bas, bas + sikisBoy) });
    p += 46 + adBoy + ekBoy + yorumBoy;
  }

  const sonuc = new Map();
  for (const [ad, k] of dosyalar) sonuc.set(ad, await sisir(k.veri, k.yontem));
  return sonuc;
}

/* ========================================================== xlsx okuma */

const metin = u8 => new TextDecoder("utf-8").decode(u8);
const xml   = s => new DOMParser().parseFromString(s, "application/xml");

/** "BC12" → { sutun: 54, satir: 12 }  (sütun 0'dan başlar) */
export function hucreAdres(ref) {
  const m = /^([A-Z]+)(\d+)$/.exec(ref || "");
  if (!m) return null;
  let s = 0;
  for (const c of m[1]) s = s * 26 + (c.charCodeAt(0) - 64);
  return { sutun: s - 1, satir: +m[2] };
}
/** 0 → "A", 26 → "AA" */
export function sutunAdi(i) {
  let s = "";
  i++;
  while (i > 0) { const k = (i - 1) % 26; s = String.fromCharCode(65 + k) + s; i = (i - k - 1) / 26; }
  return s;
}

/**
 * .xlsx dosyasını okur.
 * @returns {{sayfalar:[{ad, satirlar:[[hücre,...]]}]}}
 *   Hücreler: sayı | string | null
 */
export async function xlsxOku(arrayBuffer) {
  const z = await zipAc(arrayBuffer);
  const al = ad => z.has(ad) ? metin(z.get(ad)) : null;

  // Paylaşılan metinler
  const paylasilan = [];
  const ss = al("xl/sharedStrings.xml");
  if (ss) for (const si of xml(ss).getElementsByTagName("si")) {
    // <si> içindeki bütün <t> düğümleri birleştirilir (zengin metin parçalı olabilir)
    let s = "";
    for (const t of si.getElementsByTagName("t")) s += t.textContent;
    paylasilan.push(s);
  }

  // Sayfa adı → hedef dosya
  const rels = al("xl/_rels/workbook.xml.rels");
  const hedef = new Map();
  if (rels) for (const r of xml(rels).getElementsByTagName("Relationship"))
    hedef.set(r.getAttribute("Id"), r.getAttribute("Target").replace(/^\/?xl\//, ""));

  const wb = al("xl/workbook.xml");
  if (!wb) throw new Error("Geçerli bir Excel dosyası değil (workbook.xml yok).");

  const sayfalar = [];
  let sira = 0;
  for (const s of xml(wb).getElementsByTagName("sheet")) {
    sira++;
    const ad = s.getAttribute("name");
    const rid = s.getAttribute("r:id") || s.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id");
    let yol = hedef.get(rid);
    if (!yol) yol = `worksheets/sheet${sira}.xml`;
    const icerik = al("xl/" + yol);
    if (!icerik) { sayfalar.push({ ad, satirlar: [] }); continue; }
    sayfalar.push({ ad, satirlar: sayfaCoz(xml(icerik), paylasilan) });
  }
  return { sayfalar };
}

function sayfaCoz(doc, paylasilan) {
  const satirlar = [];
  for (const row of doc.getElementsByTagName("row")) {
    const no = +row.getAttribute("r") || satirlar.length + 1;
    const hucreler = [];
    for (const c of row.getElementsByTagName("c")) {
      const a = hucreAdres(c.getAttribute("r"));
      const tip = c.getAttribute("t");
      let deger = null;
      if (tip === "inlineStr") {
        let s = ""; for (const t of c.getElementsByTagName("t")) s += t.textContent;
        deger = s;
      } else {
        const v = c.getElementsByTagName("v")[0];
        if (v) {
          const ham = v.textContent;
          if (tip === "s")      deger = paylasilan[+ham] ?? "";
          else if (tip === "b") deger = ham === "1";
          else if (tip === "e") deger = null;               // #DIV/0! vb.
          else if (tip === "str") deger = ham;
          else { const n = Number(ham); deger = Number.isFinite(n) ? n : ham; }
        }
      }
      if (a) hucreler[a.sutun] = deger; else hucreler.push(deger);
    }
    satirlar[no - 1] = hucreler;
  }
  for (let i = 0; i < satirlar.length; i++) satirlar[i] ||= [];
  return satirlar;
}

/* ========================================================== xlsx yazma */

const CRC_TABLO = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[i] = c >>> 0;
  }
  return t;
})();
function crc32(u8) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < u8.length; i++) c = CRC_TABLO[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

async function bastir(u8) {
  if (typeof CompressionStream === "undefined") return { yontem: 0, veri: u8 };
  const cs = new CompressionStream("deflate-raw");
  const w = cs.writable.getWriter(); w.write(u8); w.close();
  const s = new Uint8Array(await new Response(cs.readable).arrayBuffer());
  return s.length < u8.length ? { yontem: 8, veri: s } : { yontem: 0, veri: u8 };
}

const kacXml = s => String(s ?? "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, "");

/**
 * Çok sayfalı .xlsx üretir.
 * @param sayfalar [{ad, satirlar:[[hücre,...]]}]  hücre: sayı | metin | null
 */
export async function xlsxYaz(sayfalar) {
  const dosyalar = new Map();

  dosyalar.set("[Content_Types].xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
    `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
    `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
    `<Default Extension="xml" ContentType="application/xml"/>` +
    `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>` +
    sayfalar.map((_, i) => `<Override PartName="/xl/worksheets/sheet${i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("") +
    `</Types>`);

  dosyalar.set("_rels/.rels",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
    `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
    `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>` +
    `</Relationships>`);

  dosyalar.set("xl/workbook.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
    `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ` +
    `xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>` +
    sayfalar.map((s, i) => `<sheet name="${kacXml(s.ad).slice(0,31)}" sheetId="${i+1}" r:id="rId${i+1}"/>`).join("") +
    `</sheets></workbook>`);

  dosyalar.set("xl/_rels/workbook.xml.rels",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
    `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
    sayfalar.map((_, i) => `<Relationship Id="rId${i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i+1}.xml"/>`).join("") +
    `</Relationships>`);

  sayfalar.forEach((s, i) => {
    const satirlar = s.satirlar.map((sat, r) => {
      const hucreler = sat.map((h, c) => {
        if (h === null || h === undefined || h === "") return "";
        const ref = sutunAdi(c) + (r + 1);
        return (typeof h === "number" && Number.isFinite(h))
          ? `<c r="${ref}"><v>${h}</v></c>`
          : `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${kacXml(h)}</t></is></c>`;
      }).join("");
      return `<row r="${r + 1}">${hucreler}</row>`;
    }).join("");
    dosyalar.set(`xl/worksheets/sheet${i+1}.xml`,
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">` +
      `<sheetData>${satirlar}</sheetData></worksheet>`);
  });

  return zipYaz(dosyalar);
}

async function zipYaz(dosyalar) {
  const kod = new TextEncoder();
  const yerel = [], merkez = [];
  let ofset = 0;

  for (const [ad, icerik] of dosyalar) {
    const ham = typeof icerik === "string" ? kod.encode(icerik) : icerik;
    const { yontem, veri } = await bastir(ham);
    const adB = kod.encode(ad), c = crc32(ham);

    const yb = new Uint8Array(30 + adB.length);
    const yd = new DataView(yb.buffer);
    yd.setUint32(0, 0x04034b50, true); yd.setUint16(4, 20, true);
    yd.setUint16(8, yontem, true);
    yd.setUint32(14, c, true); yd.setUint32(18, veri.length, true);
    yd.setUint32(22, ham.length, true); yd.setUint16(26, adB.length, true);
    yb.set(adB, 30);
    yerel.push(yb, veri);

    const mb = new Uint8Array(46 + adB.length);
    const md = new DataView(mb.buffer);
    md.setUint32(0, 0x02014b50, true); md.setUint16(4, 20, true); md.setUint16(6, 20, true);
    md.setUint16(10, yontem, true);
    md.setUint32(16, c, true); md.setUint32(20, veri.length, true);
    md.setUint32(24, ham.length, true); md.setUint16(28, adB.length, true);
    md.setUint32(42, ofset, true);
    mb.set(adB, 46);
    merkez.push(mb);

    ofset += yb.length + veri.length;
  }

  const mBoy = merkez.reduce((t, m) => t + m.length, 0);
  const son = new Uint8Array(22);
  const sd = new DataView(son.buffer);
  sd.setUint32(0, 0x06054b50, true);
  sd.setUint16(8, dosyalar.size, true); sd.setUint16(10, dosyalar.size, true);
  sd.setUint32(12, mBoy, true); sd.setUint32(16, ofset, true);

  return new Blob([...yerel, ...merkez, son],
    { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
}
