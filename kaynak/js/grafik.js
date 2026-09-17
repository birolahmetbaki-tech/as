/* grafik.js — saf SVG grafik motoru (K-17, El Kitabı 5.7)
   Faz 2'de yalnız mini grafik (sparkline) var; Faz 3'te sütun, çizgi,
   yığılmış, ısı haritası, dağılım, Pareto, CUSUM ve Sankey eklenecek.

   Bağlayıcı kurallar (5.7.2): çift eksen YOK · ince işaretler ·
   saç teli kılavuz · her veri noktasına sayı yazılmaz. */

const NS = "http://www.w3.org/2000/svg";

export function svgOge(ad, ozellik = {}, ...cocuk) {
  const d = document.createElementNS(NS, ad);
  for (const [k, v] of Object.entries(ozellik))
    if (v !== null && v !== undefined) d.setAttribute(k, v);
  for (const c of cocuk.flat()) if (c) d.append(c);
  return d;
}

/**
 * Satır içi mini grafik. Sayı yazmaz, eksen çizmez — yalnız biçim gösterir.
 * @param degerler [number|null]  null = veri yok, çizgi kopar
 */
export function miniGrafik(degerler, { en = 84, boy = 20, renk = "var(--s1)" } = {}) {
  const g = degerler.filter(v => v !== null && Number.isFinite(v));
  const svg = svgOge("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
                              role:"img", "aria-hidden":"true",
                              style:"display:block;overflow:visible" });
  if (g.length < 2) return svg;

  const enk = Math.min(...g), enb = Math.max(...g);
  const aralik = enb - enk || 1;
  const dx = en / Math.max(1, degerler.length - 1);
  const y = v => boy - 2 - ((v - enk) / aralik) * (boy - 4);

  let d = "", kalem = false;
  degerler.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) { kalem = false; return; }
    d += (kalem ? "L" : "M") + (i * dx).toFixed(1) + "," + y(v).toFixed(1) + " ";
    kalem = true;
  });
  svg.append(svgOge("path", { d, fill:"none", stroke:renk, "stroke-width":1.5,
                              "stroke-linejoin":"round", "stroke-linecap":"round",
                              opacity:.85 }));
  // Son nokta işaretlenir — seçici etiketleme kuralı (5.7.2)
  const sonIndeks = degerler.map((v, i) => [v, i]).filter(([v]) => v !== null && Number.isFinite(v)).pop();
  if (sonIndeks)
    svg.append(svgOge("circle", { cx:(sonIndeks[1] * dx).toFixed(1), cy:y(sonIndeks[0]).toFixed(1),
                                  r:2, fill:renk }));
  return svg;
}

/** Yatay oran çubuğu (ölçüm kapsamı gibi). Tek hue, ince. */
export function oranCubugu(oran, { en = 120, boy = 8, renk = "var(--s1)" } = {}) {
  const svg = svgOge("svg", { width:en, height:boy, viewBox:`0 0 ${en} ${boy}`,
                              role:"img", "aria-hidden":"true", style:"display:block" });
  svg.append(svgOge("rect", { x:0, y:0, width:en, height:boy, rx:boy/2, fill:"var(--kilavuz)" }));
  const g = Math.max(0, Math.min(1, oran || 0));
  if (g > 0) svg.append(svgOge("rect", { x:0, y:0, width:(en*g).toFixed(1), height:boy,
                                         rx:boy/2, fill:renk }));
  return svg;
}
