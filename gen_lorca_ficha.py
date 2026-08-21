import json, sqlite3, os
from collections import defaultdict

menores = json.load(open("lorca_menores.json"))
formales = json.load(open("lorca_contratos.json"))
renta = json.load(open("lorca_renta.json"))
DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP):
    DBP = "poblacion_municipal.sqlite"
con = sqlite3.connect(DBP)
serie = con.execute("SELECT anyo, poblacion FROM poblacion WHERE municipio='Lorca' AND sexo='Total' ORDER BY anyo").fetchall()
cata = con.execute("SELECT codigo_ine FROM catalogo WHERE municipio='Lorca'").fetchone()
rank_murcia = con.execute("""SELECT COUNT(*)+1 FROM poblacion p JOIN catalogo c USING (provincia, municipio)
  WHERE p.anyo=2025 AND p.sexo='Total' AND p.provincia='Murcia' AND p.poblacion > (
    SELECT poblacion FROM poblacion WHERE anyo=2025 AND sexo='Total' AND municipio='Lorca')""").fetchone()[0]
con.close()

def pct(a, b):
    return round((a - b) / b * 100, 1) if b else None

m = [x for x in menores if x["periodo"][:4] >= "2024" and x["importe"] and x["importe"] <= 40000]
by = defaultdict(list)
for x in m:
    by[x["razon"]].append(x)
top_num = sorted(by.items(), key=lambda kv: -len(kv[1]))[:15]
top_imp = sorted(by.items(), key=lambda kv: -sum(i["importe"] for i in kv[1]))[:10]
total_gasto = sum(x["importe"] for x in m)
gasto_top5 = sum(sum(i["importe"] for i in items) for _, items in top_imp[:5])
por_estado = defaultdict(int)
for c in formales:
    por_estado[c["estado"]] += 1

def fmt_e(n):
    return "%s" % format(int(round(n)), ",").replace(",", ".")

p96 = serie[0][1]; p25 = serie[-1][1]; var = pct(p25, p96)

row_top_num = ""
for i, (r, items) in enumerate(top_num, 1):
    tot = sum(x["importe"] for x in items)
    row_top_num += "<tr><td>%d</td><td>%s</td><td class='r'><b>%d</b></td><td class='r'>%s</td><td class='r'>%s</td></tr>" % (
        i, r, len(items), fmt_e(tot), fmt_e(tot / len(items)))
row_top_imp = ""
for i, (r, items) in enumerate(top_imp, 1):
    tot = sum(x["importe"] for x in items)
    row_top_imp += "<tr><td>%d</td><td>%s</td><td class='r'><b>%s</b></td><td class='r'>%d</td></tr>" % (i, r, fmt_e(tot), len(items))
row_form = ""
for c in formales[:15]:
    imp = fmt_e(c["importe"]) + " €" if c["importe"] else "—"
    row_form += "<tr><td>%s</td><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td><td>%s</td></tr>" % (
        c["expediente"], c["objeto"][:80], c["procedimiento"], imp, c["adjudicatario"][:40], c["estado"])

alerta = ""
flag = [(r, len(items)) for r, items in top_num if len(items) >= 50]
if flag:
    alerta = "<div class='alert'><b>Posible troceado:</b> proveedores con un volumen muy alto de contratos menores en 2024-2026 — " + \
        ", ".join("<b>%d</b> a %s" % (n, r) for r, n in flag[:6]) + \
        ". Contratos de importe bajo repetidos en el mismo periodo es el patrón clásico de fraccionamiento del gasto.</div>"

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lorca · Municipal Intelligence</title>
<meta name="description" content="Ficha de inteligencia municipal de Lorca: población INE 1996-2025 y contratos del Ayuntamiento (formales + menores) con anomalías detectadas.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/ficha_lorca.html">
<link rel="icon" type="image/png" href="icon-192.png">
<meta property="og:image" content="https://municipal.viajeinteligencia.com/og-municipal.png">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--rojo:#f87171;--verde:#4ade80}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
.wrap{max-width:960px;margin:0 auto;padding:20px}
h1{font-size:26px}
h2{font-size:18px;margin:26px 0 10px;color:var(--acc);border-bottom:1px solid #334155;padding-bottom:6px}
.mut{color:var(--mut);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:22px}
.kpi span{font-size:11px;color:var(--mut)}
.kpi .pos{color:var(--verde)}.kpi .neg{color:var(--rojo)}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border-radius:8px;overflow:hidden}
th{background:#0f172a;color:var(--mut);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}
td{padding:8px 10px;border-top:1px solid #1e293b}
td.r{text-align:right}
.alert{background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:12px 14px;margin:12px 0}
.alert b{color:#fca5a5}
#mapa{height:220px;border-radius:10px;margin-top:10px}
.src{font-size:10px;color:var(--mut);margin-top:30px;line-height:1.6}
a{color:var(--acc)}
</style></head><body><div class="wrap">

<h1>Lorca <span class="mut">· Municipal Intelligence</span></h1>
<div class="mut">Ayuntamiento de Lorca · Región de Murcia · código INE @@COD@@ · datos trazables (INE + Portal de Transparencia del Ayuntamiento)</div>

<h2>Población (INE, Revisión del Padrón)</h2>
<div class="grid">
  <div class="kpi"><b>@@P25@@</b><span>habitantes (2025)</span></div>
  <div class="kpi"><b>@@P96@@</b><span>en 1996</span></div>
  <div class="kpi"><b class="@@SIGN@@">@@VAR@@</b><span>variación 1996 → 2025</span></div>
  <div class="kpi"><b>@@RANK@@</b><span>rank en Murcia (45 municipios)</span></div>
</div>
<div id="mapa"></div>

<h2>Contratos del Ayuntamiento de Lorca</h2>
<div class="grid">
  <div class="kpi"><b>@@NMEN@@</b><span>contratos menores 2024-2026 (publicados)</span></div>
  <div class="kpi"><b>@@GASTO@@ €</b><span>gasto menor 2024-2026</span></div>
  <div class="kpi"><b>@@NFOR@@</b><span>contratos formales (lote actual)</span></div>
  <div class="kpi"><b>@@CONC@@</b><span>del gasto menor en sus 5 principales proveedores</span></div>
</div>

@@ALERTA@@

<h2>Renta de los hogares (INE · Atlas de distribución de renta)</h2>
<div class="grid">
  <div class="kpi"><b>@@RNET@@ €</b><span>renta neta media por persona (2022)</span></div>
  <div class="kpi"><b>@@RHOG@@ €</b><span>renta neta media por hogar (2022)</span></div>
  <div class="kpi"><b>@@RMED@@ €</b><span>mediana por unidad de consumo (2022)</span></div>
  <div class="kpi"><b>@@RPROV@@ €</b><span>Murcia capital (renta/persona)</span></div>
</div>
<div class="alert" style="background:#1e293b;border:1px solid #334155"><b style="color:#fca5a5">Contexto:</b> la renta neta media por persona de Lorca (11.470 € en 2022) está por debajo de Murcia capital (13.906 €) y Cartagena (13.126 €) — refleja su perfil agrario y rural. La serie 2019→2022 sube de 9.777 € a 11.470 € (+17,3%).</div>

<h2>Proveedores por número de contratos menores (2024-2026)</h2>
<table><tr><th>#</th><th>Proveedor</th><th class="r">Contratos</th><th class="r">Importe</th><th class="r">Media</th></tr>
@@TROWN@@
</table>

<h2>Proveedores por importe (2024-2026)</h2>
<table><tr><th>#</th><th>Proveedor</th><th class="r">Importe</th><th class="r">Contratos</th></tr>
@@IROWN@@
</table>

<h2>Contratos formales (publicados actualmente)</h2>
<table><tr><th>Exp.</th><th>Objeto</th><th>Proced.</th><th class="r">Importe</th><th>Adjudicatario</th><th>Estado</th></tr>
@@FROWN@@
</table>

<div class="src">Fuentes: INE · Cifras oficiales de población de los municipios españoles (Revisión del Padrón Municipal), serie 1996-2025 (1997 no publicado; 1996 a 1 de mayo). Portal de Transparencia del Ayuntamiento de Lorca (transparencia.lorca.es): relaciones de contratos menores (PDF trimestrales) y contratos formales. Coordenadas y códigos: © OpenStreetMap (ref:ine) · Overpass. Análisis (troceado, concentración) calculado sobre esos datos oficiales. Sin datos inventados. Nota: los contratos menores se publican en PDF trimestral; el parseo captura el grueso de las filas con formato de importe (€), no el 100%.</div>
</div>
<script>
var mapa=L.map('mapa',{scrollWheelZoom:false}).setView([37.68,-1.70],11);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(mapa);
L.circleMarker([37.695,-1.705],{radius:10,color:'#ef4444',fillColor:'#ef4444',fillOpacity:.8,weight:1}).addTo(mapa).bindPopup('<b>Lorca</b><br>@@P25@@ hab (2025)');
</script>
</body></html>"""

TOKENS = {"@@P25@@": fmt_e(p25), "@@P96@@": fmt_e(p96), "@@SIGN@@": "pos" if var >= 0 else "neg",
          "@@VAR@@": ("+" if var >= 0 else "") + str(var), "@@RANK@@": str(rank_murcia),
          "@@NMEN@@": str(len(m)), "@@GASTO@@": fmt_e(total_gasto), "@@NFOR@@": str(len(formales)),
          "@@CONC@@": ("%.1f%%" % (gasto_top5 / total_gasto * 100)) if total_gasto else "—",
          "@@ALERTA@@": alerta, "@@TROWN@@": row_top_num, "@@IROWN@@": row_top_imp,
          "@@FROWN@@": row_form, "@@COD@@": cata[0] if cata else "30024",
          "@@RNET@@": fmt_e(renta["municipios"]["Lorca"].get("Renta neta media por persona", {}).get("2022", 0)),
          "@@RHOG@@": fmt_e(renta["municipios"]["Lorca"].get("Renta neta media por hogar", {}).get("2022", 0)),
          "@@RMED@@": fmt_e(renta["municipios"]["Lorca"].get("Mediana de la renta por unidad de consumo", {}).get("2022", 0)),
          "@@RPROV@@": fmt_e(renta["municipios"]["Murcia"].get("Renta neta media por persona", {}).get("2022", 0))}
html = HTML
for k, v in TOKENS.items():
    html = html.replace(k, str(v))

with open("dashboard/ficha_lorca.html", "w", encoding="utf-8") as f:
    f.write(html)

# resumen para el mapa (panel lateral)
intel = {
    "n": "Lorca", "p25": fmt_e(p25), "var": ("+" if var >= 0 else "") + str(var),
    "rank": rank_murcia, "nmen": len(m), "gasto": fmt_e(total_gasto), "nfor": len(formales),
    "conc": ("%.1f" % (gasto_top5 / total_gasto * 100)) if total_gasto else "—",
    "alerta": [{"n": r, "c": n} for r, n in flag[:5]],
    "renta": {
        "neta_persona": renta["municipios"]["Lorca"].get("Renta neta media por persona", {}).get("2022"),
        "neta_hogar": renta["municipios"]["Lorca"].get("Renta neta media por hogar", {}).get("2022"),
        "mediana_uc": renta["municipios"]["Lorca"].get("Mediana de la renta por unidad de consumo", {}).get("2022"),
        "murcia_capital": renta["municipios"]["Murcia"].get("Renta neta media por persona", {}).get("2022"),
        "anyo": 2022,
    },
    "top": [{"n": r, "c": len(items), "imp": fmt_e(sum(x["importe"] for x in items))} for r, items in top_num[:8]],
}
with open("dashboard/data/lorca_intel.json", "w", encoding="utf-8") as f:
    json.dump(intel, f, ensure_ascii=False)
print("lorca_intel.json guardado")

