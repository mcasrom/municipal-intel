import json, sqlite3, os, re, unicodedata

DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP):
    DBP = "poblacion_municipal.sqlite"
OUT = os.path.join("dashboard", "municipio")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DBP)

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
    AND p.anyo=2025 AND p.sexo='Total' ORDER BY p.poblacion DESC LIMIT 300""").fetchall()

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
<meta property="og:image" content="https://municipal.viajeinteligencia.com/og-municipal.png">
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
</style></head><body><div class="wrap">
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
<div class="src">Municipal Intelligence © 2026 M. Castillo · fuente: INE, Cifras oficiales de población (Revisión del Padrón Municipal), población a 01/01/2025 publicada el 11/12/2025 · coordenadas y códigos: © OpenStreetMap (ref:ine) · ver <a href="../acerca.html">metodología completa</a>.</div>
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

sitemap = ["https://municipal.viajeinteligencia.com/", "https://municipal.viajeinteligencia.com/ficha_lorca.html", "https://municipal.viajeinteligencia.com/acerca.html"]
n = 0
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
    lorca_link = (f'<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px;margin:12px 0"><a href="../ficha_lorca.html" style="color:#38bdf8;font-weight:600">Ver la ficha de transparencia de Lorca →</a> (contratos del Ayuntamiento, menores y troceados)</div>' if code == "30024" else "")
    html = TEMPLATE
    for k, v in {"@@MUNI@@": muni, "@@PROV@@": prov, "@@CODE@@": code, "@@SLUG@@": slugv,
                 "@@POP@@": fmt(p25), "@@P96@@": fmt(p96),
                 "@@SIGN@@": "pos" if (var or 0) >= 0 else "neg",
                 "@@VAR@@": ("+" if (var or 0) >= 0 else "") + str(var or 0),
                 "@@RANK@@": f"{rank}º", "@@CTX@@": ctx, "@@LORCA_LINK@@": lorca_link,
                 "@@G1@@": ("+" if (g1 or 0) >= 0 else "") + str(g1 or 0) + "%",
                 "@@G5@@": ("+" if (g5 or 0) >= 0 else "") + str(g5 or 0) + "%",
                 "@@G16@@": ("+" if (g16 or 0) >= 0 else "") + str(g16 or 0) + "%",
                 "@@SVG@@": build_svg(serie), "@@ROWS@@": build_rows(serie)}.items():
        html = html.replace(k, str(v))
    with open(os.path.join(OUT, f"{slugv}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    sitemap.append(f"https://municipal.viajeinteligencia.com/municipio/{slugv}.html")
    n += 1

# sitemap
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sitemap:
    sm.append(f"  <url><loc>{u}</loc><lastmod>2026-08-21</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
sm.append("</urlset>")
with open(os.path.join("dashboard", "sitemap.xml"), "w") as f:
    f.write("\n".join(sm))
print(f"paginas municipio generadas: {n}")
print("sitemap URLs:", len(sitemap))
con.close()
