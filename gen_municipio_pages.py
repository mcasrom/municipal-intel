import json, sqlite3, os, re, unicodedata
import datetime

DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP):
    DBP = "poblacion_municipal.sqlite"
OUT = os.path.join("dashboard", "municipio")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DBP)

# H1.5: bloque "Alquiler hoy" desde el Indice VIA (si aun no hay datos, fichas salen sin bloque)
VIA = {}
VIADB = os.path.join("dashboard", "data", "via", "via.db")
if os.path.exists(VIADB):
    try:
        _c = sqlite3.connect(f"file:{VIADB}?mode=ro", uri=True)
        for _m, _eur, _alq, _an in _c.execute(
            "SELECT municipio, eur_m2_mediana, alq_mediana_80m2, anuncios "
            "FROM via_index WHERE fecha=(SELECT MAX(fecha) FROM via_index) AND anuncios>=5"):
            VIA[_m] = {"eur": _eur, "alq": _alq, "an": _an}
        _c.close()
    except sqlite3.OperationalError:
        VIA = {}
TODAY = datetime.date.today().isoformat()

def pop_of(prov, muni, anyo):
    r = con.execute("SELECT poblacion FROM poblacion WHERE provincia=? AND municipio=? AND anyo=? AND sexo='Total'", (prov, muni, anyo)).fetchone()
    return r[0] if r else None

def serie_of(prov, muni):
    return con.execute("SELECT anyo, poblacion FROM poblacion WHERE provincia=? AND municipio=? AND sexo='Total' ORDER BY anyo", (prov, muni)).fetchall()

def slug(name, prov):
    s = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode().lower()
    for art in ('la ', 'el ', 'los ', 'las ', "l'"):
        if s.startswith(art): s = s[len(art):]
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

# seleccion: top 300 por poblacion 2025
rows = con.execute("""SELECT c.municipio, c.provincia, c.codigo_ine, c.lat, c.lon, p.poblacion
    FROM catalogo c JOIN poblacion p ON p.provincia=c.provincia AND p.municipio=c.municipio
    AND p.anyo=2025 AND p.sexo='Total' ORDER BY p.poblacion DESC""").fetchall()

# slugs unicos
used = {}
pages = []
for muni, prov, code, lat, lon, pop in rows:
    s = slug(muni, prov)
    if s in used:
        ps = slug(prov, "")
        s = f"{s}-{ps}" if s != ps else f"{s}-{code[-3:]}"
    used[s] = True
    pages.append({"muni": muni, "prov": prov, "code": code, "lat": lat, "lon": lon,
                  "pop": pop, "slug": s})

def fmt(n):
    return format(int(round(n)), ",").replace(",", ".")

def pct(a, b):
    return round((a - b) / b * 100, 1) if b else None

TEMPLATE = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@MUNI@@ · Población @@PROV@@ | Municipal Intelligence</title>
<meta name="description" content="@@MUNI@@ (@@PROV@@): población oficial de @@POP@@ habitantes (2025), evolución 1996-2025 y ranking nacional. Datos INE, sin inventar.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/municipio/@@SLUG@@.html">
<link rel="icon" type="image/png" href="../icon-192.png">
<meta property="og:type" content="article">
<meta property="og:title" content="@@MUNI@@ · Población @@PROV@@">
<meta property="og:description" content="@@POP@@ habitantes (2025, INE) · evolución 1996-2025 · ranking nacional.">
<meta property="og:image" content="https://municipal.viajeinteligencia.com/@@OGIMG@@">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Población de @@MUNI@@ (@@PROV@@)",
  "description": "Serie oficial de población de @@MUNI@@, código INE @@CODE@@, según la Revisión del Padrón Municipal (INE).",
  "url": "https://municipal.viajeinteligencia.com/municipio/@@SLUG@@.html",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "spatialCoverage": {"@type": "Place", "name": "@@MUNI@@", "address": {"@type": "PostalAddress", "addressCountry": "ES", "addressRegion": "@@PROV@@"}}
}
</script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--verde:#4ade80;--rojo:#f87171}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6}
.wrap{max-width:760px;margin:0 auto;padding:22px}
h1{font-size:26px}
.mut{color:var(--mut);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}
.kpi{background:var(--card);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:20px}
.kpi span{font-size:11px;color:var(--mut)}
.pos{color:var(--verde)}.neg{color:var(--rojo)}
svg{width:100%;height:130px;background:var(--card);border-radius:10px;margin:6px 0}
table{width:100%;border-collapse:collapse;font-size:13px}
td{padding:5px 8px;border-bottom:1px solid #1e293b}
details{margin-top:14px;background:var(--card);border-radius:10px;padding:12px;font-size:13px}
summary{cursor:pointer;font-weight:600;color:var(--acc)}
a{color:var(--acc)}
.nav{display:flex;gap:12px;font-size:13px;margin-bottom:14px}
.src{font-size:11px;color:var(--mut);margin-top:28px}
.toggle{position:fixed;top:14px;right:16px;z-index:99;background:var(--card);border:1px solid #334155;color:var(--fg);border-radius:50%;width:38px;height:38px;cursor:pointer;font-size:17px;box-shadow:0 2px 10px rgba(0,0,0,.3)}
body.light{--bg:#f1f5f9;--card:#ffffff;--fg:#0f172a;--mut:#64748b;--acc:#0284c7;--verde:#059669;--rojo:#dc2626}
body.light table{background:#ffffff}
body.light th{background:#f1f5f9}
body.light td{color:#1e293b;border-color:#e2e8f0}
body.light .src{color:#64748b}
</style></head><body><div class="wrap">
<button class="toggle" onclick="tema()" id="temaBtn" title="Modo claro/oscuro">&#127769;</button>
<script>function tema(){var b=document.body;b.classList.toggle("light");var l=b.classList.contains("light");document.getElementById("temaBtn").textContent=l?"🌙":"☀️";try{localStorage.setItem("municip-tema",l?"light":"dark");}catch(e){}}</script>
<script>try{if(localStorage.getItem("municip-tema")==="light"){document.body.classList.add("light");document.getElementById("temaBtn").textContent="🌙";}}catch(e){}</script>
<div class="nav"><a href="../">← Mapa de municipios de España</a> · <a href="../acerca.html">Metodología y fuentes</a> · <a href="https://www.viajeinteligencia.com">Ecosistema de datos abiertos</a></div>
<h1>@@MUNI@@ <span class="mut">· @@PROV@@</span></h1>
<div class="mut">Código INE @@CODE@@ · datos oficiales de la Revisión del Padrón Municipal (INE) · sin datos inventados</div>
<div class="grid">
  <div class="kpi"><b>@@POP@@</b><span>habitantes (2025)</span></div>
  <div class="kpi"><b>@@P96@@</b><span>en 1996</span></div>
  <div class="kpi"><b class="@@SIGN@@">@@VAR@@</b><span>variación 1996 → 2025</span></div>
  <div class="kpi"><b>@@RANK@@</b><span>rank nacional (8.132 municipios)</span></div>
</div>
<p>@@MUNI@@ @@CTX@@</p>
@@LORCA_LINK@@
<div class="kpi" style="margin:14px 0;font-size:14px">
  Variación: <b>1 año @@G1@@</b> · <b>5 años @@G5@@</b> · <b>10 años @@G16@@</b>
</div>
<svg viewBox="0 0 700 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Evolución de la población de @@MUNI@@ 1996-2025">
@@SVG@@
</svg>
<details><summary>Serie completa de población (1996-2025)</summary>
<table>@@ROWS@@</table>
</details>
@@ALQUILER@@
<div class="alerta-box" style="background:var(--card);border-radius:10px;padding:14px;margin:14px 0">
  <b style="color:#38bdf8">¿Avísame si cambian los datos de @@MUNI@@?</b>
  <div style="font-size:12px;color:#94a3b8;margin:4px 0">Recibirás un email cuando se actualicen los datos de este municipio (población, ranking o contratos). Sin spam; baja fácil.</div>
  <div style="display:flex;gap:8px;margin-top:8px">
    <input type="email" id="alertEmail" placeholder="tu@email.com" style="flex:1;padding:8px 10px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#e2e8f0;font-size:13px">
    <button onclick="suscribir()" style="padding:8px 14px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#e2e8f0;font-size:13px;cursor:pointer">Avísame</button>
  </div>
  <div id="alertMsg" style="font-size:12px;margin-top:6px;color:#94a3b8"></div>
</div>
<div class="src">Municipal Intelligence © 2026 M. Castillo · fuente: INE, Cifras oficiales de población (Revisión del Padrón Municipal), población a 01/01/2025 publicada el 11/12/2025 · coordenadas y códigos: © OpenStreetMap (ref:ine) · ver <a href="../acerca.html">metodología completa</a>.</div>
<script>
function suscribir(){
  var email=document.getElementById('alertEmail').value.trim();
  var msg=document.getElementById('alertMsg');
  if(!email||!email.includes('@')){msg.textContent='Email no válido';return;}
  msg.textContent='Enviando…';
  fetch('../api/alerta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,codigo:'@@CODE@@'})})
    .then(function(r){return r.json();})
    .then(function(d){msg.textContent=d.ok?'Revisa tu email para confirmar':(d.error||'Error');})
    .catch(function(){msg.textContent='Error de red';});
}
</script>
</div></body></html>"""

def build_svg(serie):
    if len(serie) < 2:
        return ""
    ys = [p for _, p in serie]
    mn, mx = min(ys), max(ys)
    W, H, pad = 700, 130, 10
    xs = list(range(len(serie)))
    X = lambda i: pad + i * (W - 2 * pad) / (len(serie) - 1)
    Y = lambda v: H - pad - (v - mn) * (H - 2 * pad) / (mx - mn or 1)
    pts = " ".join(f"{X(i):.1f},{Y(p):.1f}" for i, (_, p) in enumerate(serie))
    return (f'<polyline points="{pts}" fill="none" stroke="#38bdf8" stroke-width="2"/>'
            f'<circle cx="{X(0):.1f}" cy="{Y(ys[0]):.1f}" r="3" fill="#38bdf8"/>'
            f'<circle cx="{X(len(serie)-1):.1f}" cy="{Y(ys[-1]):.1f}" r="3" fill="#f59e0b"/>')

def build_rows(serie):
    return "".join(f"<tr><td>{a}</td><td style='text-align:right'>{fmt(p)}</td></tr>" for a, p in serie)

sitemap = ["https://municipal.viajeinteligencia.com/", "https://municipal.viajeinteligencia.com/ficha_lorca.html", "https://municipal.viajeinteligencia.com/ficha_malaga.html", "https://municipal.viajeinteligencia.com/acerca.html", "https://municipal.viajeinteligencia.com/datos.html"]
n = 0
OGD = {}
try:
    OGD = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "data", "og_dinamico.json")))
except Exception:
    pass
for pg in pages:
    muni, prov, code, slugv = pg["muni"], pg["prov"], pg["code"], pg["slug"]
    p25 = pg["pop"]; p96 = pop_of(prov, muni, 1996) or p25
    g1 = pct(p25, pop_of(prov, muni, 2024)); g5 = pct(p25, pop_of(prov, muni, 2020)); g16 = pct(p25, pop_of(prov, muni, 2016))
    rank = con.execute("SELECT COUNT(*)+1 FROM poblacion WHERE anyo=2025 AND sexo='Total' AND poblacion>?", (p25,)).fetchone()[0]
    var = pct(p25, p96)
    serie = serie_of(prov, muni)
    ctx = (f"ha crecido un {abs(g16):.1f}% en los últimos 10 años (2016→2025) " if g16 and g16 > 0
           else f"ha perdido el {abs(g16):.1f}% de su población en los últimos 10 años (2016→2025) " if g16 else "presenta una serie estable ")
    ctx += f"y ocupa el puesto {rank} de 8.132 municipios de España por población en 2025. Fuente: INE."
    lorca_link = ""
    if code == "30024":
        lorca_link = f'<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px;margin:12px 0"><a href="../ficha_lorca.html" style="color:#38bdf8;font-weight:600">Ver la ficha de transparencia de Lorca →</a> (contratos del Ayuntamiento, menores y troceados)</div>'
    elif code == "29067":
        lorca_link = f'<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px;margin:12px 0"><a href="../ficha_malaga.html" style="color:#38bdf8;font-weight:600">Ver la ficha de transparencia de Málaga →</a> (contratos menores del Ayuntamiento, datos.gob.es)</div>'
    html = TEMPLATE
    v = VIA.get(muni)
    if v:
        alquiler_html = (
            '<div class="kpi" style="margin:14px 0;font-size:14px">💰 <b>Alquiler hoy:</b> '
            + str(round(v["eur"], 2)).replace(".", ",") + ' €/m² mediana · piso de 80 m² ≈ '
            + fmt(v["alq"]) + ' €/mes '
            + '<span style="color:#94a3b8">(mediana de ' + str(v["an"]) + ' anuncios activos · '
            + '<a href="../alquiler.html" style="color:#58a6ff">índice completo</a>)</span></div>')
    else:
        alquiler_html = ""
    for k, v in {"@@MUNI@@": muni, "@@PROV@@": prov, "@@CODE@@": code, "@@SLUG@@": slugv,
                 "@@POP@@": fmt(p25), "@@P96@@": fmt(p96),
                 "@@SIGN@@": "pos" if (var or 0) >= 0 else "neg",
                 "@@VAR@@": ("+" if (var or 0) >= 0 else "") + str(var or 0),
                 "@@RANK@@": f"{rank}º", "@@CTX@@": ctx, "@@LORCA_LINK@@": lorca_link,
                 "@@OGIMG@@": OGD.get(code, "og-municipal.png"),
                 "@@G1@@": ("+" if (g1 or 0) >= 0 else "") + str(g1 or 0) + "%",
                 "@@G5@@": ("+" if (g5 or 0) >= 0 else "") + str(g5 or 0) + "%",
                 "@@G16@@": ("+" if (g16 or 0) >= 0 else "") + str(g16 or 0) + "%",
                 "@@SVG@@": build_svg(serie), "@@ROWS@@": build_rows(serie),
                 "@@ALQUILER@@": alquiler_html}.items():
        html = html.replace(k, str(v))
    with open(os.path.join(OUT, f"{slugv}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    sitemap.append(f"https://municipal.viajeinteligencia.com/municipio/{slugv}.html")
    n += 1

# exportar mapa code -> slug (para el enlace del mapa con colisiones)
slugmap = {pg["code"]: pg["slug"] for pg in pages}
with open(os.path.join("dashboard", "data", "municipio_slugs.json"), "w") as f:
    json.dump(slugmap, f, separators=(",", ":"))

# sitemap
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sitemap:
    sm.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
sm.append("</urlset>")
with open(os.path.join("dashboard", "sitemap.xml"), "w") as f:
    f.write("\n".join(sm))
print(f"paginas municipio generadas: {n}")
print("sitemap URLs:", len(sitemap))
con.close()
