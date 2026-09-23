#!/usr/bin/env python3
# gen_mapa_alquiler.py — mapa Leaflet del alquiler con franjas de precio por umbrales
# + buscador + enlace a la ficha del municipio + enlace directo (?m=slug)
import sqlite3, json
from pathlib import Path

BASE = Path.home() / "municipal-intel"
DB = BASE / "data/poblacion_municipal.sqlite"
VIADB = BASE / "dashboard/data/via/via.db"
OUT = BASE / "dashboard/mapa-alquiler.html"

# slug por codigo_ine (lo exporta gen_municipio_pages.py; resuelve colisiones)
slugs = {}
_sl = BASE / "dashboard/data/municipio_slugs.json"
if _sl.exists():
    slugs = json.loads(_sl.read_text(encoding="utf-8"))

cv = sqlite3.connect(f"file:{VIADB}?mode=ro", uri=True)
fecha = cv.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
via = {}
for m, e, a, code, p25, p75, of in cv.execute(
        "SELECT municipio, eur_m2_mediana, anuncios, codigo_ine, p25, p75, oficial_eur_m2 "
        "FROM via_index WHERE fecha=? AND eur_m2_mediana>0", (fecha,)):
    via[m] = (e, a, slugs.get(code, ""), p25, p75, of)
cv.close()

cc = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
coords = {}
for m, lat, lon in cc.execute("SELECT municipio, lat, lon FROM catalogo WHERE lat IS NOT NULL AND lon IS NOT NULL"):
    coords[m] = (lat, lon)
cc.close()

# variación de población 10 años (2016-2025) para la correlación
cc2 = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
pob25 = {m: p for m, p in cc2.execute("SELECT municipio, poblacion FROM poblacion WHERE anyo='2025' AND sexo='Total'")}
pob16 = {m: p for m, p in cc2.execute("SELECT municipio, poblacion FROM poblacion WHERE anyo='2016' AND sexo='Total'")}
cc2.close()

puntos = []
for m, (e, a, s, p25, p75, of) in via.items():
    if m in coords:
        v = None
        if pob25.get(m) and pob16.get(m) and pob16[m] > 0:
            v = round((pob25[m] - pob16[m]) / pob16[m] * 100, 1)
        puntos.append({"m": m, "e": e, "a": a, "s": s or "", "p25": p25, "p75": p75,
                       "of": of, "v": v, "lat": coords[m][0], "lon": coords[m][1]})


def _n(x):
    return "null" if x is None else f"{x}"


pts_js = "[" + ",".join(
    '{"m":%s,"e":%.2f,"a":%d,"s":%s,"p25":%s,"p75":%s,"of":%s,"v":%s,"lat":%s,"lon":%s}' % (
        json.dumps(p["m"], ensure_ascii=False), p["e"], p["a"],
        json.dumps(p["s"], ensure_ascii=False), _n(p["p25"]), _n(p["p75"]),
        _n(p["of"]), _n(p["v"]), p["lat"], p["lon"])
    for p in puntos) + "]"

TEMPLATE = '''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa del alquiler en España · €/m² por municipio | Municipal Intelligence</title>
<meta name="description" content="Mapa interactivo del precio del alquiler por municipio en España: €/m² de anuncios activos, con franjas de precio, buscador y ficha de cada municipio.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/mapa-alquiler.html">
<meta property="og:title" content="Mapa del alquiler en España — €/m² por municipio">
<meta property="og:description" content="Mapa interactivo del precio del alquiler por municipio en España: €/m² de anuncios activos, con franjas de precio y leyenda.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://municipal.viajeinteligencia.com/mapa-alquiler.html">
<meta property="og:locale" content="es_ES">
<meta property="og:image" content="https://municipal.viajeinteligencia.com/og-alquiler.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"Mapa del alquiler en España"}</script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8}
*{box-sizing:border-box} body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:18px 24px;border-bottom:1px solid #334155;text-align:center}
h1{margin:0 0 4px;font-size:21px} .sub{color:var(--mut);font-size:13px}
#buscar{padding:9px 13px;border-radius:9px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;font-size:14px;width:min(340px,82vw)}
#map{height:calc(100vh - 190px);width:100%}
.legend{background:var(--card);border:1px solid #334155;border-radius:10px;padding:10px 14px;font-size:12px;color:var(--mut);line-height:1.9}
.legend b{color:var(--fg)}
</style>
</head><body>
<header><h1>🗺️ Mapa del alquiler en España</h1>
<div class="sub">€/m² mediana de anuncios activos · @@N@@ municipios · actualizado @@FECHA@@</div>
<div style="margin-top:10px"><input id="buscar" list="mlista" placeholder="🔎 Buscar municipio…" autocomplete="off"><datalist id="mlista"></datalist></div>
<div style="margin-top:10px;font-size:13px">
<a href="alquiler.html" style="color:#58a6ff;text-decoration:none;margin:0 8px">← Volver al índice de alquiler</a>
<a href="/" style="color:#58a6ff;text-decoration:none;margin:0 8px">🏘️ Municipal</a>
<a href="https://www.viajeinteligencia.com/ecosistema.html" style="color:#58a6ff;text-decoration:none;margin:0 8px">🌐 Ecosistema</a>
</div></header>
<div class="legend" style="position:absolute;z-index:1000;left:10px;bottom:10px">
<b>Precio del alquiler (€/m²)</b>
<div style="margin-top:6px"><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#16a34a;margin-right:6px"></span>menos de 8</div>
<div><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#65a30d;margin-right:6px"></span>8 – 11</div>
<div><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#ca8a04;margin-right:6px"></span>11 – 14</div>
<div><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#ea580c;margin-right:6px"></span>14 – 18</div>
<div><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#dc2626;margin-right:6px"></span>18 – 22</div>
<div><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:#7f1d1d;margin-right:6px"></span>más de 22</div>
</div>
<div id="map"></div>
<script>
var PUNTOS = @@PTS@@;
function colorDe(e){
  if (e < 8) return "#16a34a";
  if (e < 11) return "#65a30d";
  if (e < 14) return "#ca8a04";
  if (e < 18) return "#ea580c";
  if (e < 22) return "#dc2626";
  return "#7f1d1d";
}
function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
var map = L.map('map').setView([40.2, -3.7], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:18, attribution:'© OpenStreetMap'}).addTo(map);
var markers = {};
var bySlug = {};
PUNTOS.forEach(function(p){
  var s = '<b>' + esc(p.m) + '</b><br>' + p.e.toFixed(2) + ' €/m² · ' + p.a + ' anunc';
  if (p.p25 != null && p.p75 != null) s += '<br><span style="color:#94a3b8">rango ' + p.p25.toFixed(1) + '–' + p.p75.toFixed(1) + ' €/m²</span>';
  if (p.of != null) s += '<br><span style="color:#94a3b8">oficial ' + p.of.toFixed(2) + ' €/m²</span>';
  if (p.v != null) s += '<br><span style="color:' + (p.v >= 0 ? '#4ade80' : '#f87171') + '">población ' + (p.v >= 0 ? '▲ +' : '▼ ') + p.v + '% (10 años)</span>';
  if (p.s) s += '<br><a href="/municipio/' + p.s + '.html" style="color:#58a6ff;font-weight:600">Ver ficha completa →</a>';
  if (p.s) s += '<br><a href="?m=' + p.s + '" style="color:#94a3b8;font-size:12px">🔗 enlace directo a este municipio</a>';
  var mk = L.circleMarker([p.lat, p.lon], {radius:8, fillColor:colorDe(p.e), fillOpacity:0.9, color:'#fff', weight:1})
    .bindPopup(s).addTo(map);
  markers[p.m] = mk;
  if (p.s) bySlug[p.s] = p;
});
// Buscador
var byName = {};
PUNTOS.forEach(function(p){ byName[p.m] = p; });
var dl = document.getElementById('mlista');
PUNTOS.slice().sort(function(a,b){ return a.m.localeCompare(b.m, 'es'); }).forEach(function(p){
  var o = document.createElement('option'); o.value = p.m; dl.appendChild(o);
});
function irA(p){ if(!p) return; map.setView([p.lat, p.lon], 12); markers[p.m].openPopup(); }
document.getElementById('buscar').addEventListener('change', function(){
  irA(byName[this.value.trim()]);
});
// Enlace directo ?m=slug
var slug = new URLSearchParams(location.search).get('m');
if (slug && bySlug[slug]) irA(bySlug[slug]);
</script>
</body></html>'''

html = (TEMPLATE.replace("@@PTS@@", pts_js)
                .replace("@@N@@", str(len(puntos)))
                .replace("@@FECHA@@", str(fecha)))

OUT.write_text(html, encoding="utf-8")
print(f"OK -> {OUT.name} | {len(puntos)} puntos")
