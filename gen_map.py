import json, sqlite3, os

DB = "data/poblacion_municipal.sqlite"
if not os.path.exists(DB):
    DB = "poblacion_municipal.sqlite"
OUT = "dashboard"
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

con = sqlite3.connect(DB)

# catalogo: markers
catalogo = []
for r in con.execute("""SELECT c.municipio, c.provincia, c.codigo_ine, c.lat, c.lon,
                        p.poblacion FROM catalogo c
                        JOIN poblacion p ON p.provincia=c.provincia AND p.municipio=c.municipio
                        AND p.anyo=2025 AND p.sexo='Total'""").fetchall():
    muni, prov, code, lat, lon, pop = r
    catalogo.append({"c": code, "n": muni, "p": prov, "la": lat, "lo": lon, "po": int(pop)})
with open(os.path.join(OUT, "data", "catalogo.json"), "w") as f:
    json.dump(catalogo, f, ensure_ascii=False, separators=(",", ":"))
print("catalogo:", len(catalogo))

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
<title>Municipal Intelligence · Mapa de municipios de España</title>
<meta name="description" content="Población municipal de España 1996-2025 (INE): mapa, buscador y evolución de los 8.132 municipios.">
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
#side{position:absolute;top:12px;right:12px;bottom:12px;z-index:1000;width:330px;max-width:calc(100vw - 24px);background:var(--card);border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,.4);display:none;overflow:auto;padding:16px}
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
.legend{position:absolute;bottom:24px;right:12px;z-index:999;background:var(--card);border-radius:8px;padding:8px 10px;font-size:11px;color:var(--mut);box-shadow:0 2px 10px rgba(0,0,0,.4)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
</style>
</head>
<body>
<div id="map"></div>
<div id="top">
  <h1>Municipal Intelligence<small>Población de los 8.132 municipios de España · INE 1996-2025</small></h1>
  <input id="buscar" placeholder="Busca un municipio… (ej. Lorca)" autocomplete="off">
  <ul id="sug"></ul>
</div>
<div id="side">
  <button class="close" onclick="ocultarPanel()">&times;</button>
  <h2 id="sNom"></h2>
  <div class="mut"><span id="sProv"></span> · código INE <span id="sCod"></span></div>
  <div class="kpis">
    <div class="kpi"><b id="s2025"></b><span>2025</span></div>
    <div class="kpi"><b id="s1996"></b><span>1996</span></div>
    <div class="kpi"><b id="sVar"></b><span>Δ total</span></div>
  </div>
  <canvas id="graf"></canvas>
  <div class="delta" id="sDelta"></div>
  <div class="src">Fuente: INE · Cifras oficiales de población (Revisión del Padrón Municipal), serie 1996-2025 (1997 no publicado; 1996 a 1 de mayo). Coordenadas y códigos: © OpenStreetMap (ref:ine) · Overpass. Datos trazables, sin inventar.</div>
</div>
<div class="legend">
  <div><i style="background:#0ea5e9"></i>&lt; 1.000</div>
  <div><i style="background:#6366f1"></i>1.000-5.000</div>
  <div><i style="background:#8b5cf6"></i>5.000-20.000</div>
  <div><i style="background:#f59e0b"></i>20.000-100.000</div>
  <div><i style="background:#ef4444"></i>&gt; 100.000</div>
</div>
<div id="foot">Municipal Intelligence · datos abiertos INE + OpenStreetMap · sin cookies</div>
<script>
var catalogo=[], series={};
fetch('data/catalogo.json').then(r=>r.json()).then(d=>{catalogo=d; pintar();});
fetch('data/series.json').then(r=>r.json()).then(d=>series=d);

var map=L.map('map',{renderer:L.canvas(),zoomControl:true}).setView([40.3,-3.6],6);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
var grupo=L.layerGroup().addTo(map);

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
    L.circleMarker([m.la,m.lo],{radius:c.r,color:c.color,fillColor:c.color,fillOpacity:.75,weight:1}).addTo(grupo)
      .bindPopup('<b>'+m.n+'</b><br>'+m.p+' · '+m.po.toLocaleString('es-ES')+' hab');
    grupo.eachLayer?null:null;
  });
}

function fmt(n){return Number(n).toLocaleString('es-ES');}

function dibujar(cod){
  var s=series[cod]||[];
  var cv=document.getElementById('graf'), ctx=cv.getContext('2d');
  var w=cv.clientWidth,h=cv.clientHeight;
  cv.width=w;cv.height=h;ctx.clearRect(0,0,w,h);
  if(s.length<2){ctx.fillStyle='#94a3b8';ctx.fillText('serie corta',8,h/2);return;}
  var ys=s.map(x=>x[1]), mn=Math.min.apply(null,ys), mx=Math.max.apply(null,ys);
  var pad=6, X=i=>pad+i*(w-2*pad)/(s.length-1), Y=v=>h-pad-(v-mn)*(h-2*pad)/(mx-mn||1);
  ctx.strokeStyle='#38bdf8';ctx.lineWidth=2;ctx.beginPath();
  s.forEach(function(pt,i){var x=X(i),y=Y(pt[1]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
  ctx.stroke();
  ctx.fillStyle='#e2e8f0';ctx.font='10px system-ui';
  ctx.fillText(s[0][0],X(0),h-2);ctx.fillText(s[s.length-1][0],X(s.length-1)-22,h-2);
}

function mostrar(m){
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
  dibujar(m.c);
  document.getElementById('side').style.display='block';
}
function ocultarPanel(){document.getElementById('side').style.display='none';}

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
</script>
</body>
</html>
"""
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(HTML)
print("index.html:", os.path.getsize(os.path.join(OUT, "index.html"))//1024, "KB")
print("OK: dashboard/ generado")
