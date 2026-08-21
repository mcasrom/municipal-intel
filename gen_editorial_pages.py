import json, sqlite3, os, re, unicodedata

DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP):
    DBP = "poblacion_municipal.sqlite"
OUT = os.path.join("dashboard", "editorial")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DBP)

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def pct(a, b):
    return round((a - b) / b * 100, 1) if b else None

# crecimiento 2016->2025 por municipio (>=1000 hab en 2016)
rows = con.execute("""SELECT c.municipio, c.provincia, c.codigo_ine, p25.poblacion as p25, p16.poblacion as p16
    FROM catalogo c
    JOIN poblacion p25 ON p25.provincia=c.provincia AND p25.municipio=c.municipio AND p25.anyo=2025 AND p25.sexo='Total'
    JOIN poblacion p16 ON p16.provincia=c.provincia AND p16.municipio=c.municipio AND p16.anyo=2016 AND p16.sexo='Total'
    WHERE p16.poblacion >= 1000""").fetchall()
con.close()
data = [{"n": n, "p": prov, "c": code, "po": p25, "g": pct(p25, p16)} for n, prov, code, p25, p16 in rows if pct(p25, p16) is not None]
data.sort(key=lambda x: -x["g"])

def muni_url(c):
    sm = slugmap.get(c, "")
    return "https://municipal.viajeinteligencia.com/municipio/" + (sm + ".html" if sm else "")

slugmap = json.load(open(os.path.join("dashboard", "data", "municipio_slugs.json")))

def tabla(items, col="g"):
    trs = []
    for i, x in enumerate(items, 1):
        v = x["g"]
        cls = "pos" if v >= 0 else "neg"
        gtxt = ("+" if v >= 0 else "") + "%.1f%%" % v
        trs.append("<tr><td>%d</td><td><a href='%s'>%s</a></td><td>%s</td><td class='r'>%s</td><td class='r'>%s</td></tr>" % (
            i, muni_url(x["c"]), x["n"], x["p"], gtxt, format(x["po"], ",")))
    return "<table><tr><th>#</th><th>Municipio</th><th>Provincia</th><th class='r'>Δ 2016-2025</th><th class='r'>Población 2025</th></tr>" + "".join(trs) + "</table>"

T = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/editorial/@@SLUG@@.html">
<link rel="icon" type="image/png" href="../icon-192.png">
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6}
.wrap{max-width:760px;margin:0 auto;padding:22px}
h1{font-size:24px}
h2{font-size:16px;color:var(--acc);margin:18px 0 8px}
.mut{color:var(--mut);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
th{background:#0f172a;color:var(--mut);text-align:left;padding:7px 8px;font-size:11px;text-transform:uppercase}
td{padding:6px 8px;border-bottom:1px solid #1e293b}
td.r{text-align:right}
.pos{color:#4ade80}.neg{color:#f87171}
a{color:var(--acc)}
.nav{display:flex;gap:12px;font-size:13px;margin-bottom:14px;flex-wrap:wrap}
.src{font-size:11px;color:var(--mut);margin-top:26px}
</style></head><body><div class="wrap">
<div class="nav"><a href="../">← Mapa de municipios</a> · <a href="../acerca.html">Metodología</a> · <a href="../rss.xml">RSS</a></div>
<h1>@@H1@@</h1>
<div class="mut">@@INTRO@@</div>
@@BODY@@
<div class="src">Municipal Intelligence © 2026 M. Castillo · datos: INE, Cifras oficiales de población (Revisión del Padrón Municipal), 2016-2025 · variaciones calculadas sobre municipios con ≥1.000 habitantes en 2016 · ver <a href="../acerca.html">metodología</a>.</div>
</div></body></html>"""

def render(slugv, title, h1, intro, desc, body):
    h = T
    for k, v in {"@@SLUG@@": slugv, "@@TITLE@@": title, "@@H1@@": h1, "@@INTRO@@": intro, "@@DESC@@": desc, "@@BODY@@": body}.items():
        h = h.replace(k, v)
    return h

sitemap_extra = []
n = 0

# ===== Páginas NACIONALES =====
# crecen
crec = [x for x in data if x["g"] >= 0][:50]
body = "<p>Municipios de España con mayor crecimiento de población entre 2016 y 2025, según la Revisión del Padrón Municipal del INE (municipios con ≥1.000 habitantes en 2016 para evitar el ruido de los pueblos pequeños).</p>" + tabla(crec)
h = render("municipios-que-mas-crecen-espana", "Municipios que más crecen en España (2016-2025) · INE",
    "Municipios que más crecen en España 2016-2025", "Ranking de los municipios que más población ganaron entre 2016 y 2025 (INE).",
    "Municipios de España que más crecieron en población 2016-2025, según el INE: ranking con datos oficiales.", body)
open(os.path.join(OUT, "municipios-que-mas-crecen-espana.html"), "w", encoding="utf-8").write(h)
sitemap_extra.append("municipios-que-mas-crecen-espana.html"); n += 1

# se despueblan (España vaciada)
dec = [x for x in data if x["g"] < 0][:50]
body = "<p>Municipios de España con mayor pérdida de población entre 2016 y 2025 (España vaciada), según el INE (≥1.000 habitantes en 2016).</p>" + tabla(dec)
h = render("municipios-que-mas-se-desueblan-espana", "Municipios que más se despueblan en España (2016-2025) · INE",
    "Municipios que más se despueblan en España (España vaciada)", "Los municipios que más población perdieron entre 2016 y 2025, según el INE.",
    "Municipios de España que más perdieron población 2016-2025 (España vaciada): ranking con datos oficiales del INE.", body)
open(os.path.join(OUT, "municipios-que-mas-se-desueblan-espana.html"), "w", encoding="utf-8").write(h)
sitemap_extra.append("municipios-que-mas-se-desueblan-espana.html"); n += 1

# mas poblados
may = sorted(data, key=lambda x: -x["po"])[:50]
body = "<p>Los 50 municipios más poblados de España según la Revisión del Padrón Municipal 2025 (INE).</p>" + tabla(may)
h = render("municipios-mas-poblados-espana", "Los 50 municipios más poblados de España (2025) · INE",
    "Municipios más poblados de España (2025)", "Ranking de los 50 municipios con más habitantes de España a 01/01/2025 (INE).",
    "Los 50 municipios más poblados de España en 2025, según el INE: ranking con datos oficiales.", body)
open(os.path.join(OUT, "municipios-mas-poblados-espana.html"), "w", encoding="utf-8").write(h)
sitemap_extra.append("municipios-mas-poblados-espana.html"); n += 1

# ===== Páginas por PROVINCIA =====
provs = sorted(set(x["p"] for x in data))
for prov in provs:
    pv = [x for x in data if x["p"] == prov]
    if len(pv) < 3:
        continue
    sl = slug(prov)
    crec_p = sorted([x for x in pv if x["g"] >= 0], key=lambda x: -x["g"])[:10]
    if crec_p:
        body = "<p>Municipios de %s que más crecieron entre 2016 y 2025 (INE, ≥1.000 habitantes en 2016).</p>" % prov + tabla(crec_p)
        h = render("municipios-que-mas-crecen-" + sl, "Municipios que más crecen en %s (2016-2025)" % prov,
            "Municipios que más crecen en %s" % prov, "Ranking de crecimiento de población en %s, 2016-2025 (INE)." % prov,
            "Los municipios de %s que más crecieron en población entre 2016 y 2025, según el INE." % prov, body)
        open(os.path.join(OUT, "municipios-que-mas-crecen-" + sl + ".html"), "w", encoding="utf-8").write(h)
        sitemap_extra.append("municipios-que-mas-crecen-" + sl + ".html"); n += 1
    dec_p = sorted([x for x in pv if x["g"] < 0], key=lambda x: x["g"])[:10]
    if dec_p:
        body = "<p>Municipios de %s que más perdieron población entre 2016 y 2025 (INE, ≥1.000 habitantes en 2016).</p>" % prov + tabla(dec_p)
        h = render("municipios-que-mas-se-desueblan-" + sl, "Municipios que más se despueblan en %s (2016-2025)" % prov,
            "Municipios que más se despueblan en %s" % prov, "Ranking de pérdida de población en %s, 2016-2025 (INE)." % prov,
            "Los municipios de %s que más perdieron población entre 2016 y 2025, según el INE." % prov, body)
        open(os.path.join(OUT, "municipios-que-mas-se-desueblan-" + sl + ".html"), "w", encoding="utf-8").write(h)
        sitemap_extra.append("municipios-que-mas-se-desueblan-" + sl + ".html"); n += 1

print("paginas editoriales generadas:", n)

# ===== sitemap: insertar las editoriales antes del cierre =====
sm = open(os.path.join("dashboard", "sitemap.xml")).read()
insert = "".join("  <url><loc>https://municipal.viajeinteligencia.com/editorial/%s</loc><lastmod>2026-08-21</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n" % u for u in sitemap_extra)
sm = sm.replace("</urlset>", insert + "</urlset>")
open(os.path.join("dashboard", "sitemap.xml"), "w").write(sm)
print("sitemap actualizado con", len(sitemap_extra), "URLs editoriales")
