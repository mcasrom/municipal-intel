import json, sqlite3, os

SLUGMAP = {}
sm_path = os.path.join("dashboard", "data", "municipio_slugs.json")
if os.path.exists(sm_path):
    try:
        SLUGMAP = json.load(open(sm_path))
    except Exception:
        pass

DB = "data/poblacion_municipal.sqlite"
if not os.path.exists(DB):
    DB = "poblacion_municipal.sqlite"
OUT = "dashboard"
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

con = sqlite3.connect(DB)

def pop_of(prov, muni, anyo):
    r = con.execute("SELECT poblacion FROM poblacion WHERE provincia=? AND municipio=? AND anyo=? AND sexo='Total'",
                    (prov, muni, anyo)).fetchone()
    return r[0] if r else None

# catalogo: markers con indicadores (rank, variaciones)
catalogo = []
pob = con.execute("""SELECT c.municipio, c.provincia, c.codigo_ine, c.lat, c.lon,
                     p.poblacion FROM catalogo c
                     JOIN poblacion p ON p.provincia=c.provincia AND p.municipio=c.municipio
                     AND p.anyo=2025 AND p.sexo='Total'""").fetchall()
# precalcular variaciones
def pct(a, b):
    if a is None or b is None or b == 0: return None
    return round((a - b) / b * 100, 1)

g1 = {}; g5 = {}; g16 = {}
for muni, prov, code, lat, lon, pop in pob:
    p24 = pop_of(prov, muni, 2024); p20 = pop_of(prov, muni, 2020); p16 = pop_of(prov, muni, 2016)
    g1[code] = pct(pop, p24); g5[code] = pct(pop, p20); g16[code] = pct(pop, p16)

# rankings
by_pop = sorted(pob, key=lambda x: -x[5])
rank_spain = {r[2]: i + 1 for i, r in enumerate(by_pop)}
rank_prov = {}
for prov in sorted(set(r[1] for r in pob)):
    for i, r in enumerate(sorted([x for x in pob if x[1] == prov], key=lambda x: -x[5])):
        rank_prov[r[2]] = i + 1

for muni, prov, code, lat, lon, pop in pob:
    _sl = SLUGMAP.get(code, "")
    catalogo.append({"c": code, "n": muni, "p": prov, "la": lat, "lo": lon, "po": int(pop), "sl": _sl,
                     "r": rank_spain[code], "rp": rank_prov[code],
                     "g1": g1[code], "g5": g5[code], "g16": g16[code]})
with open(os.path.join(OUT, "data", "catalogo.json"), "w") as f:
    json.dump(catalogo, f, ensure_ascii=False, separators=(",", ":"))
print("catalogo:", len(catalogo))

# rankings.json: tops
def top(iterable, key, n=20, reverse=True):
    return sorted(iterable, key=key, reverse=reverse)[:n]

base_pop = {r[2]: r[5] for r in pob}
topCrec = [{"n": c["n"], "p": c["p"], "c": c["c"], "g": c["g16"], "po": c["po"], "b": base_pop.get(c["c"], 0)} for c in catalogo if c["g16"] is not None]
topDec = [{"n": c["n"], "p": c["p"], "c": c["c"], "g": c["g16"], "po": c["po"], "b": base_pop.get(c["c"], 0)} for c in catalogo if c["g16"] is not None]
# filtrar por poblacion 2016 >= 1000 para que el % sea significativo
topCrec = [x for x in topCrec if x["b"] >= 1000]
topDec = [x for x in topDec if x["b"] >= 1000]
topMay = [{"n": c["n"], "p": c["p"], "c": c["c"], "po": c["po"]} for c in catalogo]
ranking = {
    "titulo": "Crecimiento 2016 → 2025 (municipios ≥ 1.000 hab en 2016)",
    "nota": "Variación 2016→2025 sobre municipios con ≥ 1.000 habitantes en 2016 (evita el ruido de pueblos pequeños).",
    "crec": top(topCrec, lambda x: x["g"]),
    "dec": top(topDec, lambda x: x["g"], reverse=False),
    "may": top(topMay, lambda x: x["po"]),
}
with open(os.path.join(OUT, "data", "rankings.json"), "w") as f:
    json.dump(ranking, f, ensure_ascii=False, separators=(",", ":"))
print("rankings.json OK")

# series: {codigo: [[anyo, total], ...]}
series = {}
rows = con.execute("""SELECT c.codigo_ine, p.anyo, p.poblacion FROM catalogo c
                      JOIN poblacion p ON p.provincia=c.provincia AND p.municipio=c.municipio
                      AND p.sexo='Total' ORDER BY c.codigo_ine, p.anyo""").fetchall()
for code, anyo, pop in rows:
    series.setdefault(code, []).append([anyo, int(pop)])
with open(os.path.join(OUT, "data", "series.json"), "w") as f:
    json.dump(series, f, separators=(",", ":"))
print("series:", len(series), "| fichero KB:", os.path.getsize(os.path.join(OUT,"data","series.json"))//1024)
con.close()

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Municipal Intelligence · Mapa de población de los municipios de España</title>
<meta name="description" content="Mapa de la población oficial de los 8.132 municipios de España (INE, 1996-2025): busca cualquier municipio, mira su evolución, comparala con otro y descubre quién crece y quién se vacía. Datos oficiales y trazables.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/">
<meta property="og:type" content="website">
<meta property="og:title" content="Municipal Intelligence · Mapa de población de los municipios de España">
<meta property="og:description" content="Población oficial de los 8.132 municipios de España (INE 1996-2025): evolución, rankings y comparador.">
<meta property="og:url" content="https://municipal.viajeinteligencia.com/">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/png" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-192.png">
<meta property="og:image" content="https://municipal.viajeinteligencia.com/og-municipal.png">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#1e293b">
<meta name="apple-mobile-web-app-capable" content="yes">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Población de los municipios de España (INE 1996-2025)",
  "description": "Cifras oficiales de población de los 8.132 municipios de España: Revisión del Padrón Municipal (INE), serie 1996-2025, con evolución, rankings y comparador.",
  "url": "https://municipal.viajeinteligencia.com/",
  "dateModified": "2026-08-21",
  "creator": {"@type": "Person", "name": "M. Castillo"},
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "temporalCoverage": "1996/2025",
  "spatialCoverage": {"@type": "Place", "name": "España", "address": {"@type": "PostalAddress", "addressCountry": "ES"}},
  "distribution": {"@type": "DataDownload", "contentUrl": "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2883", "encodingFormat": "JSON"}
}
</script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
#map{position:absolute;inset:0}
#top{position:absolute;top:12px;left:12px;z-index:1000;background:var(--card);border-radius:10px;padding:12px 14px;box-shadow:0 4px 20px rgba(0,0,0,.4);max-width:320px;width:calc(100vw - 24px)}
#top h1{font-size:15px;margin-bottom:8px}
#top h1 small{color:var(--mut);font-weight:400;display:block;font-size:11px}
#buscar{width:100%;padding:9px 12px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:var(--fg);font-size:14px}
#sug{list-style:none;margin-top:6px;max-height:200px;overflow:auto;display:none}
#sug li{padding:8px 10px;border-radius:6px;cursor:pointer;font-size:13px}
#sug li:hover{background:#334155}
#side{position:absolute;top:12px;right:12px;bottom:12px;z-index:1000;width:330px;max-width:calc(100vw - 24px);background:var(--card);border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,.4);display:block;overflow:auto;padding:16px}
#side h2{font-size:18px}
#side .mut{color:var(--mut);font-size:12px;margin:2px 0 10px}
#side .kpis{display:flex;gap:8px;margin:10px 0}
#side .kpi{flex:1;background:#0f172a;border-radius:8px;padding:8px;text-align:center}
#side .kpi b{display:block;font-size:16px}
#side .kpi span{font-size:10px;color:var(--mut)}
#side canvas{width:100%;height:110px;margin-top:6px}
#side .delta{font-size:13px;margin-top:8px}
#side .src{font-size:10px;color:var(--mut);margin-top:14px;line-height:1.5}
#side .close{position:absolute;top:10px;right:12px;background:none;border:none;color:var(--mut);font-size:20px;cursor:pointer}
.leaflet-popup-content-wrapper{background:#1e293b;color:var(--fg)}
.leaflet-popup-tip{background:#1e293b}
#foot{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);z-index:999;font-size:10px;color:var(--mut);background:rgba(15,23,42,.85);padding:4px 10px;border-radius:20px;white-space:nowrap}
#landing{position:absolute;inset:0;z-index:2000;background:rgba(2,6,23,.82);display:none;align-items:center;justify-content:center;padding:20px}
#landBox{background:var(--card);border-radius:14px;max-width:560px;width:100%;padding:26px;box-shadow:0 10px 50px rgba(0,0,0,.6);position:relative}
#landBox .close{position:absolute;top:12px;right:16px;background:none;border:none;color:var(--mut);font-size:22px;cursor:pointer}
.cta{flex:1;min-width:130px;padding:10px 12px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:var(--fg);font-size:13px;cursor:pointer}
.cta:hover{border-color:var(--acc);background:#1e293b}
#kofi{position:absolute;bottom:44px;left:12px;z-index:1500;width:42px;height:42px;border-radius:50%;background:var(--card);border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 2px 10px rgba(0,0,0,.5)}
#kofi a{text-decoration:none}
#kofi:hover{border-color:var(--acc);background:#334155}
#ecosistema{position:absolute;bottom:44px;left:60px;z-index:1500;width:42px;height:42px;border-radius:50%;background:var(--card);border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 2px 10px rgba(0,0,0,.5)}
#ecosistema a{text-decoration:none}
#ecosistema:hover{border-color:var(--acc);background:#334155}
.legend{position:absolute;bottom:24px;right:12px;z-index:999;background:var(--card);border-radius:8px;padding:8px 10px;font-size:11px;color:var(--mut);box-shadow:0 2px 10px rgba(0,0,0,.4)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
#top .btn{width:100%;margin-top:8px;padding:8px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:var(--fg);font-size:12px;cursor:pointer}
#top .btn:hover{background:#334155}
#sRank{font-size:13px;color:var(--acc);margin:6px 0}
#sCtx{font-size:13px;line-height:1.5;color:var(--fg);background:#0f172a;border-radius:8px;padding:10px 12px;margin:6px 0}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.chip{padding:3px 8px;border-radius:14px;font-size:11px;background:#0f172a;border:1px solid #334155}
.chip b{color:var(--acc)}
#cmp{width:100%;margin-top:8px;padding:8px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:var(--fg);font-size:12px}
#cmpLabel{font-size:11px;color:var(--mut);margin-top:10px}
#topPanel{position:absolute;top:12px;left:12px;z-index:1001;background:var(--card);border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,.4);width:330px;max-width:calc(100vw - 24px);padding:12px 14px;display:none;max-height:75vh;overflow:auto}
#topPanel h3{font-size:14px;margin-bottom:8px}
#topPanel .tabs{display:flex;gap:6px;margin-bottom:8px}
#topPanel .tabs button{flex:1;padding:6px;border:1px solid #334155;border-radius:6px;background:#0f172a;color:var(--mut);font-size:11px;cursor:pointer}
#topPanel .tabs button.act{color:var(--fg);border-color:var(--acc);background:#1e293b}
#topPanel table{width:100%;border-collapse:collapse;font-size:12px}
#topPanel td{padding:5px 6px;border-bottom:1px solid #1e293b}
#topPanel td:nth-child(2){text-align:right;color:var(--mut)}
#topPanel td:last-child{text-align:right}
#topPanel tr{cursor:pointer}
#topPanel tr:hover{background:#1e293b}
#topPanel .gpos{color:#4ade80}
#topPanel .gneg{color:#f87171}
#topPanel .close{position:absolute;top:10px;right:12px;background:none;border:none;color:var(--mut);font-size:20px;cursor:pointer}
#cmp2{border-top:1px solid #334155;margin-top:10px;padding-top:10px;display:none}
#cmp2 b{color:var(--acc);font-size:12px}
</style>
</head>
<body>
<div id="map"></div>
<div id="landing">
  <div id="landBox">
    <button class="close" onclick="cerrarLanding()">&times;</button>
    <h1 style="font-size:22px;margin-bottom:4px">Municipal Intelligence</h1>
    <div style="color:#94a3b8;font-size:13px;margin-bottom:14px">Mapa de la población oficial de los <b style="color:#e2e8f0">8.132 municipios de España</b> · INE 1996-2025</div>
    <div style="font-size:14px;line-height:1.6;margin-bottom:10px">
      Busca cualquier municipio y mira <b>su población, su evolución y su posición</b> en el ranking de España.<br>
      Compara dos municipios entre sí.<br>
      Descubre <b>quién crece y quién se vacía</b> (España vaciada).
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <button class="cta" onclick="cerrarLanding()">Explorar el mapa</button>
      <button class="cta" onclick="verRankings()">Ver rankings</button>
    </div>
    <div style="border-top:1px solid #334155;padding-top:10px;margin-top:6px">
      <div style="font-size:12px;font-weight:700;color:#38bdf8;margin-bottom:6px">Caso de estudio · Transparencia del Ayuntamiento de Lorca</div>
      <div style="font-size:13px;color:#94a3b8;line-height:1.5;margin-bottom:8px">Contratos menores, proveedores y posibles troceados del Ayuntamiento — un ejemplo de la capa de inteligencia municipal.</div>
      <button class="cta" onclick="irLorca()" style="background:#1e293b">Ver Lorca (transparencia) →</button>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
      <a class="cta" style="display:block;text-align:center;text-decoration:none" href="https://ko-fi.com/m_castillo" target="_blank" rel="noopener">☕ Apoyar en Ko-fi</a>
      <a class="cta" style="display:block;text-align:center;text-decoration:none" href="mailto:info@viajeinteligencia.com">Contacto</a>
    </div>
    <div style="font-size:11px;color:#94a3b8;margin-top:10px">
      Datos: INE a 01/01/2025 (publicado 11/12/2025) · © OpenStreetMap · <a href="acerca.html" style="color:#38bdf8">Metodología, fuentes y licencia</a>
    </div>
  </div>
</div>
<div id="top">
  <h1>Municipal Intelligence<small>Población de los 8.132 municipios de España · INE</small></h1>
  <div id="fresco" style="font-size:10px;color:#94a3b8;margin-bottom:8px">Datos: población a 01/01/2025 (INE, publicado 11/12/2025). Contratos de Lorca: trimestrales hasta Q2 2026 (transparencia.lorca.es).</div>
  <input id="buscar" placeholder="Busca un municipio… (ej. Lorca)" autocomplete="off">
  <ul id="sug"></ul>
  <button class="btn" onclick="verRankings()">Rankings · crecimientos · descensos</button>
</div>
<div id="topPanel">
  <button class="close" onclick="ocultarRankings()">&times;</button>
  <h3 id="rkTitulo">Rankings</h3>
  <div class="tabs">
    <button class="act" onclick="tabRank('crec')">Crecen</button>
    <button onclick="tabRank('dec')">Caen</button>
    <button onclick="tabRank('may')">Mayores</button>
  </div>
  <table id="rkTabla"></table>
</div>
<div id="side">
  <button class="close" onclick="ocultarPanel()">&times;</button>
  <h2 id="sNom"></h2>
  <div class="mut"><span id="sProv"></span> · código INE <span id="sCod"></span></div>
  <div id="sWelcome" style="margin-top:12px;line-height:1.6">
    <div style="font-size:14px;font-weight:600;color:#38bdf8;margin-bottom:8px">¿Cómo usar?</div>
    <div style="font-size:13px;color:#94a3b8">
      <b style="color:#e2e8f0">Clic en un punto</b> del mapa → ficha del municipio (población, evolución, ranking, comparador).<br><br>
      <b style="color:#e2e8f0">Clic en Lorca</b> → además, la transparencia del Ayuntamiento (contratos menores, troceado).<br><br>
      <b style="color:#e2e8f0">Botón "Rankings"</b> (arriba) → municipios que más crecen / caen / mayores.<br><br>
      Usa el <b style="color:#e2e8f0">buscador</b> para ir directo a un municipio.
    </div>
  </div>
  <div id="sDatos" style="display:none">
  <div id="sFichaMun" style="display:none;margin:6px 0"></div>
  <div id="sRank"></div>
  <div class="kpis">
    <div class="kpi"><b id="s2025"></b><span>2025</span></div>
    <div class="kpi"><b id="s1996"></b><span>1996</span></div>
    <div class="kpi"><b id="sVar"></b><span>Δ total</span></div>
  </div>
  <div class="chips" id="sChips"></div>
  <div class="delta" id="sDelta"></div>
  <div id="sCtx"></div>
  <div id="sFicha" style="display:none;margin-top:10px"></div>
  <canvas id="graf"></canvas>
  <div id="cmpLabel">Comparar con otro municipio</div>
  <input id="cmp" placeholder="Escribe un municipio…" autocomplete="off">
  <ul id="sug2"></ul>
  <div id="cmp2"><b id="cmpNom"></b> <span id="cmpVal" class="mut" style="font-size:11px"></span><br><span id="cmpSerie" style="font-size:11px"></span></div>
  <div class="src">Datos actualizados: población INE a 01/01/2025 (publicada 11/12/2025), serie 1996-2025 (1997 no publicado; 1996 a 1 de mayo). Contratos del Ayuntamiento de Lorca: relaciones trimestrales de contratos menores (última Q2 2026) y formales vía transparencia.lorca.es. Coordenadas y códigos: © OpenStreetMap (ref:ine) · Overpass. Indicadores calculados sobre datos oficiales. Sin datos inventados.</div>
  </div>
</div>
<div class="legend">
  <div><i style="background:#0ea5e9"></i>&lt; 1.000</div>
  <div><i style="background:#6366f1"></i>1.000-5.000</div>
  <div><i style="background:#8b5cf6"></i>5.000-20.000</div>
  <div><i style="background:#f59e0b"></i>20.000-100.000</div>
  <div><i style="background:#ef4444"></i>&gt; 100.000</div>
</div>
<div id="kofi" title="Apoyar el proyecto en Ko-fi"><a href="https://ko-fi.com/m_castillo" target="_blank" rel="noopener">☕</a></div>
<div id="ecosistema" title="Ecosistema de datos abiertos de viajeinteligencia.com"><a href="https://www.viajeinteligencia.com" target="_blank" rel="noopener">🌍</a></div>
<div id="foot">Municipal Intelligence © 2026 M. Castillo · datos abiertos INE + OpenStreetMap · <a href="acerca.html" style="color:#38bdf8">Metodología, fuentes y licencia</a> · <a href="mailto:info@viajeinteligencia.com" style="color:#38bdf8">Contacto</a> · <a href="https://ko-fi.com/m_castillo" style="color:#38bdf8">Ko-fi</a> · <a href="https://www.viajeinteligencia.com" style="color:#38bdf8">Ecosistema de datos abiertos</a> · sin cookies</div>
<script>
var catalogo=[], series={}, lorcaIntel=null;
fetch('data/catalogo.json').then(r=>r.json()).then(d=>{catalogo=d; pintar();});
fetch('data/series.json').then(r=>r.json()).then(d=>series=d);
fetch('data/lorca_intel.json').then(r=>r.json()).then(d=>lorcaIntel=d);

var map=L.map('map',{renderer:L.canvas(),zoomControl:true}).setView([40.3,-3.6],6);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
var grupo=L.layerGroup().addTo(map);

if('serviceWorker' in navigator){
  navigator.serviceWorker.register('sw.js').catch(function(){});
}

// ---- LANDING (funnel) ----
function cerrarLanding(){document.getElementById('landing').style.display='none';}
function irLorca(){cerrarLanding();var m=catalogo.find(x=>x.c==='30024');if(m)irA(m);}
try{if(!sessionStorage.getItem('municipal_visto')){document.getElementById('landing').style.display='flex';sessionStorage.setItem('municipal_visto','1');}}catch(e){document.getElementById('landing').style.display='flex';}

function clase(p){
  if(p<1000)return {r:3,color:'#0ea5e9'};
  if(p<5000)return {r:5,color:'#6366f1'};
  if(p<20000)return {r:7,color:'#8b5cf6'};
  if(p<100000)return {r:10,color:'#f59e0b'};
  return {r:14,color:'#ef4444'};
}
var idx={}; // codigo -> index
function pintar(){
  catalogo.forEach(function(m,i){
    idx[m.c]=i;
    var c=clase(m.po);
    var crec=m.g16!=null?(m.g16>=0?'<br><span style="color:#4ade80">▲ +'+m.g16.toFixed(1)+'% en 10 años</span>':'<br><span style="color:#f87171">▼ '+m.g16.toFixed(1)+'% en 10 años</span>'):'';
    var mk=L.circleMarker([m.la,m.lo],{radius:c.r,color:c.color,fillColor:c.color,fillOpacity:.75,weight:1}).addTo(grupo);
    mk.bindPopup('<b>'+m.n+'</b> ('+m.p+')<br>'+m.po.toLocaleString('es-ES')+' hab (2025)'+crec);
    mk.on('click',function(){map.setView([m.la,m.lo],10,{animate:true});mostrar(m);});
  });
}

function fmt(n){return Number(n).toLocaleString('es-ES');}

var actual=null, compCode=null;
function dibujar(cod, cod2){
  var cv=document.getElementById('graf'), ctx=cv.getContext('2d');
  var w=cv.clientWidth,h=cv.clientHeight;
  cv.width=w;cv.height=h;ctx.clearRect(0,0,w,h);
  var pad=6, X=i=>pad+i*(w-2*pad)/(28), hh=h-2*pad;
  function dib(c2,col){
    var s=series[c2]||[];
    if(s.length<2)return;
    var ys=s.map(x=>x[1]), mn=Math.min.apply(null,ys), mx=Math.max.apply(null,ys);
    var Y=v=>h-pad-(v-mn)*(hh)/(mx-mn||1);
    ctx.strokeStyle=col;ctx.lineWidth=cod2?1.5:2;ctx.globalAlpha=cod2?.85:1;ctx.beginPath();
    s.forEach(function(pt,i){var x=X(anyoIndex(pt[0])),y=Y(pt[1]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
    ctx.stroke();ctx.globalAlpha=1;
  }
  function anyoIndex(a){ // posicion en la serie 1996-2025 (29 puntos, 1997 no publicado)
    return [1996,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025].indexOf(a);
  }
  dib(cod,'#38bdf8');
  if(cod2)dib(cod2,'#f472b6');
  ctx.fillStyle='#e2e8f0';ctx.font='10px system-ui';
  var s=series[cod]||[];
  if(s.length){ctx.fillText(s[0][0],X(anyoIndex(s[0][0])),h-2);ctx.fillText(s[s.length-1][0],X(anyoIndex(s[s.length-1][0]))-22,h-2);}
  if(cod2&&series[cod2]&&series[cod2].length){var s2=series[cod2];ctx.fillText('1996',X(0),h-2);}
}

function mostrar(m){
  actual=m;
  var s=series[m.c]||[];
  document.getElementById('sNom').textContent=m.n;
  document.getElementById('sProv').textContent=m.p;
  document.getElementById('sCod').textContent=m.c;
  document.getElementById('s2025').textContent=fmt(m.po);
  var a=s[0]?s[0][1]:null;
  document.getElementById('s1996').textContent=a!=null?fmt(a):'—';
  var d=m.po-(a||m.po);
  document.getElementById('sVar').textContent=(a?((d/a)*100).toFixed(1):'—')+'%';
  document.getElementById('sVar').style.color=d>=0?'#4ade80':'#f87171';
  document.getElementById('sDelta').textContent='Creció de '+fmt(a||0)+' ('+s[0][0]+') a '+fmt(m.po)+' ('+s[s.length-1][0]+')'+(d>=0?' (+'+fmt(d)+')':' ('+fmt(d)+')');
  document.getElementById('sRank').textContent='Rank '+m.r+' de 8.132 en España · '+m.rp+'º de su provincia';
  var chips='';
  chips+='<span class="chip">1 año: <b>'+fmtNum(m.g1)+'%</b></span>';
  chips+='<span class="chip">5 años: <b>'+fmtNum(m.g5)+'%</b></span>';
  chips+='<span class="chip">10 años: <b>'+fmtNum(m.g16)+'%</b></span>';
  document.getElementById('sChips').innerHTML=chips;
  var ctxLine=document.getElementById('sCtx');
  if(m.g16==null){ctxLine.textContent='Sin datos suficientes de evolución para este municipio.';}
  else{
    var dir=m.g16>=0?'ha crecido':'ha caído';
    var txt=m.n+' '+dir+' un '+Math.abs(m.g16).toFixed(1)+'% en los últimos 10 años';
    if(m.g1!=null)txt+=' · último año: '+(m.g1>=0?'+':'')+m.g1.toFixed(1)+'%';
    txt+=' · es el '+m.rp+'º municipio de '+m.p+' por población';
    ctxLine.textContent=txt;
  }
  var fichaMun=document.getElementById('sFichaMun');
  if(m.sl){ fichaMun.style.display='block'; fichaMun.innerHTML='<a href="municipio/'+m.sl+'.html" style="color:#38bdf8;font-size:13px;font-weight:600">Ver ficha de población de '+m.n+' →</a>'; }
  else { fichaMun.style.display='none'; fichaMun.innerHTML=''; }
  var fich=document.getElementById('sFicha');
  if(m.c==='30024' && lorcaIntel){
    var li=lorcaIntel;
    var rows='';
    li.top.forEach(function(t){rows+='<tr><td>'+t.n+'</td><td class="r"><b>'+t.c+'</b></td><td class="r">'+t.imp+' €</td></tr>';});
    var alerta='';
    if(li.alerta&&li.alerta.length){
      alerta='<div style="background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:8px 10px;margin:8px 0;font-size:12px"><b style="color:#fca5a5">Posible troceado:</b> '+li.alerta.map(function(a){return a.c+' a '+a.n;}).join(', ')+'</div>';
    }
    fich.style.display='block';
    fich.innerHTML='<div style="border-top:1px solid #334155;margin-top:10px;padding-top:10px">'+
      '<div style="font-weight:700;color:#38bdf8;font-size:13px;margin-bottom:6px">Transparencia del Ayuntamiento (Lorca)</div>'+
      '<div class="kpis" style="margin:6px 0">'+
      '<div class="kpi"><b>'+fmt(li.nmen)+'</b><span>contratos menores 24-26</span></div>'+
      '<div class="kpi"><b>'+li.gasto+' €</b><span>gasto</span></div>'+
      '<div class="kpi"><b>'+li.nfor+'</b><span>formales</span></div>'+
      '</div>'+
      '<div style="font-size:11px;color:#94a3b8;margin-bottom:4px">Proveedores por nº de contratos menores</div>'+
      '<table style="width:100%;font-size:11px;border-collapse:collapse"><tr style="color:#94a3b8;text-align:left"><th>Proveedor</th><th>#</th><th>Importe</th></tr>'+rows+'</table>'+
      (li.renta?('<div class="kpis" style="margin:8px 0"><div class="kpi"><b>'+li.renta.neta_persona.toLocaleString('es-ES')+' €</b><span>renta neta/persona '+li.renta.anyo+'</span></div><div class="kpi"><b>'+li.renta.neta_hogar.toLocaleString('es-ES')+' €</b><span>neta/hogar</span></div></div><div style="font-size:11px;color:#94a3b8">Murcia capital: '+li.renta.murcia_capital.toLocaleString('es-ES')+' €/persona · INE Atlas</div>'):'')+
      alerta+
      '<a href="ficha_lorca.html" style="display:block;text-align:center;margin-top:8px;padding:8px;border:1px solid #334155;border-radius:8px;color:#38bdf8;font-size:12px;font-weight:600">Ver la ficha completa de Lorca →</a>'+
      '</div>';
  } else { fich.style.display='none'; fich.innerHTML=''; }
  document.getElementById('sWelcome').style.display='none';
  document.getElementById('sDatos').style.display='block';
  document.getElementById('side').style.display='block';
  dibujar(m.c, compCode);
  if(compCode){
    var cm=catalogo[idx[compCode]];
    if(cm){
      document.getElementById('cmp2').style.display='block';
      document.getElementById('cmpNom').textContent=cm.n;
      var cs=series[cm.c]||[];
      var dv=cm.po-(cs[0]?cs[0][1]:cm.po);
      document.getElementById('cmpVal').textContent=cm.p+' · '+fmt(cm.po)+' hab · Δ'+(dv>=0?'+':'')+fmtNum((cs[0]?dv/cs[0][1]*100:0))+'%';
    }
  }
}
function fmtNum(x){return x==null?'—':(x>=0?'+':'')+x.toFixed(1);}
function ocultarPanel(){
  document.getElementById('sWelcome').style.display='block';
  document.getElementById('sDatos').style.display='none';
  document.getElementById('sNom').textContent='Municipal Intelligence';
  document.getElementById('sProv').textContent='Mapa de los 8.132 municipios de España · población INE 1996-2025';
}

var busq=document.getElementById('buscar'), sug=document.getElementById('sug');
busq.addEventListener('input',function(){
  var q=busq.value.toLowerCase();
  if(q.length<2){sug.style.display='none';return;}
  var r=catalogo.filter(m=>m.n.toLowerCase().includes(q)||m.c.includes(q)).slice(0,40);
  if(!r.length){sug.style.display='none';return;}
  sug.innerHTML='';
  r.forEach(function(m){
    var li=document.createElement('li');
    li.textContent=m.n+' ('+m.p+') — '+fmt(m.po)+' hab';
    li.onclick=function(){sug.style.display='none';busq.value=m.n;irA(m);};
    sug.appendChild(li);
  });
  sug.style.display='block';
});
busq.addEventListener('keydown',function(e){
  if(e.key==='Enter'){var r=catalogo.filter(m=>m.n.toLowerCase()===busq.value.toLowerCase());if(r.length)irA(r[0]);}
});
function irA(m){
  map.setView([m.la,m.lo],10);
  mostrar(m);
  grupo.eachLayer(function(l){if(l.getLatLng()&&Math.abs(l.getLatLng().lat-m.la)<.001&&Math.abs(l.getLatLng().lng-m.lo)<.001){l.openPopup();}});
}
document.addEventListener('click',function(e){if(!sug.contains(e.target)&&e.target!==busq)sug.style.display='none';});

// ---- COMPARADOR ----
var cmpBus=document.getElementById('cmp'), sug2=document.getElementById('sug2');
cmpBus.addEventListener('input',function(){
  var q=cmpBus.value.toLowerCase();
  if(q.length<2){sug2.style.display='none';return;}
  var r=catalogo.filter(m=>m.n.toLowerCase().includes(q)).slice(0,25);
  if(!r.length){sug2.style.display='none';return;}
  sug2.innerHTML='';
  r.forEach(function(m){
    var li=document.createElement('li');
    li.textContent=m.n+' ('+m.p+')';
    li.onclick=function(){sug2.style.display='none';cmpBus.value=m.n;ponComparar(m);};
    sug2.appendChild(li);
  });
  sug2.style.display='block';
});
document.addEventListener('click',function(e){if(!sug2.contains(e.target)&&e.target!==cmpBus)sug2.style.display='none';});
function ponComparar(m){
  compCode=m.c;
  if(actual)mostrar(actual);
}
document.getElementById('cmp2').addEventListener('dblclick',function(){
  compCode=null;
  document.getElementById('cmp2').style.display='none';
  cmpBus.value='';
  if(actual)dibujar(actual.c,null);
});

// ---- RANKINGS ----
var ranking={}, rkTipo='crec';
fetch('data/rankings.json').then(r=>r.json()).then(d=>ranking=d);
function verRankings(){
  ocultarPanel();
  document.getElementById('rkTitulo').textContent='Crecimiento 2016 → 2025';
  rkTipo='crec';
  document.getElementById('topPanel').style.display='block';
  pintarRank();
}
function ocultarRankings(){document.getElementById('topPanel').style.display='none';}
function tabRank(t){
  rkTipo=t;
  var tts=document.querySelectorAll('#topPanel .tabs button');
  tts.forEach(function(b){b.classList.remove('act');});
  var mapb={'crec':0,'dec':1,'may':2};
  tts[mapb[t]].classList.add('act');
  document.getElementById('rkTitulo').textContent = t==='crec'?'Crecimiento 2016 → 2025':(t==='dec'?'Descenso 2016 → 2025':'Mayores municipios 2025');
  pintarRank();
}
function pintarRank(){
  var arr=ranking[rkTipo]||[];
  var tb=document.getElementById('rkTabla');
  tb.innerHTML='';
  arr.forEach(function(m,i){
    var tr=document.createElement('tr');
    var g = rkTipo==='may' ? fmt(m.po) : (m.g!=null?(m.g>=0?'+'+m.g.toFixed(1)+'%':m.g.toFixed(1)+'%'):'—');
    var cls = rkTipo==='may'?'':(m.g>=0?'gpos':'gneg');
    tr.innerHTML='<td>'+(i+1)+'. '+m.n+' <span style="color:#94a3b8">('+m.p+')</span></td><td class="'+cls+'">'+g+'</td>';
    tr.onclick=function(){var mm=catalogo[idx[m.c]];if(mm){ocultarRankings();irA(mm);}};
    tb.appendChild(tr);
  });
}
</script>
</body>
</html>
"""
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(HTML)
print("index.html:", os.path.getsize(os.path.join(OUT, "index.html"))//1024, "KB")
print("OK: dashboard/ generado")
