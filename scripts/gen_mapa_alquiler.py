#!/usr/bin/env python3
# gen_mapa_alquiler.py — mapa Leaflet del alquiler con franjas de precio por umbrales
import sqlite3, json
from pathlib import Path

BASE = Path.home() / "municipal-intel"
DB = BASE / "data/poblacion_municipal.sqlite"
VIADB = BASE / "dashboard/data/via/via.db"
OUT = BASE / "dashboard/mapa-alquiler.html"

cv = sqlite3.connect(f"file:{VIADB}?mode=ro", uri=True)
fecha = cv.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
via = {m: (e, a) for m, e, a in cv.execute(
    "SELECT municipio, eur_m2_mediana, anuncios FROM via_index WHERE fecha=? AND eur_m2_mediana>0", (fecha,))}
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
for m, (e, a) in via.items():
    if m in coords:
        v = None
        if pob25.get(m) and pob16.get(m) and pob16[m] > 0:
            v = round((pob25[m] - pob16[m]) / pob16[m] * 100, 1)
        puntos.append({"m": m, "e": e, "a": a, "v": v, "lat": coords[m][0], "lon": coords[m][1]})

pts_js = "[" + ",".join(
    f'{{"m":"{p["m"]}","e":{p["e"]:.2f},"a":{p["a"]},"v":{p["v"] if p["v"] is not None else "null"},"lat":{p["lat"]},"lon":{p["lon"]}}}' for p in puntos) + "]"

html_cabeza = f'''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa del alquiler en España · €/m² por municipio | Municipal Intelligence</title>
<meta name="description" content="Mapa interactivo del precio del alquiler por municipio en España: €/m² de anuncios activos, con franjas de precio y leyenda.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/mapa-alquiler.html">
<meta property="og:title" content="Mapa del alquiler en España — €/m² por municipio">
<meta property="og:image" content="https://municipal.viajeinteligencia.com/og-alquiler.png">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"Mapa del alquiler en España"}}</script>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8}}
*{{box-sizing:border-box}} body{{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg)}}
header{{padding:18px 24px;border-bottom:1px solid #334155;text-align:center}}
h1{{margin:0 0 4px;font-size:21px}} .sub{{color:var(--mut);font-size:13px}}
#map{{height:calc(100vh - 150px);width:100%}}
.legend{{background:var(--card);border:1px solid #334155;border-radius:10px;padding:10px 14px;font-size:12px;color:var(--mut);line-height:1.9}}
.legend b{{color:var(--fg)}}
</style>
</head><body>
<header><h1>🗺️ Mapa del alquiler en España</h1>
<div class="sub">€/m² mediana de anuncios activos · {len(puntos)} municipios · actualizado {fecha}</div></header>
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
var PUNTOS = {pts_js};
var map = L.map('map').setView([40.2, -3.7], 6);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:18, attribution:'© OpenStreetMap'}}).addTo(map);
PUNTOS.forEach(function(p) {{
  var c = "#16a34a";
  if (p.e >= 8 && p.e < 11) c = "#65a30d";
  else if (p.e >= 11 && p.e < 14) c = "#ca8a04";
  else if (p.e >= 14 && p.e < 18) c = "#ea580c";
  else if (p.e >= 18 && p.e < 22) c = "#dc2626";
  else if (p.e >= 22) c = "#7f1d1d";
  L.circleMarker([p.lat, p.lon], {{radius:8, fillColor:c, fillOpacity:0.9, color:'#fff', weight:1}})
    .bindPopup('<b>' + p.m + '</b><br>' + p.e.toFixed(2) + ' €/m² · ' + p.a + ' anunc'
      + (p.v != null ? '<br><span style="color:' + (p.v >= 0 ? '#4ade80' : '#f87171') + '">población ' + (p.v >= 0 ? '▲ +' : '▼ ') + p.v + '% (10 años)</span>' : ''))
    .addTo(map);
}});
</script>
</body></html>'''

OUT.write_text(html_cabeza, encoding="utf-8")
print(f"OK -> {OUT.name} | {len(puntos)} puntos")
